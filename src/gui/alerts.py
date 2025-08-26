# src/gui/alerts.py

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

class AlertDialog(QDialog):
    """A custom dialog to show critical security alerts."""
    def __init__(self, ip, port, reason, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("🚨 Critical Security Alert")
        self.setWindowIcon(self.style().standardIcon(getattr(self.style(), 'SP_MessageBoxWarning')))
        self.setMinimumWidth(350)

        layout = QVBoxLayout(self)
        
        title = QLabel("High-Risk Port Detected!")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        message = QLabel(
            f"A potentially dangerous port was found open on the following device:\n\n"
            f"<b>IP Address:</b> {ip}\n"
            f"<b>Port:</b> {port}\n"
            f"<b>Reason:</b> {reason}\n\n"
            "It is highly recommended to close this port if it is not needed."
        )
        message.setWordWrap(True)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        
        layout.addWidget(title)
        layout.addWidget(message)
        layout.addWidget(ok_button, alignment=Qt.AlignCenter)