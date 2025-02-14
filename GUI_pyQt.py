import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QCheckBox, QFrame, QStackedWidget
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt
import os

class GUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Data Collection App")
        self.setGeometry(100, 100, 1100, 700)
        self.setMinimumSize(800, 600)  # Set a minimum size if needed
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QHBoxLayout(self.central_widget)
        
        self.sidebar = Sidebar(self)
        self.main_layout.addWidget(self.sidebar)
        
        self.main_frame = MainFrame(self)
        self.main_layout.addWidget(self.main_frame)
        
        self.stacked_widget = self.main_frame.stacked_widget
        
        self.unisensory_neutral_visual = self.create_frame("Unisensory Neutral Visual")
        self.unisensory_alcohol_visual = self.create_frame("Unisensory Alcohol Visual")
        self.multisensory_neutral_visual_olfactory = self.create_frame("Multisensory Neutral Visual & Olfactory")
        self.multisensory_alcohol_visual_olfactory = self.create_frame("Multisensory Alcohol Visual & Olfactory")
        self.multisensory_neutral_visual_tactile_olfactory = self.create_frame("Multisensory Neutral Visual, Tactile & Olfactory")
        self.multisensory_alcohol_visual_tactile_olfactory = self.create_frame("Multisensory Alcohol Visual, Tactile & Olfactory")
        
        self.stacked_widget.addWidget(self.unisensory_neutral_visual)
        self.stacked_widget.addWidget(self.unisensory_alcohol_visual)
        self.stacked_widget.addWidget(self.multisensory_neutral_visual_olfactory)
        self.stacked_widget.addWidget(self.multisensory_alcohol_visual_olfactory)
        self.stacked_widget.addWidget(self.multisensory_neutral_visual_tactile_olfactory)
        self.stacked_widget.addWidget(self.multisensory_alcohol_visual_tactile_olfactory)
        
        self.stacked_widget.setCurrentWidget(self.unisensory_neutral_visual)
        
    def create_frame(self, title):
        return Frame(self, title)
    
    def show_unisensory_neutral_visual(self):
        self.stacked_widget.setCurrentWidget(self.unisensory_neutral_visual)
    
    def show_unisensory_alcohol_visual(self):
        self.stacked_widget.setCurrentWidget(self.unisensory_alcohol_visual)
    
    def show_multisensory_neutral_visual_olfactory(self):
        self.stacked_widget.setCurrentWidget(self.multisensory_neutral_visual_olfactory)
    
    def show_multisensory_alcohol_visual_olfactory(self):
        self.stacked_widget.setCurrentWidget(self.multisensory_alcohol_visual_olfactory)
    
    def show_multisensory_neutral_visual_tactile_olfactory(self):
        self.stacked_widget.setCurrentWidget(self.multisensory_neutral_visual_tactile_olfactory)
    
    def show_multisensory_alcohol_visual_tactile_olfactory(self):
        self.stacked_widget.setCurrentWidget(self.multisensory_alcohol_visual_tactile_olfactory)
    
    def open_secondary_gui(self, state):
        if state == Qt.Checked:
            self.display_window = DisplayWindow(self)
            self.display_window.show()
        else:
            if hasattr(self, 'display_window'):
                self.display_window.close()

class Sidebar(QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: #53366b;")
        self.setMinimumWidth(330)
        
        self.layout = QVBoxLayout(self)
        
        self.brand_frame = QFrame(self)
        self.brand_frame.setStyleSheet(f"background-color: #F5E1FD;")
        self.brand_frame.setMaximumHeight(105)
        self.layout.addWidget(self.brand_frame)
        
        self.brand_layout = QVBoxLayout(self.brand_frame)
        
        self.sidebar_title1 = QLabel("Multisensory", self)
        self.sidebar_title1.setFont(QFont("", 15, QFont.Bold))
        self.sidebar_title1.setStyleSheet(f"background-color: #F5E1FD;")
        self.brand_layout.addWidget(self.sidebar_title1)
        
        self.sidebar_title2 = QLabel("Tests", self)
        self.sidebar_title2.setFont(QFont("", 15, QFont.Bold))
        self.sidebar_title2.setStyleSheet(f"background-color: #F5E1FD;")
        self.brand_layout.addWidget(self.sidebar_title2)
        
        self.submenu_frame = QFrame(self)
        self.submenu_frame.setStyleSheet(f"background-color: #F5E1FD;")
        self.layout.addWidget(self.submenu_frame)
        
        self.submenu_layout = QVBoxLayout(self.submenu_frame)
        self.submenu_layout.setAlignment(Qt.AlignTop)  # Align submenu to the top
        
        self.add_submenu("Experiment 1", [
            ("Unisensory Neutral Visual", parent.show_unisensory_neutral_visual),
            ("Unisensory Alcohol Visual", parent.show_unisensory_alcohol_visual),
            ("Multisensory Neutral Visual & Olfactory", parent.show_multisensory_neutral_visual_olfactory),
            ("Multisensory Alcohol Visual & Olfactory", parent.show_multisensory_alcohol_visual_olfactory),
            ("Multisensory Neutral Visual, Tactile & Olfactory", parent.show_multisensory_neutral_visual_tactile_olfactory),
            ("Multisensory Alcohol Visual, Tactile & Olfactory", parent.show_multisensory_alcohol_visual_tactile_olfactory)
        ])
        
    def add_submenu(self, heading, options):
        heading_label = QLabel(heading, self)
        heading_label.setFont(QFont("Arial", 9))
        heading_label.setStyleSheet(f"background-color: #F5E1FD; color: #333333;")
        self.submenu_layout.addWidget(heading_label)
        
        for option_text, option_func in options:
            button = QPushButton(option_text, self)
            button.setFont(QFont("Arial", 8, QFont.Bold))
            button.setStyleSheet(f"background-color: #F5E1FD;")
            button.clicked.connect(option_func)
            self.submenu_layout.addWidget(button)

class MainFrame(QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        
        self.stacked_widget = QStackedWidget(self)
        self.layout.addWidget(self.stacked_widget)

class Frame(QFrame):
    def __init__(self, parent, title):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        
        top_frame = QFrame(self)
        top_frame.setStyleSheet(f"background-color: rgb(146, 63, 179);")
        top_frame.setMaximumHeight(140)
        self.layout.addWidget(top_frame)
        
        top_layout = QVBoxLayout(top_frame)
        
        header = QLabel(title, self)
        header.setFont(QFont("Helvetica", 17, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet(f"background-color: rgb(146, 63, 179);")
        top_layout.addWidget(header)
        
        button_layout = QHBoxLayout()
        top_layout.addLayout(button_layout)
        
        start_button = QPushButton("Start", self)
        button_layout.addWidget(start_button)
        
        stop_button = QPushButton("Stop", self)
        button_layout.addWidget(stop_button)
        
        pause_button = QPushButton("Pause", self)
        button_layout.addWidget(pause_button)
        
        vr_button = QCheckBox("VR", self)
        button_layout.addWidget(vr_button)
        
        display_button = QCheckBox("Display", self)
        display_button.stateChanged.connect(parent.open_secondary_gui)
        button_layout.addWidget(display_button)
        
        viewing_booth_button = QCheckBox("Viewing Booth", self)
        button_layout.addWidget(viewing_booth_button)
        
        middle_frame = QFrame(self)
        middle_frame.setStyleSheet(f"background-color: #CBC3E3;")
        middle_frame.setMinimumHeight(490)
        self.layout.addWidget(middle_frame)
        
        bottom_frame = QFrame(self)
        bottom_frame.setStyleSheet(f"background-color: #bc85fa;")
        bottom_frame.setMaximumHeight(70)
        self.layout.addWidget(bottom_frame)
        
        bottom_layout = QHBoxLayout(bottom_frame)
        
        visual_checkbox = QCheckBox("Visual", self)
        bottom_layout.addWidget(visual_checkbox)
        
        olfactory_checkbox = QCheckBox("Olfactory", self)
        bottom_layout.addWidget(olfactory_checkbox)
        
        tactile_checkbox = QCheckBox("Tactile", self)
        bottom_layout.addWidget(tactile_checkbox)
        
        input_keyboard_checkbox = QCheckBox("Input Keyboard", self)
        bottom_layout.addWidget(input_keyboard_checkbox)
        
        eye_tracker_checkbox = QCheckBox("Eye Tracker", self)
        bottom_layout.addWidget(eye_tracker_checkbox)

class DisplayWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Display App")
        self.setGeometry(100, 100, 700, 700)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        self.layout = QVBoxLayout(central_widget)
        
        # Top frame with start and stop buttons
        top_frame = QFrame(self)
        top_frame.setMaximumHeight(50)
        top_frame.setStyleSheet("background-color: #F0F0F0;")
        self.layout.addWidget(top_frame)
        
        top_layout = QHBoxLayout(top_frame)
        
        start_button = QPushButton("Start", self)
        top_layout.addWidget(start_button)
        
        stop_button = QPushButton("Stop", self)
        top_layout.addWidget(stop_button)
        
        # Bottom frame with the image
        bottom_frame = QFrame(self)
        bottom_frame.setStyleSheet("background-color: #FFFFFF;")
        self.layout.addWidget(bottom_frame)
        
        bottom_layout = QVBoxLayout(bottom_frame)
        
        image_path = os.path.join(os.path.dirname(__file__), 'Images', 'Beer.jpg')
        pixmap = QPixmap(image_path)
        
        self.image_label = QLabel(self)
        self.image_label.setPixmap(pixmap)
        self.image_label.setAlignment(Qt.AlignCenter)
        
        bottom_layout.addWidget(self.image_label)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = GUI()
    gui.show()
    sys.exit(app.exec_())