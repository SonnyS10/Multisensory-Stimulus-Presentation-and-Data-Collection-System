from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QPushButton, 
                             QWidget, QGridLayout, QSizePolicy)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QTimer
import os
import csv
from datetime import datetime
import logging

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
            "How strong is your urge to drink alcohol right now?\n\n"
            "Select a number from 0 to 6 below:"
        )
        instructions.setFont(QFont("Arial", 20, QFont.Bold))
        instructions.setAlignment(Qt.AlignCenter)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Craving meanings and buttons
        meanings = [
            "Not at all strong",
            "Very slightly strong",
            "Slightly strong",
            "Moderately strong",
            "Quite strong",
            "Strong",
            "Very strong"
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
            btn = QPushButton(str(i))
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
            btn.clicked.connect(lambda checked, val=i: self.handle_craving_button(val))
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
        
        self.craving_buttons[value].setStyleSheet("""
            QPushButton {
                background-color: #bc85fa;
                border-radius: 35px;
                border: 2px solid #bc85fa;
                color: white;
            }
        """)
        
        self.craving_response = value
        self.save_craving_rating()
        
        # Log the craving rating to control window
        craving_label = f"craving_rating_{self.craving_response}"
        logging.info(f"Manual craving rating recorded: {craving_label} for subject {self.subject_id}")
        
        # Close after a brief delay
        QTimer.singleShot(500, self.accept)
    
    def save_craving_rating(self):
        """Save the craving rating to a CSV file with error handling and logging."""
        if not self.base_dir or not self.subject_id:
            logging.error(f"Cannot save craving rating: base_dir={self.base_dir}, subject_id={self.subject_id}")
            return False
        
        try:
            # Create subject-level directory path by going up from test directory
            # Assuming base_dir is like: /path/subject_1/test_1/
            # We want to save to: /path/subject_1/craving_rating.csv
            subject_dir = os.path.dirname(self.base_dir)  # Go up one level from test directory
            os.makedirs(subject_dir, exist_ok=True)
            
            ratings_file = os.path.join(subject_dir, "craving_rating.csv")
            file_exists = os.path.isfile(ratings_file)
            
            with open(ratings_file, 'a', newline='') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(['Timestamp', 'Subject_ID', 'Craving_Rating', 'Source'])
                writer.writerow([
                    datetime.now().isoformat(),
                    self.subject_id,
                    self.craving_response,
                    'Manual Button'
                ])
            
            logging.info(f"Craving rating {self.craving_response} saved for subject {self.subject_id}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to save craving rating: {e}", exc_info=True)
            return False