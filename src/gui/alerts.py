# src/gui/alerts.py

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap, QPalette, QColor

class AlertDialog(QDialog):
    """An enhanced custom dialog to show critical security alerts."""
    def __init__(self, ip, port, reason, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Critical Security Alert")
        self.setWindowIcon(self.style().standardIcon(getattr(self.style(), 'SP_MessageBoxWarning')))
        self.setMinimumWidth(500)
        self.setMinimumHeight(350)
        self.setModal(True)
        
        # Set application font
        self.setFont(QFont("Segoe UI", 10))
        
        # Apply modern theme styling
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 2px solid #dc3545;
                border-radius: 12px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                color: #ffffff;
                background-color: transparent;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-weight: 600;
                font-size: 11px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #a71e2a;
            }
            QFrame {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 8px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # Header with warning icon
        header_frame = QFrame()
        header_layout = QVBoxLayout(header_frame)
        header_layout.setAlignment(Qt.AlignCenter)
        
        # Warning indicator
        warning_label = QLabel("⚠")
        warning_label.setStyleSheet("font-size: 64px; color: #ffc107; font-weight: bold;")
        warning_label.setAlignment(Qt.AlignCenter)
        
        # Title
        title = QLabel("CRITICAL SECURITY ALERT")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #dc3545; margin-top: 10px;")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        
        header_layout.addWidget(warning_label)
        header_layout.addWidget(title)
        
        # Information frame
        info_frame = QFrame()
        info_layout = QVBoxLayout(info_frame)
        info_layout.setSpacing(15)
        info_layout.setContentsMargins(20, 20, 20, 20)
        
        subtitle = QLabel("High-Risk Port Detected")
        subtitle.setStyleSheet("font-size: 16px; font-weight: 600; color: #ffc107; margin-bottom: 10px;")
        subtitle.setFont(QFont("Segoe UI", 12, QFont.DemiBold))
        
        # Details section
        details_html = f"""
        <div style="line-height: 1.6;">
            <p style="margin-bottom: 15px;">A potentially dangerous port was found open on the following device:</p>
            
            <table style="width: 100%; margin: 15px 0;">
                <tr style="margin-bottom: 8px;">
                    <td style="padding: 5px 0; font-weight: 600; color: #ffffff; width: 30%;">IP Address:</td>
                    <td style="padding: 5px 0; color: #ffc107; font-weight: 600;">{ip}</td>
                </tr>
                <tr style="margin-bottom: 8px;">
                    <td style="padding: 5px 0; font-weight: 600; color: #ffffff;">Port:</td>
                    <td style="padding: 5px 0; color: #dc3545; font-weight: 600;">{port}</td>
                </tr>
                <tr style="margin-bottom: 8px;">
                    <td style="padding: 5px 0; font-weight: 600; color: #ffffff;">Security Risk:</td>
                    <td style="padding: 5px 0; color: #ffffff;">{reason}</td>
                </tr>
            </table>
            
            <p style="margin-top: 20px; padding: 15px; background-color: #444444; border-radius: 6px; border-left: 4px solid #ffc107;">
                <strong style="color: #ffc107;">Recommendation:</strong><br>
                It is highly recommended to close this port if it is not needed or ensure it is properly secured with authentication and access controls.
            </p>
        </div>
        """
        
        message = QLabel(details_html)
        message.setWordWrap(True)
        message.setStyleSheet("font-size: 11px; color: #ffffff;")
        message.setFont(QFont("Segoe UI", 10))
        
        info_layout.addWidget(subtitle)
        info_layout.addWidget(message)
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        ok_button = QPushButton("Acknowledge Alert")
        ok_button.clicked.connect(self.accept)
        ok_button.setFont(QFont("Segoe UI", 10, QFont.DemiBold))
        
        button_layout.addWidget(ok_button)
        button_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        # Add all to main layout
        layout.addWidget(header_frame)
        layout.addWidget(info_frame)
        layout.addLayout(button_layout)