from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

class Sidebar(QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: #53366b;")
        self.setMinimumWidth(330)
        
        # Set the vertical layout for the sidebar
        self.layout = QVBoxLayout(self)
        
        # Set the layout for the sidebar title
        self.brand_frame = QFrame(self)
        self.brand_frame.setStyleSheet(f"background-color: #F5E1FD;")
        self.brand_frame.setMaximumHeight(105)
        self.layout.addWidget(self.brand_frame)
        
        self.brand_layout = QVBoxLayout(self.brand_frame)
        
        # Set the size and font of sidebar title
        self.sidebar_title1 = QLabel("Multisensory", self)
        self.sidebar_title1.setFont(QFont("", 15, QFont.Bold))
        self.sidebar_title1.setStyleSheet(f"background-color: #F5E1FD;")
        self.brand_layout.addWidget(self.sidebar_title1)
        
        self.sidebar_title2 = QLabel("Tests", self)
        self.sidebar_title2.setFont(QFont("", 15, QFont.Bold))
        self.sidebar_title2.setStyleSheet(f"background-color: #F5E1FD;")
        self.brand_layout.addWidget(self.sidebar_title2)
        
        # Set the layout for the submenu
        self.submenu_frame = QFrame(self)
        self.submenu_frame.setStyleSheet(f"background-color: #F5E1FD;")
        self.layout.addWidget(self.submenu_frame)
        
        self.submenu_layout = QVBoxLayout(self.submenu_frame)
        self.submenu_layout.setAlignment(Qt.AlignTop)  # Align submenu to the top
        
        # Add the passive viewing tests to the sidebar
        self.add_submenu("Passive Viewing", [
            ("Unisensory Neutral Visual", parent.show_unisensory_neutral_visual),
            ("Unisensory Alcohol Visual", parent.show_unisensory_alcohol_visual),
            ("Multisensory Neutral Visual & Olfactory", parent.show_multisensory_neutral_visual_olfactory),
            ("Multisensory Alcohol Visual & Olfactory", parent.show_multisensory_alcohol_visual_olfactory),
            ("Multisensory Neutral Visual, Tactile & Olfactory", parent.show_multisensory_neutral_visual_tactile_olfactory),
            ("Multisensory Alcohol Visual, Tactile & Olfactory", parent.show_multisensory_alcohol_visual_tactile_olfactory)
        ])
        
        # Add the stroop tests to the sidebar
        self.add_submenu("Stroop Test", [
            ("Multisensory Alcohol (Visual & Tactile)", parent.show_multisensory_alcohol_visual_tactile),
            ("Multisensory Neutral (Visual & Tactile)", parent.show_multisensory_neutral_visual_tactile),
            ("Multisensory Alcohol (Visual & Olfactory)", parent.show_multisensory_alcohol_visual_olfactory2),
            ("Multisensory Neutral (Visual & Olfactory)", parent.show_multisensory_neutral_visual_olfactory2)
        ])

        instructions_button = QPushButton("Show Instructions", self)
        instructions_button.setFont(QFont("Arial", 8, QFont.Bold))
        instructions_button.setStyleSheet("background-color: #F5E1FD;")
        instructions_button.clicked.connect(parent.show_instruction_frame)
        self.layout.addWidget(instructions_button)
        
    # Add a submenu with a heading and options  
    def add_submenu(self, heading, options):
        heading_label = QLabel(heading, self)
        heading_label.setFont(QFont("Arial", 7))
        heading_label.setStyleSheet(f"background-color: #F5E1FD; color: #333333;")
        self.submenu_layout.addWidget(heading_label)
        
        # Add buttons for each option in the submenu
        for option_text, option_func in options:
            button = QPushButton(option_text, self)
            button.setFont(QFont("Arial", 6, QFont.Bold))
            button.setStyleSheet(f"background-color: #F5E1FD;")
            button.clicked.connect(option_func)
            self.submenu_layout.addWidget(button)
