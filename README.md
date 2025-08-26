DoormaNet
=========

A simple network scanner with a PyQt5 GUI. It discovers devices via ARP, scans TCP ports, attempts banner grabbing, and includes basic Windows protections (block IP via firewall, block domains via hosts file).

Requirements
- Python 3.9+ (Windows recommended)
- Administrator privileges for firewall and hosts edits

Install
1) Create/activate a virtual environment
2) Install dependencies

Run (development)
Use Python directly:
- python -m pip install -r requirements.txt
- python -m pip install -e .
- python -m main

Or use the console entry point after editable install:
- doormanet

Notes
- ARP discovery and low-level networking may require running in an elevated shell.
- Firewall IP blocking and hosts edits require Run as administrator.
- On first run, the target network is auto-detected; you can override in the UI.

Build (optional)
If you want a single-file exe using PyInstaller, run from an elevated terminal:
- pyinstaller --noconfirm --windowed --name DoormaNet --add-data "assets;assets" src/main.py

Troubleshooting
- If scapy ARP returns nothing, try disabling your VPN, or run as admin.
- If firewall rule creation fails, ensure the shell is elevated.
- If UI doesn’t start, verify PyQt5 and that you’re using the right Python.
