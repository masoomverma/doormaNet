import sys
import os
import threading
import time
import datetime
import platform
import socket
import psutil
try:
    import winreg  # Windows registry access
except ImportError:
    winreg = None

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QTabWidget, QListWidget, QMenu, QMessageBox,
                             QProgressBar, QStatusBar, QFrame, QGroupBox,
                             QGridLayout, QTextEdit, QCheckBox, QListWidgetItem,
                             QSystemTrayIcon, QStyle, QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt, QThread, QTimer, pyqtSignal, QObject, QSize
from PyQt5.QtGui import QFont, QColor

# Import local modules
from gui.worker import ScannerWorker
from core import utils
from protection import firewall_manager, hosts_editor
from gui.alerts import AlertDialog

class NetworkMonitor(QObject):
    """Monitor network changes and trigger scans."""
    network_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.current_network = None
        self.monitoring = False
        
    def start_monitoring(self):
        if not self.monitoring:  # Prevent multiple monitor threads
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_network, daemon=True)
            self.monitor_thread.start()
    
    def stop_monitoring(self):
        self.monitoring = False
        # Give the thread time to stop
        if hasattr(self, 'monitor_thread'):
            try:
                self.monitor_thread.join(timeout=2)
            except:
                pass
    
    def _monitor_network(self):
        while self.monitoring:
            try:
                current_network = utils.get_local_network_range()
                if current_network != self.current_network and current_network:
                    self.current_network = current_network
                    self.network_changed.emit(current_network)
                time.sleep(10)  # Check every 10 seconds
            except Exception:
                pass

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("doormaNet - Network Security Suite")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1200, 800)
        
        # Set application font
        app_font = QFont("Segoe UI", 10)
        QApplication.instance().setFont(app_font)
        
        # Detect and apply system theme
        self.detect_and_apply_theme()
        
        # Initialize network monitor
        self.network_monitor = NetworkMonitor()
        self.network_monitor.network_changed.connect(self.on_network_changed)
        
        # Notification system
        self.notifications = []
        self.max_notifications = 50
        self.all_blocked_domains = []  # Store all blocked domains for filtering
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - doormaNet Network Security Suite")
        
        # Auto-scan settings
        self.auto_scan_enabled = True
        
        # --- Main Tab Widget ---
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.setCentralWidget(self.tabs)

        # --- Create Enhanced Scanner Tab ---
        self.scanner_tab = QWidget()
        self.tabs.addTab(self.scanner_tab, "Network Scanner")
        self.setup_enhanced_scanner_ui()

        # --- Create Enhanced Website Blocker Tab ---
        self.blocker_tab = QWidget()
        self.tabs.addTab(self.blocker_tab, "Website Blocker")
        self.setup_enhanced_blocker_ui()
        
        # --- Create Notifications Tab ---
        self.notifications_tab = QWidget()
        self.tabs.addTab(self.notifications_tab, "Notifications")
        self.setup_notifications_ui()
        
        # --- Create System Info Tab ---
        self.info_tab = QWidget()
        self.tabs.addTab(self.info_tab, "System Info")
        self.setup_info_ui()

        # --- Finalize Functionality ---
        self.thread = None
        self.worker = None
        self.tray_icon = None  # Initialize tray icon
        self.scan_timer = QTimer()
        self.scan_timer.timeout.connect(self.update_scan_progress)
        self.scan_progress = 0
        self.auto_fill_target()
        
        # Start network monitoring
        self.network_monitor.start_monitoring()
        
        # Add initial notification
        self.add_notification("SYSTEM", "Application Started", "doormaNet is now monitoring your network security", "INFO")

    def closeEvent(self, event):
        """Handle application close event with proper cleanup."""
        try:
            # Stop network monitoring
            if hasattr(self, 'network_monitor'):
                self.network_monitor.stop_monitoring()
            
            # Clean up scan timer
            if hasattr(self, 'scan_timer'):
                self.scan_timer.stop()
            
            # Clean up scanning thread
            if self.thread is not None:
                try:
                    if self.worker:
                        self.worker.scan_finished.disconnect()
                        self.worker.result_found.disconnect()
                        self.worker.critical_finding.disconnect()
                        self.worker.status_update.disconnect()
                    self.thread.started.disconnect()
                except:
                    pass
                
                self.thread.quit()
                self.thread.wait(1000)  # Wait max 1 second
                self.thread.deleteLater()
                if self.worker:
                    self.worker.deleteLater()
            
            # Clean up tray icon
            if hasattr(self, 'tray_icon') and self.tray_icon:
                self.tray_icon.hide()
                self.tray_icon.deleteLater()
                
        except Exception as e:
            pass  # Ignore cleanup errors
        
        # Accept the close event
        event.accept()

    def detect_and_apply_theme(self):
        """Detect system theme and apply corresponding theme."""
        try:
            # Try to read Windows theme setting
            if winreg:
                registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                apps_use_light_theme, _ = winreg.QueryValueEx(registry_key, "AppsUseLightTheme")
                winreg.CloseKey(registry_key)
            
                if apps_use_light_theme == 0:
                    self.apply_dark_theme()
                else:
                    self.apply_light_theme()
            else:
                # Default to dark theme if winreg not available
                self.apply_dark_theme()
        except:
            # Default to dark theme if detection fails
            self.apply_dark_theme()
    
    def apply_dark_theme(self):
        """Apply a professional dark theme."""
        self._is_dark_theme = True
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
            }
            QTabWidget::pane {
                border: 1px solid #404040;
                background-color: #2d2d2d;
            }
            QTabBar::tab {
                background-color: #3c3c3c;
                color: #ffffff;
                padding: 14px 28px;
                margin: 1px;
                border: 1px solid #404040;
                border-radius: 4px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
                font-weight: 500;
            }
            QTabBar::tab:selected {
                background-color: #0078d4;
                border-color: #005a9e;
                color: #ffffff;
                font-weight: 600;
            }
            QTabBar::tab:hover {
                background-color: #4a4a4a;
                border-color: #505050;
            }
            QTabBar::tab:!selected:hover {
                background-color: #484848;
            }
            QGroupBox {
                font-family: 'Segoe UI', Arial, sans-serif;
                font-weight: 600;
                font-size: 14px;
                border: 2px solid #404040;
                border-radius: 6px;
                margin-top: 15px;
                padding-top: 15px;
                background-color: #2d2d2d;
                color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
                color: #ffffff;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 14px 28px;
                border-radius: 4px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-weight: 500;
                font-size: 13px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QPushButton:disabled {
                background-color: #404040;
                color: #808080;
            }
            QLineEdit {
                padding: 12px;
                border: 2px solid #404040;
                border-radius: 4px;
                background-color: #3c3c3c;
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #0078d4;
            }
            QTableWidget {
                background-color: #2d2d2d;
                alternate-background-color: #3c3c3c;
                gridline-color: #404040;
                color: #ffffff;
                border: 1px solid #404040;
                border-radius: 4px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 12px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #0078d4;
            }
            QHeaderView::section {
                background-color: #3c3c3c;
                color: #ffffff;
                padding: 14px;
                border: 1px solid #404040;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-weight: 600;
                font-size: 13px;
            }
            QListWidget {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 10px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 12px;
                border-radius: 4px;
                margin: 2px;
            }
            QListWidget::item:selected {
                background-color: #0078d4;
            }
            QListWidget::item:hover {
                background-color: #4a4a4a;
            }
            QProgressBar {
                border: 2px solid #404040;
                border-radius: 4px;
                text-align: center;
                background-color: #3c3c3c;
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-weight: 500;
                font-size: 12px;
                min-height: 25px;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 2px;
            }
            QLabel {
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
            }
            QStatusBar {
                background-color: #3c3c3c;
                color: #ffffff;
                border-top: 1px solid #404040;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
                padding: 6px;
            }
            QTextEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 15px;
                font-family: 'Segoe UI', 'Consolas', monospace;
                font-size: 12px;
                line-height: 1.4;
            }
            QCheckBox {
                color: #ffffff;
                spacing: 10px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #404040;
                border-radius: 3px;
                background-color: #2d2d2d;
            }
            QCheckBox::indicator:checked {
                background-color: #0078d4;
                border-color: #005a9e;
            }
        """)
    
    def apply_light_theme(self):
        """Apply a professional light theme."""
        self._is_dark_theme = False
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
                color: #000000;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
            }
            QTabWidget::pane {
                border: 1px solid #d0d0d0;
                background-color: #f8f8f8;
            }
            QTabBar::tab {
                background-color: #e8e8e8;
                color: #000000;
                padding: 14px 28px;
                margin: 1px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
                font-weight: 500;
            }
            QTabBar::tab:selected {
                background-color: #0078d4;
                color: #ffffff;
                border-color: #005a9e;
                font-weight: 600;
            }
            QTabBar::tab:hover {
                background-color: #d8d8d8;
                border-color: #c0c0c0;
            }
            QTabBar::tab:!selected:hover {
                background-color: #e0e0e0;
            }
            QGroupBox {
                font-family: 'Segoe UI', Arial, sans-serif;
                font-weight: 600;
                font-size: 14px;
                border: 2px solid #d0d0d0;
                border-radius: 6px;
                margin-top: 15px;
                padding-top: 15px;
                background-color: #f8f8f8;
                color: #000000;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
                color: #000000;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 14px 28px;
                border-radius: 4px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-weight: 500;
                font-size: 13px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QPushButton:disabled {
                background-color: #d0d0d0;
                color: #808080;
            }
            QLineEdit {
                padding: 12px;
                border: 2px solid #d0d0d0;
                border-radius: 4px;
                background-color: #ffffff;
                color: #000000;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #0078d4;
            }
            QTableWidget {
                background-color: #ffffff;
                alternate-background-color: #f8f8f8;
                gridline-color: #d0d0d0;
                color: #000000;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 12px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #0078d4;
                color: #ffffff;
            }
            QHeaderView::section {
                background-color: #e8e8e8;
                color: #000000;
                padding: 14px;
                border: 1px solid #d0d0d0;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-weight: 600;
                font-size: 13px;
            }
            QListWidget {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 10px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 12px;
                border-radius: 4px;
                margin: 2px;
            }
            QListWidget::item:selected {
                background-color: #0078d4;
                color: #ffffff;
            }
            QListWidget::item:hover {
                background-color: #e8e8e8;
            }
            QProgressBar {
                border: 2px solid #d0d0d0;
                border-radius: 4px;
                text-align: center;
                background-color: #f8f8f8;
                color: #000000;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-weight: 500;
                font-size: 12px;
                min-height: 25px;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 2px;
            }
            QLabel {
                color: #000000;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
            }
            QStatusBar {
                background-color: #e8e8e8;
                color: #000000;
                border-top: 1px solid #d0d0d0;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
                padding: 6px;
            }
            QTextEdit {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 15px;
                font-family: 'Segoe UI', 'Consolas', monospace;
                font-size: 12px;
                line-height: 1.4;
            }
            QCheckBox {
                color: #000000;
                spacing: 10px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #d0d0d0;
                border-radius: 3px;
                background-color: #ffffff;
            }
            QCheckBox::indicator:checked {
                background-color: #0078d4;
                border-color: #005a9e;
            }
        """)

    def setup_enhanced_scanner_ui(self):
        """Creates an enhanced UI for the Network Scanner tab."""
        main_layout = QVBoxLayout(self.scanner_tab)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header section
        header_group = QGroupBox("Network Scanning Configuration")
        header_group.setFont(QFont("Segoe UI", 13, QFont.Bold))
        header_layout = QGridLayout(header_group)
        
        # Target input section
        target_label = QLabel("Target Network:")
        target_label.setFont(QFont("Segoe UI", 12, QFont.Normal))
        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("e.g., 192.168.1.0/24 or 10.0.0.1-50")
        self.target_input.setFont(QFont("Segoe UI", 12))
        
        # Scan button with enhanced styling
        self.scan_button = QPushButton("Start Network Scan")
        self.scan_button.setMinimumHeight(45)
        self.scan_button.setFont(QFont("Segoe UI", 12, QFont.DemiBold))
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFont(QFont("Segoe UI", 11))
        self.progress_bar.setMinimumHeight(30)
        
        # Status label
        self.scan_status_label = QLabel("Ready to scan")
        self.scan_status_label.setFont(QFont("Segoe UI", 12))
        self.scan_status_label.setStyleSheet("color: #28a745; font-weight: 500;")
        
        header_layout.addWidget(target_label, 0, 0)
        header_layout.addWidget(self.target_input, 0, 1, 1, 2)
        header_layout.addWidget(self.scan_button, 1, 0)
        header_layout.addWidget(self.progress_bar, 1, 1, 1, 2)
        header_layout.addWidget(self.scan_status_label, 2, 0, 1, 3)
        
        # Results section
        results_group = QGroupBox("Scan Results")
        results_group.setFont(QFont("Segoe UI", 13, QFont.Bold))
        results_layout = QVBoxLayout(results_group)
        
        # Enhanced results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["IP Address", "Port", "Service", "Risk Level"])
        
        # Set header font
        header_font = QFont("Segoe UI", 13, QFont.DemiBold)
        self.results_table.horizontalHeader().setFont(header_font)
        
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.results_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.results_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.results_table.customContextMenuRequested.connect(self.show_context_menu)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSortingEnabled(True)
        
        # Results summary
        self.results_summary = QLabel("No scan performed yet")
        self.results_summary.setFont(QFont("Segoe UI", 12))
        self.results_summary.setStyleSheet("color: #6c757d; font-style: italic;")
        
        results_layout.addWidget(self.results_summary)
        results_layout.addWidget(self.results_table)
        
        # Add to main layout
        main_layout.addWidget(header_group)
        main_layout.addWidget(results_group)
        
        # Connect signals
        self.scan_button.clicked.connect(self.start_scan)

    def setup_enhanced_blocker_ui(self):
        """Creates an enhanced UI for the Website Blocker tab."""
        main_layout = QVBoxLayout(self.blocker_tab)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header section
        header_group = QGroupBox("Website Blocking Control")
        header_group.setFont(QFont("Segoe UI", 13, QFont.Bold))
        header_layout = QGridLayout(header_group)
        
        # Domain input section
        domain_label = QLabel("Domain to Block:")
        domain_label.setFont(QFont("Segoe UI", 12, QFont.Normal))
        self.domain_input = QLineEdit()
        self.domain_input.setPlaceholderText("e.g., facebook.com, youtube.com, badsite.com")
        self.domain_input.setFont(QFont("Segoe UI", 12))
        
        # Enhanced buttons
        self.block_button = QPushButton("Block Domain")
        self.block_button.setFont(QFont("Segoe UI", 12, QFont.DemiBold))
        self.block_button.setMinimumHeight(45)
        self.block_button.setStyleSheet("""
            QPushButton {
                background-color: #d83c3c;
                color: white;
                padding: 12px 24px;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover {
                background-color: #c23232;
            }
        """)
        
        self.unblock_button = QPushButton("Unblock Domain")
        self.unblock_button.setFont(QFont("Segoe UI", 12, QFont.DemiBold))
        self.unblock_button.setMinimumHeight(45)
        self.unblock_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 12px 24px;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        
        header_layout.addWidget(domain_label, 0, 0)
        header_layout.addWidget(self.domain_input, 0, 1, 1, 2)
        header_layout.addWidget(self.block_button, 1, 0)
        header_layout.addWidget(self.unblock_button, 1, 1)
        
        # Currently blocked section
        blocked_group = QGroupBox("Currently Blocked Domains")
        blocked_group.setFont(QFont("Segoe UI", 13, QFont.Bold))
        blocked_layout = QVBoxLayout(blocked_group)
        
        # Search box for blocked domains
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        search_label.setFont(QFont("Segoe UI", 12))
        self.blocked_search = QLineEdit()
        self.blocked_search.setFont(QFont("Segoe UI", 12))
        self.blocked_search.setPlaceholderText("Search blocked domains...")
        self.blocked_search.textChanged.connect(self.filter_blocked_list)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.blocked_search)
        
        # Enhanced blocked list
        self.blocked_list = QListWidget()
        self.blocked_list.setMinimumHeight(300)
        self.blocked_list.setFont(QFont("Segoe UI", 12))
        
        # Blocked domains counter
        self.blocked_count_label = QLabel("No domains blocked")
        self.blocked_count_label.setFont(QFont("Segoe UI", 12))
        self.blocked_count_label.setStyleSheet("color: #6c757d; font-style: italic;")
        
        blocked_layout.addWidget(self.blocked_count_label)
        blocked_layout.addLayout(search_layout)
        blocked_layout.addWidget(self.blocked_list)
        
        # Quick actions section
        quick_actions_group = QGroupBox("Quick Actions")
        quick_actions_group.setFont(QFont("Segoe UI", 13, QFont.Bold))
        quick_layout = QHBoxLayout(quick_actions_group)
        
        self.clear_all_button = QPushButton("Clear All Blocks")
        self.clear_all_button.setFont(QFont("Segoe UI", 12, QFont.DemiBold))
        self.clear_all_button.setMinimumHeight(45)
        self.clear_all_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                padding: 12px 24px;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        
        self.refresh_button = QPushButton("Refresh List")
        self.refresh_button.setFont(QFont("Segoe UI", 12, QFont.DemiBold))
        self.refresh_button.setMinimumHeight(45)
        
        quick_layout.addWidget(self.clear_all_button)
        quick_layout.addWidget(self.refresh_button)
        quick_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        # Add to main layout
        main_layout.addWidget(header_group)
        main_layout.addWidget(blocked_group)
        main_layout.addWidget(quick_actions_group)
        
        # Connect signals
        self.block_button.clicked.connect(self.handle_block_domain)
        self.unblock_button.clicked.connect(self.handle_unblock_domain)
        self.clear_all_button.clicked.connect(self.clear_all_blocks)
        self.refresh_button.clicked.connect(self.refresh_blocked_list)
        self.blocked_list.itemClicked.connect(self.on_blocked_item_clicked)
        self.domain_input.returnPressed.connect(self.handle_block_domain)
        
        self.refresh_blocked_list()

    def setup_info_ui(self):
        """Creates a system information tab."""
        main_layout = QVBoxLayout(self.info_tab)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # System info group
        info_group = QGroupBox("System Information")
        info_group.setFont(QFont("Segoe UI", 13, QFont.Bold))
        info_layout = QVBoxLayout(info_group)
        info_layout.setContentsMargins(15, 20, 15, 15)  # Reduced top margin
        
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMinimumHeight(320)  # Slightly reduced
        self.info_text.setMaximumHeight(340)   # Balanced height
        self.info_text.setFont(QFont("Segoe UI", 13))
        self.info_text.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.info_text.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Load system info
        self.load_system_info()
        
        info_layout.addWidget(self.info_text)
        
        # About section
        about_group = QGroupBox("About doormaNet")
        about_group.setFont(QFont("Segoe UI", 13, QFont.Bold))
        about_layout = QVBoxLayout(about_group)
        about_layout.setContentsMargins(15, 20, 15, 15)  # Consistent margins
        
        # About section with scrollable text
        about_text = QTextEdit()
        about_text.setReadOnly(True)
        about_text.setHtml("""
        <div style="font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.4; padding: 10px;">
        
        <h2 style="color: #0078d4; font-size: 18px; font-weight: bold; margin: 0 0 8px 0;">
        doormaNet v1.0
        </h2>
        
        <p style="font-size: 14px; font-weight: 600; margin: 0 0 12px 0; color: #333; text-align: left;">
        A comprehensive network security scanner and protection suite
        </p>
        
        <h3 style="color: #0078d4; font-size: 14px; font-weight: bold; margin: 12px 0 8px 0; text-align: left;">
        Key Features:
        </h3>
        <ul style="margin: 0 0 12px 0; padding-left: 18px; text-align: left;">
            <li style="margin-bottom: 4px; font-size: 12px; line-height: 1.4;">
            <strong>Network Discovery & Port Scanning:</strong> Comprehensive network mapping and vulnerability detection
            </li>
            <li style="margin-bottom: 4px; font-size: 12px; line-height: 1.4;">
            <strong>Website Blocking:</strong> Advanced content filtering via hosts file modification
            </li>
            <li style="margin-bottom: 4px; font-size: 12px; line-height: 1.4;">
            <strong>Firewall Integration:</strong> Seamless integration with Windows Firewall for IP blocking
            </li>
            <li style="margin-bottom: 4px; font-size: 12px; line-height: 1.4;">
            <strong>Real-time Alerts:</strong> Critical security alert system with desktop notifications
            </li>
            <li style="margin-bottom: 4px; font-size: 12px; line-height: 1.4;">
            <strong>Automatic Monitoring:</strong> Network change detection and automatic scanning
            </li>
        </ul>
        
        <h3 style="color: #0078d4; font-size: 14px; font-weight: bold; margin: 12px 0 8px 0; text-align: left;">
        Technical Specifications:
        </h3>
        <ul style="margin: 0 0 12px 0; padding-left: 18px; text-align: left;">
            <li style="margin-bottom: 3px; font-size: 12px; line-height: 1.3;">Built with PyQt5 framework for modern GUI</li>
            <li style="margin-bottom: 3px; font-size: 12px; line-height: 1.3;">Python 3.13+ compatible</li>
            <li style="margin-bottom: 3px; font-size: 12px; line-height: 1.3;">Multi-threaded scanning engine</li>
            <li style="margin-bottom: 3px; font-size: 12px; line-height: 1.3;">Cross-platform compatibility (Windows focus)</li>
            <li style="margin-bottom: 3px; font-size: 12px; line-height: 1.3;">Professional dark/light theme system</li>
        </ul>
        
        <div style="background-color: #f8f9fa; border-left: 4px solid #0078d4; padding: 10px; margin: 12px 0 5px 0; border-radius: 4px; text-align: left;">
            <p style="margin: 0; font-size: 12px; color: #6c757d; line-height: 1.4;">
            <strong style="color: #0078d4;">Developer:</strong> Masoom Verma<br>
            <strong style="color: #0078d4;">Version:</strong> 1.0.0<br>
            <strong style="color: #0078d4;">Release Date:</strong> August 2025<br>
            <strong style="color: #0078d4;">License:</strong> MIT License
            </p>
        </div>
        
        </div>
        """)
        about_text.setFont(QFont("Segoe UI", 13))
        about_text.setMinimumHeight(280)  # Balanced with system info
        about_text.setMaximumHeight(320)  # Reasonable max height
        about_text.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        about_text.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        about_text.setFrameStyle(QTextEdit.NoFrame)  # Remove border for cleaner look
        
        about_layout.addWidget(about_text)
        
        main_layout.addWidget(info_group)
        main_layout.addWidget(about_group)
        
        # No stretch to maintain proper proportions

    def setup_notifications_ui(self):
        """Setup the notifications tab UI with better formatting and layout."""
        layout = QVBoxLayout(self.notifications_tab)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header section with title and controls in a toolbar-style layout
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.StyledPanel)
        header_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(120, 120, 120, 0.1);
                border: 1px solid rgba(120, 120, 120, 0.3);
                border-radius: 6px;
                padding: 10px;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(15, 10, 15, 10)
        
        # Title with icon-style formatting
        title_label = QLabel("🔔 Security Notifications")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title_label.setStyleSheet("color: #0078d4; border: none; background: transparent;")
        header_layout.addWidget(title_label)
        
        # Notification count
        self.notification_count_label = QLabel("0 notifications")
        self.notification_count_label.setFont(QFont("Segoe UI", 11))
        self.notification_count_label.setStyleSheet("color: #6c757d; border: none; background: transparent;")
        header_layout.addWidget(self.notification_count_label)
        
        header_layout.addStretch()
        
        # Clear notifications button in toolbar
        clear_btn = QPushButton("Clear All")
        clear_btn.setFont(QFont("Segoe UI", 11, QFont.DemiBold))
        clear_btn.setMinimumHeight(35)
        clear_btn.clicked.connect(self.clear_notifications)
        clear_btn.setStyleSheet("""
            QPushButton {
                max-width: 100px;
                background-color: #6c757d;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #545b62;
            }
        """)
        header_layout.addWidget(clear_btn)
        
        layout.addWidget(header_frame)
        
        # Notifications display area with better styling
        notifications_frame = QFrame()
        notifications_frame.setFrameStyle(QFrame.StyledPanel)
        notifications_frame.setStyleSheet("""
            QFrame {
                border: 1px solid rgba(120, 120, 120, 0.3);
                border-radius: 6px;
                background-color: rgba(240, 240, 240, 0.05);
            }
        """)
        notifications_layout = QVBoxLayout(notifications_frame)
        notifications_layout.setContentsMargins(10, 15, 10, 15)
        
        # Notifications list with enhanced styling
        self.notifications_list = QListWidget()
        self.notifications_list.setAlternatingRowColors(True)
        self.notifications_list.setFont(QFont("Segoe UI", 11))
        self.notifications_list.setMinimumHeight(380)  # Optimized height
        self.notifications_list.setWordWrap(True)
        self.notifications_list.setSpacing(3)
        self.notifications_list.setTextElideMode(Qt.ElideNone)
        self.notifications_list.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: transparent;
                outline: none;
            }
            QListWidget::item {
                border: 1px solid rgba(120, 120, 120, 0.2);
                border-radius: 4px;
                margin: 2px;
                padding: 8px;
                background-color: rgba(255, 255, 255, 0.02);
            }
            QListWidget::item:hover {
                background-color: rgba(120, 120, 120, 0.1);
            }
        """)
        notifications_layout.addWidget(self.notifications_list)
        
        layout.addWidget(notifications_frame)
        
        # Settings section in a compact group
        settings_group = QGroupBox("Notification Settings")
        settings_group.setFont(QFont("Segoe UI", 12, QFont.Bold))
        settings_group.setMaximumHeight(120)  # Compact height
        settings_layout = QVBoxLayout(settings_group)
        settings_layout.setSpacing(8)
        settings_layout.setContentsMargins(15, 15, 15, 10)
        
        # Settings in a horizontal layout for space efficiency
        settings_row1 = QHBoxLayout()
        
        # Enable auto-scan checkbox
        self.auto_scan_checkbox = QCheckBox("Auto network scanning")
        self.auto_scan_checkbox.setFont(QFont("Segoe UI", 11))
        self.auto_scan_checkbox.setChecked(True)
        self.auto_scan_checkbox.stateChanged.connect(self.toggle_auto_scan)
        settings_row1.addWidget(self.auto_scan_checkbox)
        
        # Quick scan checkbox
        self.quick_scan_checkbox = QCheckBox("Quick scan mode")
        self.quick_scan_checkbox.setFont(QFont("Segoe UI", 11))
        self.quick_scan_checkbox.setChecked(True)
        settings_row1.addWidget(self.quick_scan_checkbox)
        
        settings_layout.addLayout(settings_row1)
        
        # Desktop notifications
        self.desktop_notifications = QCheckBox("Desktop notifications for security threats")
        self.desktop_notifications.setFont(QFont("Segoe UI", 11))
        self.desktop_notifications.setChecked(True)
        settings_layout.addWidget(self.desktop_notifications)
        
        layout.addWidget(settings_group)

    def load_system_info(self):
        """Load and display system information."""
        try:
            # Get detailed system information
            system_name = platform.system()
            system_release = platform.release()
            system_version = platform.version()
            processor = platform.processor()
            architecture = platform.architecture()[0]
            machine = platform.machine()
            hostname = socket.gethostname()
            
            # Get network information
            try:
                local_ip = socket.gethostbyname(hostname)
            except:
                local_ip = "Unable to determine"
            
            # Get hardware information
            cpu_count = psutil.cpu_count(logical=False)
            cpu_count_logical = psutil.cpu_count(logical=True)
            memory_total = round(psutil.virtual_memory().total / (1024**3), 2)
            memory_available = round(psutil.virtual_memory().available / (1024**3), 2)
            memory_percent = psutil.virtual_memory().percent
            
            # Get disk information
            disk_usage = psutil.disk_usage('/')
            disk_total = round(disk_usage.total / (1024**3), 2)
            disk_used = round(disk_usage.used / (1024**3), 2)
            disk_free = round(disk_usage.free / (1024**3), 2)
            disk_percent = round((disk_used / disk_total) * 100, 1)
            
            # Get boot time
            boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
            current_time = datetime.datetime.now()
            uptime = current_time - boot_time
            
            # Format the information with HTML for better presentation
            info_html = f"""
            <div style="font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; line-height: 1.5; padding: 10px;">
            
            <h3 style="color: #0078d4; margin: 0 0 12px 0; font-size: 16px; font-weight: bold;">Operating System</h3>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 18px;">
                <tr><td style="font-weight: bold; padding: 6px 15px 6px 0; width: 30%; vertical-align: top; font-size: 13px;">System:</td><td style="padding: 6px 0; font-size: 13px;">{system_name} {system_release}</td></tr>
                <tr><td style="font-weight: bold; padding: 6px 15px 6px 0; vertical-align: top; font-size: 13px;">Version:</td><td style="padding: 6px 0; font-size: 13px;">{system_version}</td></tr>
                <tr><td style="font-weight: bold; padding: 6px 15px 6px 0; vertical-align: top; font-size: 13px;">Architecture:</td><td style="padding: 6px 0; font-size: 13px;">{architecture} ({machine})</td></tr>
                <tr><td style="font-weight: bold; padding: 6px 15px 6px 0; vertical-align: top; font-size: 13px;">Hostname:</td><td style="padding: 6px 0; font-size: 13px;">{hostname}</td></tr>
                <tr><td style="font-weight: bold; padding: 6px 15px 6px 0; vertical-align: top; font-size: 13px;">Local IP:</td><td style="padding: 6px 0; font-size: 13px;">{local_ip}</td></tr>
            </table>

            <h3 style="color: #0078d4; margin: 18px 0 12px 0; font-size: 16px; font-weight: bold;">Hardware Information</h3>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 18px;">
                <tr><td style="font-weight: bold; padding: 6px 15px 6px 0; width: 30%; vertical-align: top; font-size: 13px;">Processor:</td><td style="padding: 6px 0; font-size: 13px;">{processor}</td></tr>
                <tr><td style="font-weight: bold; padding: 6px 15px 6px 0; vertical-align: top; font-size: 13px;">CPU Cores:</td><td style="padding: 6px 0; font-size: 13px;">{cpu_count} physical, {cpu_count_logical} logical</td></tr>
                <tr><td style="font-weight: bold; padding: 6px 15px 6px 0; vertical-align: top; font-size: 13px;">Total Memory:</td><td style="padding: 6px 0; font-size: 13px;">{memory_total} GB</td></tr>
                <tr><td style="font-weight: bold; padding: 6px 15px 6px 0; vertical-align: top; font-size: 13px;">Available Memory:</td><td style="padding: 6px 0; font-size: 13px;">{memory_available} GB ({100-memory_percent:.1f}% free)</td></tr>
                <tr><td style="font-weight: bold; padding: 6px 15px 6px 0; vertical-align: top; font-size: 13px;">Disk Space:</td><td style="padding: 6px 0; font-size: 13px;">{disk_used} GB / {disk_total} GB ({disk_percent}% used)</td></tr>
            </table>

            <h3 style="color: #0078d4; margin: 18px 0 12px 0; font-size: 16px; font-weight: bold;">System Status</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr><td style="font-weight: bold; padding: 6px 15px 6px 0; width: 30%; vertical-align: top; font-size: 13px;">Python Version:</td><td style="padding: 6px 0; font-size: 13px;">{platform.python_version()}</td></tr>
                <tr><td style="font-weight: bold; padding: 6px 15px 6px 0; vertical-align: top; font-size: 13px;">Boot Time:</td><td style="padding: 6px 0; font-size: 13px;">{boot_time.strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
                <tr><td style="font-weight: bold; padding: 6px 15px 6px 0; vertical-align: top; font-size: 13px;">System Uptime:</td><td style="padding: 6px 0; font-size: 13px;">{str(uptime).split('.')[0]}</td></tr>
            </table>
            </div>
            """
            
            self.info_text.setHtml(info_html)
            
        except Exception as e:
            error_html = f"""
            <div style="font-family: 'Segoe UI', Arial, sans-serif; font-size: 12px; color: #dc3545;">
            <h3 style="color: #dc3545;">Error Loading System Information</h3>
            <p><strong>Error Details:</strong> {str(e)}</p>
            <p>Some system information may not be available due to permission restrictions or missing dependencies.</p>
            </div>
            """
            self.info_text.setHtml(error_html)

    def clear_all_blocks(self):
        """Clear all blocked domains after confirmation."""
        reply = QMessageBox.question(
            self, 
            "Confirm Clear All", 
            "Are you sure you want to unblock ALL domains?\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Get all blocked domains and unblock them
            blocked_domains = hosts_editor.get_blocked_domains()
            success_count = 0
            
            for item in blocked_domains:
                if isinstance(item, dict):
                    domain = item["domain"]
                else:
                    domain = item
                success, _ = hosts_editor.unblock_domain(domain)
                if success:
                    success_count += 1
            
            QMessageBox.information(
                self, 
                "Clear Complete", 
                f"Successfully unblocked {success_count} out of {len(blocked_domains)} domains."
            )
            self.refresh_blocked_list()

    def update_scan_progress(self):
        """Update scan progress bar animation."""
        self.scan_progress = (self.scan_progress + 5) % 100
        self.progress_bar.setValue(self.scan_progress)

    def refresh_blocked_list(self):
        self.blocked_list.clear()
        self.all_blocked_domains = hosts_editor.get_blocked_domains()  # Store for filtering
        
        self.display_blocked_domains(self.all_blocked_domains)
        
        # Update counter
        count = len(self.all_blocked_domains)
        if count == 0:
            self.blocked_count_label.setText("No domains currently blocked")
            self.blocked_count_label.setStyleSheet("color: #28a745; font-style: italic;")
        else:
            self.blocked_count_label.setText(f"{count} domain{'s' if count != 1 else ''} currently blocked")
            self.blocked_count_label.setStyleSheet("color: #dc3545; font-weight: 500;")

    def display_blocked_domains(self, domains_to_show):
        """Display a list of blocked domains in the UI."""
        self.blocked_list.clear()
        
        for item in domains_to_show:
            if isinstance(item, dict):
                domain = item["domain"]
                timestamp = item["timestamp"]
                display_text = f"{domain}\nBlocked on: {timestamp}"
            else:
                # Fallback for old format
                domain = item
                display_text = f"{domain}\nBlocked on: Unknown date"
            
            list_item = QListWidgetItem(display_text)
            list_item.setFont(QFont("Segoe UI", 11))
            list_item.setSizeHint(QSize(0, 50))  # Make items taller to show timestamp
            # Store the domain name in item data for easy access
            list_item.setData(Qt.UserRole, domain)
            self.blocked_list.addItem(list_item)

    def filter_blocked_list(self):
        """Filter the blocked domains list based on search text."""
        search_text = self.blocked_search.text().lower()
        
        if not search_text:
            # Show all domains if search is empty
            self.display_blocked_domains(self.all_blocked_domains)
        else:
            # Filter domains that contain the search text
            filtered_domains = []
            for item in self.all_blocked_domains:
                if isinstance(item, dict):
                    domain = item["domain"]
                else:
                    domain = item
                
                if search_text in domain.lower():
                    filtered_domains.append(item)
            
            self.display_blocked_domains(filtered_domains)

    def on_blocked_item_clicked(self, item):
        """Handle clicking on a blocked domain item."""
        domain = item.data(Qt.UserRole)
        if domain:
            self.domain_input.setText(domain)

    def handle_block_domain(self):
        domain = self.domain_input.text().strip()
        if not domain:
            QMessageBox.warning(self, "Input Error", "Please enter a domain name.")
            return
        
        # Remove any protocol prefixes
        domain = domain.replace("https://", "").replace("http://", "").replace("www.", "")
        
        success, message = hosts_editor.block_domain(domain)
        if success:
            QMessageBox.information(self, "Success", f"Successfully blocked: {domain}")
            self.refresh_blocked_list()
            self.domain_input.clear()
            self.status_bar.showMessage(f"Blocked domain: {domain}", 3000)
        else:
            QMessageBox.critical(self, "Error", message)

    def handle_unblock_domain(self):
        domain = self.domain_input.text().strip()
        if not domain:
            QMessageBox.warning(self, "Input Error", "Please select or enter a domain to unblock.")
            return
        
        # Remove emoji prefix if present (for backwards compatibility)
        domain = domain.replace("🚫 ", "")
        
        success, message = hosts_editor.unblock_domain(domain)
        if success:
            QMessageBox.information(self, "Success", f"Successfully unblocked: {domain}")
            self.refresh_blocked_list()
            self.domain_input.clear()
            self.status_bar.showMessage(f"Unblocked domain: {domain}", 3000)
        else:
            QMessageBox.critical(self, "Error", message)

    def auto_fill_target(self):
        detected_range = utils.get_local_network_range()
        self.target_input.setText(detected_range)

    def start_scan(self):
        # Prevent starting multiple scans
        if self.thread is not None and self.thread.isRunning():
            return
        
        self.results_table.setRowCount(0)
        self.scan_button.setEnabled(False)
        self.scan_button.setText("Scanning in Progress...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.scan_status_label.setText("Discovering hosts...")
        self.scan_status_label.setStyleSheet("color: #ffc107; font-weight: 500;")
        
        target = self.target_input.text()
        
        # Clean up any existing thread
        if self.thread is not None:
            try:
                self.thread.quit()
                self.thread.wait(1000)
                self.thread.deleteLater()
                if self.worker:
                    self.worker.deleteLater()
            except:
                pass
        
        # Create new thread and worker
        self.thread = QThread()
        self.worker = ScannerWorker(target)
        self.worker.moveToThread(self.thread)
        
        # Connect signals with error handling
        try:
            self.thread.started.connect(self.worker.run)
            self.worker.scan_finished.connect(self.scan_complete)
            self.worker.result_found.connect(self.add_result_to_table)
            self.worker.critical_finding.connect(self.show_critical_alert)
            self.worker.status_update.connect(self.update_scan_status)
        except Exception as e:
            print(f"Error connecting signals: {e}")
            return
        
        self.thread.start()
        
        # Start progress animation
        self.scan_timer.start(100)

    def update_scan_status(self, message):
        """Update scan status from worker thread."""
        self.scan_status_label.setText(f"Scanning: {message}")
        self.status_bar.showMessage(message)

    def scan_complete(self):
        self.scan_button.setEnabled(True)
        self.scan_button.setText("Start Network Scan")
        self.progress_bar.setVisible(False)
        self.scan_timer.stop()
        
        # Update status and results summary
        row_count = self.results_table.rowCount()
        if row_count == 0:
            self.scan_status_label.setText("Scan complete - No open ports found")
            self.scan_status_label.setStyleSheet("color: #28a745; font-weight: 500;")
            self.results_summary.setText("No vulnerabilities detected in the scanned network.")
            self.results_summary.setStyleSheet("color: #28a745; font-style: italic;")
        else:
            self.scan_status_label.setText(f"Scan complete - {row_count} open port{'s' if row_count != 1 else ''} found")
            self.scan_status_label.setStyleSheet("color: #dc3545; font-weight: 500;")
            self.results_summary.setText(f"Found {row_count} open port{'s' if row_count != 1 else ''} that may require attention.")
            self.results_summary.setStyleSheet("color: #ffc107; font-style: italic;")
        
        self.status_bar.showMessage(f"Scan completed - {row_count} results found", 5000)
        
        # Proper thread cleanup to prevent WPARAM errors
        if self.thread is not None:
            # Disconnect all signals before quitting
            try:
                self.worker.scan_finished.disconnect()
                self.worker.result_found.disconnect()
                self.worker.critical_finding.disconnect()
                self.worker.status_update.disconnect()
                self.thread.started.disconnect()
            except:
                pass  # Ignore if signals are already disconnected
            
            self.thread.quit()
            self.thread.wait(2000)  # Wait max 2 seconds
            self.thread.deleteLater()
            self.worker.deleteLater()
            self.thread = None
            self.worker = None

    def add_result_to_table(self, ip, port, banner):
        from core import config
        
        row_position = self.results_table.rowCount()
        self.results_table.insertRow(row_position)
        
        # IP Address
        ip_item = QTableWidgetItem(ip)
        ip_item.setFont(QFont("Segoe UI", 12))
        
        # Port
        port_item = QTableWidgetItem(str(port))
        port_item.setFont(QFont("Segoe UI", 12, QFont.DemiBold))
        
        # Service/Banner
        service_item = QTableWidgetItem(banner if banner != "N/A" else "Unknown Service")
        service_item.setFont(QFont("Segoe UI", 12))
        
        # Risk Level
        risk_level = "HIGH" if port in config.CRITICAL_PORTS else "MEDIUM"
        risk_item = QTableWidgetItem(risk_level)
        risk_item.setFont(QFont("Segoe UI", 12, QFont.DemiBold))
        
        # Color coding based on risk
        if port in config.CRITICAL_PORTS:
            for item in [ip_item, port_item, service_item, risk_item]:
                item.setBackground(QColor(220, 60, 60, 30))  # Light red background
        
        self.results_table.setItem(row_position, 0, ip_item)
        self.results_table.setItem(row_position, 1, port_item)
        self.results_table.setItem(row_position, 2, service_item)
        self.results_table.setItem(row_position, 3, risk_item)

    def show_context_menu(self, position):
        item = self.results_table.itemAt(position)
        if not item:
            return
        selected_ip = self.results_table.item(item.row(), 0).text()
        selected_port = self.results_table.item(item.row(), 1).text()
        
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #4a4a4a;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 6px;
                padding: 5px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 10px;
            }
            QMenu::item {
                padding: 8px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #0078d4;
            }
        """)
        
        block_ip_action = menu.addAction(f"Block IP: {selected_ip}")
        copy_ip_action = menu.addAction(f"Copy IP: {selected_ip}")
        copy_port_action = menu.addAction(f"Copy Port: {selected_port}")
        
        action = menu.exec_(self.results_table.mapToGlobal(position))
        
        if action == block_ip_action:
            self.block_selected_ip(selected_ip)
        elif action == copy_ip_action:
            QApplication.clipboard().setText(selected_ip)
            self.status_bar.showMessage(f"Copied IP: {selected_ip}", 2000)
        elif action == copy_port_action:
            QApplication.clipboard().setText(selected_port)
            self.status_bar.showMessage(f"Copied port: {selected_port}", 2000)

    def block_selected_ip(self, ip_address):
        reply = QMessageBox.question(
            self, 
            "Confirm IP Block", 
            f"Are you sure you want to block IP address: {ip_address}?\n\nThis will create a firewall rule to block all traffic from this IP.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success, message = firewall_manager.block_ip(ip_address)
            if success:
                QMessageBox.information(self, "Success", f"Successfully blocked IP: {ip_address}")
                self.status_bar.showMessage(f"Blocked IP: {ip_address}", 3000)
            else:
                QMessageBox.critical(self, "Error", f"{message}\n\nPlease try running the application 'As Administrator'.")

    def show_critical_alert(self, ip, port, reason):
        """Creates and shows the alert dialog when a critical port is found."""
        dialog = AlertDialog(ip, port, reason, self)
        dialog.exec_()
        
        # Also show in status bar
        self.status_bar.showMessage(f"CRITICAL: {reason} found on {ip}:{port}", 10000)

    def add_notification(self, notification_type, title, message, severity="INFO"):
        """Add a new notification to the list with enhanced formatting."""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        # Create professionally formatted notification with icons
        if severity == "CRITICAL":
            severity_icon = "🔴"
            severity_color = "#dc3545"
        elif severity == "WARNING":
            severity_icon = "🟡"
            severity_color = "#ffc107"
        elif severity == "INFO":
            severity_icon = "🔵"
            severity_color = "#0078d4"
        else:
            severity_icon = "⚪"
            severity_color = "#6c757d"
        
        # Create enhanced notification text with better formatting
        notification_text = f"{severity_icon} [{timestamp}] {severity}\n{title}\n{message}"
        
        # Add to notifications list
        self.notifications.append({
            'timestamp': timestamp,
            'type': notification_type,
            'title': title,
            'message': message,
            'severity': severity
        })
        
        # Create list item with enhanced formatting
        item = QListWidgetItem()
        item.setText(notification_text)
        
        # Set enhanced styling based on severity and theme
        item_font = QFont("Segoe UI", 11)
        item.setFont(item_font)
        
        # Theme-aware color styling with better contrast
        if hasattr(self, '_is_dark_theme') and self._is_dark_theme:
            # Dark theme colors - more vibrant
            if severity == "CRITICAL":
                item.setBackground(QColor(70, 25, 25))  # Deeper red
                item.setForeground(QColor(255, 170, 170))  # Brighter red text
            elif severity == "WARNING":
                item.setBackground(QColor(70, 55, 25))  # Deeper yellow
                item.setForeground(QColor(255, 230, 130))  # Brighter yellow text
            elif severity == "INFO":
                item.setBackground(QColor(25, 45, 75))  # Deeper blue
                item.setForeground(QColor(170, 200, 255))  # Brighter blue text
        else:
            # Light theme colors - better contrast
            if severity == "CRITICAL":
                item.setBackground(QColor(255, 245, 245))  # Very light red
                item.setForeground(QColor(170, 30, 30))  # Darker red
            elif severity == "WARNING":
                item.setBackground(QColor(255, 252, 240))  # Very light yellow
                item.setForeground(QColor(190, 150, 30))  # Darker yellow
            elif severity == "INFO":
                item.setBackground(QColor(245, 250, 255))  # Very light blue
                item.setForeground(QColor(30, 90, 170))  # Darker blue
        
        # Set consistent item height
        item.setSizeHint(QSize(0, 75))
        
        self.notifications_list.insertItem(0, item)  # Add to top
        
        # Update notification count if label exists
        count = len(self.notifications)
        if hasattr(self, 'notification_count_label'):
            self.notification_count_label.setText(f"{count} notification{'s' if count != 1 else ''}")
        
        # Limit notifications count
        if len(self.notifications) > self.max_notifications:
            self.notifications.pop()
            if self.notifications_list.count() > self.max_notifications:
                self.notifications_list.takeItem(self.notifications_list.count() - 1)
        
        # Show desktop notification if enabled
        if hasattr(self, 'desktop_notifications') and self.desktop_notifications.isChecked():
            try:
                self.show_desktop_notification(title, message, severity)
            except Exception as e:
                pass
    
    def show_desktop_notification(self, title, message, severity):
        """Show desktop notification with improved error handling."""
        try:
            # Use QSystemTrayIcon for more reliable notifications
            if not hasattr(self, 'tray_icon'):
                self.tray_icon = QSystemTrayIcon(self)
                # Use the application icon if available
                self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
            
            # Only show if system tray is available
            if QSystemTrayIcon.isSystemTrayAvailable():
                # Map severity to icon type
                if severity == "CRITICAL":
                    icon_type = QSystemTrayIcon.Critical
                elif severity == "WARNING":
                    icon_type = QSystemTrayIcon.Warning
                else:
                    icon_type = QSystemTrayIcon.Information
                
                # Show notification with timeout
                self.tray_icon.showMessage(
                    f"doormaNet - {title}",
                    message,
                    icon_type,
                    5000  # 5 seconds
                )
            else:
                # Fallback to status bar message if no system tray
                if hasattr(self, 'status_bar'):
                    self.status_bar.showMessage(f"{severity}: {title} - {message}", 5000)
                    
        except Exception as e:
            # Fallback to status bar for any errors
            try:
                if hasattr(self, 'status_bar'):
                    self.status_bar.showMessage(f"Notification: {title}", 3000)
            except:
                pass  # Silent fallback
    
    def clear_notifications(self):
        """Clear all notifications and update display."""
        self.notifications.clear()
        self.notifications_list.clear()
        
        # Update notification count
        if hasattr(self, 'notification_count_label'):
            self.notification_count_label.setText("0 notifications")
        
        # Add a system message about clearing
        self.add_notification("SYSTEM", "Notifications Cleared", "All previous notifications have been cleared from the display.", "INFO")
    
    def toggle_auto_scan(self, state):
        """Toggle automatic scanning on network changes."""
        if state == 2:  # Checked
            self.network_monitor.start_monitoring()
            self.add_notification("SYSTEM", "Auto-Scan Enabled", 
                                "Automatic network scanning is now active.", "INFO")
        else:
            self.network_monitor.stop_monitoring()
            self.add_notification("SYSTEM", "Auto-Scan Disabled", 
                                "Automatic network scanning has been disabled.", "INFO")
    
    def on_network_changed(self, network_info):
        """Handle network change events."""
        if hasattr(self, 'auto_scan_checkbox') and self.auto_scan_checkbox.isChecked():
            # network_info is a string description of the network change
            self.add_notification("NETWORK", "Network Change Detected", 
                                f"Network status: {network_info}", "INFO")
            
            # Start automatic scan
            if hasattr(self, 'quick_scan_checkbox') and self.quick_scan_checkbox.isChecked():
                self.start_quick_scan()
            else:
                self.start_full_scan()
    
    def start_quick_scan(self):
        """Start a quick network scan."""
        self.add_notification("SCAN", "Quick Scan Started", 
                            "Performing quick network security scan...", "INFO")
        # Use existing scan functionality with limited scope
        target = utils.get_local_network_range()
        self.target_input.setText(target)
        self.start_scan()
        
    def start_full_scan(self):
        """Start a full network scan."""
        self.add_notification("SCAN", "Full Scan Started", 
                            "Performing comprehensive network security scan...", "INFO")
        # Use existing scanner functionality
        target = utils.get_local_network_range()
        self.target_input.setText(target)
        self.start_scan()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
