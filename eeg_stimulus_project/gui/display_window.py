import sys
import os
sys.path.append('C:\\Users\\cpl4168\\Documents\\Paid Research\\Software-for-Paid-Research-')
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QMainWindow, QWidget, QVBoxLayout, QStackedLayout, QSizePolicy
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt, QTimer, QEvent, pyqtSignal
from eeg_stimulus_project.stimulus.Display import Display
from eeg_stimulus_project.data.data_saving import Save_Data

class MirroredDisplayWindow(QWidget):
    def __init__(self, parent=None, current_test=None):
        super().__init__(parent)
        self.current_test = current_test
        self.setFixedSize(700, 700)

        self.stacked_layout = QStackedLayout(self)

        # Overlay widget
        self.overlay_widget = QWidget()
        self.overlay_layout = QVBoxLayout(self.overlay_widget)
        self.overlay_widget.setStyleSheet("background-color: white;")
        self.overlay_widget.setGeometry(0, 0, 700, 650)

        self.instructions_label = QLabel(
            "Directions: [Your directions here]\n\nPress the SPACE BAR to begin the experiment.",
            self.overlay_widget
        )
        self.instructions_label.setFont(QFont("Arial", 18))
        self.instructions_label.setAlignment(Qt.AlignCenter)
        self.overlay_layout.addWidget(self.instructions_label)

        self.countdown_label = QLabel("", self.overlay_widget)
        self.countdown_label.setFont(QFont("Arial", 36, QFont.Bold))
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.setVisible(False)
        self.overlay_layout.addWidget(self.countdown_label)

        # Main experiment widget
        self.experiment_widget = QWidget()
        self.experiment_layout = QVBoxLayout(self.experiment_widget)

        bottom_frame = QFrame(self.experiment_widget)
        bottom_frame.setStyleSheet("background-color: #FFFFFF;")
        bottom_layout = QHBoxLayout(bottom_frame)
        self.image_label = QLabel(self.experiment_widget)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        bottom_layout.addWidget(self.image_label)
        self.experiment_layout.addWidget(bottom_frame)

        self.timer_label = QLabel("00:00:00", self.experiment_widget)
        self.timer_label.setFont(QFont("Arial", 20))
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setMaximumHeight(50)
        self.experiment_layout.addWidget(self.timer_label)

        self.stacked_layout.addWidget(self.overlay_widget)      # index 0
        self.stacked_layout.addWidget(self.experiment_widget)   # index 1

        self.stacked_layout.setCurrentIndex(0)

    # Methods to update the mirror
    def set_pixmap(self, pixmap):
        if pixmap:
            scaled_pixmap = pixmap.scaled(
                self.image_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
        else:
            self.image_label.clear()

    def set_instruction_text(self, text, font=None):
        self.image_label.clear()
        self.instructions_label.setText(text)
        if font:
            self.instructions_label.setFont(font)

    def set_timer(self, text):
        self.timer_label.setText(text)

    def set_overlay_visible(self, visible):
        self.stacked_layout.setCurrentIndex(0 if visible else 1)

    def set_countdown(self, text, visible=True):
        self.countdown_label.setText(text)
        self.countdown_label.setVisible(visible)

    def start_countdown(self):
        self.instructions_label.setVisible(False)
        self.countdown_label.setVisible(True)
        self.countdown_seconds = 3
        self.countdown_label.setText(str(self.countdown_seconds))
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.countdown_timer.start(1000)

    def update_countdown(self):
        self.countdown_seconds -= 1
        if self.countdown_seconds > 0:
            self.countdown_label.setText(str(self.countdown_seconds))
        else:
            self.countdown_timer.stop()
            self.countdown_label.setText("Go!")
            QTimer.singleShot(1000, self.begin_experiment)

    def begin_experiment(self):
        self.stacked_layout.setCurrentIndex(1)
        
# --- In DisplayWindow ---

class DisplayWindow(QMainWindow):
    experiment_started = pyqtSignal()

    def __init__(self, parent=None, current_test=None):
        super().__init__(parent)
        self.current_test = current_test
        self.setWindowTitle("Display App")
        self.setGeometry(100, 100, 700, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.stacked_layout = QStackedLayout(central_widget)

        # --- Overlay widget for instructions and countdown ---
        self.overlay_widget = QWidget()
        self.overlay_layout = QVBoxLayout(self.overlay_widget)
        self.overlay_widget.setStyleSheet("background-color: white;")
        self.overlay_widget.setGeometry(0, 0, 700, 650)

        self.instructions_label = QLabel(
            "Directions: [Your directions here]\n\nPress the SPACE BAR to begin the experiment.",
            self.overlay_widget
        )
        self.instructions_label.setFont(QFont("Arial", 18))
        self.instructions_label.setAlignment(Qt.AlignCenter)
        self.overlay_layout.addWidget(self.instructions_label)

        self.countdown_label = QLabel("", self.overlay_widget)
        self.countdown_label.setFont(QFont("Arial", 36, QFont.Bold))
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.setVisible(False)
        self.overlay_layout.addWidget(self.countdown_label)

        # --- Main experiment widget (image, timer, buttons) ---
        self.experiment_widget = QWidget()
        self.experiment_layout = QVBoxLayout(self.experiment_widget)

        # Bottom frame with the image
        bottom_frame = QFrame(self.experiment_widget)
        bottom_frame.setStyleSheet("background-color: #FFFFFF;")
        bottom_layout = QHBoxLayout(bottom_frame)
        self.image_label = QLabel(self.experiment_widget)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        bottom_layout.addWidget(self.image_label)
        self.experiment_layout.addWidget(bottom_frame)

        # Timer label
        self.timer_label = QLabel("00:00:00", self.experiment_widget)
        self.timer_label.setFont(QFont("Arial", 20))
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setMaximumHeight(50)
        self.experiment_layout.addWidget(self.timer_label)

        # Add both widgets to the stacked layout
        self.stacked_layout.addWidget(self.overlay_widget)      # index 0
        self.stacked_layout.addWidget(self.experiment_widget)   # index 1

        # Show overlay first
        self.stacked_layout.setCurrentIndex(0)

        # Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.elapsed_time = 0

        self.Paused = False

        # User data
        self.user_data = {
            'user_inputs': [],
            'elapsed_time': []
        }  # List to store user inputs

        self.setFocusPolicy(Qt.StrongFocus)
        self.countdown_seconds = 3

        self.current_pixmap = None

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
            self.current_pixmap = pixmap
            self.update_image_label()
            self.current_image_index += 1
            QTimer.singleShot(5000, self.display_images_passive)  # Display each image for 5 seconds
        else:
            self.current_image_index = 0  # Reset for the next trial

    def display_images_stroop(self):
        self.base_dir = os.environ.get('BASE_DIR', '')
        self.test_number = os.environ.get('TEST_NUMBER', '')
        
        if self.current_image_index < len(self.images):
            pixmap = QPixmap(self.images[self.current_image_index].filename)
            self.current_pixmap = pixmap
            self.update_image_label()
            QTimer.singleShot(2000, self.hide_image)  # Hide image after 2 seconds
        else:
            self.timer.stop()
            save_data = Save_Data(self.base_dir, self.test_number)
            save_data.save_data_stroop(self.current_test, self.user_data['user_inputs'], self.user_data['elapsed_time'])
            self.current_image_index = 0  # Reset for the next trial

    def update_image_label(self):
        if self.current_pixmap:
            scaled_pixmap = self.current_pixmap.scaled(
                self.image_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
            # Update the mirror
            if hasattr(self, 'mirror_widget') and self.mirror_widget is not None:
                self.mirror_widget.set_pixmap(self.current_pixmap)
        else:
            self.image_label.clear()
            if hasattr(self, 'mirror_widget'):
                self.mirror_widget.set_pixmap(None)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.image_label.text():  # If instructions are showing
            self.set_instruction_text()
        else:
            self.update_image_label()

    def set_instruction_text(self):
        text = "Press the 'Y' key if congruent.\nPress the 'N' key if incongruent."
        self.image_label.setText(text)
        self.image_label.setAlignment(Qt.AlignCenter)
        label_height = self.image_label.height()
        font_size = max(8, int(label_height * 0.04))
        font = QFont("Arial", font_size, QFont.Bold)
        self.image_label.setFont(font)
        # Update the mirror
        if hasattr(self, 'mirror_widget'):
            self.mirror_widget.set_instruction_text(text, font)

    def hide_image(self):
        self.image_label.clear()  # Clear the image
        self.set_instruction_text()
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
        timer_text = f"{minutes:02}:{seconds:02}:{milliseconds:03}"
        self.timer_label.setText(timer_text)
        if hasattr(self, 'mirror_widget') and self.mirror_widget is not None:
            self.mirror_widget.set_timer(self.timer_label.text())
        
    def keyPressEvent(self, event):
        if self.overlay_widget.isVisible() and event.key() == Qt.Key_Space:
            self.start_countdown()
        else:
            super().keyPressEvent(event)

    def start_countdown(self):
        self.instructions_label.setVisible(False)
        self.countdown_label.setVisible(True)
        self.countdown_seconds = 3
        self.countdown_label.setText(str(self.countdown_seconds))
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.countdown_timer.start(1000)
        # Start the mirror's countdown as well
        if hasattr(self, 'mirror_widget'):
            self.mirror_widget.start_countdown()

    def update_countdown(self):
        self.countdown_seconds -= 1
        if self.countdown_seconds > 0:
            self.countdown_label.setText(str(self.countdown_seconds))
        else:
            self.countdown_timer.stop()
            self.countdown_label.setText("Go!")
            QTimer.singleShot(1000, self.begin_experiment)

    def begin_experiment(self):
        self.stacked_layout.setCurrentIndex(1)
        if hasattr(self, 'mirror_widget'):
            self.mirror_widget.begin_experiment()
        self.experiment_started.emit()  # Emit the signal to start the experiment
        self.run_trial()

    def set_mirror(self, mirror_widget):
        self.mirror_widget = mirror_widget

    def closeEvent(self, event):
        # Stop the timer to prevent update_timer from running after close
        if hasattr(self, 'timer') and self.timer.isActive():
            self.timer.stop()
        # Close or remove the mirror widget if it exists
        if hasattr(self, 'mirror_widget') and self.mirror_widget is not None:
            self.mirror_widget.setParent(None)  # Remove from layout
            self.mirror_widget.deleteLater()    # Schedule for deletion
            self.mirror_widget = None
        super().closeEvent(event)