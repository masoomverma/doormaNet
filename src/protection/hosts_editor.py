import os
from core import config
# The path to the hosts file on Windows
HOSTS_FILE_PATH = r"C:\Windows\System32\drivers\etc\hosts"

def get_blocked_domains():
    """Reads the hosts file and returns a list of domains blocked by this tool."""
    blocked = []
    try:
        with open(HOSTS_FILE_PATH, 'r')     as f:
            for line in f.readlines():
                if f"# Blocked by DoormaNet" in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        blocked.append(parts[1])
    except FileNotFoundError:
        pass # File doesn't exist, so no domains are blocked
    return blocked

def block_domain(domain):
    """Adds a domain to the hosts file to block it."""
    try:
        with open(HOSTS_FILE_PATH, 'a') as f:
            f.write(f"\n{config.HOSTS_REDIRECT_IP}\t{domain}\t# Blocked by DoormaNet\n")
        return True, f"Successfully blocked {domain}."
    except PermissionError:
        return False, "Permission denied. Please run as administrator."
    except Exception as e:
        return False, f"An error occurred: {e}"

def unblock_domain(domain):
    """Removes a domain from the hosts file to unblock it."""
    try:
        with open(HOSTS_FILE_PATH, 'r') as f:
            lines = f.readlines()
        
        # Write the file back, excluding the line with the domain to unblock
        with open(HOSTS_FILE_PATH, 'w') as f:
            found = False
            for line in lines:
                if domain in line and "# Blocked by DoormaNet" in line:
                    found = True
                    continue # Skip writing this line to the file
                f.write(line)
        
        if found:
            return True, f"Successfully unblocked {domain}."
        else:
            return False, f"Domain {domain} was not found in the blocklist."

    except PermissionError:
        return False, "Permission denied. Please run as administrator."
    except Exception as e:
        return False, f"An error occurred: {e}"