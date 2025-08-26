import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QTabWidget, QListWidget, QMenu, QMessageBox)
from PyQt5.QtCore import Qt, QThread

# Import local modules
from gui.worker import ScannerWorker
from core import utils
from protection import firewall_manager, hosts_editor
from gui.alerts import AlertDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("doormaNet")
        self.setGeometry(100, 100, 800, 600)
        
        # --- Main Tab Widget ---
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # --- Create Scanner Tab ---
        self.scanner_tab = QWidget()
        self.tabs.addTab(self.scanner_tab, "Network Scanner")
        self.setup_scanner_ui()

        # --- Create Website Blocker Tab ---
        self.blocker_tab = QWidget()
        self.tabs.addTab(self.blocker_tab, "Website Blocker")
        self.setup_blocker_ui()

        # --- Finalize Functionality ---
        self.thread = None
        self.worker = None
        self.auto_fill_target()

    def setup_scanner_ui(self):
        """Creates the UI for the Network Scanner tab."""
        main_layout = QVBoxLayout(self.scanner_tab)
        
        controls_layout = QHBoxLayout()
        target_label = QLabel("Target Network:")
        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("e.g., 192.168.1.0/24")
        self.scan_button = QPushButton("Start Scan")
        
        controls_layout.addWidget(target_label)
        controls_layout.addWidget(self.target_input)
        controls_layout.addWidget(self.scan_button)

        self.results_table = QTableWidget()
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels(["IP Address", "Port", "Service/Banner"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.results_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.results_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.results_table.customContextMenuRequested.connect(self.show_context_menu)

        main_layout.addLayout(controls_layout)
        main_layout.addWidget(self.results_table)
        
        self.scan_button.clicked.connect(self.start_scan)

    def setup_blocker_ui(self):
        """Creates the UI for the Website Blocker tab."""
        layout = QVBoxLayout(self.blocker_tab)
        
        controls_layout = QHBoxLayout()
        self.domain_input = QLineEdit()
        self.domain_input.setPlaceholderText("e.g., example.com")
        self.block_button = QPushButton("Block")
        self.unblock_button = QPushButton("Unblock")
        
        controls_layout.addWidget(QLabel("Domain:"))
        controls_layout.addWidget(self.domain_input)
        controls_layout.addWidget(self.block_button)
        controls_layout.addWidget(self.unblock_button)
        
        self.blocked_list = QListWidget()
        
        layout.addLayout(controls_layout)
        layout.addWidget(QLabel("Currently Blocked:"))
        layout.addWidget(self.blocked_list)
        
        self.block_button.clicked.connect(self.handle_block_domain)
        self.unblock_button.clicked.connect(self.handle_unblock_domain)
        self.blocked_list.itemClicked.connect(lambda item: self.domain_input.setText(item.text()))
        
        self.refresh_blocked_list()

    def refresh_blocked_list(self):
        self.blocked_list.clear()
        blocked_domains = hosts_editor.get_blocked_domains()
        for domain in blocked_domains:
            self.blocked_list.addItem(domain)

    def handle_block_domain(self):
        domain = self.domain_input.text().strip()
        if not domain:
            QMessageBox.warning(self, "Input Error", "Please enter a domain name.")
            return
        success, message = hosts_editor.block_domain(domain)
        QMessageBox.information(self, "Result", message)
        if success:
            self.refresh_blocked_list()
            self.domain_input.clear()

    def handle_unblock_domain(self):
        domain = self.domain_input.text().strip()
        if not domain:
            QMessageBox.warning(self, "Input Error", "Please select or enter a domain to unblock.")
            return
        success, message = hosts_editor.unblock_domain(domain)
        QMessageBox.information(self, "Result", message)
        if success:
            self.refresh_blocked_list()
            self.domain_input.clear()

    def auto_fill_target(self):
        detected_range = utils.get_local_network_range()
        self.target_input.setText(detected_range)

    def start_scan(self):
        self.results_table.setRowCount(0)
        self.scan_button.setEnabled(False)
        self.scan_button.setText("Scanning...")
        target = self.target_input.text()
        self.thread = QThread()
        self.worker = ScannerWorker(target)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.scan_finished.connect(self.scan_complete)
        self.worker.result_found.connect(self.add_result_to_table)
        self.worker.critical_finding.connect(self.show_critical_alert)
        self.thread.start()

    def scan_complete(self):
        self.scan_button.setEnabled(True)
        self.scan_button.setText("Start Scan")
        if self.thread is not None:
            self.thread.quit()
            self.thread.wait()

    def add_result_to_table(self, ip, port, banner):
        row_position = self.results_table.rowCount()
        self.results_table.insertRow(row_position)
        self.results_table.setItem(row_position, 0, QTableWidgetItem(ip))
        self.results_table.setItem(row_position, 1, QTableWidgetItem(str(port)))
        self.results_table.setItem(row_position, 2, QTableWidgetItem(banner))

    def show_context_menu(self, position):
        item = self.results_table.itemAt(position)
        if not item:
            return
        selected_ip = self.results_table.item(item.row(), 0).text()
        menu = QMenu()
        block_action = menu.addAction(f"Block IP: {selected_ip}")
        action = menu.exec_(self.results_table.mapToGlobal(position))
        if action == block_action:
            self.block_selected_ip(selected_ip)

    def block_selected_ip(self, ip_address):
        success, message = firewall_manager.block_ip(ip_address)
        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.critical(self, "Error", f"{message}\n\nPlease try running the application 'As Administrator'.")

    def show_critical_alert(self, ip, port, reason):
        """Creates and shows the alert dialog when a critical port is found."""
        dialog = AlertDialog(ip, port, reason, self)
        dialog.exec_()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())