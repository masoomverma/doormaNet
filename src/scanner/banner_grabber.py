import socket
from core import config

def grab_banner(target_ip, port):
    """
    Connects to a port and grabs the service banner.

    Args:
        target_ip (str): The IP address of the target.
        port (int): The port number to connect to.

    Returns:
        The service banner as a string, or None if it fails.
    """
    try:
        sock = socket.socket()
        sock.settimeout(config.BANNER_TIMEOUT)
        sock.connect((target_ip, port))
        # Try a simple HTTP request first; many services reply with a banner or error
        sock.sendall(b"GET / HTTP/1.0\r\nHost: %b\r\n\r\n" % target_ip.encode())
        banner = sock.recv(1024)
        return banner.decode('utf-8', errors='ignore').strip() or None
    
    except Exception as e:
        return None
    
    finally:
        sock.close()


if __name__ == "__main__":
    target_ip = "192.168.1.1"
    port = 80

    print(f"Grabbing banner from {target_ip}:{port}")
    banner = grab_banner(target_ip, port)
    
    if banner:
        print(f"--- Banner ---")
        print(banner)
        print(f"--------------")
    else:
        print("[-] Could not retrieve banner.")
