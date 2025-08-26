# src/core/config.py

# --- Scanner Settings ---
# The range of TCP ports to scan on each host.
PORTS_TO_SCAN = range(1, 1025)

# The number of concurrent threads to use for scanning.
MAX_WORKERS = 50

# --- Timeout Settings (in seconds) ---
TCP_TIMEOUT = 1
UDP_TIMEOUT = 2
BANNER_TIMEOUT = 2

# --- Protection Settings ---
# The IP address to redirect blocked domains to.
HOSTS_REDIRECT_IP = "127.0.0.1"

# --- Alert Settings ---
# Dictionary of known high-risk ports and their services.
CRITICAL_PORTS = {
    21: "FTP (Unencrypted file transfer)",
    23: "Telnet (Unencrypted remote login)",
    25: "SMTP (Unencrypted email sending)",
    110: "POP3 (Unencrypted email receiving)",
    143: "IMAP (Unencrypted email receiving)",
    445: "SMB (Direct file sharing, often targeted by ransomware)",
    3389: "RDP (Remote Desktop, common attack vector)"
}