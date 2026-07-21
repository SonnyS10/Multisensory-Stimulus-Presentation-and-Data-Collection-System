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
from PyQt5.QtCore import Qt, QTimer, QEvent, pyqtSignal, pyqtSlot, QMetaObject
from eeg_stimulus_project.assets.asset_handler import Display
from eeg_stimulus_project.data.session_data_logger import determine_congruence_condition
from eeg_stimulus_project.lsl.labels import LSLLabelStream
from eeg_stimulus_project.utils.eye_tracking_software import PupilLabs
from eeg_stimulus_project.gui.stimulus_order_frame import CravingRatingAsset
from eeg_stimulus_project.stimulus.olfactory.olfactory_controller import OlfactoryController
from eeg_stimulus_project.stimulus.olfactory.olfactory_timing import get_olfactory_timing_settings, ScentDispenseRunner
import threading
import json
import logging
import random
from logging.handlers import QueueHandler


INSTRUCTION_FONT_SIZE = 28
TOUCH_INSTRUCTION_FONT_SIZE = 38
TEXT_SIZE_MIN = 18
TEXT_SIZE_MAX = 54

STROOP_PRACTICE_TESTS = {
    "Stroop Practice Neutral (Visual & Tactile)",
    "Stroop Practice Neutral (Visual & Olfactory)",
}


def is_stroop_practice_test(test_name):
    return str(test_name or "").strip() in STROOP_PRACTICE_TESTS


def clamp_text_size(size):
    try:
        size = int(size)
    except (TypeError, ValueError):
        size = INSTRUCTION_FONT_SIZE
    return max(TEXT_SIZE_MIN, min(TEXT_SIZE_MAX, size))


def configure_instruction_label(label):
    """Make instruction labels wrap automatically and stay centered within a comfortable width."""
    label.setWordWrap(True)
    label.setAlignment(Qt.AlignCenter)
    label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
    label.setMinimumHeight(0)
    label.setMaximumHeight(16777215)
    label.setContentsMargins(40, 20, 40, 20)
    label.setStyleSheet("padding-left: 40px; padding-right: 40px; margin: 0px;")


def get_turntable_instruction_text(test_name):
    name = str(test_name or "").strip()
    if name in ("Unisensory Neutral Visual", "Unisensory Alcohol Visual"):
        return (
            "During this task, you will see objects presented one at a time in the viewing booth. "
            "Please view each object as it is presented. In between each object, you will see an empty slot. "
            "While viewing the objects, please try to minimize movements including blinks. "
            "At the end of a series, you will be asked to answer a question by pressing a button on the keyboard."
        )
    if name in ("Multisensory Neutral Visual & Olfactory", "Multisensory Alcohol Visual & Olfactory"):
        return (
            "During this task, you will see objects presented one at a time in the viewing booth. "
            "Please view each object as it is presented. In between each object, you will see an empty slot. "
            "Please breathe through your nose to pick up the scent that will be released at the same time."
        )
    if name in ("Multisensory Neutral Visual, Tactile & Olfactory", "Multisensory Alcohol Visual, Tactile & Olfactory"):
        return (
            "Once prompted, lightly place your left hand on the object in the touchbox. "
            "This will trigger an object to be presented in the viewing booth and a scent to be released. "
            "Please breathe through your nose the entire time. After 2-3 seconds, please remove your hand from the object but keep it on the handrest. "
            "Please try to minimize any additional movements, including eye blinks while the task is ongoing."
        )
    return None


def get_test_instruction_text(test_name, instruction_only=False):
    if instruction_only:
        turntable_text = get_turntable_instruction_text(test_name)
        if turntable_text:
            return turntable_text

    name = str(test_name or "").strip()
    if name in ["Unisensory Neutral Visual", "Unisensory Alcohol Visual"]:
        return (
            "During this task you will be shown a cross in the middle of the screen. "
            "As you focus on the cross, a series of images will be shown one at a time. "
            "All you need to do is make sure you view each image and remain fixated on the cross in between images. "
            "While viewing the images, please try to minimize movements including blinks. "
            "At the end of a series, you will be asked to answer a question by pressing a button on the keyboard."
        )
    if name in ["Multisensory Neutral Visual & Olfactory", "Multisensory Alcohol Visual & Olfactory"]:
        return (
            "During this task you will be shown a cross in the middle of the screen. "
            "As you focus on the cross, a series of images paired with scents will be presented. "
            "For this task, your job is to view the images presented on the screen while breathing through your nose to pick up the scent that will be released at the same time. "
            "Please try to minimize any movements including eye blinks while the images are being shown during the task. "
            "At the end of a series, you will be asked to answer a question by pressing a button on the keyboard."
        )
    if name in ["Multisensory Neutral Visual, Tactile & Olfactory", "Multisensory Alcohol Visual, Tactile & Olfactory"]:
        return (
            "Once prompted on the screen, lightly place your left hand on the object in the touchbox. "
            "This will trigger the screen image to appear and a scent to be released. "
            "Please breathe through your nose the entire time. After 2-3 seconds, please remove your hand from the object but keep it on the handrest. "
            "Please try to minimize any additional movements, including eye blinks while the task is ongoing."
        )
    if name in [
        "Stroop Practice Neutral (Visual & Tactile)",
        "Stroop Multisensory Alcohol (Visual & Tactile)",
        "Stroop Multisensory Neutral (Visual & Tactile)",
    ]:
        return (
            "For this task, you will be using both hands. Your left hand will be placed on objects in the touchbox and your right hand should press the right or left arrow keys on the keyboard. "
            "During the task, you will see a series of images on the screen while touching an object in the touchbox. "
            "Your job is to determine if the image shown on the screen matches the physical object. Once prompted, lightly place your left hand on the object in the touchbox, which should trigger the image to be presented. "
            "Press the right arrow if the two match, and the left arrow if they do not match. "
            "Please respond as quickly and as accurately as possible, and try to minimize additional movements, including eye blinks."
        )
    if name in [
        "Stroop Practice Neutral (Visual & Olfactory)",
        "Stroop Multisensory Alcohol (Visual & Olfactory)",
        "Stroop Multisensory Neutral (Visual & Olfactory)",
    ]:
        return (
            "For this task, you will be shown a series of images on the screen, and presented with a scent at the same time. "
            "Your job is to determine if the image shown on the screen matches the scent. "
            "When prompted by the screen, you will use your right hand to press the right arrow if the two match, and the left arrow if they do not match. "
            "Please breathe through your nose the entire time. Please respond as quickly and as accurately as possible, and try to minimize additional movements, including eye blinks while the task is ongoing."
        )
    return (
        "Directions: Please read the instructions carefully. "
        "When you are ready, press the SPACE BAR to begin the experiment."
    )


def get_instruction_prompt(instruction_only=False):
    if instruction_only:
        return "Press the SPACE BAR when you have finished reading the instructions, then wait for the test to begin."
    return "Press the SPACE BAR to begin the experiment."


#This is the class that creates the mirror display window that resides in the main display window to be used by the experimenter to make sure the experiment is running correctly
#It contains the same layout and functionality as the main display window, but it is not interactive
#It is used to show the experimenter what the subject is seeing
class MirroredDisplayWindow(QWidget):
    def __init__(self, parent=None, current_test=None, baseline_mode=False, instruction_only=False, text_size=None):
        super().__init__(parent)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  

        self.current_test = current_test
        self.instruction_only = instruction_only
        self.display_text_size = clamp_text_size(text_size)
        self.current_text_delta = 0

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
        self.instructions_label.setFont(self._instruction_font())
        configure_instruction_label(self.instructions_label)
        self.overlay_layout.addWidget(self.instructions_label, alignment=Qt.AlignCenter)

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

        if baseline_mode:
            self.show_crosshair_instructions()
        else:
            self.show_main_instructions()

        self.paused = False

    def _instruction_font(self, delta=0):
        return QFont("Arial", clamp_text_size(self.display_text_size + delta), QFont.Bold)

    def set_text_size(self, size):
        self.display_text_size = clamp_text_size(size)
        if self.instructions_label.text().strip() != "+":
            self.instructions_label.setFont(self._instruction_font(delta=self.current_text_delta))

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
            text = "Press the Right Arrow key if stimuli match.\nPress the Left Arrow key if stimuli don't match."
        self.image_label.clear()
        self.current_text_delta = 0
        self.instructions_label.setText(text)
        self.instructions_label.setAlignment(Qt.AlignCenter)
        self.instructions_label.setVisible(True)
        self.countdown_label.setVisible(False)  # <-- Hide countdown label
        if font is None:
            font = self._instruction_font()
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
            '''We will switch it to both tactile and olfactory later'''
            #if "Tactile" not in self.current_test and "Olfactory" not in self.current_test:
            #    QTimer.singleShot(1000, self.begin_experiment)

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
        self.current_text_delta = 2
        self.instructions_label.setFont(self._instruction_font(delta=2))
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
        self.current_text_delta = 0
        self.instructions_label.setFont(self._instruction_font())
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
        self.current_text_delta = 0
        self.instructions_label.setFont(self._instruction_font())
        instruction_text = get_test_instruction_text(self.current_test, self.instruction_only)
        self.instructions_label.setText(f"{instruction_text}\n\n{get_instruction_prompt(self.instruction_only)}")
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
                 randomize_cues=False, seed=None, repetitions=None, local_mode=None, scent_numbers=None,
                 baseline_mode=False, subject_id=None, apparatus="Display",
                 session_logger=None, session_owner=None, instruction_only=False, text_size=None):
        super().__init__()
        
        self.shared_status = shared_status if shared_status else {'eyetracker_connected': False}
        self.eyetracker = eyetracker
        self.client = client
        self.label_stream = label_stream if label_stream else (LSLLabelStream() if local_mode else None)
        self.alcohol_folder = alcohol_folder
        self.non_alcohol_folder = non_alcohol_folder
        self.randomize_cues = randomize_cues
        self.seed = seed
        self.frame = parent_frame  # Store reference to the Frame instance
        self.repetitions = repetitions
        self.local_mode = local_mode
        self.scent_numbers = scent_numbers if scent_numbers is not None else {}
        self.baseline_mode = baseline_mode
        # Must be initialized before show_main_instructions() is called at the
        # end of this constructor. Turntable-only runs use this flag to show
        # participant instructions without starting a Display stimulus run.
        self.instruction_only = bool(instruction_only)
        self.display_text_size = clamp_text_size(text_size)
        self.current_text_delta = 0
        self.subject_id = subject_id or "unknown"
        self.apparatus = apparatus
        # session_logger/session_owner are injected by GUI.open_secondary_gui().
        # The logger is created exactly once per day/test_number at the GUI
        # (session) level -- see GUI.ensure_session_logger() in main_gui.py --
        # and the SAME instance/open file is shared across every condition's
        # DisplayWindow so a full session lands in one CSV. session_owner is
        # the GUI instance itself, which owns the block_index/trial_number
        # counters so they keep incrementing across condition switches
        # instead of resetting every time a new DisplayWindow is created.
        self.session_logger = session_logger
        self.session_owner = session_owner
        self._tactile_fired_this_trial = False
        self._stroop_stimulus_onset_ms = 0

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
        self.instructions_label.setFont(self._instruction_font())
        configure_instruction_label(self.instructions_label)
        self.overlay_layout.addWidget(self.instructions_label, alignment=Qt.AlignCenter)

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
        self._dispense_scent_before_next_image = False
        self.next_is_craving = False  # Flag to indicate if the next image is a craving rating image
        # Olfactory defaults; the controller is only opened below when this window
        # actually presents stimuli (see instruction_only guard).
        self.olfactory_controller = None
        self.olfactory_connected = False
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
        # Only open the olfactory serial ports when this DisplayWindow is actually
        # presenting stimuli. In instruction_only mode the turntable (viewing booth)
        # is the presentation device and owns the scent controller; if we connected
        # here we would hold COM8/COM9 and the turntable's olfactory connect would
        # silently fail (a serial port can only be opened by one handle at a time).
        if "Olfactory" in self.current_test and not self.instruction_only:
            self.olfactory_controller = OlfactoryController()
            self.olfactory_connected = self.olfactory_controller.connect()

        # Show initial screen - baseline shows crosshair, normal tests show main instructions
        if self.baseline_mode:
            self.show_crosshair_instructions()
        else:
            self.show_main_instructions()

    def _instruction_font(self, delta=0):
        return QFont("Arial", clamp_text_size(self.display_text_size + delta), QFont.Bold)

    def set_text_size(self, size):
        self.display_text_size = clamp_text_size(size)
        current_instruction = self.instructions_label.text().strip()
        if current_instruction and current_instruction != "+" and self.current_text_delta is not None:
            self.instructions_label.setFont(self._instruction_font(delta=self.current_text_delta))
        if self.image_label.text().strip():
            self.image_label.setFont(self._instruction_font())
        if hasattr(self, 'mirror_widget') and self.mirror_widget is not None:
            self.mirror_widget.set_text_size(self.display_text_size)

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
                    # NOTE: block_index/trial_number are intentionally NOT reset
                    # here. They live on session_owner (the GUI instance) and
                    # must keep incrementing across condition switches within
                    # this same day/session -- see GUI.peek_craving_block_index()
                    # / GUI.advance_craving_block_index() (and the Stroop
                    # equivalents) in main_gui.py.
                    self.timer.start(1)  # Start the timer with 100 ms interval
                if "Stroop" in str(current_test):
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
        self.emit_marker(label)
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
        self.emit_marker(label)
        self.Paused = False
        self.run_trial()  # Resume the trial
        if hasattr(self, 'mirror_widget') and self.mirror_widget is not None:
            self.mirror_widget.resume_trial()

    #This is the main logic for displaying the images in the passive test, it handles the image transition and the timer for the images         
    def display_images_passive(self):
        if self.stopped or self.Paused:
            return  # Do not proceed if stopped or paused
        img = self.images[self.current_image_index]
        if hasattr(img, 'filename') and img.filename:
            # Every olfactory block presents the scent first, then waits the configured
            # scent dispense delay (see olfactory_timing.py) before showing the image. This
            # keeps the scent->image order and timing identical across realism blocks:
            # Olfactory-only dispenses here; Tactile+Olfactory dispenses when the touch arms
            # _dispense_scent_before_next_image. Both then delay equally.
            is_olfactory = "Olfactory" in self.current_test
            dispense_after_touch = self.should_dispense_scent_after_touch()

            if is_olfactory and dispense_after_touch and self._dispense_scent_before_next_image:
                # Tactile+Olfactory: touch armed the scent. Dispense, wait, then show image.
                self.scent_function(img)
                self._dispense_scent_before_next_image = False
                QTimer.singleShot(get_olfactory_timing_settings().get_scent_dispense_delay_ms(), lambda: self._display_image_after_scent_delay(img))
            elif is_olfactory and not dispense_after_touch:
                # Olfactory-only: dispense scent, wait for it to reach the participant, then show image.
                self.scent_function(img)
                QTimer.singleShot(get_olfactory_timing_settings().get_scent_dispense_delay_ms(), lambda: self._display_image_after_scent_delay(img))
            else:
                # No scent involved (or scent already handled): display image immediately.
                self._display_image_after_scent_delay(img)
        elif hasattr(img, 'asset_type') and img.asset_type == "craving_rating":
            # Handle the craving rating asset (e.g., show a rating dialog or skip)
            # Example: show a custom widget or message
            self.show_craving_rating_screen()
        else:
            # Handle other asset types or skip
            pass

    def _display_image_after_scent_delay(self, img):
        """Display image after scent has had time to dispense."""
        if self.stopped or self.Paused:
            return
        pixmap = QPixmap(img.filename)
        self.current_pixmap = pixmap
        self.update_image_label()
        # Push the filename (without extension) as label
        if hasattr(img, 'filename'):
            label = self.build_image_label(img)
            self.emit_marker(label)
            if self.eyetracker is not None:
                self.eyetracker.send_marker(label)  # Send label to Pupil Labs
            self.current_label = label
        
        if "Tactile" in self.current_test:
            # For tactile, show image for 2 seconds, then show crosshair and wait for touch
            QTimer.singleShot(2000, lambda: self.show_crosshair_and_wait_tactile())
        else:
            # Only show crosshair if next asset is NOT a craving rating
            if self.next_asset_is_craving():
                QTimer.singleShot(2000, lambda: self.show_crosshair_before_craving())
            else:
                QTimer.singleShot(2000, lambda: self.show_crosshair_between_images('passive'))

    #This is the main logic for displaying the images in the stroop test, it handles the image transition and the timer for the images
    #It also handles the user input and the elapsed time when the test is done
    def display_images_stroop(self):
        if self.stopped or self.Paused:
            return  # Do not proceed if stopped or paused
        self._tactile_fired_this_trial = False
        img = self.images[self.current_image_index]
        if self.should_dispense_scent_after_touch() and self._dispense_scent_before_next_image:
            self.scent_function(img)
            self._dispense_scent_before_next_image = False
        
        # For olfactory tests, send scent first and wait 2 seconds before showing image
        should_delay_for_scent = "Olfactory" in self.current_test and not self.should_dispense_scent_after_touch()
        
        if should_delay_for_scent:
            # Send scent first
            self.scent_function(img)
            # Wait for scent to dispense (overridable), then display image
            QTimer.singleShot(get_olfactory_timing_settings().get_scent_dispense_delay_ms(), lambda: self._display_stroop_image_after_scent_delay(img))
        else:
            # No scent delay needed, display image immediately
            self._display_stroop_image_after_scent_delay(img)

    def _display_stroop_image_after_scent_delay(self, img):
        """Display stroop image after scent has had time to dispense."""
        if self.stopped or self.Paused:
            return
        pixmap = QPixmap(img.filename)
        self.current_pixmap = pixmap
        self.update_image_label()
        if hasattr(img, 'filename'):
            label = self.build_image_label(img)
            self.emit_marker(label)
            self.current_label = label
        
        if "Tactile" in self.current_test:
            # For tactile Stroop, show image for 2s, then instruction, then crosshair, then next button, then touch
            QTimer.singleShot(2000, self.hide_image)
        else:
            # Olfactory Stroop
            self.stroop_transition_timer.timeout.disconnect()
            self.stroop_transition_timer.timeout.connect(self.hide_image)
            self.stroop_transition_timer.start(2000)

    #This method is called to hide the image and show the instruction text, it clears the image label and sets the instruction text
    def hide_image(self):
        if self.stopped or self.Paused:
            return  # Do not proceed if stopped or paused
        self.image_label.clear()
        self._stroop_stimulus_onset_ms = self.elapsed_time
        if is_stroop_practice_test(self.current_test):
            self.set_instruction_text()
        elif hasattr(self, 'mirror_widget') and self.mirror_widget is not None:
            self.mirror_widget.set_pixmap(None)
        self.waiting_for_stroop_response = True
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
        if self.stopped or self.Paused:
            return  # Do not proceed if stopped or paused
        # --- Clear craving rating widgets (everything after the first two persistent labels) ---
        self.clear_overlay()

        label = "Crosshair Shown"
        self.emit_marker(label)
        duration_ms = random.randint(2000, 6000)
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
            if "Tactile" in self.current_test and "Olfactory" in self.current_test:
                if self.current_image_index == (len(self.images) - 1):
                    QTimer.singleShot(duration_ms, self._advance_image)
                else:
                    pass  # Wait for next button
            #elif "Olfactory" in self.current_test:
            #    # Probably same as tactile + olfactory
            #    pass  # Wait for smell
            else:
                QTimer.singleShot(duration_ms, self._advance_image)
        elif test_type == 'stroop':
            if "Tactile" in self.current_test:
                if self.current_image_index == (len(self.images) - 1):
                    QTimer.singleShot(duration_ms, self._advance_image)
                else:
                    pass  # Wait for next button
            else:
                # Olfactory Stroop
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
        self.emit_marker(label)

        # Always set the instruction text for both display and mirror
        if "Olfactory" in self.current_test:
            # Can be touched upon later
            if initial:
                instruction_text = "Please touch the object to begin. Once you touch the object, a brief scent will be dispensed."
            else:
                instruction_text = "You may now touch the object. Once you touch the object, a brief scent will be dispensed."
        else:
            instruction_text = "Please touch the object to begin." if initial else "You may now touch the object."
        self.current_text_delta = TOUCH_INSTRUCTION_FONT_SIZE - INSTRUCTION_FONT_SIZE
        font = self._instruction_font(delta=TOUCH_INSTRUCTION_FONT_SIZE - INSTRUCTION_FONT_SIZE)

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
            self.mirror_widget.current_text_delta = TOUCH_INSTRUCTION_FONT_SIZE - INSTRUCTION_FONT_SIZE
            self.mirror_widget.set_overlay_visible(True)

        # State flags
        self.showing_touch_instruction = True
        if initial:
            self.waiting_for_initial_touch = True

        self.send_message({"action": "touchbox_lsl_true"})
        self._arm_touch_detection()

    def _arm_touch_detection(self):
        """Arm tactile threshold forwarding (works in local and distributed modes)."""
        try:
            self.shared_status['touch_detection_armed'] = True
            self.shared_status['lsl_enabled'] = True
            self.shared_status['pending_touch_advance'] = False
            logging.info(
                "[TACTILE] touch_detection_armed=True from display "
                "(apparatus waiting for participant touch)"
            )
        except Exception as exc:
            logging.error("[TACTILE] Failed to arm touch detection: %s", exc)

    def _disarm_touch_detection(self):
        try:
            self.shared_status['touch_detection_armed'] = False
            self.shared_status['lsl_enabled'] = False
            self.shared_status['pending_touch_advance'] = False
        except Exception as exc:
            logging.error("[TACTILE] Failed to disarm touch detection: %s", exc)

    @pyqtSlot()
    def end_touch_instruction_and_advance(self):
        phase = "initial" if self.waiting_for_initial_touch else "advance"
        self.emit_marker(f"Touch Detected | phase={phase}")
        logging.info("[TACTILE] GUI advancing after touch (phase=%s)", phase)
        self._disarm_touch_detection()
        self._tactile_fired_this_trial = True
        if self.should_dispense_scent_after_touch():
            self._dispense_scent_before_next_image = True
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
        if self.stopped or self.Paused:
            return  # Do not proceed if stopped or paused
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

            self.emit_marker(label)
            #self.label_stream.push_label("Test Ended")
            self.paused_image_index = 0
            self.paused_time = 0
            self.timer.stop()
            #if self.eyetracker and self.eyetracker.device is not None:
            #    self.eyetracker.stop_recording()
            #self.show_craving_rating_screen()
            self.end_screen()

    def poll_label(self):
        # This will print the current label and the current time in ms
        logging.info(f"Polled at {self.elapsed_time} ms: Current label = {self.current_label}")
        self.send_message({"action": "client_log", "message": f"Polled at {self.elapsed_time} ms: Current label = {self.current_label}"})

    #This method is needed to make the image transition timer work, it is called when the image transition timer times out. It is the main way the pause and resume functionality works
    #It is called from the image_transition_timer
    def _on_image_transition(self):
        if not self.Paused and not self.stopped:
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
        self.instructions_label.setMinimumHeight(0)
        self.instructions_label.setMaximumHeight(16777215)
        self.instructions_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.instructions_label.adjustSize()
        max_width = max(320, int(self.width() * 0.8))
        self.instructions_label.setMaximumWidth(max_width)
        self.instructions_label.setMinimumWidth(0)
        self.instructions_label.setAlignment(Qt.AlignCenter)
        self.instructions_label.setContentsMargins(40, 20, 40, 20)
        if self.instructions_label.text().strip() == "+":
            self.instructions_label.setFont(QFont("Arial", 72, QFont.Bold))
        elif self.current_text_delta is not None:
            self.instructions_label.setFont(self._instruction_font())

    #This method is called to set the instruction text for the experiment, it sets the font size and the alignment of the text
    def set_instruction_text(self):
        img = self.images[self.current_image_index]
        image_name = os.path.splitext(os.path.basename(img.filename))[0]
        label = f"Response Instructions Shown | image={image_name}"
        self.emit_marker(label)
        text = "Press the Right Arrow key if stimuli match.\nPress the Left Arrow key if stimuli don't match."
        self.current_text_delta = 0
        self.image_label.setText(text)
        self.image_label.setAlignment(Qt.AlignCenter)
        font = self._instruction_font()
        self.image_label.setFont(font)
        # Update the mirror
        if hasattr(self, 'mirror_widget') and self.mirror_widget is not None:
            self.mirror_widget.set_instruction_text(text, font)
        self.current_label = label
        self.waiting_for_stroop_response = True  # <--- Add this line

    #This method is called to wait for the user input, it installs an event filter to capture the key press events
    def wait_for_input(self):
        self.installEventFilter(self)

    #This method is called to handle the key press events, it checks if the key pressed is Right or Left Arrow and stores the user input and the elapsed time
    def eventFilter(self, source, event):
        # Only handle image input if index is valid
        if self.Paused == False and hasattr(self, 'images') and 0 <= self.current_image_index < len(self.images):
            if event.type() == QEvent.KeyPress:
                if event.key() == Qt.Key_Right or event.key() == Qt.Key_Left:
                    img = self.images[self.current_image_index]
                    key_pressed = "yes" if event.key() == Qt.Key_Right else "no"
                    if event.key() == Qt.Key_Right:
                        self.user_data['user_inputs'].append('Yes') # Store the user input
                        if hasattr(img, 'filename'):
                            label = self.build_response_label(img, "Yes")
                            self.emit_marker(label)
                            self.current_label = label  # Push label to LSL stream
                    else:
                        self.user_data['user_inputs'].append('No')  # Store the user input
                        if hasattr(img, 'filename'):
                            label = self.build_response_label(img, "No")
                            self.emit_marker(label)
                            self.current_label = label  # Push label to LSL stream
                    self.user_data['elapsed_time'].append(self.elapsed_time)  # Store the elapsed time
                    self._log_stroop_response(key_pressed)
                    self.waiting_for_stroop_response = False
                    self.removeEventFilter(self)
                    if "Tactile" in self.current_test:
                        if self.next_asset_is_craving():
                            # Show crosshair, then craving rating, then crosshair and wait for next button
                            self.show_crosshair_before_craving()
                        else:
                            # Standard tactile: show crosshair and wait for next button
                            self.show_crosshair_and_wait_tactile(stroop=True)
                    else:
                        # Olfactory Stroop
                        if self.next_asset_is_craving():
                            self._advance_image()
                        else:
                            self.show_crosshair_between_images('stroop')
                    return True
        # Handle craving rating input
        if hasattr(self, 'craving_response') and self.craving_response is None:
            if event.type() == QEvent.KeyPress:
                key = event.key()
                if Qt.Key_0 <= key <= Qt.Key_6:
                    self.handle_craving_button(key - Qt.Key_0)
                    return True
        return super().eventFilter(source, event)

    #This method is called to update the timer label, it updates the elapsed time and formats the timer text
    def update_timer(self):
        self.elapsed_time += 1  # Increment by 1 millisecond
        if (self.showing_touch_instruction or self.waiting_for_initial_touch):
            if self.shared_status.get('pending_touch_advance'):
                self.shared_status['pending_touch_advance'] = False
                logging.info("[TACTILE] GUI consumed pending_touch_advance from shared_status")
                QMetaObject.invokeMethod(
                    self, "end_touch_instruction_and_advance", Qt.QueuedConnection
                )
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
            if self.instruction_only:
                self.begin_instruction_only_session()
            else:
                self.start_countdown()
        else:
            super().keyPressEvent(event)

    #This method is called to start the countdown, it hides the instruction label and shows the countdown label, it also starts the countdown timer
    def start_countdown(self):
        label = "Starting countdown"
        self.emit_marker(label)
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
            self.emit_marker(label)
            QTimer.singleShot(1000, self.after_countdown)

    def after_countdown(self):
        if self.instruction_only:
            self.begin_instruction_only_session()
        elif "Tactile" in self.current_test:
            self.show_touch_instruction(initial=True)
        #elif "Olfactory" in self.current_test and "Tactile" not in self.current_test:
        #    # For olfactory only, probably need to wait for smell
        #    pass
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

    def begin_instruction_only_session(self):
        self.emit_marker("Instructions reading complete")
        self.instructions_label.setVisible(False)
        self.countdown_label.setVisible(False)
        self.stacked_layout.setCurrentIndex(1)
        if hasattr(self, 'mirror_widget'):
            self.mirror_widget.begin_experiment()
        self.experiment_started.emit()

    #This method is called to set the mirror widget, it sets the mirror widget to the passed widget
    def set_mirror(self, mirror_widget):
        self.mirror_widget = mirror_widget

    #This method is called to close the event, it stops the timer and closes the mirror widget if it exists
    def closeEvent(self, event):
        if getattr(self, 'stopped', False):
            logging.info("Closing DisplayWindow...")
            self.stop_global_key_listener()
            # Cancel ALL pending timers to prevent callbacks after close
            timer_attrs = (
                '_crosshair_instruction_timer', '_crosshair_period_timer',
                'image_transition_timer', 'stroop_transition_timer',
            )
            for attr in timer_attrs:
                t = getattr(self, attr, None)
                if t is not None and t.isActive():
                    t.stop()
            # Stop countdown timer if active
            if hasattr(self, 'countdown_timer'):
                ct = getattr(self, 'countdown_timer', None)
                if ct is not None and ct.isActive():
                    ct.stop()
            # Allow closing and do cleanup
            if hasattr(self, 'timer') and self.timer.isActive():
                self.timer.stop()
            if hasattr(self, 'mirror_widget') and self.mirror_widget is not None:
                self.mirror_widget.setParent(None)
                self.mirror_widget.deleteLater()
                self.mirror_widget = None
            if self.eyetracker and self.eyetracker.device is not None:
                self.eyetracker.stop_recording()
            if hasattr(self, 'olfactory_controller') and self.olfactory_controller:
                self.olfactory_controller.close()          
            super().closeEvent(event)
        else:
            # Prevent closing if stop wasn't pressed
            event.ignore()

    def end_screen(self):
        if self.stopped or self.Paused:
            return  # Do not proceed if stopped or paused
        label = "End Screen Shown"
        self.emit_marker(label)
        self.instructions_label.setText("Test has ended.\n Please wait for the experimenter to close the test.")
        logging.info("Test has ended, please press the stop button to close the test.")
        self.send_message({"action": "client_log", "message": "Test has ended, please press the stop button to close the test."})
        self.current_text_delta = 2
        self.instructions_label.setFont(self._instruction_font(delta=2))
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
        if self.stopped:
            return
        # Show your pre-instructions
        label = "Crosshair Instructions Shown"
        self.emit_marker(label)
        self.instructions_label.setText("Instructions: Please relax and focus on the \n crosshair when it appears.\n This will last for 4 minutes.")
        self.current_text_delta = 0
        self.instructions_label.setFont(self._instruction_font())
        self.instructions_label.setVisible(True)
        self.countdown_label.setVisible(False)
        self.overlay_widget.setVisible(True)
        self.stacked_layout.setCurrentWidget(self.overlay_widget)
        if hasattr(self, 'mirror_widget') and self.mirror_widget is not None:
            self.mirror_widget.show_crosshair_instructions()
        # After a short delay (5 seconds), show the crosshair
        self._crosshair_instruction_timer = QTimer(self)
        self._crosshair_instruction_timer.setSingleShot(True)
        self._crosshair_instruction_timer.timeout.connect(self.show_crosshair_period)
        self._crosshair_instruction_timer.start(5000)
        
    def show_crosshair_period(self):
        if self.stopped:
            return
        # Show a crosshair for 4 minutes
        label = "Crosshair Shown"
        self.emit_marker(label)
        self.instructions_label.setText("+")
        self.instructions_label.setFont(QFont("Arial", 72, QFont.Bold))
        self.instructions_label.setAlignment(Qt.AlignCenter)
        self.instructions_label.setVisible(True)
        self.countdown_label.setVisible(False)
        self.overlay_widget.setVisible(True)
        self.stacked_layout.setCurrentWidget(self.overlay_widget)
        if hasattr(self, 'mirror_widget') and self.mirror_widget is not None:
            self.mirror_widget.show_crosshair_period()
        # After 4 minutes, end the baseline or show main instructions for the test
        self._crosshair_period_timer = QTimer(self)
        self._crosshair_period_timer.setSingleShot(True)
        if self.baseline_mode:
            self._crosshair_period_timer.timeout.connect(self.end_screen)
        else:
            self._crosshair_period_timer.timeout.connect(self.show_main_instructions)
        self._crosshair_period_timer.start(240000)

    def show_main_instructions(self):
        if self.stopped:
            return
        # Restore your original instructions and allow the experiment to proceed
        label = "Main Instructions Shown"
        self.emit_marker(label)
        self.current_text_delta = 0
        self.instructions_label.setFont(self._instruction_font())
        instruction_text = get_test_instruction_text(self.current_test, self.instruction_only)
        self.instructions_label.setText(f"{instruction_text}\n\n{get_instruction_prompt(self.instruction_only)}")
        self.instructions_label.setVisible(True)
        self.countdown_label.setVisible(False)
        self.overlay_widget.setVisible(True)
        self.stacked_layout.setCurrentWidget(self.overlay_widget)
        if hasattr(self, 'mirror_widget') and self.mirror_widget is not None:
            self.mirror_widget.show_main_instructions()
        self.ready_for_space = True

    def send_message(self, message_dict):
        if getattr(self, 'stopped', False):
            return  # Don't send messages after the test has been stopped
        if self.client:
            try:
                self.connection.sendall((json.dumps(message_dict) + "\n").encode('utf-8'))
            except Exception as e:
                logging.info(f"Error sending message: {e}")
                # Don't call send_message here to avoid infinite recursion

    def push_local_label(self, label):
        if self.label_stream is not None:
            self.label_stream.push_label(label)

    def emit_marker(self, label):
        self.send_message({"action": "label", "label": label})
        self.push_local_label(label)
        logging.info(f"Current label: {label}")
        self.send_message({"action": "client_log", "message": f"Current label: {label}"})

    def scent_number_for_image(self, img):
        key = getattr(img, "filename", None)
        scent_number = self.scent_numbers.get(key, None)
        if scent_number in ("", "None"):
            return None
        return scent_number

    def should_dispense_scent_after_touch(self):
        return "Tactile" in self.current_test and "Olfactory" in self.current_test

    def build_image_label(self, img):
        image_name = os.path.splitext(os.path.basename(img.filename))[0]
        label = f"{image_name} Image"
        scent_number = self.scent_number_for_image(img)
        if "Olfactory" in self.current_test and scent_number:
            label = f"{label} | scent={scent_number}"
        return label

    def _current_sensory_condition(self):
        test = self.current_test or ""
        has_olfactory = "Olfactory" in test
        has_tactile = "Tactile" in test
        if has_tactile and has_olfactory:
            return "Multisensory_Visuo_Tactile_Olfactory"
        if has_olfactory:
            return "Multisensory_Visuo_Olfactory"
        if has_tactile:
            return "Multisensory_Visuo_Tactile"
        return "Unisensory_Visual"

    def _image_cue_type(self, img):
        filename = getattr(img, "filename", "") or ""
        if self.alcohol_folder and self.alcohol_folder in filename:
            return "Alcohol"
        if self.non_alcohol_folder and self.non_alcohol_folder in filename:
            return "Neutral"
        test = self.current_test or ""
        if "Alcohol" in test and "Neutral" not in test.split("Alcohol")[0]:
            return "Alcohol"
        if "Neutral" in test:
            return "Neutral"
        if "Alcohol" in test:
            return "Alcohol"
        return "Neutral"

    def _log_craving_rating(self, craving_score):
        payload = {
            "action": "crave",
            "crave": craving_score,
            "sensory_condition": self._current_sensory_condition(),
            "cue_type": self._current_block_cue_type(),
            "apparatus": self.apparatus,
        }
        if self.client:
            self.send_message(payload)
            return
        if self.session_logger is None:
            return
        if self.session_owner is None:
            logging.error(
                "session_logger is set but session_owner is missing; cannot "
                "obtain a session-scoped block_index. Craving rating not logged."
            )
            return
        block_index = self.session_owner.peek_craving_block_index()
        try:
            if self.session_logger.task_name == "Cross_Modal_Stroop":
                self.session_logger.append_stroop_craving_rating(
                    block_index=block_index,
                    sensory_condition=payload["sensory_condition"],
                    cue_type=payload["cue_type"],
                    craving_score=craving_score,
                    apparatus=self.apparatus,
                )
            else:
                self.session_logger.append_craving_rating(
                    block_index=block_index,
                    sensory_condition=payload["sensory_condition"],
                    cue_type=payload["cue_type"],
                    craving_score=craving_score,
                    apparatus=self.apparatus,
                )
            # Only advance the shared session counter once the row is
            # durably on disk, so a failed write never burns a block_index.
            self.session_owner.advance_craving_block_index()
        except Exception as exc:
            logging.error(f"Failed to log craving rating: {exc}", exc_info=True)

    def _current_block_cue_type(self):
        test = self.current_test or ""
        if "Alcohol" in test and "Neutral" not in test.split("Alcohol")[0]:
            return "Alcohol"
        if "Neutral" in test:
            return "Neutral"
        if "Alcohol" in test:
            return "Alcohol"
        return "Neutral"

    def _log_stroop_response(self, key_pressed):
        if not hasattr(self, "images") or not (0 <= self.current_image_index < len(self.images)):
            return

        img = self.images[self.current_image_index]
        if not hasattr(img, "filename"):
            return

        image_type = self._image_cue_type(img)
        scent_number = self.scent_number_for_image(img)
        congruence = determine_congruence_condition(image_type, scent_number)
        expected_key = "yes" if congruence == "Congruent" else "no"
        reaction_time_ms = max(0, self.elapsed_time - self._stroop_stimulus_onset_ms)

        payload = {
            "action": "stroop_trial",
            "image_shown": os.path.basename(img.filename),
            "image_type": image_type,
            "scent_number": scent_number,
            "has_tactile_trigger": self._tactile_fired_this_trial,
            "key_pressed": key_pressed,
            "expected_key": expected_key,
            "reaction_time_ms": reaction_time_ms,
            "apparatus": self.apparatus,
            "block_name": self.current_test,
            "is_practice": is_stroop_practice_test(self.current_test),
        }
        if self.client:
            self.send_message(payload)
            return
        if self.session_logger is None:
            return
        if self.session_owner is None:
            logging.error(
                "session_logger is set but session_owner is missing; cannot "
                "obtain a session-scoped trial_number. Stroop trial not logged."
            )
            return

        trial_number = self.session_owner.peek_next_stroop_trial_number()
        try:
            self.session_logger.append_stroop_trial(
                trial_number=trial_number,
                image_shown=payload["image_shown"],
                image_type=payload["image_type"],
                scent_number=payload["scent_number"],
                has_tactile_trigger=payload["has_tactile_trigger"],
                key_pressed=payload["key_pressed"],
                expected_key=payload["expected_key"],
                reaction_time_ms=payload["reaction_time_ms"],
                block_name=payload["block_name"],
                is_practice=payload["is_practice"],
                apparatus=self.apparatus,
            )
            self.session_owner.advance_stroop_trial_number()
        except Exception as exc:
            logging.error(f"Failed to log Stroop trial: {exc}", exc_info=True)

    def build_response_label(self, img, response):
        image_name = os.path.splitext(os.path.basename(img.filename))[0]
        label = f"Response | image={image_name} | response={response}"
        scent_number = self.scent_number_for_image(img)
        if "Olfactory" in self.current_test and scent_number:
            label = f"{label} | scent={scent_number}"
        return label

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
        # Now clear overlay and craving_buttons as before
        self.clear_overlay()

        self.craving_buttons = []

        # The persistent instructions_label belongs to the standard overlay flow.
        # Build this prompt with the scale so the whole rating screen is centered.
        self.instructions_label.setVisible(False)
        self.countdown_label.setVisible(False)

        prompt_label = QLabel(self.overlay_widget)
        prompt_label.setText(
            "How strong is your urge to drink alcohol right now?\n\n"
            "Select a number from 0 to 6 below:"
        )
        self.current_text_delta = None
        prompt_label.setFont(QFont("Arial", 28, QFont.Bold))
        prompt_label.setAlignment(Qt.AlignCenter)
        prompt_label.setWordWrap(True)
        prompt_label.setContentsMargins(40, 0, 40, 0)
        prompt_label.setMinimumHeight(130)
        prompt_label.setMaximumWidth(1200)
        prompt_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        prompt_label.setStyleSheet("color: #222; margin: 0px;")

        # Craving meanings for each number
        meanings = [
            "Not at all strong",
            "Very slightly strong",
            "Slightly strong",
            "Moderately strong",
            "Quite strong",
            "Strong",
            "Very strong"
        ]

        # Create a grid layout for labels and buttons
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(36)
        grid.setVerticalSpacing(18)
        grid.setAlignment(Qt.AlignCenter)

        self.craving_buttons = []
        for i in range(7):
            # Add label above button
            label = QLabel(meanings[i], self.overlay_widget)
            label.setFont(QFont("Arial", 16))
            label.setAlignment(Qt.AlignCenter)
            label.setWordWrap(True)
            label.setFixedWidth(180)
            label.setMinimumHeight(108)
            label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            grid.addWidget(label, 0, i, alignment=Qt.AlignHCenter)

            # Add button
            btn = QPushButton(str(i), self.overlay_widget)
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
            btn.clicked.connect(lambda checked, val=i: self.handle_craving_button(val))
            self.craving_buttons.append(btn)
            grid.addWidget(btn, 1, i, alignment=Qt.AlignHCenter)

        #for i in range(7):
        #    grid.setColumnStretch(i, 1)
        #grid.setRowStretch(0, 1)
        #grid.setRowStretch(1, 0)

        grid_widget = QWidget(self.overlay_widget)
        grid_widget.setLayout(grid)
        grid_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        grid_widget.setMaximumWidth(1500)

        content_widget = QWidget(self.overlay_widget)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(24)
        content_layout.addWidget(prompt_label, alignment=Qt.AlignHCenter)
        content_layout.addWidget(grid_widget, alignment=Qt.AlignHCenter)
        content_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        # Center the prompt and rating controls together in the available screen area.
        vcenter_layout = QVBoxLayout()
        vcenter_layout.addStretch(1)
        vcenter_layout.addWidget(content_widget, alignment=Qt.AlignCenter)
        vcenter_layout.addStretch(1)

        self.overlay_layout.addLayout(vcenter_layout)

        label = "Craving Rating Instructions Shown"
        self.emit_marker(label)

        # Mirror widget update
        if hasattr(self, 'mirror_widget') and self.mirror_widget is not None:
            self.mirror_widget.set_instruction_text(
                "Craving Rating Instructions Being Shown",
                QFont("Arial", 28, QFont.Bold)
            )
            self.mirror_widget.set_overlay_visible(True)

        self.overlay_widget.setVisible(True)
        self.stacked_layout.setCurrentWidget(self.overlay_widget)
        self.craving_response = None

        self.installEventFilter(self)

    def handle_craving_button(self, value):
        if self.craving_response is not None:
            return  # Already handled
        if value < 0 or value >= len(self.craving_buttons):
            return
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
        craving_label = f"craving_rating_{self.craving_response}"
        self._log_craving_rating(value)
        if not self.client:
            self.push_local_label(craving_label)
            logging.info(f"Current label: {craving_label}")
            if self.eyetracker is not None:
                self.eyetracker.send_marker(craving_label)
        self.removeEventFilter(self)
        # After craving rating is saved, go to the next step
        QTimer.singleShot(500, self.show_crosshair_after_craving)

    def show_crosshair_after_craving(self):
        if self.stopped or self.Paused:
            return  # Do not proceed if stopped or paused
        # Show crosshair for a short period after craving rating
        self.emit_marker("Crosshair Shown | phase=after_craving")
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
            #elif "Olfactory" in self.current_test and "Tactile" not in self.current_test:
            #    # For olfactory only, probably need to wait for smell
            #    pass
            else:
                QTimer.singleShot(1000, self._advance_image)
        else:
            QTimer.singleShot(1000, self.end_screen)

    def show_crosshair_before_craving(self):
        if self.stopped or self.Paused:
            return  # Do not proceed if stopped or paused
        # Show crosshair for a short period before craving rating
        self.emit_marker("Crosshair Shown | phase=before_craving")
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
            if key in (keyboard.Key.right, keyboard.Key.left) and getattr(self, 'waiting_for_stroop_response', False):
                key_name = 'RIGHT' if key == keyboard.Key.right else 'LEFT'
                print(f"[DEBUG] Global key pressed: {key_name}")
                # Only post event if window is not focused
                if not self.isActiveWindow():
                    self.post_key_event(key_name)
                return

            if hasattr(key, 'char') and key.char is not None:
                key_name = key.char.upper()
                
                # Handle 0-6 for craving rating responses
                if key_name in ['0', '1', '2', '3', '4', '5', '6'] and hasattr(self, 'craving_response') and self.craving_response is None:
                    print(f"[DEBUG] Global craving key pressed: {key_name}")
                    # Only post event if window is not focused
                    if not self.isActiveWindow():
                        self.post_key_event(key_name)
                        
        except Exception as e:
            print(f"Error in global key handler: {e}")

    def post_key_event(self, key_name):
        # Map key_name to Qt key
        key_map = {
            'RIGHT': Qt.Key_Right,
            'LEFT': Qt.Key_Left,
            '0': Qt.Key_0,
            '1': Qt.Key_1,
            '2': Qt.Key_2,
            '3': Qt.Key_3,
            '4': Qt.Key_4,
            '5': Qt.Key_5,
            '6': Qt.Key_6
        }
        qt_key = key_map.get(key_name)
        if qt_key is not None:
            event = QKeyEvent(QEvent.KeyPress, qt_key, Qt.NoModifier)
            QApplication.postEvent(self, event)

    # Something to start scent workflow
    def scent_function(self, img=None):
        if img is None:
            img = self.images[self.current_image_index]
        scent_number = self.scent_number_for_image(img)
        if self.olfactory_connected and scent_number:
            # Dispense using the current (possibly overridden) timing/mode -- see
            # olfactory_timing.py. Keeps a reference on self so the runner's
            # timers aren't garbage collected before it finishes.
            self._scent_runner = ScentDispenseRunner(self.olfactory_controller, scent_number, parent=self)
            if self._scent_runner.start():
                image_name = os.path.splitext(os.path.basename(img.filename))[0]
                label = f"Scent {scent_number} Dispensed | image={image_name}"
                self.emit_marker(label)
                if self.eyetracker is not None:
                    self.eyetracker.send_marker(label)
