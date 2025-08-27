# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_all

# Add the src directory to the path
src_path = os.path.join(os.path.dirname(os.path.abspath('.')), 'src')

# Collect all data and hidden imports for scapy
datas_scapy, binaries_scapy, hiddenimports_scapy = collect_all('scapy')

# Collect all data and hidden imports for PyQt5
datas_pyqt5, binaries_pyqt5, hiddenimports_pyqt5 = collect_all('PyQt5')

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=binaries_scapy + binaries_pyqt5,
    datas=datas_scapy + datas_pyqt5,
    hiddenimports=[
        # PyQt5 modules
        'PyQt5.QtWidgets',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        # Scapy modules
        'scapy.all',
        'scapy.layers.inet',
        'scapy.sendrecv',
        # System modules
        'psutil',
        'datetime',
        'platform', 
        'socket',
        'threading',
        'winreg',
        # Our local modules
        'gui.main_window',
        'gui.worker',
        'gui.alerts',
        'core.config',
        'core.logger',
        'core.scanner_engine',
        'core.utils',
        'scanner.network_discovery',
        'scanner.tcp_scanner',
        'scanner.udp_scanner',
        'scanner.banner_grabber',
        'protection.firewall_manager',
        'protection.hosts_editor',
    ] + hiddenimports_scapy + hiddenimports_pyqt5,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'win10toast',  # Excluded due to WPARAM/LRESULT errors
        'tkinter',     # Not used
        'matplotlib',  # Not used
        'numpy',       # Not used
        'pandas',      # Not used
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='doormaNet',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True if you want console output for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # No icon for now - requires PIL for custom icons
)
