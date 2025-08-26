import socket
from core import config
from datetime import datetime

def scan_port(target_ip, port):
    """
    Scans a single port on a target IP.
    Returns True if the port is open, False otherwise.
    """
    try:
        # 1. Create a new socket object using IPv4 and TCP protocols.
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # 2. Set a 1-second timeout to avoid getting stuck on a non-responsive port.
        sock.settimeout(config.TCP_TIMEOUT)
        
        # 3. Attempt to connect. connect_ex() returns 0 on success.
        result = sock.connect_ex((target_ip, port))
        
        # 4. Check the result of the connection attempt.
        if result == 0:
            return True # Port is open
        else:
            return False # Port is closed
            
    except socket.error as e:
        # Handle potential network errors gracefully.
        print(f"Socket error while scanning {target_ip}:{port} - {e}")
        return False
        
    finally:
        # 5. Ensure the socket is always closed to release resources.
        sock.close()

# --- Example Usage (for testing this file directly) ---
if __name__ == "__main__":
    target = "127.0.0.1" # Scan your local machine (localhost)
    print(f"Scanning target: {target}")
    start_time = datetime.now()

    # Scan the first 1024 ports, which are the most common service ports.
    for p in range(1, 1025):
        if scan_port(target, p):
            print(f"Port {p} is open")

    end_time = datetime.now()
    print(f"Scan completed in: {end_time - start_time}")