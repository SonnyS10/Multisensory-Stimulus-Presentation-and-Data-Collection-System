from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QPushButton, 
                             QWidget, QGridLayout, QSizePolicy)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QTimer
import os
import csv
from datetime import datetime

class CravingRatingDialog(QDialog):
    def __init__(self, parent=None, base_dir=None, subject_id=None):
        super().__init__(parent)
        self.base_dir = base_dir
        self.subject_id = subject_id
        self.craving_response = None
        self.craving_buttons = []
        
        self.setWindowTitle("Craving Rating")
        self.setMinimumSize(900, 500)  # Minimum size instead of fixed
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Instructions
        instructions = QLabel(
            "How much are you craving alcohol right now?\n"
            "Select a number from 1 to 7 below:"
        )
        instructions.setFont(QFont("Arial", 20, QFont.Bold))
        instructions.setAlignment(Qt.AlignCenter)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Craving meanings and buttons
        meanings = [
            "Not craving\nat all",
            "Almost\ncraving",
            "Barely\ncraving",
            "Somewhat\ncraving",
            "Craving",
            "Really\ncraving",
            "Extremely\ncraving"
        ]
        
        grid = QGridLayout()
        grid.setSpacing(30)
        grid.setAlignment(Qt.AlignCenter)
        
        for i in range(7):
            # Label
            label = QLabel(meanings[i])
            label.setFont(QFont("Arial", 12))
            label.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
            label.setMinimumHeight(50)
            label.setMaximumWidth(140)
            label.setWordWrap(True)
            grid.addWidget(label, 0, i, alignment=Qt.AlignHCenter | Qt.AlignBottom)
            
            # Button
            btn = QPushButton(str(i+1))
            btn.setFont(QFont("Arial", 20, QFont.Bold))
            btn.setMinimumSize(70, 70)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Changed from Fixed to Expanding
            btn.setMaximumSize(100, 100)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #e0e0e0;
                    border-radius: 35px;
                    border: 2px solid #bc85fa;
                    color: #333;
                }
                QPushButton:hover {
                    background-color: #bc85fa;
                    color: white;
                }
            """)
            btn.clicked.connect(lambda checked, val=i+1: self.handle_craving_button(val))
            self.craving_buttons.append(btn)
            grid.addWidget(btn, 1, i, alignment=Qt.AlignHCenter)
        
        grid_widget = QWidget()
        grid_widget.setLayout(grid)
        grid_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Changed from Fixed to Expanding
        
        layout.addWidget(grid_widget, alignment=Qt.AlignCenter)
        layout.addStretch()
    
    def handle_craving_button(self, value):
        if self.craving_response is not None:
            return  # Already selected
        
        # Highlight selected button
        for btn in self.craving_buttons:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #e0e0e0;
                    border-radius: 35px;
                    border: 2px solid #bc85fa;
                    color: #333;
                }
                QPushButton:hover {
                    background-color: #bc85fa;
                    color: white;
                }
            """)
        
        self.craving_buttons[value-1].setStyleSheet("""
            QPushButton {
                background-color: #bc85fa;
                border-radius: 35px;
                border: 2px solid #bc85fa;
                color: white;
            }
        """)
        
        self.craving_response = value
        self.save_craving_rating()
        
        # Close after a brief delay
        QTimer.singleShot(500, self.accept)
    
    def save_craving_rating(self):
        """Save the craving rating to a CSV file."""
        if not self.base_dir or not self.subject_id:
            return
        
        # Create or update craving_rating.csv
        ratings_file = os.path.join(self.base_dir, "craving_rating.csv")
        
        file_exists = os.path.isfile(ratings_file)
        
        with open(ratings_file, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['Timestamp', 'Subject_ID', 'Craving_Rating'])
            writer.writerow([datetime.now().isoformat(), self.subject_id, self.craving_response])