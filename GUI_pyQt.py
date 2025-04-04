import sys
from time import sleep
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QCheckBox, QFrame, QStackedWidget
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt, QTimer, QEvent
import os
import random
from Display import Display  # Import the Display class from Display.py
import csv
from save_data import Save_Data  # Import the Save_Data class
from EEG_widget import EEGGraphWidget # Import the EEGGraphWidget from EEG_widget.py

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
        
        self.unisensory_neutral_visual = self.create_frame("Unisensory Neutral Visual", is_stroop_test=False)
        self.unisensory_alcohol_visual = self.create_frame("Unisensory Alcohol Visual", is_stroop_test=False)
        self.multisensory_neutral_visual_olfactory = self.create_frame("Multisensory Neutral Visual & Olfactory", is_stroop_test=False)
        self.multisensory_alcohol_visual_olfactory = self.create_frame("Multisensory Alcohol Visual & Olfactory", is_stroop_test=False)
        self.multisensory_neutral_visual_tactile_olfactory = self.create_frame("Multisensory Neutral Visual, Tactile & Olfactory", is_stroop_test=False)
        self.multisensory_alcohol_visual_tactile_olfactory = self.create_frame("Multisensory Alcohol Visual, Tactile & Olfactory", is_stroop_test=False)
        
        # New frames for Stroop Test
        self.multisensory_alcohol_visual_tactile = self.create_frame("Multisensory Alcohol (Visual & Tactile)", is_stroop_test=True)
        self.multisensory_neutral_visual_tactile = self.create_frame("Multisensory Neutral (Visual & Tactile)", is_stroop_test=True)
        self.multisensory_alcohol_visual_olfactory2 = self.create_frame("Multisensory Alcohol (Visual & Olfactory)", is_stroop_test=True)
        self.multisensory_neutral_visual_olfactory2 = self.create_frame("Multisensory Neutral (Visual & Olfactory)", is_stroop_test=True)
        
        self.stacked_widget.addWidget(self.unisensory_neutral_visual)
        self.stacked_widget.addWidget(self.unisensory_alcohol_visual)
        self.stacked_widget.addWidget(self.multisensory_neutral_visual_olfactory)
        self.stacked_widget.addWidget(self.multisensory_alcohol_visual_olfactory)
        self.stacked_widget.addWidget(self.multisensory_neutral_visual_tactile_olfactory)
        self.stacked_widget.addWidget(self.multisensory_alcohol_visual_tactile_olfactory)
        
        # Add new frames to stacked_widget
        self.stacked_widget.addWidget(self.multisensory_alcohol_visual_tactile)
        self.stacked_widget.addWidget(self.multisensory_neutral_visual_tactile)
        self.stacked_widget.addWidget(self.multisensory_alcohol_visual_olfactory2)
        self.stacked_widget.addWidget(self.multisensory_neutral_visual_olfactory2)
        
        self.stacked_widget.setCurrentWidget(self.unisensory_neutral_visual)
        
    def create_frame(self, title, is_stroop_test=False):
        return Frame(self, title, is_stroop_test)
    
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
    
    # New methods to show new frames
    def show_multisensory_alcohol_visual_tactile(self):
        self.stacked_widget.setCurrentWidget(self.multisensory_alcohol_visual_tactile)
    
    def show_multisensory_neutral_visual_tactile(self):
        self.stacked_widget.setCurrentWidget(self.multisensory_neutral_visual_tactile)
    
    def show_multisensory_alcohol_visual_olfactory2(self):
        self.stacked_widget.setCurrentWidget(self.multisensory_alcohol_visual_olfactory2)
    
    def show_multisensory_neutral_visual_olfactory2(self):
        self.stacked_widget.setCurrentWidget(self.multisensory_neutral_visual_olfactory2)
    
    def open_secondary_gui(self, state):
        if state == Qt.Checked:
            self.display_window = DisplayWindow(self)
            self.display_window.show()
        else:
            if hasattr(self, 'display_window'):
                self.display_window.close()
    
    def get_current_test(self):
        current_widget = self.stacked_widget.currentWidget()
        if current_widget == self.unisensory_neutral_visual:
            return 'Unisensory Neutral Visual'
        elif current_widget == self.unisensory_alcohol_visual:
            return 'Unisensory Alcohol Visual'
        elif current_widget == self.multisensory_neutral_visual_olfactory:
            return 'Multisensory Neutral Visual & Olfactory'
        elif current_widget == self.multisensory_alcohol_visual_olfactory:
            return 'Multisensory Alcohol Visual & Olfactory'
        elif current_widget == self.multisensory_neutral_visual_tactile_olfactory:
            return 'Multisensory Neutral Visual, Tactile & Olfactory'
        elif current_widget == self.multisensory_alcohol_visual_tactile_olfactory:
            return 'Multisensory Alcohol Visual, Tactile & Olfactory'
        elif current_widget == self.multisensory_alcohol_visual_tactile:
            return 'Multisensory Alcohol (Visual & Tactile)'
        elif current_widget == self.multisensory_neutral_visual_tactile:
            return 'Multisensory Neutral (Visual & Tactile)'
        elif current_widget == self.multisensory_alcohol_visual_olfactory2:
            return 'Multisensory Alcohol (Visual & Olfactory)'
        elif current_widget == self.multisensory_neutral_visual_olfactory2:
            return 'Multisensory Neutral (Visual & Olfactory)'
        else:
            return None

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
        
        self.add_submenu("Passive Viewing", [
            ("Unisensory Neutral Visual", parent.show_unisensory_neutral_visual),
            ("Unisensory Alcohol Visual", parent.show_unisensory_alcohol_visual),
            ("Multisensory Neutral Visual & Olfactory", parent.show_multisensory_neutral_visual_olfactory),
            ("Multisensory Alcohol Visual & Olfactory", parent.show_multisensory_alcohol_visual_olfactory),
            ("Multisensory Neutral Visual, Tactile & Olfactory", parent.show_multisensory_neutral_visual_tactile_olfactory),
            ("Multisensory Alcohol Visual, Tactile & Olfactory", parent.show_multisensory_alcohol_visual_tactile_olfactory)
        ])
        
        # Add new submenu for Stroop Test
        self.add_submenu("Stroop Test", [
            ("Multisensory Alcohol (Visual & Tactile)", parent.show_multisensory_alcohol_visual_tactile),
            ("Multisensory Neutral (Visual & Tactile)", parent.show_multisensory_neutral_visual_tactile),
            ("Multisensory Alcohol (Visual & Olfactory)", parent.show_multisensory_alcohol_visual_olfactory2),
            ("Multisensory Neutral (Visual & Olfactory)", parent.show_multisensory_neutral_visual_olfactory2)
        ])
        
    def add_submenu(self, heading, options):
        heading_label = QLabel(heading, self)
        heading_label.setFont(QFont("Arial", 7))
        heading_label.setStyleSheet(f"background-color: #F5E1FD; color: #333333;")
        self.submenu_layout.addWidget(heading_label)
        
        for option_text, option_func in options:
            button = QPushButton(option_text, self)
            button.setFont(QFont("Arial", 6, QFont.Bold))
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
    def __init__(self, parent, title, is_stroop_test=False):
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
        
        # Middle frame with the EEG graph
        self.middle_frame = QFrame(self)
        self.middle_frame.setStyleSheet(f"background-color: #CBC3E3;")
        self.middle_frame.setMinimumHeight(490)
        self.layout.addWidget(self.middle_frame)

        middle_layout = QVBoxLayout(self.middle_frame)

        # Add EEGGraphWidget to the middle frame
        self.eeg_graph = EEGGraphWidget()
        middle_layout.addWidget(self.eeg_graph)

        # Add navigation buttons for EEG graph
        nav_layout = QHBoxLayout()
        middle_layout.addLayout(nav_layout)

        prev_button = QPushButton("Previous Page", self)
        prev_button.clicked.connect(self.eeg_graph.previous_page)
        nav_layout.addWidget(prev_button)

        next_button = QPushButton("Next Page", self)
        next_button.clicked.connect(self.eeg_graph.next_page)
        nav_layout.addWidget(next_button)
        
        if is_stroop_test:
            button_layout = QHBoxLayout()
            top_layout.addLayout(button_layout)

            start_button = QPushButton("Start", self)
            #start_button.clicked.connect(parent.open_secondary_gui)
            button_layout.addWidget(start_button)

            stop_button = QPushButton("Stop", self)
            button_layout.addWidget(stop_button)

            pause_button = QPushButton("Pause", self)
            button_layout.addWidget(pause_button)

            display_button = QCheckBox("Display", self)
            display_button.stateChanged.connect(parent.open_secondary_gui)
            button_layout.addWidget(display_button)

            bottom_frame = QFrame(self)
            bottom_frame.setStyleSheet(f"background-color: #bc85fa;")
            bottom_frame.setMaximumHeight(70)
            self.layout.addWidget(bottom_frame)

        if not is_stroop_test:
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

        self.subject_id = os.getenv('SUBJECT_ID')
        self.test_number = os.getenv('TEST_NUMBER')
        self.base_dir = os.getenv('BASE_DIR')

        self.parent = parent  # Store reference to parent GUI
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        self.layout = QVBoxLayout(central_widget)
        
        # Top frame with start and stop buttons
        top_frame = QFrame(self)
        top_frame.setMaximumHeight(50)
        top_frame.setStyleSheet("background-color:rgb(255, 255, 255);")
        self.layout.addWidget(top_frame)
        
        top_layout = QHBoxLayout(top_frame)
        
        start_button = QPushButton("Start", self)
        start_button.clicked.connect(self.run_trial)
        top_layout.addWidget(start_button)

        pause_button = QPushButton("Pause", self)
        pause_button.clicked.connect(self.pause_trial)
        top_layout.addWidget(pause_button)
        
        resume_button = QPushButton("Resume", self)
        resume_button.clicked.connect(self.resume_trial)
        top_layout.addWidget(resume_button)
        
        stop_button = QPushButton("Stop", self)
        top_layout.addWidget(stop_button)
        
        # Bottom frame with the image
        bottom_frame = QFrame(self)
        bottom_frame.setStyleSheet("background-color: #FFFFFF;")
        self.layout.addWidget(bottom_frame)
        
        bottom_layout = QVBoxLayout(bottom_frame)
        
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        bottom_layout.addWidget(self.image_label)

        # Timer label
        self.timer_label = QLabel("00:00:00", self)
        self.timer_label.setFont(QFont("Arial", 20))
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setMaximumHeight(50)
        self.layout.addWidget(self.timer_label)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.elapsed_time = 0

        self.Paused = False

        self.user_data = {
            'user_inputs': [],
            'elapsed_time': []
        }  # List to store user inputs

    def run_trial(self, event=None):
        current_test = self.parent.get_current_test()
        print(f"Current test: {current_test}")
        print(f"Available tests: {list(Display.test_assets.keys())}")
        if current_test:
            try:
                self.images = Display.test_assets[current_test]
                self.current_image_index = 0
                self.elapsed_time = 0  # Reset the elapsed time
                self.timer.start(1)  # Start the timer with 100 ms interval
                if current_test in ['Multisensory Alcohol (Visual & Tactile)', 'Multisensory Neutral (Visual & Tactile)', 'Multisensory Alcohol (Visual & Olfactory)', 'Multisensory Neutral (Visual & Olfactory)']:
                    self.display_images_stroop()
                else:
                    self.display_images_passive()
            except KeyError as e:
                print(f"KeyError: {e}")

    def pause_trial(self, event=None):
        self.timer.stop()
        self.Paused = True
        print(self.elapsed_time)
        
    def resume_trial(self, event=None):
        self.timer.start(1)
        self.Paused = False
               
    def display_images_passive(self):
        if self.current_image_index < len(self.images):
            pixmap = QPixmap(self.images[self.current_image_index].filename)
            self.image_label.setPixmap(pixmap)
            self.current_image_index += 1
            QTimer.singleShot(5000, self.display_images_passive)  # Display each image for 5 seconds
        else:
            self.current_image_index = 0  # Reset for the next trial

    def display_images_stroop(self):
        if self.current_image_index < len(self.images):
            pixmap = QPixmap(self.images[self.current_image_index].filename)
            self.image_label.setPixmap(pixmap)
            QTimer.singleShot(2000, self.hide_image)  # Hide image after 2 seconds
        else:
            self.timer.stop()
            save_data = Save_Data(self.base_dir, self.test_number)
            save_data.save_data_stroop(self.parent.get_current_test(), self.user_data['user_inputs'], self.user_data['elapsed_time'])
            self.current_image_index = 0  # Reset for the next trial

    def hide_image(self):
        self.image_label.clear()  # Clear the image
        self.image_label.setText("Press the 'Y' key if congruent.\nPress the 'N' key if incongruent.")  # Display text while waiting for input
        self.wait_for_input()  # Wait for input before displaying the next image

    def wait_for_input(self):
        self.installEventFilter(self)

    def eventFilter(self, source, event):
            if self.Paused == False:
                if event.type() == QEvent.KeyPress:
                    if event.key() == Qt.Key_Y or event.key() == Qt.Key_N:
                        if event.key() == Qt.Key_Y:
                            self.user_data['user_inputs'].append('Yes') # Store the user input
                        else:
                            self.user_data['user_inputs'].append('No')  # Store the user input
                        self.user_data['elapsed_time'].append(self.elapsed_time)  # Store the elapsed time
                        self.removeEventFilter(self)
                        self.display_next_image()
                        return True
            return super().eventFilter(source, event)

    def display_next_image(self):
        self.current_image_index += 1
        self.display_images_stroop()  # Display the next image

    def update_timer(self):
        self.elapsed_time += 1  # Increment by 1 millisecond
        minutes, remainder = divmod(self.elapsed_time, 60000)
        seconds, milliseconds = divmod(remainder, 1000)
        self.timer_label.setText(f"{minutes:02}:{seconds:02}:{milliseconds:03}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = GUI()
    gui.show()
    sys.exit(app.exec_())