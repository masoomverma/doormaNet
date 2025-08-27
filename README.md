DoormaNet
=========

A professional network security and monitoring application with an elegant PyQt5 GUI. Features comprehensive network discovery, port scanning, banner grabbing, website blocking with timestamp tracking, and Windows firewall integration for complete network protection.

## Features

- **Network Scanner**: ARP-based device discovery with TCP/UDP port scanning
- **Website Blocker**: Domain blocking via hosts file with datetime tracking
- **System Notifications**: Native Windows notifications with theme-aware colors
- **Firewall Integration**: IP blocking through Windows Firewall rules
- **Professional UI**: Modern interface with Segoe UI fonts and dark/light theme support
- **System Information**: Real-time display of network and system details

## Requirements

- Python 3.9+ (Windows 10/11 recommended)
- Administrator privileges for firewall and hosts file modifications
- PyQt5 for the graphical interface
- Scapy for network operations

## Quick Start

### Option 1: Use Pre-built Executable
Download and run `doormaNet.exe` (requires administrator privileges for full functionality)

### Option 2: Development Setup
1. Create and activate a virtual environment:
   ```powershell
   python -m venv .lib
   .lib\Scripts\Activate.ps1
   ```

2. Install dependencies:
   ```powershell
   python -m pip install -r requirements.txt
   python -m pip install -e .
   ```

3. Run the application:
   ```powershell
   python src/main.py
   ```
   Or use the console entry point:
   ```powershell
   doormanet
   ```

## Building Executable

To create a standalone executable using PyInstaller:

```powershell
# Ensure you're in an elevated PowerShell and have activated the virtual environment
pyinstaller --clean doormanet.spec
```

The executable will be created in the `dist` folder (~72MB).

## Usage Notes

- **Administrator Rights**: Required for firewall rules and hosts file modifications
- **Network Discovery**: ARP scanning may require elevated privileges or VPN disconnection
- **Website Blocking**: Domains are blocked via hosts file with automatic timestamp logging
- **Notifications**: Uses native Windows system tray notifications
- **Theme Support**: Automatically adapts to Windows light/dark theme settings

## Project Structure

```
doormaNet/
├── src/
│   ├── main.py              # Application entry point
│   ├── core/                # Core functionality (config, logging, scanning)
│   ├── gui/                 # PyQt5 interface components
│   ├── scanner/             # Network scanning modules
│   └── protection/          # Firewall and hosts file management
├── assets/                  # Icons and images
├── logs/                    # Application logs
├── doormanet.spec          # PyInstaller configuration
└── requirements.txt        # Python dependencies
```

## Troubleshooting

- **No ARP Results**: Disable VPN or run as administrator
- **Firewall Errors**: Ensure PowerShell is running as administrator
- **UI Issues**: Verify PyQt5 installation and Python version compatibility
- **Notifications**: If system notifications don't appear, check Windows notification settings
- **Build Issues**: Ensure all dependencies are installed and use the provided spec file

## Development

The application uses a modular architecture with separate components for scanning, protection, and GUI management. All UI components follow professional design principles with consistent fonts, spacing, and theme integration.
