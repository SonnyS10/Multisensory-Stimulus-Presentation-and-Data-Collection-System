import sys
import os
from pathlib import Path
import csv
from pynput import keyboard

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QMainWindow, QWidget, QVBoxLayout, QStackedLayout, QSizePolicy, QPushButton, QGridLayout, QApplication
from PyQt5.QtGui import QFont, QPixmap, QKeyEvent
from PyQt5.QtCore import Qt, QTimer, QEvent, pyqtSignal, pyqtSlot
from eeg_stimulus_project.assets.asset_handler import Display
from eeg_stimulus_project.data.data_saving import Save_Data
from eeg_stimulus_project.lsl.labels import LSLLabelStream
from eeg_stimulus_project.utils.pupil_labs import PupilLabs
from eeg_stimulus_project.gui.stimulus_order_frame import CravingRatingAsset
import threading
import json
import time
import logging
import random
from logging.handlers import QueueHandler

#This is the class that creates the mirror display window that resides in the main display window to be used by the experimenter to make sure the experiment is running correctly
#It contains the same layout and functionality as the main display window, but it is not interactive
#It is used to show the experimenter what the subject is seeing
class MirroredDisplayWindow(QWidget):
    def __init__(self, parent=None, current_test=None):
        super().__init__(parent)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  

        self.current_test = current_test

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

        self.show_crosshair_instructions()

        self.paused = False

    #Method to update the mirror image
    def set_pixmap(self, pixmap):
        if pixmap:
            scaled_pixmap = pixmap.scaled(
                self.image_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
            self.set_overlay_visible(False)  # <-- Switch to experiment view
        else:
            self.image_label.clear()

    #Method to update the mirror text        
    def set_instruction_text(self, text=None, font=None):
        if text is None:
            text = "Press the 'Y' key if congruent.\nPress the 'N' key if incongruent."
        self.image_label.clear()
        self.instructions_label.setText(text)
        self.instructions_label.setAlignment(Qt.AlignCenter)
        self.instructions_label.setVisible(True)
        self.countdown_label.setVisible(False)  # <-- Hide countdown label
        if font is None:
            # Use a more reliable font size calculation with a reasonable minimum
            label_height = self.instructions_label.height()
            if label_height <= 0:
                # If height is not yet available, use a reasonable default
                font_size = 18
            else:
                font_size = max(18, int(label_height * 0.04))  # Increased minimum from 8 to 18
            font = QFont("Arial", font_size, QFont.Bold)
        self.instructions_label.setFont(font)
        self.set_overlay_visible(True)

    #Method to set the timer text
    def set_timer(self, text):
        self.timer_label.setText(text)

    #Method to set the overlay visibility
    def set_overlay_visible(self, visible):
        self.stacked_layout.setCurrentIndex(0 if visible else 1)

    #Method to set the countdown text
    def set_countdown(self, text, visible=True):
        self.countdown_label.setText(text)
        self.countdown_label.setVisible(visible)

    #Method to start the countdown only called from the DisplayWindow
    def start_countdown(self):
        self.instructions_label.setVisible(False)
        self.countdown_label.setVisible(True)
        self.countdown_seconds = 3
        self.countdown_label.setText(str(self.countdown_seconds))
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.countdown_timer.start(1000)

    #Method to update the countdown
    def update_countdown(self):
        self.countdown_seconds -= 1
        if self.countdown_seconds > 0:
            self.countdown_label.setText(str(self.countdown_seconds))
        else:
            self.countdown_timer.stop()
            self.countdown_label.setText("Go!")
            if "Tactile" not in self.current_test:
                QTimer.singleShot(1000, self.begin_experiment)

    #Method to show the instruction for the next image
    def show_instruction_for_next_image(self, text=None, font=None):
        self.set_instruction_text(text, font)
        self.set_pixmap(None)

    #Method to show the image
    def begin_experiment(self):
        self.stacked_layout.setCurrentIndex(1)

    #Method to pause the trial, this method is called from the DisplayWindow when the trial is paused
    def pause_trial(self, event=None):
        self.paused = True

    #Method to resume the trial, this method is called from the DisplayWindow when the trial is resumed
    def resume_trial(self, event=None):
        self.paused = False
        
    def end_screen(self):
        self.instructions_label.setText("Test has ended.\n Please wait for the experimenter to close the test.")
        self.instructions_label.setFont(QFont("Arial", 22))
        self.instructions_label.setAlignment(Qt.AlignCenter)
        self.instructions_label.setVisible(True)
        self.countdown_label.setVisible(False)
        self.overlay_widget.setStyleSheet("background-color: white;")
        self.overlay_widget.setMinimumSize(0, 0)
        self.overlay_widget.setMaximumSize(16777215, 16777215)
        self.stacked_layout.setCurrentWidget(self.overlay_widget)
        if hasattr(self, 'mirror_widget') and self.mirror_widget is not None:
            self.mirror_widget.end_screen()

    def show_crosshair_instructions(self):
        self.instructions_label.setFont(QFont("Arial", 18))
        self.instructions_label.setText("Instructions: Please relax and focus on the crosshair when it appears.\n\nThis will last for 2 minutes.")
        self.instructions_label.setVisible(True)
        self.countdown_label.setVisible(False)
        self.overlay_widget.setVisible(True)
        self.stacked_layout.setCurrentWidget(self.overlay_widget)
        self.stacked_layout.setCurrentIndex(0)
    
    def show_crosshair_period(self):
        self.instructions_label.setFont(QFont("Arial", 72, QFont.Bold))
        self.instructions_label.setText("+")
        self.instructions_label.setAlignment(Qt.AlignCenter)
        self.instructions_label.setVisible(True)
        self.countdown_label.setVisible(False)
        self.overlay_widget.setVisible(True)
        self.stacked_layout.setCurrentWidget(self.overlay_widget)
    
    def show_main_instructions(self):
        self.instructions_label.setFont(QFont("Arial", 18))
        self.instructions_label.setText("Directions: [Your directions here]\n\nPress the SPACE BAR to begin the experiment.")
        self.instructions_label.setVisible(True)
        self.countdown_label.setVisible(False)
        self.overlay_widget.setVisible(True)
        self.stacked_layout.setCurrentWidget(self.overlay_widget)

#This is the main display window that contains the experiment and the logic to make the mirror display function 
#It is the main window that the subject sees and interacts with
class DisplayWindow(QMainWindow):
    experiment_started = pyqtSignal()
    proceed_after_crosshair = pyqtSignal()  # Add this at class level

    def __init__(self, connection, log_queue, label_stream, parent_frame, current_test, base_dir, test_number,
                 eyetracker=None, shared_status=None, client=False, alcohol_folder=None, non_alcohol_folder=None,
                 randomize_cues=False, seed=None, repetitions=None, local_mode=None):  # <-- Add repetitions here
        super().__init__()
        
        self.shared_status = shared_status if shared_status else {'eyetracker_connected': False}
        self.eyetracker = eyetracker
        self.client = client
        self.label_stream = label_stream if label_stream else LSLLabelStream()
        self.alcohol_folder = alcohol_folder
        self.non_alcohol_folder = non_alcohol_folder
        self.randomize_cues = randomize_cues
        self.seed = seed
        self.frame = parent_frame  # Store reference to the Frame instance
        self.repetitions = repetitions
        self.local_mode = local_mode

        if self.local_mode:
            if self.shared_status.get('eyetracker_connected', False):
                # Eye tracker is connected, uses same instance of eye tracker or creates a new one if needed
                if self.eyetracker is None or self.eyetracker.device is None:
                    self.eyetracker = PupilLabs()
                if self.eyetracker and self.eyetracker.device is not None:
                    self.eyetracker.start_recording()
                else:
                    logging.info("Eyetracker not connected")
                    self.send_message({"action": "client_log", "message": "Eyetracker not connected"})
            else:
                logging.info("Eyetracker not connected in Control Window")
                self.send_message({"action": "client_log", "message": "Eyetracker not connected in Control Window"})
     
        self.current_label = None

        self.current_test = current_test
        self.base_dir = base_dir
        self.test_number = test_number
        self.connection = connection

        self.setWindowTitle("Display App")
        self.setGeometry(100, 100, 700, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.stacked_layout = QStackedLayout(central_widget)

        self.overlay_widget = QWidget()
        self.overlay_layout = QVBoxLayout(self.overlay_widget)
        self.overlay_widget.setStyleSheet("background-color: white;")
        self.overlay_widget.setGeometry(0, 0, 700, 650)

        #This is the overlay that shows the instructions for the experiment that the subject sees
        #IN THE FUTURE THIS SHOULD BE DIFFERENT FOR EACH TEST
        self.instructions_label = QLabel("Directions: [Your directions here]\n\nPress the SPACE BAR to begin the experiment.", self.overlay_widget)
        #self.instructions_label.setFont(QFont("Arial", 18))
        self.instructions_label.setAlignment(Qt.AlignCenter)
        self.instructions_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.instructions_label.setMaximumHeight(120)
        self.instructions_label.setWordWrap(True)
        self.overlay_layout.addWidget(self.instructions_label)

        self.countdown_label = QLabel("", self.overlay_widget)
        self.countdown_label.setFont(QFont("Arial", 36, QFont.Bold))
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.setVisible(False)
        self.overlay_layout.addWidget(self.countdown_label)

        # Main experiment widget
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
        #self.timer_label = QLabel("00:00:00", self.experiment_widget)
        #self.timer_label.setFont(QFont("Arial", 20))
        #self.timer_label.setAlignment(Qt.AlignCenter)
        #self.timer_label.setMaximumHeight(50)
        #self.experiment_layout.addWidget(self.timer_label)

        # Add both widgets to the stacked layout
        self.stacked_layout.addWidget(self.overlay_widget)      # index 0
        self.stacked_layout.addWidget(self.experiment_widget)   # index 1

        # Show overlay first
        self.stacked_layout.setCurrentIndex(0)

        self.show_crosshair_instructions()

        # Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.elapsed_time = 0

        # Passive Transition timer
        self.image_transition_timer = QTimer(self)
        self.image_transition_timer.setSingleShot(True)
        self.image_transition_timer.timeout.connect(self._on_image_transition)

        # Stroop Transition timer
        self.stroop_transition_timer = QTimer(self)
        self.stroop_transition_timer.setSingleShot(True)
        self.stroop_transition_timer.timeout.connect(self.hide_image)

        self.setup_logging(log_queue)

        #LSL Label Polling Timer - good for debugging 
        #self.label_poll_timer = QTimer(self)
        #self.label_poll_timer.timeout.connect(self.poll_label)
        #self.label_poll_timer.start(1000)  # Poll every 100 ms (change as needed)

        self.Paused = False

        # User data
        self.user_data = {
            'user_inputs': [],
            'elapsed_time': []
        }  # List to store user inputs and elapsed time

        self.setFocusPolicy(Qt.StrongFocus)
        self.countdown_seconds = 3

        self.current_pixmap = None

        # Initialize image index after pause
        self.paused_image_index = 0
        # Initialize paused time
        self.paused_time = 0 

        self.stopped = False  # Flag to indicate if the trial has been stopped

        #self.proceed_after_crosshair.connect(self.show_touch_instruction)
        self.waiting_for_next = False
        self.ready_for_space = False  # Flag to indicate if the space bar can be pressed to start the trial
        self.showing_touch_instruction = False  # Flag to indicate if the touch instruction is being shown
        self.waiting_for_initial_touch = False
        self.next_is_craving = False  # Flag to indicate if the next image is a craving rating image
        # Step 4: Load assets using user folders if provided
        Display.test_assets = Display.get_assets(
            alcohol_folder, non_alcohol_folder, randomize_cues=randomize_cues, seed=seed, repetitions=repetitions
        )

        # Move to monitor two and fullscreen
        app = QApplication.instance()
        if app is not None:
            screens = app.screens()
            if len(screens) > 1:
                screen = screens[1]  # Second monitor (index 1)
                geometry = screen.geometry()
                self.move(geometry.left(), geometry.top())
                self.showFullScreen()
            else:
                # Only one monitor, just move to default position and size (not fullscreen)
                self.move(100, 100)
                self.resize(700, 700)
        else:
            # Fallback: just move to default position and size
            self.move(100, 100)
            self.resize(700, 700)

    #This method is called when the user presses the space bar to start the experiment, it handles the countdown and the selection of the test to start the experiment
    def run_trial(self, event=None):
        current_test = self.current_test
        logging.info(f"Current test: {current_test}")
        self.send_message({"action": "client_log", "message": f"Current test: {current_test}"})
        #print(f"Available tests: {list(Display.test_assets.keys())}")
        if current_test:
            try:
                if self.paused_time > 0:
                    self.elapsed_time = self.paused_time
                    self.current_image_index = self.paused_image_index - 1
                    self.timer.start(1)  # Start the timer with 100 ms interval
                else:
                    # When loading images for the current test:
                    from eeg_stimulus_project.assets.asset_handler import Display
                    self.images = Display.get_assets(
                        alcohol_folder=self.alcohol_folder,
                        non_alcohol_folder=self.non_alcohol_folder,
                        randomize_cues=self.randomize_cues,
                        seed=self.seed,
                        repetitions=self.repetitions  # <-- Add this line
                    )[current_test]
                    self.current_image_index = 0  # Reset the image index for the new trial
                    self.elapsed_time = 0  # Reset the elapsed time
                    self.timer.start(1)  # Start the timer with 100 ms interval
                if current_test in ['Stroop Multisensory Alcohol (Visual & Tactile)', 'Stroop Multisensory Neutral (Visual & Tactile)', 'Stroop Multisensory Alcohol (Visual & Olfactory)', 'Stroop Multisensory Neutral (Visual & Olfactory)']:
                    self.display_images_stroop()
                else:
                    self.display_images_passive()
            except KeyError as e:
                logging.info(f"KeyError: {e}")
                self.send_message({"action": "client_log", "message": f"KeyError: {e}"})

        # After loading self.images:
        if "stroop" not in self.current_test.lower():
            if not self.images or not isinstance(self.images[-1], CravingRatingAsset):
                craving = CravingRatingAsset()
                craving.is_original = True
                self.images.append(craving)

    #This method is called when the user presses the pause button to pause the trial, it stops the timer and the image transition timer, it also stores the current image index and the elapsed time, it also tells the mirror widget to pause
    def pause_trial(self, event=None):
        label = "Paused Trial"
        self.send_message({"action": "label", "label": label})  # Send label to the server
        self.timer.stop()
        self.image_transition_timer.stop()  # Stop the image transition timer
        if hasattr(self, 'stroop_transition_timer'):
            self.stroop_transition_timer.stop()  # Stop the Stroop timer
        self.paused_time = self.elapsed_time
        logging.info(self.paused_time)
        self.send_message({"action": "client_log", "message": f"Paused time: {self.paused_time}"})
        self.paused_image_index = self.current_image_index 
        logging.info(self.paused_image_index)
        self.send_message({"action": "client_log", "message": f"Paused image index: {self.paused_image_index}"})
         # Store the current image index
        self.Paused = True
        if hasattr(self, 'mirror_widget') and self.mirror_widget is not None:
            self.mirror_widget.pause_trial()

    #This method is called when the user presses the resume button to resume the trial, it starts the timer and the image transition timer, it also sets the paused time to 0 and also tells the mirror widget to resume
    #It also calls the run_trial method to start the trial again
    def resume_trial(self, event=None):
        label = "Resumed Trial"
        self.send_message({"action": "label", "label": label})  # Send label to the server
        self.Paused = False
        self.run_trial()  # Resume the trial
        if hasattr(self, 'mirror_widget') and self.mirror_widget is not None:
            self.mirror_widget.resume_trial()

    #This is the main logic for displaying the images in the passive test, it handles the image transition and the timer for the images         
    def display_images_passive(self):
        img = self.images[self.current_image_index]
        if hasattr(img, 'filename') and img.filename:
            pixmap = QPixmap(img.filename)
            self.current_pixmap = pixmap
            self.update_image_label()
            # Push the filename (without extension) as label
            if hasattr(img, 'filename'):
                label = f"{os.path.splitext(os.path.basename(img.filename))[0]} Image"
                self.send_message({"action": "label", "label": label})  # Send label to the server
                self.label_stream.push_label(label)
                logging.info(f"Current label: {label}")
                self.send_message({"action": "client_log", "message": f"Current label: {label}"})
                if self.eyetracker is not None:
                    self.eyetracker.send_marker(label)  # Send label to Pupil Labs
                self.current_label = label
            if "Tactile" in self.current_test:
                # For tactile, show image for 5 seconds, then show crosshair and wait for touch
                QTimer.singleShot(2000, lambda: self.show_crosshair_and_wait_tactile())
            else:
            # Only show crosshair if next asset is NOT a craving rating
                if self.next_asset_is_craving():
                    QTimer.singleShot(2000, lambda: self.show_crosshair_before_craving())
                else:
                    QTimer.singleShot(2000, lambda: self.show_crosshair_between_images('passive'))
        elif hasattr(img, 'asset_type') and img.asset_type == "craving_rating":
            # Handle the craving rating asset (e.g., show a rating dialog or skip)
            # Example: show a custom widget or message
            self.show_craving_rating_screen()
        else:
            # Handle other asset types or skip
            pass

    #This is the main logic for displaying the images in the stroop test, it handles the image transition and the timer for the images
    #It also handles the user input and the elapsed time when the test is done
    def display_images_stroop(self):
        img = self.images[self.current_image_index]
        pixmap = QPixmap(img.filename)
        self.current_pixmap = pixmap
        self.update_image_label()
        if hasattr(img, 'filename'):
            label = f"{os.path.splitext(os.path.basename(img.filename))[0]} Image"
            self.send_message({"action": "label", "label": label})
            self.label_stream.push_label(label)
            logging.info(f"Current label: {label}")
            self.send_message({"action": "client_log", "message": f"Current label: {label}"})
            self.current_label = label
        if "Tactile" in self.current_test:
            # For tactile Stroop, show image for 2s, then instruction, then crosshair, then next button, then touch
            QTimer.singleShot(2000, self.hide_image)
        else:
            self.stroop_transition_timer.timeout.disconnect()
            self.stroop_transition_timer.timeout.connect(self.hide_image)
            self.stroop_transition_timer.start(2000)

    #This method is called to hide the image and show the instruction text, it clears the image label and sets the instruction text
    def hide_image(self):
        self.image_label.clear()
        self.set_instruction_text()
        self.wait_for_input()

    def show_crosshair_and_wait_tactile(self, stroop=False):
        # Show crosshair for random duration, then enable next button
        self.show_crosshair_between_images('stroop' if stroop else 'passive')
        if self.current_image_index < (len(self.images) - 1):
            self.waiting_for_next = True
            if hasattr(self.frame, 'next_button'):
                self.frame.next_button.setEnabled(True)
            else:
                print("Next button not found in parent widget.")
        else:
            print("Current image index is at the last image, waiting for next button is not applicable.")

    def show_crosshair_between_images(self, test_type):
        # --- Clear craving rating widgets (everything after the first two persistent labels) ---
        self.clear_overlay()

        label = "Crosshair Shown"
        self.send_message({"action": "label", "label": label})  # Send label to the server
        duration_ms = random.randint(800, 1200)
        self.instructions_label.setText("+")
        self.instructions_label.setFont(QFont("Arial", 72, QFont.Bold))
        self.instructions_label.setAlignment(Qt.AlignCenter)
        self.instructions_label.setVisible(True)
        self.countdown_label.setVisible(False)
        self.overlay_widget.setVisible(True)
        self.stacked_layout.setCurrentWidget(self.overlay_widget)
        if hasattr(self, 'mirror_widget') and self.mirror_widget is not None:
            self.mirror_widget.show_crosshair_period()
        if test_type == 'passive':
            if "Tactile" in self.current_test:
                if self.current_image_index == (len(self.images) - 1):
                    QTimer.singleShot(duration_ms, self._advance_image)
                else:
                    pass  # Wait for next button
            else:
                QTimer.singleShot(duration_ms, self._advance_image)
        elif test_type == 'stroop':
            if "Tactile" in self.current_test:
                if self.current_image_index == (len(self.images) - 1):
                    QTimer.singleShot(duration_ms, self._advance_image)
                else:
                    pass  # Wait for next button
            else:
                print("Advancing image")
                QTimer.singleShot(duration_ms, self._advance_image)

    @pyqtSlot()
    def proceed_from_next_button(self):
        if self.waiting_for_next:
            self.waiting_for_next = False
            if hasattr(self.frame, 'next_button'):
                self.frame.next_button.setEnabled(False)
            self.show_touch_instruction()

    def show_touch_instruction(self, initial=False):
        label = "Touch Instruction Shown"
        self.send_message({"action": "label", "label": label})  # Send label to the server

        # Always set the instruction text for both display and mirror
        instruction_text = "Please touch the object to begin." if initial else "You may now touch the object."
        font = QFont("Arial", 32, QFont.Bold)

        # Display widget
        self.instructions_label.setText(instruction_text)
        self.instructions_label.setFont(font)
        self.instructions_label.setAlignment(Qt.AlignCenter)
        self.instructions_label.setVisible(True)
        self.countdown_label.setVisible(False)
        self.overlay_widget.setVisible(True)
        self.stacked_layout.setCurrentWidget(self.overlay_widget)

        # Mirror widget
        if hasattr(self, 'mirror_widget') and self.mirror_widget is not None:
            self.mirror_widget.set_instruction_text(instruction_text, font)
            self.mirror_widget.set_overlay_visible(True)

        # State flags
        self.showing_touch_instruction = True
        if initial:
            self.waiting_for_initial_touch = True

        self.send_message({"action": "touchbox_lsl_true"})

    @pyqtSlot()
    def end_touch_instruction_and_advance(self):
        if self.waiting_for_initial_touch:
            self.waiting_for_initial_touch = False
            self.showing_touch_instruction = False
            self.begin_experiment()  # This will show the first image
            self.mirror_widget.begin_experiment()  # Also start the mirror widget
            return
        if not self.showing_touch_instruction:
            print("Touch advance ignored: not showing touch instruction.")
            return
        self.showing_touch_instruction = False
        self._advance_image()

    def _advance_image(self):
        self.current_image_index += 1
        if self.current_image_index < len(self.images):
            current_asset = self.images[self.current_image_index]
            if isinstance(current_asset, CravingRatingAsset):
                self.show_craving_rating_screen()
            elif hasattr(current_asset, 'filename'):
                if "Stroop" in self.current_test:
                    self.display_images_stroop()
                else:
                    self.display_images_passive()
            else:
                logging.warning(f"Unknown asset type at index {self.current_image_index}: {type(current_asset)}")
        else:
            # End Logic
            if "Stroop" in self.current_test:
                label = "Stroop Test Ended"
                #save_data = Save_Data(self.base_dir, self.test_number)
                #save_data.save_data_stroop(self.current_test, self.user_data['user_inputs'], self.user_data['elapsed_time'])
            else:
                label = "Passive Test Ended"

            self.send_message({"action": "label", "label": label})
            #self.label_stream.push_label("Test Ended")
            self.paused_image_index = 0
            self.paused_time = 0
            self.timer.stop()
            #if self.eyetracker and self.eyetracker.device is not None:
            #    self.eyetracker.stop_recording()
            #self.show_craving_rating_screen()
            self.show_post_test_crosshair_instructions()

    def poll_label(self):
        # This will print the current label and the current time in ms
        logging.info(f"Polled at {self.elapsed_time} ms: Current label = {self.current_label}")
        self.send_message({"action": "client_log", "message": f"Polled at {self.elapsed_time} ms: Current label = {self.current_label}"})

    #This method is needed to make the image transition timer work, it is called when the image transition timer times out. It is the main way the pause and resume functionality works
    #It is called from the image_transition_timer
    def _on_image_transition(self):
        if not self.Paused:
            self.display_images_passive()

    #This method is called to update the image label with the current image, it scales the image to fit the label and also updates the mirror widget if it exists
    def update_image_label(self):
        if self.current_pixmap:
            scaled_pixmap = self.current_pixmap.scaled(
                self.image_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
            # Switch to experiment view so the image is visible
            self.stacked_layout.setCurrentIndex(1)
            # Update the mirror
            if hasattr(self, 'mirror_widget') and self.mirror_widget is not None:
                self.mirror_widget.set_pixmap(self.current_pixmap)
        else:
            self.image_label.clear()
            if hasattr(self, 'mirror_widget') and self.mirror_widget is not None:
                self.mirror_widget.set_pixmap(None)

    #This method is called when the window is resized, it updates the image label and the instruction text
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Set instructions_label height to about half the window height
        half_height = int(self.height() * 0.5)
        self.instructions_label.setMinimumHeight(half_height)
        self.instructions_label.setMaximumHeight(half_height)
        self.instructions_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # Dynamically scale font size based on label height
        font_size = max(18, min(int(half_height * 0.25), 40))
        font = QFont("Arial", font_size, QFont.Bold)
        self.instructions_label.setFont(font)

    #This method is called to set the instruction text for the experiment, it sets the font size and the alignment of the text
    def set_instruction_text(self):
        label = "Response Instructions Shown"
        self.send_message({"action": "label", "label": label})  # Send label to the server
        img = self.images[self.current_image_index]
        text = "Press the 'Y' key if congruent.\nPress the 'N' key if incongruent."
        self.image_label.setText(text)
        self.image_label.setAlignment(Qt.AlignCenter)
        label_height = self.image_label.height()
        font_size = max(8, int(label_height * 0.04))
        font = QFont("Arial", font_size, QFont.Bold)
        self.image_label.setFont(font)
        # Update the mirror
        if hasattr(self, 'mirror_widget') and self.mirror_widget is not None:
            self.mirror_widget.set_instruction_text(text, font)
        if hasattr(img, 'filename'):
            label = f"Instruction Text: {os.path.splitext(os.path.basename(img.filename))[0]} Image"
            self.label_stream.push_label(label)
            logging.info(f"Current label: {label}")
            self.send_message({"action": "client_log", "message": f"Current label: {label}"})
            self.current_label = label
        self.waiting_for_stroop_response = True  # <--- Add this line

    #This method is called to wait for the user input, it installs an event filter to capture the key press events
    def wait_for_input(self):
        self.installEventFilter(self)

    #This method is called to handle the key press events, it checks if the key pressed is 'Y' or 'N' and stores the user input and the elapsed time
    def eventFilter(self, source, event):
        # Only handle image input if index is valid
        if self.Paused == False and hasattr(self, 'images') and 0 <= self.current_image_index < len(self.images):
            if event.type() == QEvent.KeyPress:
                if event.key() == Qt.Key_Y or event.key() == Qt.Key_N:
                    img = self.images[self.current_image_index]
                    if event.key() == Qt.Key_Y:
                        self.user_data['user_inputs'].append('Yes') # Store the user input
                        if hasattr(img, 'filename'):
                            label = f"{os.path.splitext(os.path.basename(img.filename))[0]} Image: Yes"
                            self.send_message({"action": "label", "label": label})
                            self.label_stream.push_label(label)
                            logging.info(f"Current label: {label}")
                            self.send_message({"action": "client_log", "message": f"Current label: {label}"})
                            self.current_label = label  # Push label to LSL stream
                    else:
                        self.user_data['user_inputs'].append('No')  # Store the user input
                        if hasattr(img, 'filename'):
                            label = f"{os.path.splitext(os.path.basename(img.filename))[0]} Image: No"
                            self.send_message({"action": "label", "label": label})
                            self.label_stream.push_label(label)
                            logging.info(f"Current label: {label}")
                            self.send_message({"action": "client_log", "message": f"Current label: {label}"})
                            self.current_label = label  # Push label to LSL stream
                    self.user_data['elapsed_time'].append(self.elapsed_time)  # Store the elapsed time
                    self.removeEventFilter(self)
                    if "Tactile" in self.current_test:
                        if self.next_asset_is_craving():
                            # Show crosshair, then craving rating, then crosshair and wait for next button
                            self.show_crosshair_before_craving()
                        else:
                            # Standard tactile: show crosshair and wait for next button
                            self.show_crosshair_and_wait_tactile(stroop=True)
                    else:
                        if self.next_asset_is_craving():
                            self._advance_image()
                        else:
                            self.show_crosshair_between_images('stroop')
                    return True
        # Handle craving rating input
        if hasattr(self, 'craving_response') and self.craving_response is None:
            if event.type() == QEvent.KeyPress:
                key = event.key()
                if Qt.Key_1 <= key <= Qt.Key_7:
                    self.handle_craving_button(key - Qt.Key_0)
                    return True
        return super().eventFilter(source, event)

    #This method is called to update the timer label, it updates the elapsed time and formats the timer text
    def update_timer(self):
        self.elapsed_time += 1  # Increment by 1 millisecond
        minutes, remainder = divmod(self.elapsed_time, 60000)
        seconds, milliseconds = divmod(remainder, 1000)
        timer_text = f"{minutes:02}:{seconds:02}:{milliseconds:03}"
        # Only update the mirror's timer label
        if hasattr(self, 'mirror_widget') and self.mirror_widget is not None:
            self.mirror_widget.set_timer(timer_text)

    #This method is called to handle the key press events, it checks if the overlay widget is visible and if the space bar is pressed, it starts the countdown    
    def keyPressEvent(self, event):
        if self.overlay_widget.isVisible() and event.key() == Qt.Key_Space and self.ready_for_space:
            self.ready_for_space = False
            self.start_countdown()
        else:
            super().keyPressEvent(event)

    #This method is called to start the countdown, it hides the instruction label and shows the countdown label, it also starts the countdown timer
    def start_countdown(self):
        label = "Starting countdown"
        self.send_message({"action": "label", "label": label})  # Send label to the server
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

    #This method is called to update the countdown label, it decrements the countdown seconds and updates the countdown label, if the countdown reaches 0, it stops the timer and calls the begin_experiment method
    def update_countdown(self):
        self.countdown_seconds -= 1
        if self.countdown_seconds > 0:
            self.countdown_label.setText(str(self.countdown_seconds))
        else:
            self.countdown_timer.stop()
            self.countdown_label.setText("Go!")
            label = "Countdown Finished, starting experiment"
            self.send_message({"action": "label", "label": label})  # Send label to the server
            QTimer.singleShot(1000, self.after_countdown)

    def after_countdown(self):
        if "Tactile" in self.current_test:
            self.show_touch_instruction(initial=True)
        else:
            self.begin_experiment()

    #This method is called to begin the experiment, it sets the stacked layout to the experiment widget and starts the experiment
    def begin_experiment(self):
        self.stacked_layout.setCurrentIndex(1)
        if hasattr(self, 'mirror_widget'):
            self.mirror_widget.begin_experiment()
        self.experiment_started.emit()
        self.run_trial()
        self.start_global_key_listener()

    #This method is called to set the mirror widget, it sets the mirror widget to the passed widget
    def set_mirror(self, mirror_widget):
        self.mirror_widget = mirror_widget

    #This method is called to close the event, it stops the timer and closes the mirror widget if it exists
    def closeEvent(self, event):
        if getattr(self, 'stopped', False):
            logging.info("Closing DisplayWindow...")
            self.send_message({"action": "client_log", "message": "Closing DisplayWindow..."})
            self.stop_global_key_listener()
            # Allow closing and do cleanup
            if hasattr(self, 'timer') and self.timer.isActive():
                self.timer.stop()
            if hasattr(self, 'mirror_widget') and self.mirror_widget is not None:
                self.mirror_widget.setParent(None)
                self.mirror_widget.deleteLater()
                self.mirror_widget = None
            if self.eyetracker and self.eyetracker.device is not None:
                self.eyetracker.stop_recording()          
            super().closeEvent(event)
        else:
            # Prevent closing if stop wasn't pressed
            event.ignore()

    def end_screen(self):
        label = "End Screen Shown"
        self.send_message({"action": "label", "label": label})  # Send label to the server
        self.instructions_label.setText("Test has ended.\n Please wait for the experimenter to close the test.")
        logging.info("Test has ended, please press the stop button to close the test.")
        self.send_message({"action": "client_log", "message": "Test has ended, please press the stop button to close the test."})
        #self.instructions_label.setFont(QFont("Arial", 22))
        self.instructions_label.setAlignment(Qt.AlignCenter)
        self.instructions_label.setVisible(True)
        self.countdown_label.setVisible(False)
        self.overlay_widget.setStyleSheet("background-color: white;")
        self.overlay_widget.setMinimumSize(0, 0)
        self.overlay_widget.setMaximumSize(16777215, 16777215)
        self.stacked_layout.setCurrentWidget(self.overlay_widget)
        if hasattr(self, 'mirror_widget') and self.mirror_widget is not None:
            self.mirror_widget.end_screen()

    def show_crosshair_instructions(self):
        # Show your pre-instructions
        label = "Crosshair Instructions Shown"
        self.send_message({"action": "label", "label": label})  # Send label to the server
        self.instructions_label.setText("Instructions: Please relax and focus on the \n crosshair when it appears.\n This will last for 2 minutes.")
        self.instructions_label.setVisible(True)
        self.countdown_label.setVisible(False)
        self.overlay_widget.setVisible(True)
        self.stacked_layout.setCurrentWidget(self.overlay_widget)
        if hasattr(self, 'mirror_widget') and self.mirror_widget is not None:
            self.mirror_widget.show_crosshair_instructions()
        # After a short delay (5 seconds), show the crosshair
        QTimer.singleShot(5000, self.show_crosshair_period)  # Show crosshair after 5 seconds (adjust as needed)
        
    def show_crosshair_period(self):
        # Show a crosshair for 2 minutes
        label = "Crosshair Shown"
        self.send_message({"action": "label", "label": label})  # Send label to the server
        self.instructions_label.setText("+")
        self.instructions_label.setFont(QFont("Arial", 72, QFont.Bold))
        self.instructions_label.setAlignment(Qt.AlignCenter)
        self.instructions_label.setVisible(True)
        self.countdown_label.setVisible(False)
        self.overlay_widget.setVisible(True)
        self.stacked_layout.setCurrentWidget(self.overlay_widget)
        if hasattr(self, 'mirror_widget') and self.mirror_widget is not None:
            self.mirror_widget.show_crosshair_period()
        # After 2 Minutes, show the main instructions (not restart the experiment)
        QTimer.singleShot(500, self.show_main_instructions)  # 2 minutes (120000)

    def show_main_instructions(self):
        # Restore your original instructions and allow the experiment to proceed
        label = "Main Instructions Shown"
        self.send_message({"action": "label", "label": label})  # Send label to the server
        #self.instructions_label.setFont(QFont("Arial", 18))
        self.instructions_label.setText("Directions: [Your directions here]\n\nPress the SPACE BAR to begin the experiment.")
        self.instructions_label.setVisible(True)
        self.countdown_label.setVisible(False)
        self.overlay_widget.setVisible(True)
        self.stacked_layout.setCurrentWidget(self.overlay_widget)
        if hasattr(self, 'mirror_widget') and self.mirror_widget is not None:
            self.mirror_widget.show_main_instructions()
        self.ready_for_space = True

    def send_message(self, message_dict):
        if self.client:
            try:
                self.connection.sendall((json.dumps(message_dict) + "\n").encode('utf-8'))
            except Exception as e:
                logging.info(f"Error sending message: {e}")
                # Don't call send_message here to avoid infinite recursion

    def clear_overlay(self):
        # Clear the overlay layout and widgets
        for i in reversed(range(2, self.overlay_layout.count())):
            item = self.overlay_layout.itemAt(i)
            if item is not None:
                widget = item.widget()
                layout = item.layout()
                if widget is not None:
                    self.overlay_layout.removeWidget(widget)
                    widget.deleteLater()
                elif layout is not None:
                    while layout.count():
                        child = layout.takeAt(0)
                        if child.widget():
                            child.widget().deleteLater()
            self.overlay_layout.removeItem(item)

    def setup_logging(self, log_queue):
        queue_handler = QueueHandler(log_queue)
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        logger.handlers = []
        logger.addHandler(queue_handler)

    def show_craving_rating_screen(self):
         # --- Adjustable parameters ---
        craving_bar_vertical_offset = 120  # Pixels from the top of the overlay (increase to move bar lower)
        craving_bar_spacing = 40           # Space between instruction and bar

        # Now clear overlay and craving_buttons as before
        self.clear_overlay()

        self.craving_buttons = []

        # Use the persistent instructions_label for craving instructions
        self.instructions_label.setText(
            "How much are you craving alcohol right now?\n"
            "Select a number from 1 to 7 below:"
        )
        self.instructions_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.instructions_label.setAlignment(Qt.AlignCenter)
        self.instructions_label.setWordWrap(True)
        self.instructions_label.setStyleSheet("color: #222; margin-bottom: 24px;")
        self.instructions_label.setVisible(True)
        self.countdown_label.setVisible(False)

        # Craving meanings for each number
        meanings = [
            "Not craving at all",
            "Almost craving",
            "Barely craving",
            "Somewhat craving",
            "Craving",
            "Really craving",
            "Extremely craving"
        ]

        # Create a grid layout for labels and buttons
        grid = QGridLayout()
        grid.setSpacing(50)
        grid.setAlignment(Qt.AlignCenter)

        self.craving_buttons = []
        for i in range(7):
            # Add label above button
            label = QLabel(meanings[i], self.overlay_widget)
            label.setFont(QFont("Arial", 14))
            label.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
            label.setWordWrap(True)
            label.setMinimumHeight(60)
            label.setMaximumWidth(160)
            label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
            grid.addWidget(label, 0, i, alignment=Qt.AlignHCenter | Qt.AlignBottom)

            # Add button
            btn = QPushButton(str(i+1), self.overlay_widget)
            btn.setFont(QFont("Arial", 22, QFont.Bold))
            btn.setFixedSize(70, 70)
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

        #for i in range(7):
        #    grid.setColumnStretch(i, 1)
        #grid.setRowStretch(0, 1)
        #grid.setRowStretch(1, 0)

        grid_widget = QWidget(self.overlay_widget)
        grid_widget.setLayout(grid)
        grid_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        grid_widget.setMaximumWidth(1200)

        # --- Center the grid with adjustable vertical offset ---
        vcenter_layout = QVBoxLayout()
        vcenter_layout.addSpacing(craving_bar_vertical_offset)  # Top offset
        vcenter_layout.addWidget(grid_widget, alignment=Qt.AlignHCenter)
        vcenter_layout.addSpacing(craving_bar_spacing)          # Space below grid (optional)
        vcenter_layout.addStretch(1)                            # Fill remaining space

        self.overlay_layout.addLayout(vcenter_layout)

        label = "Craving Rating Instructions Shown"
        self.send_message({"action": "label", "label": label})  # Send label to the server

        # Mirror widget update
        if hasattr(self, 'mirror_widget') and self.mirror_widget is not None:
            self.mirror_widget.set_instruction_text(
                "Craving Rating Instructions Being Shown",
                QFont("Arial", 24, QFont.Bold)
            )
            self.mirror_widget.set_overlay_visible(True)

        self.overlay_widget.setVisible(True)
        self.stacked_layout.setCurrentWidget(self.overlay_widget)
        self.craving_response = None

        self.installEventFilter(self)

    def handle_craving_button(self, value):
        if self.craving_response is not None:
            return  # Already handled
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
        self.send_message({"action": "crave", "crave": self.craving_response})  # Send label to the server
        self.removeEventFilter(self)
        # After craving rating is saved, go to the next step
        QTimer.singleShot(500, self.show_crosshair_after_craving)

    def show_crosshair_after_craving(self):
        # Show crosshair for a short period after craving rating
        self.clear_overlay()
        self.instructions_label.setText("+")
        self.instructions_label.setFont(QFont("Arial", 72, QFont.Bold))
        self.instructions_label.setAlignment(Qt.AlignCenter)
        self.instructions_label.setVisible(True)
        self.countdown_label.setVisible(False)
        self.overlay_widget.setVisible(True)
        self.stacked_layout.setCurrentWidget(self.overlay_widget)
        if hasattr(self, 'mirror_widget') and self.mirror_widget is not None:
            self.mirror_widget.show_crosshair_period()
        # Advance after crosshair
        if self.current_image_index < len(self.images) - 1:
            next_asset = self.images[self.current_image_index + 1]
            if "Tactile" in self.current_test and hasattr(self.frame, 'next_button'):
                # After craving rating, show crosshair and enable next button for tactile
                self.waiting_for_next = True
                self.frame.next_button.setEnabled(True)
                # Optionally, keep crosshair showing until next button is pressed
            else:
                QTimer.singleShot(1000, self._advance_image)
        else:
            QTimer.singleShot(1000, self.show_post_test_crosshair_instructions)
        
    def show_crosshair_before_craving(self):
        # Show crosshair for a short period before craving rating
        self.clear_overlay()
        self.instructions_label.setText("+")
        self.instructions_label.setFont(QFont("Arial", 72, QFont.Bold))
        self.instructions_label.setAlignment(Qt.AlignCenter)
        self.instructions_label.setVisible(True)
        self.countdown_label.setVisible(False)
        self.overlay_widget.setVisible(True)
        self.stacked_layout.setCurrentWidget(self.overlay_widget)
        if hasattr(self, 'mirror_widget') and self.mirror_widget is not None:
            self.mirror_widget.show_crosshair_period()
        QTimer.singleShot(1000, self._advance_image)  # 1 second crosshair before craving rating

    def next_asset_is_craving(self):
        next_idx = self.current_image_index + 1
        return next_idx < len(self.images) and isinstance(self.images[next_idx], CravingRatingAsset)

    def show_post_test_crosshair_instructions(self):
        # Remove all widgets and layouts after the persistent instruction and countdown labels
        self.clear_overlay()

        # Now update the instructions as usual
        label = "Post-Test Crosshair Instructions Shown"
        self.send_message({"action": "label", "label": label})  # Send label to the server
        self.instructions_label.setText("Instructions: Please relax and focus on the \n crosshair when it appears.\n This will last for 2 minutes.")
        self.instructions_label.setVisible(True)
        self.countdown_label.setVisible(False)
        self.overlay_widget.setVisible(True)
        self.stacked_layout.setCurrentWidget(self.overlay_widget)
        if hasattr(self, 'mirror_widget') and self.mirror_widget is not None:
            self.mirror_widget.show_crosshair_instructions()
        # After a short delay (5 seconds), show the crosshair
        QTimer.singleShot(5000, self.show_post_test_crosshair_period)  # Show crosshair after 5 seconds

    def show_post_test_crosshair_period(self):
        # Show a crosshair for 2 minutes after the test has ended
        label = "Post-Test Crosshair Shown"
        self.send_message({"action": "label", "label": label})  # Send label to the server
        self.instructions_label.setText("+")
        self.instructions_label.setFont(QFont("Arial", 72, QFont.Bold))
        self.instructions_label.setAlignment(Qt.AlignCenter)
        self.instructions_label.setVisible(True)
        self.countdown_label.setVisible(False)
        self.overlay_widget.setVisible(True)
        self.stacked_layout.setCurrentWidget(self.overlay_widget)
        if hasattr(self, 'mirror_widget') and self.mirror_widget is not None:
            self.mirror_widget.show_crosshair_period()
        # After 2 minutes, show the end screen (not restart the experiment)
        QTimer.singleShot(500, self.end_screen)  # Show end screen after 2 minutes (120000)

    def start_global_key_listener(self):
        # Start listening for global key presses
        self.global_key_listener = keyboard.Listener(on_press=self.handle_global_key)
        self.global_key_listener.start()

    def stop_global_key_listener(self):
        # Stop the global key listener
        if hasattr(self, 'global_key_listener') and self.global_key_listener is not None:
            self.global_key_listener.stop()
            self.global_key_listener = None

    def handle_global_key(self, key):
        try:
            if hasattr(key, 'char') and key.char is not None:
                key_name = key.char.upper()
                if key_name in ['Y', 'N'] and getattr(self, 'waiting_for_stroop_response', False):
                    print(f"[DEBUG] Global key pressed: {key_name}")
                    # Only post event if window is not focused
                    if not self.isActiveWindow():
                        self.post_key_event(key_name)
        except Exception as e:
            print(f"Error in global key handler: {e}")

    def post_key_event(self, key_name):
        # Map key_name to Qt key
        key_map = {'Y': Qt.Key_Y, 'N': Qt.Key_N}
        qt_key = key_map.get(key_name)
        if qt_key is not None:
            event = QKeyEvent(QEvent.KeyPress, qt_key, Qt.NoModifier)
            QApplication.postEvent(self, event)
