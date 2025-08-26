# src/gui/worker.py

from PyQt5.QtCore import QObject, pyqtSignal
from core.scanner_engine import run_full_scan
from core import config

class ScannerWorker(QObject):
    """
    A worker object that runs the scan in a separate thread.
    Emits signals to communicate with the main GUI thread.
    """
    result_found = pyqtSignal(str, int, str) # ip, port, banner
    scan_finished = pyqtSignal()
    status_update = pyqtSignal(str)
    critical_finding = pyqtSignal(str, int, str) # ip, port, reason
    
    def __init__(self, network_range):
        super().__init__()
        self.network_range = network_range

    def run(self):
        """Starts the scan and emits signals for results."""
        self.status_update.emit(f"Discovering hosts on {self.network_range}...")
        results = run_full_scan(self.network_range)
        
        self.status_update.emit("Scan finished. Populating results...")
        for ip, ports in results.items():
            for port, banner in ports.items():
                # Emit the standard result for the table
                self.result_found.emit(ip, port, banner)
                
                # Check if the found port is in our critical list from the config file
                if port in config.CRITICAL_PORTS:
                    reason = config.CRITICAL_PORTS[port]
                    # If it is, emit the special signal for the alert pop-up
                    self.critical_finding.emit(ip, port, reason)

        self.scan_finished.emit()