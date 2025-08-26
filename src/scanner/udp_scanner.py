# src/scanner/udp_scanner.py

import socket

def scan_udp_port(target_ip, port, timeout=2):
    """
    Scans a single UDP port on a target IP.
    Returns True if the port is likely open or filtered, False if it's closed.
    """
    try:
        # Create a UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        
        # Send an empty UDP packet to the target port
        sock.sendto(b'', (target_ip, port))
        
        # Listen for a response. For UDP, any response indicates the port is open.
        # However, it's more common to get no response for an open port.
        # The real test is waiting for an ICMP "port unreachable" error,
        # which a standard UDP socket cannot receive. 
        # A timeout here implies the port is open or filtered by a firewall.
        sock.recvfrom(1024)
        return True # A response was received, so port is open

    except socket.timeout:
        # If we time out, no "port unreachable" message was received.
        # This means the port is either open or firewalled.
        return True 
        
    except socket.error as e:
        # An ICMP "port unreachable" error will often be caught here on Windows
        # The error code for this is typically 10054
        if e.errno == 10054:
            return False # Port is closed
        print(f"Socket error on port {port}: {e}")
        return False
        
    finally:
        sock.close()

# --- Example Usage (for testing this file directly) ---
if __name__ == "__main__":
    # Note: UDP scanning is significantly slower and less reliable than TCP.
    # Common UDP ports: 53 (DNS), 123 (NTP), 161 (SNMP)
    target = "127.0.0.1"
    print(f"Scanning UDP ports on target: {target}")

    for p in [53, 123, 161, 500]:
        print(f"Scanning port {p}...")
        if scan_udp_port(target, p):
            print(f"  Port {p} is open or filtered")
        else:
            print(f"  Port {p} is closed")