from scapy.all import ARP, Ether, srp

def discover_hosts(network_range):
    """
    Discovers active hosts on the local network using an ARP scan.
    
    Args:
        network_range (str): The network range in CIDR notation (e.g., '192.168.1.0/24').
        
    Returns:
        A list of dictionaries, where each dictionary contains the 'ip' and 'mac' of a discovered host.
    """
    arp_request = ARP(pdst=network_range)

    broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
    arp_request_broadcast = broadcast / arp_request
    answered_list = srp(arp_request_broadcast, timeout=1, verbose=False)[0]

    clients_list = []
    for element in answered_list:
        clients_dict = {"ip": element[1].psrc, "mac": element[1].hwsrc}
        clients_list.append(clients_dict)
    return clients_list

if __name__ == "__main__":
    network = "192.168.56.1/24"
    print(f"Discovering hosts on {network}...")

    discovered_devices = discover_hosts(network)

    if discovered_devices:
        print("Available devices in the network:")
        print("IP" + " " *18 + "MAC")
        for client in discovered_devices:
            print("{:16}    {}".format(client['ip'], client['mac']))
    else:
        print("[-] No devices found.")