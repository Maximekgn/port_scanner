import subprocess
import platform
import ipaddress
import socket
from concurrent.futures import ThreadPoolExecutor
from rich.console import Console
from rich.table import Table
from rich.progress import track

# Initialize Rich console for stylized display
console = Console()

# Detect OS to adapt ping command
is_windows = platform.system().lower() == "windows"

# Ports to check (add ports according to your needs)
PORTS_TO_CHECK = [22, 80, 443, 8080, 3306]

def get_local_network():
    """Gets the local IP address and returns the CIDR of the local network."""
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    ip_parts = local_ip.split('.')
    return f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.0/24"

def ping(ip):
    """Pings an IP address to check if it's active."""
    cmd = ["ping", "-n", "1", "-w", "300", str(ip)] if is_windows else ["ping", "-c", "1", "-W", "1", str(ip)]
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, universal_newlines=True)
        if "TTL=" in output or "ttl=" in output:
            return str(ip)
    except subprocess.CalledProcessError:
        return None

def check_ports(ip):
    """Checks for open ports on an IP address."""
    open_ports = []
    for port in PORTS_TO_CHECK:
        try:
            sock = socket.create_connection((str(ip), port), timeout=1)
            open_ports.append(port)
            sock.close()
        except (socket.timeout, socket.error):
            pass
    return open_ports

def scan_network(cidr):
    """Scans the network and returns active IPs."""
    network = ipaddress.ip_network(cidr, strict=False)
    active_ips = []

    console.print(f"[bold cyan]Scanning network {cidr}...[/bold cyan]\n")
    with ThreadPoolExecutor(max_workers=100) as executor:
        for result in track(executor.map(ping, network.hosts()), total=network.num_addresses - 2, description="Scanning..."):
            if result:
                active_ips.append(result)
    return active_ips

def show_results(ip_list):
    """Displays results in a Rich table."""
    table = Table(title="Active IPs and Open Ports", header_style="bold magenta")
    table.add_column("IP Address", style="green")
    table.add_column("Open Ports", style="bold yellow")

    for ip in ip_list:
        open_ports = check_ports(ip)
        if open_ports:
            table.add_row(ip, ", ".join(map(str, open_ports)))
        else:
            table.add_row(ip, "None")

    console.print(table)

if __name__ == "__main__":
    console.print("welcome to the network scanner")
    console.print("do you want to add a custom port to check?")
    custom_port = input("Enter the port number: ")
    if custom_port:
        PORTS_TO_CHECK.append(int(custom_port))
    subnet = get_local_network()
    ips = scan_network(subnet)
    show_results(ips)
