import sys
import os
sys.path.append('C:\\Users\\srs1520\\Documents\\Paid Research\\Software-for-Paid-Research-')
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QMainWindow, QWidget, QVBoxLayout
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt, QTimer, QEvent
from eeg_stimulus_project.stimulus.Display import Display
from eeg_stimulus_project.data.data_saving import Save_Data

class DisplayWindow(QMainWindow):
    def __init__(self, parent=None, current_test=None):
        super().__init__(parent)
        self.current_test=current_test
        self.setWindowTitle("Display App")
        self.setGeometry(100, 100, 700, 700)

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
        
        # Bottom frame with the image
        bottom_frame = QFrame(self)
        bottom_frame.setStyleSheet("background-color: #FFFFFF;")
        self.layout.addWidget(bottom_frame)
        
        bottom_layout = QHBoxLayout(bottom_frame)
        
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
        current_test = self.current_test
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
        self.base_dir = os.environ.get('BASE_DIR', '')
        self.test_number = os.environ.get('TEST_NUMBER', '')
        
        if self.current_image_index < len(self.images):
            pixmap = QPixmap(self.images[self.current_image_index].filename)
            self.image_label.setPixmap(pixmap)
            QTimer.singleShot(2000, self.hide_image)  # Hide image after 2 seconds
        else:
            self.timer.stop()
            save_data = Save_Data(self.base_dir, self.test_number)
            save_data.save_data_stroop(self.current_test, self.user_data['user_inputs'], self.user_data['elapsed_time'])
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

