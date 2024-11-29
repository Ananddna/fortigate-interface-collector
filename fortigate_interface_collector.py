import pandas as pd
import logging
from netmiko import ConnectHandler
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import re
import csv
import sys
import os  # Added to use environment variables

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('interface_status.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FortiInterfaceCollector:
    def __init__(self, credentials, timeout=30):
        self.credentials = credentials
        self.timeout = timeout
        self.successful_devices = 0
        self.failed_devices = 0

    def connect_to_device(self, device):
        """Connect to FortiGate device and collect interface data."""
        device_info = {
            'device_type': 'fortinet',
            'ip': device['IP_Address'],
            'username': self.credentials[0]['username'],
            'password': self.credentials[0]['password'],
            'timeout': self.timeout
        }

        try:
            with ConnectHandler(**device_info) as conn:
                config = conn.send_command('show system interface', expect_string=r'#')
                physical = conn.send_command('get system interface physical', expect_string=r'#')
                netlink = conn.send_command('diagnose netlink interface list', expect_string=r'#')
                
                return {
                    'hostname': device['Caption'],
                    'ip': device['IP_Address'],
                    'success': True,
                    'config': config,
                    'physical': physical,
                    'netlink': netlink
                }
        except Exception as e:
            logger.error(f"Error connecting to {device['Caption']}: {str(e)}")
            return {
                'hostname': device['Caption'],
                'ip': device['IP_Address'],
                'success': False,
                'error': str(e)
            }

    def get_netlink_interface_block(self, interface_name, netlink_output):
        """Extract the netlink block for a specific interface."""
        lines = netlink_output.split('\n')
        interface_block = []
        in_interface = False

        for line in lines:
            if f'if={interface_name} ' in line or f'if={interface_name}@' in line:
                in_interface = True
                interface_block = [line]
            elif in_interface and line.strip():
                interface_block.append(line)
            elif in_interface and not line.strip():
                break

        return ' '.join(interface_block) if interface_block else ''

    def is_physical_interface_active(self, interface_name, status_in_physical, netlink_output):
        """Determine if a physical interface is active."""
        if status_in_physical.lower() != 'up':
            return False

        block_text = self.get_netlink_interface_block(interface_name, netlink_output)
        no_carrier = 'no_carrier' in block_text
        return not no_carrier

    def is_vlan_interface_active(self, interface_name, netlink_output):
        """Determine if a VLAN interface is active."""
        block_text = self.get_netlink_interface_block(interface_name, netlink_output)
        flags_up = 'flags=up' in block_text
        state_start_present = 'state=start present' in block_text
        run_state = 'run' in block_text
        return flags_up and state_start_present and run_state

    def is_aggregate_interface_active(self, interface_name, netlink_output):
        """Determine if an aggregate interface is active."""
        block_text = self.get_netlink_interface_block(interface_name, netlink_output)
        flags_up = 'flags=up' in block_text
        master = 'master' in block_text
        return flags_up and master

    def is_special_interface_active(self, interface_name, netlink_output):
        """Determine if a special interface (SSL VPN, tunnel) is active."""
        block_text = self.get_netlink_interface_block(interface_name, netlink_output)
        flags_up = 'flags=up' in block_text
        return flags_up

    def parse_interface_data(self, data):
        """Parse interface data and determine active status."""
        interfaces = {}
        current_interface = None

        # First pass: Basic interface info
        for line in data['config'].splitlines():
            line = line.strip()
            if line.startswith('edit'):
                match = re.search(r'edit\s+"?([^"\s]+)"?', line)
                if match:
                    current_interface = match.group(1)
                    interfaces[current_interface] = {
                        'name': current_interface,
                        'alias': '',
                        'status': '',
                        'type': '',
                        'ip_address': '',
                        'is_active': False,
                        'parent': None,
                        'members': []
                    }
            elif current_interface:
                if 'set alias' in line:
                    match = re.search(r'set alias\s+"?([^"]+)"?', line)
                    if match:
                        interfaces[current_interface]['alias'] = match.group(1)
                elif 'set ip' in line and 'set ips' not in line:
                    match = re.search(r'set ip (\d+\.\d+\.\d+\.\d+\s+\d+\.\d+\.\d+\.\d+)', line)
                    if match:
                        interfaces[current_interface]['ip_address'] = match.group(1)
                elif 'set type' in line:
                    match = re.search(r'set type (\w+)', line)
                    if match:
                        interfaces[current_interface]['type'] = match.group(1)
                elif 'set interface' in line:
                    match = re.search(r'set interface\s+"?([^"]+)"?', line)
                    if match:
                        interfaces[current_interface]['parent'] = match.group(1)
                elif 'set member' in line:
                    # Correctly parse multiple members
                    members = re.findall(r'"([^"]+)"', line)
                    interfaces[current_interface]['members'] = members
                elif 'set vlanid' in line:
                    # Set interface type to 'vlan' when 'set vlanid' is present
                    interfaces[current_interface]['type'] = 'vlan'

        # Set default type to 'physical' if not specified
        for interface in interfaces.values():
            if not interface['type']:
                interface['type'] = 'physical'

        # Second pass: Physical status
        for line in data['physical'].splitlines():
            if '==[' in line:
                match = re.search(r'==\[([^\]]+)\]', line)
                if match:
                    current_interface = match.group(1)
            elif current_interface and current_interface in interfaces:
                if 'status:' in line:
                    status_match = re.search(r'status:\s+(\w+)', line)
                    if status_match:
                        status = status_match.group(1)
                        interfaces[current_interface]['status'] = status

        # Process interfaces in specific order
        interface_order = ['physical', 'aggregate', 'vlan', 'tunnel', 'ssl-tunnel', 'switch', 'loopback']
        # Create a sorted list of interfaces based on the desired order
        sorted_interfaces = []
        for int_type in interface_order:
            sorted_interfaces.extend(
                [name for name, iface in interfaces.items() if iface['type'] == int_type]
            )
        # Add any interfaces that didn't match the predefined types
        sorted_interfaces.extend(
            [name for name in interfaces.keys() if name not in sorted_interfaces]
        )

        # Third pass: Determine is_active based on the rules
        for name in sorted_interfaces:
            interface = interfaces[name]
            if interface['type'] == 'physical':
                # For physical interfaces
                status = interface.get('status', '').lower()
                is_active = self.is_physical_interface_active(
                    name, status, data['netlink']
                )
                interface['is_active'] = is_active

            elif interface['type'] == 'aggregate':
                # For aggregate interfaces
                is_active = self.is_aggregate_interface_active(name, data['netlink'])
                # At least one member port is up
                has_active_member = any(
                    interfaces.get(member, {}).get('is_active', False) 
                    for member in interface['members']
                )
                interface['is_active'] = is_active and has_active_member

            elif interface['type'] == 'vlan':
                # For VLAN interfaces
                parent = interfaces.get(interface['parent'])
                parent_active = parent and parent.get('is_active', False)
                netlink_active = self.is_vlan_interface_active(name, data['netlink'])
                interface['is_active'] = parent_active and netlink_active

            elif interface['type'] in ['tunnel', 'ssl-tunnel']:
                # For special interfaces
                is_active = self.is_special_interface_active(name, data['netlink'])
                interface['is_active'] = is_active

            elif interface['type'] in ['management', 'mgmt', 'ha']:
                # For management interfaces, treated as physical
                status = interface.get('status', '').lower()
                interface['is_active'] = (status == 'up')

            else:
                # Default case for other interface types
                interface['is_active'] = False

        return interfaces

    def collect_active_interfaces(self, devices, max_workers=5, max_devices=None):
        """Collect interface data from multiple devices."""
        if max_devices:
            devices = devices[:max_devices]

        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_device = {
                executor.submit(self.connect_to_device, device): device 
                for device in devices
            }
            
            for future in as_completed(future_to_device):
                device = future_to_device[future]
                try:
                    result = future.result()
                    if result['success']:
                        interfaces = self.parse_interface_data(result)
                        for name, data in interfaces.items():
                            display_name = data['alias'] if data['alias'] else name
                            results.append({
                                'Device': device['Caption'],
                                'Interface_Name': display_name,
                                'Original_Name': name,
                                'Status': data['status'],
                                'Is_Active': data['is_active'],
                                'Type': data['type'],
                                'IP_Address': data['ip_address'],
                                'Parent_Interface': data['parent'] if data['parent'] else ''
                            })
                        self.successful_devices += 1
                    else:
                        self.failed_devices += 1
                except Exception as e:
                    self.failed_devices += 1
                    logger.error(f"Error processing {device['Caption']}: {str(e)}")

        return results

def main():
    try:
        # Replace with a placeholder or environment variable
        inventory_file = os.getenv('INVENTORY_FILE', 'path_to_inventory.csv')
        df = pd.read_csv(inventory_file)
    except Exception as e:
        logger.error(f"Error reading inventory: {str(e)}")
        sys.exit(1)

    # Use environment variables for credentials
    credentials = [
        {
            'username': os.getenv('DEVICE_USERNAME', 'your_username'),
            'password': os.getenv('DEVICE_PASSWORD', 'your_password')
        }
        # You can add more credential sets if needed
    ]

    collector = FortiInterfaceCollector(credentials)

    try:
        results = collector.collect_active_interfaces(
            df.to_dict('records'),
            max_workers=100,
            # max_devices=None
        )

        if results:
            # Save to CSV
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'interface_status_{timestamp}.csv'
            
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = results[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)
            
            # Group and display results by device
            devices = {}
            for result in results:
                device = result['Device']
                if device not in devices:
                    devices[device] = []
                devices[device].append(result)

            print("\nActive Interfaces Summary:")
            for device in sorted(devices.keys()):
                print(f"\n{device}:")
                # Sort interfaces within device
                sorted_interfaces = sorted(devices[device], 
                                        key=lambda x: x['Interface_Name'].lower())
                for interface in sorted_interfaces:
                    status_symbol = '✓' if interface['Is_Active'] else '✗'
                    print(f"{status_symbol} {interface['Interface_Name']}")
            print(f"\nResults saved to: {output_file}")
            print(f"Successful devices: {collector.successful_devices}")
            print(f"Failed devices: {collector.failed_devices}")

    except Exception as e:
        logger.error(f"Error in main process: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
