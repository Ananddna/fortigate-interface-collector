# FortiGate Firewall Interface Status Collector

## Overview

This Python script connects to FortiGate firewalls to collect interface statuses and analyze interface activity. The goal is to help network engineers easily monitor and troubleshoot devices by providing detailed information about physical, VLAN, aggregate, and other types of interfaces.

## Features

- **Interface Data Collection**: Retrieves interface information from FortiGate firewalls, including configuration, physical status, and network link details.
- **Multithreading**: Utilizes multithreading to collect data from multiple devices concurrently, improving efficiency.
- **Supports Various Interface Types**: Analyzes physical, VLAN, aggregate, SSL VPN, and management interfaces for activity status.
- **CSV Output**: Outputs interface status to a CSV file for easy review and reporting.

## Requirements

- Python 3.8+
- Libraries: 
  - `netmiko`
  - `pandas`
  - `concurrent.futures`

Install the required dependencies using:

```bash
pip install -r requirements.txt
```

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/fortigate-interface-collector.git
   cd fortigate-interface-collector
   ```

2. **Create a Virtual Environment (optional)**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Prepare Inventory File**

   Ensure you have a CSV file (`consolidated_inventory_firewall.csv`) with the following format:

   ```csv
   Device_Name,IP_Address,Device_Type
   FortiGate1,192.168.1.1,fortinet
   FortiGate2,192.168.1.2,fortinet
   ```

2. **Update Credentials**

   Update the `credentials` list in the script with your FortiGate login details. Replace sensitive information with your own credentials.

3. **Run the Script**

   ```bash
   python fortigate_interface_collector.py
   ```

4. **Output**

   The script generates a CSV file (`interface_status_<timestamp>.csv`) that contains the interface status information for all the devices.

## Example Output

The output CSV file will have columns like:

- **Device**: Device name
- **Interface_Name**: Display name of the interface
- **Original_Name**: Original interface name
- **Status**: Interface status (up/down)
- **Is_Active**: Boolean indicating whether the interface is active
- **Type**: Interface type (physical, VLAN, etc.)
- **IP_Address**: Interface IP address
- **Parent_Interface**: Parent interface if applicable

## Logging

Logs are generated in the `interface_status.log` file, capturing the connection status for each device and any errors encountered.

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

## Contributing

Contributions are welcome! Please fork the repository, create a branch, and submit a pull request for any improvements or bug fixes.

## Future Improvements

- **Scalability**: Enhance the script to support larger environments with hundreds of devices.
- **Visualization**: Add data visualization to monitor interface activity over time.
- **Alerting**: Integrate with a notification system to alert on critical interface status changes.

## Contact

For any questions or issues, please open an issue on GitHub.
