FortiGate Firewall Interface Status and Info Collector

Overview

This project is a Python-based tool designed to connect to FortiGate firewalls, collect interface statuses, and analyze interface activity. It helps network engineers easily monitor and troubleshoot devices by providing detailed information about physical, VLAN, aggregate, and tunnel interfaces. The tool supports multithreaded data collection for enhanced efficiency.

Features

Collects Interface Data: Retrieves information about physical, VLAN, aggregate, and tunnel interfaces from FortiGate firewalls.

Multithreaded Collection: Utilizes multithreading to gather data from multiple devices concurrently, improving efficiency.

Analyzes Interface Status: Identifies active versus inactive interfaces, providing a detailed status overview.

Supports Various Interface Types: Handles physical, VLAN, aggregate, and special interfaces (e.g., SSL VPN).

Prerequisites

Python 3.8 or newer.

Access credentials for the FortiGate devices.

Network reachability to FortiGate devices (SSH access).

Installation

Clone the repository:

git clone https://github.com/yourusername/fortigate-interface-collector.git

Navigate to the project directory:

cd fortigate-interface-collector

Create a virtual environment (optional but recommended):

python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

Install dependencies:

pip install -r requirements.txt

Usage

Prepare the Inventory File: Create or modify sample_inventory.csv with your FortiGate device information. The CSV should have columns like Device_Name, IP_Address, and Device_Type.

Example:

Device_Name,IP_Address,Device_Type
FortiGate1,192.168.1.1,fortinet
FortiGate2,192.168.1.2,fortinet

Run the Script:

python fortigate_interface_collector.py

Options:

Customize the credentials list inside the script or adjust the timeout settings as per your network requirements.

Expected Output

CSV File: The script generates a CSV file (interface_status_<timestamp>.csv) that contains information about each interface, including:

Device Name

Interface Name

Status (Up/Down)

IP Address (if applicable)

Interface Type (e.g., physical, VLAN)

Active Status

Logs: The script also creates a log file (interface_status.log) to capture the status of each connection and any errors encountered.

Deployment

Scheduling: To automate interface collection, you can schedule the script using cron on Linux or Task Scheduler on Windows.

Example cron job to run the script daily at 2 AM:

0 2 * * * /usr/bin/python3 /path/to/fortigate_interface_collector.py

Sample Output

The output CSV will look similar to:

Device,Interface_Name,Original_Name,Status,Is_Active,Type,IP_Address,Parent_Interface
FortiGate1,wan1,wan1,up,True,physical,192.168.1.1,
FortiGate1,lan1,lan1,up,True,vlan,192.168.10.1,wan1

License

This project is licensed under the MIT License - see the LICENSE file for details.

Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

Future Improvements

Scalability: Enhance the script to handle a larger number of devices.

Data Visualization: Integrate with tools like Grafana or Power BI for visualizing interface statuses over time.

Email Notifications: Add an option to send email alerts when critical interfaces are down.

Contact

For any questions or issues, please open an issue on the GitHub repository.
