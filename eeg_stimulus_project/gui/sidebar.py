from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

class Sidebar(QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #53366b;
                border-top-right-radius: 18px;
                border-bottom-right-radius: 18px;
            }
        """)
        self.setMinimumWidth(500)
        self.setMaximumWidth(340)

        # Set the vertical layout for the sidebar
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(18, 18, 18, 18)
        self.layout.setSpacing(18)

        # Brand/title section
        self.brand_frame = QFrame(self)
        self.brand_frame.setStyleSheet("""
            QFrame {
                background-color: #F5E1FD;
                border-radius: 12px;
            }
        """)
        self.brand_frame.setMaximumHeight(90)
        self.layout.addWidget(self.brand_frame)

        self.brand_layout = QVBoxLayout(self.brand_frame)
        self.brand_layout.setContentsMargins(0, 0, 0, 0)
        self.brand_layout.setSpacing(0)

        self.sidebar_title1 = QLabel("Multisensory", self)
        self.sidebar_title1.setFont(QFont("Segoe UI", 18, QFont.Bold))
        self.sidebar_title1.setStyleSheet("color: #53366b; background: transparent;")
        self.sidebar_title1.setAlignment(Qt.AlignCenter)
        self.brand_layout.addWidget(self.sidebar_title1)

        self.sidebar_title2 = QLabel("Tests", self)
        self.sidebar_title2.setFont(QFont("Segoe UI", 18, QFont.Bold))
        self.sidebar_title2.setStyleSheet("color: #53366b; background: transparent;")
        self.sidebar_title2.setAlignment(Qt.AlignCenter)
        self.brand_layout.addWidget(self.sidebar_title2)

        # Submenu section
        self.submenu_frame = QFrame(self)
        self.submenu_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f6ff;
                border-radius: 10px;
            }
        """)
        self.layout.addWidget(self.submenu_frame)

        self.submenu_layout = QVBoxLayout(self.submenu_frame)
        self.submenu_layout.setContentsMargins(10, 10, 10, 10)
        self.submenu_layout.setSpacing(10)
        self.submenu_layout.setAlignment(Qt.AlignTop)

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

        # Instructions button
        self.instructions_button = QPushButton("Hide Instructions", self)
        self.instructions_button.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.instructions_button.setStyleSheet("""
            QPushButton {
                background-color: #7E57C2;
                color: white;
                border-radius: 8px;
                padding: 10px 0px;
                margin-top: 18px;
            }
            QPushButton:hover {
                background-color: #512da8;
            }
        """)
        self.instructions_button.clicked.connect(parent.toggle_instruction_frame)
        self.layout.addWidget(self.instructions_button)

        # Latency Checker Button
        latency_button = QPushButton("Latency Checker", self)
        latency_button.setFont(QFont("Segoe UI", 11, QFont.Bold))
        latency_button.setStyleSheet("""
            QPushButton {
                background-color: #7E57C2;
                color: white;
                border-radius: 8px;
                padding: 10px 0px;
                margin-top: 18px;
            }
            QPushButton:hover {
                background-color: #512da8;
            }
        """)
        latency_button.clicked.connect(parent.toggle_latency_checker)
        self.layout.addWidget(latency_button)

        # Stimulus Order Button
        stimulus_order_button = QPushButton("Stimulus Order", self)
        stimulus_order_button.setFont(QFont("Segoe UI", 11, QFont.Bold))
        stimulus_order_button.setStyleSheet("""
            QPushButton {
                background-color: #7E57C2;
                color: white;
                border-radius: 8px;
                padding: 10px 0px;
                margin-top: 18px;
            }
            QPushButton:hover {
                background-color: #512da8;
            }
        """)
        stimulus_order_button.clicked.connect(parent.toggle_stimulus_order)
        self.layout.addWidget(stimulus_order_button)

    # Add a submenu with a heading and options  
    def add_submenu(self, heading, options):
        heading_label = QLabel(heading, self)
        heading_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        heading_label.setStyleSheet("color: #7E57C2; background: transparent; margin-bottom: 2px;")
        self.submenu_layout.addWidget(heading_label)

        # Add buttons for each option in the submenu
        for option_text, option_func in options:
            button = QPushButton(option_text, self)
            button.setFont(QFont("Segoe UI", 10))
            button.setStyleSheet("""
                QPushButton {
                    background-color: #ede7f6;
                    color: #53366b;
                    border-radius: 7px;
                    padding: 7px 0px;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #d1b3ff;
                }
            """)
            button.clicked.connect(option_func)
            self.submenu_layout.addWidget(button)

    def highlight_tests(self, test_number):
        # Collect all test buttons in order of creation
        # Passive: first 6, Stroop: next 4
        buttons = []
        for i in range(self.submenu_layout.count()):
            widget = self.submenu_layout.itemAt(i).widget()
            if isinstance(widget, QPushButton):
                buttons.append(widget)
        # Passive: buttons[0:6], Stroop: buttons[6:10]
        passive_buttons = buttons[0:6]
        stroop_buttons = buttons[6:10]
        default_style = """
            QPushButton {
                background-color: #ede7f6;
                color: #53366b;
                border-radius: 7px;
                padding: 7px 0px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #d1b3ff;
            }
        """
        highlight_style = """
            QPushButton {
                background-color: #ffe082;
                color: #53366b;
                border-radius: 7px;
                padding: 7px 0px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #ffd54f;
            }
        """
        # Reset all
        for btn in passive_buttons + stroop_buttons:
            btn.setStyleSheet(default_style)
        # Highlight relevant
        if str(test_number) == '1':
            for btn in passive_buttons:
                btn.setStyleSheet(highlight_style)
        elif str(test_number) == '2':
            for btn in stroop_buttons:
                btn.setStyleSheet(highlight_style)
