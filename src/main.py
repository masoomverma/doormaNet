import sys
import concurrent.futures
from PyQt5.QtWidgets import QApplication

# Import local modules from the project structure
from scanner import network_discovery, tcp_scanner, banner_grabber
from core import utils, logger, config
from gui.main_window import MainWindow

# --- Backend Scanning Engine ---

def scan_host(ip):
    """
    Scans a single host for open ports and banners.
    """
    # This print statement will show progress in the terminal where the app is launched
    print(f"[*] Scanning host: {ip}")
    open_ports = {}
    # Use the port range from the config file
    for port in config.PORTS_TO_SCAN:
        if tcp_scanner.scan_port(ip, port):
            banner = banner_grabber.grab_banner(ip, port)
            # Store the banner if found, otherwise store a default message
            open_ports[port] = banner if banner else "N/A"
    
    return ip, open_ports

def run_full_scan(network_range):
    """
    Orchestrates a full network scan: discovery, port scanning, and banner grabbing.
    This is the main function called by the GUI's worker thread.
    """
    print(f"--- Starting Full Scan on {network_range} ---")
    
    # Step 1: Discover all active hosts on the network
    active_hosts = network_discovery.discover_hosts(network_range)
    if not active_hosts:
        print("\n[!] No active hosts found. Exiting scan.")
        return {}
    
    # Extract just the IP addresses for scanning
    host_ips = [host['ip'] for host in active_hosts]
    print(f"\n[*] Found {len(host_ips)} active hosts: {host_ips}")
    
    all_results = {}
    
    # Step 2: Scan all discovered hosts concurrently using a thread pool for speed
    print("\n--- Scanning Hosts for Open Ports ---")
    # Use the worker count from the config file
    with concurrent.futures.ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as executor:
        # Create a mapping of future tasks to their corresponding IP addresses
        future_to_host = {executor.submit(scan_host, ip): ip for ip in host_ips}
        
        # Process results as they are completed
        for future in concurrent.futures.as_completed(future_to_host):
            ip = future_to_host[future]
            try:
                ip_result, open_ports = future.result()
                if open_ports:
                    all_results[ip_result] = open_ports
            except Exception as exc:
                print(f"[!] Host {ip} generated an exception: {exc}")
                
    print("\n--- Full Scan Complete ---")
    logger.save_log(all_results)
    
    return all_results

# --- Main Application Entry Point ---

if __name__ == "__main__":
    """
    This is the main entry point for the entire DoormaNet application.
    It initializes and runs the PyQt5 GUI.
    """
    # Create the application instance
    app = QApplication(sys.argv)
    
    # Create the main window from our GUI module
    window = MainWindow()
    
    # Show the window to the user
    window.show()
    
    # Start the application's event loop and handle clean exit
    sys.exit(app.exec_())