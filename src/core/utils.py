import psutil
import ipaddress
import socket

def get_local_network_range():
    """
    Automatically detects the local network range using psutil.
    """
    try:
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        for intface, addr_list in addrs.items():
            if stats[intface].isup:
                for addr in addr_list:
                    if addr.family == socket.AF_INET:
                        ip_address = addr.address
                        netmask = addr.netmask
                        if ip_address and netmask and not ip_address.startswith("127."):
                            network = ipaddress.IPv4Network(f"{ip_address}/{netmask}", strict=False)
                            return str(network)
    except Exception as e:
        print(f"Error detecting network: {e}")
    return "192.168.1.0/24"


if __name__ == "__main__":
    detected_range = get_local_network_range()
    print(f"Detected local network range: {detected_range}")