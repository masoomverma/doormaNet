import ctypes
import subprocess
import sys

def is_admin():
    """Check if the script is running with administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def block_ip(ip_address):
    """
    Creates a new inbound rule in Windows Defender Firewall to block an IP address.
    Returns True if successful, False otherwise, along with a message.
    """
    # Note: This command requires administrator privileges to run successfully.
    # Your final .exe will need to be run "As Administrator" for this to work.
    
    rule_name = f"DoormaNet-Block-{ip_address}"
    command = [
        "netsh", "advfirewall", "firewall", "add", "rule",
        f'name={rule_name}',
        "dir=in",
        "action=block",
        f'remoteip={ip_address}'
    ]
    
    try:
        # We use check_output to run the command and capture its output.
        # stderr=subprocess.STDOUT is used to capture error messages as well.
        # shell=True is sometimes needed on Windows for commands like netsh
        subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
        message = f"Successfully created firewall rule to block {ip_address}."
        print(message)
        return True, message
    except subprocess.CalledProcessError as e:
        # This error is often caused by not having administrator privileges.
        error_message = e.output.decode('utf-8', errors='ignore').strip()
        message = f"Error: Could not block {ip_address}. Reason: {error_message}"
        print(message)
        return False, message

# --- Example Usage (requires running this script in an Admin terminal) ---
if __name__ == '__main__':
    # You must run this from a command prompt with "Run as administrator"
    test_ip = "192.168.1.254" # An example IP to block
    print(f"Attempting to block IP: {test_ip}")
    success, msg = block_ip(test_ip)
    print(msg)