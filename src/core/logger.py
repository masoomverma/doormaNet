# src/core/logger.py

import os
from datetime import datetime

LOGS_DIR = "logs"

def save_log(results):
    """
    Formats the scan results and saves them to a timestamped file in the logs directory.
    """
    if not results:
        # Don't save a log if there were no results
        return

    # Ensure the logs directory exists
    os.makedirs(LOGS_DIR, exist_ok=True)

    # Create a unique filename with the current timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = os.path.join(LOGS_DIR, f"scan_log_{timestamp}.txt")

    try:
        with open(filename, 'w') as f:
            f.write(f"Scan Results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*40 + "\n\n")

            for ip, ports in results.items():
                f.write(f"Host: {ip}\n")
                for port, banner in ports.items():
                    banner_info = banner if banner != "N/A" else "No banner retrieved"
                    f.write(f"  - Port {port:<5}: {banner_info}\n")
                f.write("\n")
        
        print(f"[+] Scan log saved to: {filename}")

    except IOError as e:
        print(f"[!] Error: Could not save log file. Reason: {e}")