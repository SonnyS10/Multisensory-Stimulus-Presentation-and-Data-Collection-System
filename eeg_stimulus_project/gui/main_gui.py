import sys
sys.path.append('\\Users\\cpl4168\\Documents\\Paid Research\\Software-for-Paid-Research-')
from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel, QPushButton, QCheckBox, QApplication, QMessageBox, QStackedWidget, QDialog
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QMetaObject, Qt
import time
import json
import os
import threading
from eeg_stimulus_project.gui.sidebar import Sidebar
from eeg_stimulus_project.gui.main_frame import MainFrame
from eeg_stimulus_project.gui.display_window import DisplayWindow, MirroredDisplayWindow
from eeg_stimulus_project.gui.stimulus_order_frame import StimulusOrderFrame
from eeg_stimulus_project.data.data_saving import Save_Data
from eeg_stimulus_project.utils.labrecorder import LabRecorder
from eeg_stimulus_project.utils.pupil_labs import PupilLabs
from eeg_stimulus_project.lsl.labels import LSLLabelStream
from eeg_stimulus_project.assets.asset_handler import Display
import logging
from logging.handlers import QueueHandler


class GUI(QMainWindow):
    def __init__(self, connection, shared_status, log_queue, base_dir, test_number, client=False,
                 alcohol_folder=None, non_alcohol_folder=None, local_mode=False):
        super().__init__()
        self.shared_status = shared_status
        self.connection = connection
        self.client = client
        self.log_queue = log_queue
        self.alcohol_folder = alcohol_folder
        self.non_alcohol_folder = non_alcohol_folder
        self.eyetracker_connected = False
        self.labrecorder_connected = False
        self.local_mode = local_mode
        
        if connection is not None:
            self.start_listener()

        # Set up logging (handled in main process setup)
        #self.setup_logging(log_queue)

        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()

        self.base_dir = base_dir
        self.test_number = test_number
        self.setWindowTitle("Experiment Control Window")
        self.setGeometry(0, 100, screen_geometry.width() // 2, screen_geometry.height() - 150)
        self.setMinimumSize(800, 600)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QHBoxLayout(self.central_widget)
        
        self.sidebar = Sidebar(self)
        self.main_layout.addWidget(self.sidebar)

        # Highlight tests based on test_number
        self.sidebar.highlight_tests(self.test_number)
        
        self.main_frame = MainFrame(self)
        self.main_layout.addWidget(self.main_frame)
        
        self.stacked_widget = self.main_frame.stacked_widget
        
        #Passive Test Frames
        self.unisensory_neutral_visual = self.create_frame("Unisensory Neutral Visual", is_stroop_test=False)
        self.unisensory_alcohol_visual = self.create_frame("Unisensory Alcohol Visual", is_stroop_test=False)
        self.multisensory_neutral_visual_olfactory = self.create_frame("Multisensory Neutral Visual & Olfactory", is_stroop_test=False)
        self.multisensory_alcohol_visual_olfactory = self.create_frame("Multisensory Alcohol Visual & Olfactory", is_stroop_test=False)
        self.multisensory_neutral_visual_tactile_olfactory = self.create_frame("Multisensory Neutral Visual, Tactile & Olfactory", is_stroop_test=False)
        self.multisensory_alcohol_visual_tactile_olfactory = self.create_frame("Multisensory Alcohol Visual, Tactile & Olfactory", is_stroop_test=False)
        
        #Stroop Test Frames
        self.multisensory_alcohol_visual_tactile = self.create_frame("Stroop Multisensory Alcohol (Visual & Tactile)", is_stroop_test=True)
        self.multisensory_neutral_visual_tactile = self.create_frame("Stroop Multisensory Neutral (Visual & Tactile)", is_stroop_test=True)
        self.multisensory_alcohol_visual_olfactory2 = self.create_frame("Stroop Multisensory Alcohol (Visual & Olfactory)", is_stroop_test=True)
        self.multisensory_neutral_visual_olfactory2 = self.create_frame("Stroop Multisensory Neutral (Visual & Olfactory)", is_stroop_test=True)

        # Instructions and Latency Checker Frame
        self.instruction_frame = InstructionFrame(self)
        self.latency_checker = LatencyChecker(self)
        self.stimulus_order_frame = StimulusOrderFrame(
            parent=self,
            alcohol_folder=self.alcohol_folder,
            non_alcohol_folder=self.non_alcohol_folder
            
        )
        
        # Add new frames to stacked_widget
        #IN THE FUTURE WE ADD A BEGINNING FRAME THAT HAS INTSRUCTIONS
        self.stacked_widget.addWidget(self.unisensory_neutral_visual)
        self.stacked_widget.addWidget(self.unisensory_alcohol_visual)
        self.stacked_widget.addWidget(self.multisensory_neutral_visual_olfactory)
        self.stacked_widget.addWidget(self.multisensory_alcohol_visual_olfactory)
        self.stacked_widget.addWidget(self.multisensory_neutral_visual_tactile_olfactory)
        self.stacked_widget.addWidget(self.multisensory_alcohol_visual_tactile_olfactory)
        self.stacked_widget.addWidget(self.multisensory_alcohol_visual_tactile)
        self.stacked_widget.addWidget(self.multisensory_neutral_visual_tactile)
        self.stacked_widget.addWidget(self.multisensory_alcohol_visual_olfactory2)
        self.stacked_widget.addWidget(self.multisensory_neutral_visual_olfactory2)
        self.stacked_widget.addWidget(self.instruction_frame)
        self.stacked_widget.addWidget(self.latency_checker)
        self.stacked_widget.addWidget(self.stimulus_order_frame)
        
        self.stacked_widget.setCurrentWidget(self.instruction_frame)
        self.last_test_frame = self.unisensory_neutral_visual  # Default to first test

        self._latency_test_active = False
        self._latency_rtts = []
        self._latency_test_count = 0

    def show_test_frame(self, frame_or_name):
        # If a string is passed, map it to the correct frame
        if isinstance(frame_or_name, str):
            test_name_to_frame = {
                'Unisensory Neutral Visual': self.unisensory_neutral_visual,
                'Unisensory Alcohol Visual': self.unisensory_alcohol_visual,
                'Multisensory Neutral Visual & Olfactory': self.multisensory_neutral_visual_olfactory,
                'Multisensory Alcohol Visual & Olfactory': self.multisensory_alcohol_visual_olfactory,
                'Multisensory Neutral Visual, Tactile & Olfactory': self.multisensory_neutral_visual_tactile_olfactory,
                'Multisensory Alcohol Visual, Tactile & Olfactory': self.multisensory_alcohol_visual_tactile_olfactory,
                'Stroop Multisensory Alcohol (Visual & Tactile)': self.multisensory_alcohol_visual_tactile,
                'Stroop Multisensory Neutral (Visual & Tactile)': self.multisensory_neutral_visual_tactile,
                'Stroop Multisensory Alcohol (Visual & Olfactory)': self.multisensory_alcohol_visual_olfactory2,
                'Stroop Multisensory Neutral (Visual & Olfactory)': self.multisensory_neutral_visual_olfactory2,
            }
            frame = test_name_to_frame.get(frame_or_name)
            if frame is not None:
                self.last_test_frame = frame
                self.stacked_widget.setCurrentWidget(frame)
                self.sidebar.instructions_button.setText("Show Instructions")
            else:
                QMessageBox.warning(self, "Test Not Found", f"No frame found for test: {frame_or_name}")
        else:
            # Assume it's a frame object
            self.last_test_frame = frame_or_name
            self.stacked_widget.setCurrentWidget(frame_or_name)
            self.sidebar.instructions_button.setText("Show Instructions")

    #Functions to show different frames
    def create_frame(self, title, is_stroop_test=False):
        return Frame(self, title, self.connection, is_stroop_test, self.shared_status, self.base_dir, self.test_number, self.client, self.log_queue, self.eyetracker_connected, self.labrecorder_connected, self.local_mode)
    
    def show_unisensory_neutral_visual(self):
        self.show_test_frame(self.unisensory_neutral_visual)
    
    def show_unisensory_alcohol_visual(self):
        self.show_test_frame(self.unisensory_alcohol_visual)
    
    def show_multisensory_neutral_visual_olfactory(self):
        self.show_test_frame(self.multisensory_neutral_visual_olfactory)
    
    def show_multisensory_alcohol_visual_olfactory(self):
        self.show_test_frame(self.multisensory_alcohol_visual_olfactory)
    
    def show_multisensory_neutral_visual_tactile_olfactory(self):
        self.show_test_frame(self.multisensory_neutral_visual_tactile_olfactory)
    
    def show_multisensory_alcohol_visual_tactile_olfactory(self):
        self.show_test_frame(self.multisensory_alcohol_visual_tactile_olfactory)
    
    def show_multisensory_alcohol_visual_tactile(self):
        self.show_test_frame(self.multisensory_alcohol_visual_tactile)
    
    def show_multisensory_neutral_visual_tactile(self):
        self.show_test_frame(self.multisensory_neutral_visual_tactile)
    
    def show_multisensory_alcohol_visual_olfactory2(self):
        self.show_test_frame(self.multisensory_alcohol_visual_olfactory2)
    
    def show_multisensory_neutral_visual_olfactory2(self):
        self.show_test_frame(self.multisensory_neutral_visual_olfactory2)

    def show_first_test_frame(self):
        self.show_test_frame(self.unisensory_neutral_visual)

    def toggle_instruction_frame(self):
        if self.stacked_widget.currentWidget() == self.instruction_frame:
            self.stacked_widget.setCurrentWidget(self.last_test_frame)
            self.sidebar.instructions_button.setText("Show Instructions")
        else:
            self.stacked_widget.setCurrentWidget(self.instruction_frame)
            self.sidebar.instructions_button.setText("Hide Instructions")

    def toggle_latency_checker(self):
        if self.stacked_widget.currentWidget() == self.latency_checker:
            self.stacked_widget.setCurrentWidget(self.last_test_frame)
        else:
            self.stacked_widget.setCurrentWidget(self.latency_checker)
            self.sidebar.instructions_button.setText("Show Instructions")

    def toggle_stimulus_order(self):
        if self.stacked_widget.currentWidget() == self.stimulus_order_frame:
            self.stacked_widget.setCurrentWidget(self.last_test_frame)
        else:
            # Get the current test name
            current_test = self.get_current_test()
            # Select it in the stimulus order frame
            self.stimulus_order_frame.select_test(current_test)
            self.stacked_widget.setCurrentWidget(self.stimulus_order_frame)
            self.sidebar.instructions_button.setText("Show Instructions")

    def update_custom_orders(self, custom_orders):
        """Update the custom orders in the Display class."""
        Display.set_custom_orders(custom_orders)

    
    # Function to open the secondary GUI and its mirror widget in the middle frame.
    # This function is called when the checkbox is checked/unchecked
    def open_secondary_gui(self, state, log_queue, label_stream, eyetracker=None, shared_status=None):
        def any_display_widget_open():
            # Check all frames for an open display_widget
            frames = [
                self.unisensory_neutral_visual,
                self.unisensory_alcohol_visual,
                self.multisensory_neutral_visual_olfactory,
                self.multisensory_alcohol_visual_olfactory,
                self.multisensory_neutral_visual_tactile_olfactory,
                self.multisensory_alcohol_visual_tactile_olfactory,
                self.multisensory_alcohol_visual_tactile,
                self.multisensory_neutral_visual_tactile,
                self.multisensory_alcohol_visual_olfactory2,
                self.multisensory_neutral_visual_olfactory2,
            ]
            return any(getattr(f, 'display_widget', None) is not None for f in frames)

        current_frame = self.stacked_widget.currentWidget()  # Get the active Frame
        if state == Qt.Checked:
            if any_display_widget_open():
                logging.info("A display widget is already open in another frame. Not creating a new one.")
                self.send_message({"action": "client_log", "message": "A display widget is already open in another frame. Not creating a new one."})
                return
            if not hasattr(current_frame, 'display_widget') or current_frame.display_widget is None:
                current_test = self.get_current_test()
                # Get randomization and repetitions settings from stimulus_order_frame
                randomize_cues, seed = self.stimulus_order_frame.get_randomization_settings()
                repetitions = self.stimulus_order_frame.get_repetitions_settings()
                
                # Create both widgets
                current_frame.display_widget = DisplayWindow(
                    self.connection, log_queue, label_stream, current_frame, current_test,
                    self.base_dir, self.test_number, eyetracker=eyetracker, shared_status=shared_status, client=self.client,
                    alcohol_folder=self.alcohol_folder,
                    non_alcohol_folder=self.non_alcohol_folder,
                    randomize_cues=randomize_cues,
                    seed=seed,
                    repetitions=repetitions, local_mode=self.local_mode
                )
                current_frame.display_widget.experiment_started.connect(current_frame.enable_pause_resume_buttons)
                current_frame.mirror_display_widget = MirroredDisplayWindow(current_frame, current_test=current_test)
                current_frame.display_widget.set_mirror(current_frame.mirror_display_widget)
                # Add both to the middle_frame layout
                middle_layout = current_frame.middle_frame.layout()  # Or however you access the layout
                middle_layout.addWidget(current_frame.mirror_display_widget)
                middle_layout.setStretchFactor(current_frame.mirror_display_widget, 1)  # Optional, ensures it gets all available space
                # Show the main display as a window
                current_frame.display_widget.show()
            else:
                logging.info("Display widget already exists, not creating a new one.")
                self.send_message({"action": "client_log", "message": "Display widget already exists, not creating a new one."})
        else:
            #Remove/hide the widgets when the stop button is pressed
            if hasattr(current_frame, 'display_widget') and current_frame.display_widget is not None:
                current_frame.display_widget.close()  # Properly close the window
                current_frame.display_widget.setParent(None)
                current_frame.display_widget = None
            if hasattr(current_frame, 'mirror_display_widget') and current_frame.mirror_display_widget is not None:
                current_frame.mirror_display_widget.close()  # Properly close the window
                current_frame.mirror_display_widget.setParent(None)
                current_frame.mirror_display_widget = None

    #A function to get the current test name
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
            return 'Stroop Multisensory Alcohol (Visual & Tactile)'
        elif current_widget == self.multisensory_neutral_visual_tactile:
            return 'Stroop Multisensory Neutral (Visual & Tactile)'
        elif current_widget == self.multisensory_alcohol_visual_olfactory2:
            return 'Stroop Multisensory Alcohol (Visual & Olfactory)'
        elif current_widget == self.multisensory_neutral_visual_olfactory2:
            return 'Stroop Multisensory Neutral (Visual & Olfactory)'
        else:
            return None

    def start_latency_test(self):
        if self._latency_test_active:
            return  # Already running
        self._latency_test_active = True
        self._latency_rtts = []
        self._latency_test_count = 0
        self.latency_checker.latency_label.setText("Measuring latency...")
        def ping_loop():
            start_time = time.time()
            while time.time() - start_time < 5.0:
                self.send_latency_ping(single_test=False)
                time.sleep(.1)  # 10 pings per second
            # After 5 seconds, show average
            self._latency_test_active = False
            if self._latency_rtts:
                avg = sum(self._latency_rtts) / len(self._latency_rtts)
                self.latency_checker.update_latency(0, count=len(self._latency_rtts), avg=avg)
            else:
                self.latency_checker.latency_label.setText("No latency samples received.")
        threading.Thread(target=ping_loop, daemon=True).start()

    def send_latency_ping(self, single_test=True):
        if self.connection:
            self._ping_time = time.time()
            msg = {"action": "latency_ping", "timestamp": self._ping_time}
            try:
                self.connection.sendall((json.dumps(msg) + "\n").encode('utf-8'))
            except Exception as e:
                logging.info(f"Error sending ping: {e}")
                self.send_message({"action": "client_log", "message": f"Error sending ping: {e}"})
            if single_test:
                self._latency_test_active = False  # For single ping

    def handle_latency_pong(self, pong_msg):
        pong_time = time.time()
        sent_time = pong_msg.get("timestamp")
        if sent_time:
            rtt = pong_time - sent_time
            latency_ms = rtt * 1000
            if self._latency_test_active:
                self._latency_rtts.append(latency_ms)
                self._latency_test_count += 1
            else:
                self.latency_checker.update_latency(latency_ms)

    def start_listener(self):
        def listen():
            buffer = ""
            while True:
                try:
                    data = self.connection.recv(4096).decode('utf-8')
                    if not data:
                        break
                    buffer += data
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        if not line.strip():
                            continue
                        msg = json.loads(line)
                        if msg.get("action") == "latency_pong":
                            self.handle_latency_pong(msg)
                        elif msg.get("action") == "host_status":
                            status = msg.get("status", "Unknown")
                            self.latency_checker.update_status(status)
                        elif msg.get("action") == "object_touched":
                            current_frame = self.stacked_widget.currentWidget()
                            if hasattr(current_frame, 'display_widget') and current_frame.display_widget is not None:
                                QMetaObject.invokeMethod(current_frame.display_widget, "end_touch_instruction_and_advance", Qt.QueuedConnection)
                        elif msg.get("action") == "labrecorder_connected":
                            self.labrecorder_connected = True
                            self.shared_status['lab_recorder_connected'] = True
                        elif msg.get("action") == "eyetracker_connected":
                            self.shared_status['eyetracker_connected'] = True
                            self.eyetracker_connected = True
                        elif msg.get("action") == "tactile_connected":
                            self.shared_status['tactile_connected'] = True
                except Exception as e:
                    logging.info(f"Listener error: {e}")
                    self.send_message({"action": "client_log", "message": f"Listener error: {e}"})
                    break
        threading.Thread(target=listen, daemon=True).start()

    def setup_logging(self, log_queue):
        queue_handler = QueueHandler(log_queue)
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        logger.handlers = []  # Remove other handlers
        logger.addHandler(queue_handler)

    def send_message(self, message_dict):
        if self.client:
            # If this is a client, send the message to the server
            try:
                self.connection.sendall((json.dumps(message_dict) + "\n").encode('utf-8'))
            except Exception as e:
                logging.info(f"Error sending message: {e}")
                # Don't call send_message here to avoid infinite recursion

class Frame(QFrame):
    def __init__(self, parent, title, connection, is_stroop_test=False, shared_status=None, base_dir=None, test_number=None, client=False, log_queue=None, eyetracker_connected=None, labrecorder_connected=None, local_mode=False):
        super().__init__(parent)

        self.tests_run = set()
        self.shared_status = shared_status
        self.base_dir = base_dir
        self.test_number = test_number
        self.labrecorder = None
        self.label_stream = None
        self.eyetracker = None
        self.connection = connection
        self.client = client
        self.log_queue = log_queue
        self.parent = parent
        self.eyetracker_connected = eyetracker_connected
        self.labrecorder_connected = labrecorder_connected
        self.local_mode = local_mode

        # --- Aesthetic Styles ---
        self.setStyleSheet("""
            QFrame {
                background-color: #999999;
                border-radius: 16px;
                border: 1.5px solid #bc85fa;
            }
        """)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(18)

        # Top frame/header
        top_frame = QFrame(self)
        top_frame.setStyleSheet("""
            QFrame {
                background-color: #7E57C2;
                border-radius: 12px;
            }
        """)
        top_frame.setMaximumHeight(150)
        self.layout.addWidget(top_frame)

        top_layout = QVBoxLayout(top_frame)
        top_layout.setContentsMargins(15, 15, 15, 15)
        top_layout.setSpacing(8)

        header = QLabel(title, self)
        header.setFont(QFont("Segoe UI", 20, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("color: white;")
        top_layout.addWidget(header)

        # Middle frame for EEG graph or display windows
        self.middle_frame = QFrame(self)
        self.middle_frame.setStyleSheet("""
            QFrame {
                background-color: #ede7f6;
                border-radius: 10px;
            }
        """)
        self.middle_frame.setMinimumHeight(420)
        self.layout.addWidget(self.middle_frame)
        self.middle_frame.setLayout(QHBoxLayout())
        self.layout.addSpacing(10)

        # Button style for all buttons
        button_style = """
            QPushButton {
                background-color: #42A5F5;
                color: white;
                border-radius: 8px;
                padding: 8px 22px;
                font-size: 15px;
            }
            QPushButton:disabled {
                background-color: #bdbdbd;
                color: #eee;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QCheckBox {
                font-size: 15px;
                padding: 2px 8px;
            }
        """

        #If the test is a stroop test, add these buttons and checkboxes
        if is_stroop_test:
            button_layout = QHBoxLayout()
            button_layout.setSpacing(14)
            top_layout.addLayout(button_layout)

            self.start_button = QPushButton("Start", self)
            self.start_button.setStyleSheet(button_style)
            self.start_button.clicked.connect(self.start_button_clicked)
            button_layout.addWidget(self.start_button)

            stop_button = QPushButton("Stop", self)
            stop_button.setStyleSheet(button_style)
            stop_button.clicked.connect(self.stop_button_clicked_stroop)
            button_layout.addWidget(stop_button)

            self.pause_button = QPushButton("Pause", self)
            self.pause_button.setStyleSheet(button_style)
            self.pause_button.setEnabled(False)
            self.pause_button.clicked.connect(self.pause_display_window)
            button_layout.addWidget(self.pause_button)

            self.resume_button = QPushButton("Resume", self)
            self.resume_button.setStyleSheet(button_style)
            self.resume_button.setEnabled(False)
            self.resume_button.clicked.connect(self.resume_display_window)
            button_layout.addWidget(self.resume_button)

            self.next_button = QPushButton("Next", self)
            self.next_button.setStyleSheet(button_style)
            self.next_button.setEnabled(False)
            self.next_button.clicked.connect(self.on_next_button_clicked)
            button_layout.addWidget(self.next_button)

            self.display_button = QCheckBox("Display", self)
            self.display_button.setStyleSheet(button_style)
            button_layout.addWidget(self.display_button)

            bottom_frame = QFrame(self)
            bottom_frame.setStyleSheet("background-color: #bc85fa; border-radius: 8px;")
            bottom_frame.setMaximumHeight(50)
            self.layout.addWidget(bottom_frame)

        # If the test is NOT a stroop test (Passive Test), add these buttons and checkboxes
        if not is_stroop_test:
            button_layout = QHBoxLayout()
            button_layout.setSpacing(14)
            top_layout.addLayout(button_layout)

            self.start_button = QPushButton("Start", self)
            self.start_button.setStyleSheet(button_style)
            self.start_button.clicked.connect(self.start_button_clicked)
            button_layout.addWidget(self.start_button)

            stop_button = QPushButton("Stop", self)
            stop_button.setStyleSheet(button_style)
            stop_button.clicked.connect(self.stop_button_clicked_passive)
            button_layout.addWidget(stop_button)

            self.pause_button = QPushButton("Pause", self)
            self.pause_button.setStyleSheet(button_style)
            self.pause_button.setEnabled(False)
            self.pause_button.clicked.connect(self.pause_display_window)
            button_layout.addWidget(self.pause_button)

            self.resume_button = QPushButton("Resume", self)
            self.resume_button.setStyleSheet(button_style)
            self.resume_button.setEnabled(False)
            self.resume_button.clicked.connect(self.resume_display_window)
            button_layout.addWidget(self.resume_button)

            self.next_button = QPushButton("Next", self)
            self.next_button.setStyleSheet(button_style)
            self.next_button.setEnabled(False)
            self.next_button.clicked.connect(self.on_next_button_clicked)
            button_layout.addWidget(self.next_button)

            self.vr_button = QCheckBox("VR", self)
            self.vr_button.setStyleSheet(button_style)
            button_layout.addWidget(self.vr_button)

            self.display_button = QCheckBox("Display", self)
            self.display_button.setStyleSheet(button_style)
            button_layout.addWidget(self.display_button)

            self.viewing_booth_button = QCheckBox("Viewing Booth", self)
            self.viewing_booth_button.setStyleSheet(button_style)
            button_layout.addWidget(self.viewing_booth_button)

            bottom_frame = QFrame(self)
            bottom_frame.setStyleSheet("background-color: #bc85fa; border-radius: 8px;")
            bottom_frame.setMaximumHeight(50)
            self.layout.addWidget(bottom_frame)

    #Function to handle what happens when the start button is clicked for stroop tests and passive tests when the display button is checked
    #IN THE FUTURE WE NEED TO ADD WHAT HAPPENS WHEN THE OTHER BUTTONS ARE CHECKED(VR, Viewing Booth)
    def start_button_clicked(self):
        print(self.shared_status['lab_recorder_connected'])
        print(self.shared_status['eyetracker_connected'])
        # Check if at least one of the checkboxes is checked
        checked = False
        # Defensive: check if the attributes exist (they may not in all test types)
        for attr in ['display_button', 'vr_button', 'viewing_booth_button']:
            btn = getattr(self, attr, None)
            if btn is not None and btn.isChecked():
                checked = True
                break

        if not checked:
            QMessageBox.critical(self, "Error", "Please select at least one display mode (VR, Display, or Viewing Booth) before starting.")
            return

        # --- Labrecroder/Eyetracker connection warning ---
        if not self.shared_status.get('lab_recorder_connected', False) or not self.shared_status.get('eyetracker_connected', False):
            reply = QMessageBox.question(
                self,
                "LabRecorder/Eyetracker Not Connected",
                "The LabRecorder and/or Eyetracker software is not connected, are you sure you want to proceed?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        # --- Tactile connection warning ---
        is_tactile = "Tactile" in self.parent.get_current_test()
        if is_tactile and not self.shared_status.get('tactile_connected', False):
            reply = QMessageBox.question(
                self,
                "Tactile Box Not Connected",
                "The tactile box is not connected, are you sure you want to proceed?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        current_test = self.parent.get_current_test()
        if current_test in self.tests_run:
            reply = QMessageBox.question(
                self,
                "Test Already Run",
                f"The test '{current_test}' has already been run in this session.\n"
                "Are you sure you want to continue? This will overwrite any previously saved data for this test.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        if hasattr(self, 'display_button') and self.display_button.isChecked():
            self.send_message({"action": "start_button", "test": self.parent.get_current_test()})
            if self.label_stream is None:                
                self.label_stream = LSLLabelStream()
                self.parent.open_secondary_gui(Qt.Checked, self.log_queue, label_stream=self.label_stream, eyetracker=self.eyetracker, shared_status=self.shared_status)
                self.start_button.setEnabled(False)  # Disable the start button after starting the stream
            if self.local_mode:
                if self.shared_status.get('lab_recorder_connected', False):
                    if self.labrecorder is None or self.labrecorder.s is None:
                        self.labrecorder = LabRecorder(self.base_dir)
                    if self.labrecorder and self.labrecorder.s is not None:
                        self.labrecorder.Start_Recorder(self.parent.get_current_test())
                    else:
                        logging.info("LabRecorder not connected")
                        self.send_message({"action": "client_log", "message": "LabRecorder not connected"})
                else:
                    logging.info("LabRecorder not connected in Control Window")
                    self.send_message({"action": "client_log", "message": "LabRecorder not connected in Control Window"})
            
        else:
            self.parent.open_secondary_gui(Qt.Unchecked, self.log_queue, label_stream=None)

        # After successfully starting the test, add it to the set
        self.tests_run.add(current_test)

        if hasattr(self, 'viewing_booth_button') and self.viewing_booth_button.isChecked():
            test_name = self.parent.get_current_test()
            test_order = self.parent.stimulus_order_frame.working_orders.get(test_name, [])
            test_order_names = [os.path.splitext(os.path.basename(img.filename))[0] for img in test_order if hasattr(img, 'filename')]

            # Prompt for object-to-bay assignment
            #from eeg_stimulus_project.stimulus.turn_table_code.object_to_bay_dialog import ObjectToBayDialog
            #dlg = ObjectToBayDialog(test_order_names, num_bays=16, parent=self)
            #if dlg.exec_() == QDialog.Accepted:
            #    object_to_bay = dlg.get_assignments()
            #    from eeg_stimulus_project.stimulus.turn_table_code.turntable_gui import TurntableWindow
            #    self.turntable_window = TurntableWindow(test_order=test_order_names, object_to_bay=object_to_bay)
            #    self.turntable_window.show()
            #else:
            #    QMessageBox.information(self, "Cancelled", "Test cancelled: you must assign all objects to bays.")

            from eeg_stimulus_project.stimulus.turn_table_code.turntable_gui import TurntableWindow
            self.turntable_window = TurntableWindow(test_order=test_order_names, object_to_bay={})
            self.turntable_window.show()

    #Function to handle what happens when the stop button is clicked for stroop tests(calls the data_saving file)
    def stop_button_clicked_stroop(self):
        self.send_message({"action": "stop_button", "test": self.parent.get_current_test()})

        save_data = Save_Data(self.base_dir, self.test_number)
        self.start_button.setEnabled(True)  # Re-enable the start button after stopping
        try:
            if hasattr(self, 'display_widget') and self.display_widget is not None:
                save_data.save_data_stroop(
                    self.parent.get_current_test(),
                    self.display_widget.user_data['user_inputs'],
                    self.display_widget.user_data['elapsed_time']
                )
            else:
                logging.info("No display_widget found for saving data.")
                self.send_message({"action": "client_log", "message": "No display_widget found for saving data."})
        except Exception as e:
            logging.info(f"Error saving data: {e}")
            self.send_message({"action": "client_log", "message": f"Error saving data: {e}"})
        # Stop LabRecorder if connected
        if self.labrecorder and self.labrecorder.s is not None:
            self.labrecorder.Stop_Recorder()
        # Stop the eyetracker if connected`
        #if self.eyetracker and self.eyetracker.device is not None:
        #    self.eyetracker.stop_recording()
        if hasattr(self, 'display_widget') and self.display_widget is not None:
            self.display_widget.stopped = True
            self.display_widget.close()  # Close the display widget
        time.sleep(2)  # Give some time for the display widget to stop
        self.parent.open_secondary_gui(Qt.Unchecked, self.log_queue, label_stream=None)
        self.label_stream = None  # Reset the label stream after stopping

    #Function to handle what happens when the stop button is clicked for passive tests(calls the data_saving file)
    def stop_button_clicked_passive(self):
        self.send_message({"action": "stop_button", "test": self.parent.get_current_test()})

        save_data = Save_Data(self.base_dir, self.test_number)
        self.start_button.setEnabled(True)  # Re-enable the start button after stopping
        try:
            if hasattr(self, 'display_widget') and self.display_widget is not None:
                save_data.save_data_passive(self.parent.get_current_test())
            else:
                logging.info("No display_widget found for saving data.")
                self.send_message({"action": "client_log", "message": "No display_widget found for saving data."})
        except Exception as e:
            logging.info(f"Error saving data: {e}")
            self.send_message({"action": "client_log", "message": f"Error saving data: {e}"})
        # Stop LabRecorder if connected
        if self.labrecorder and self.labrecorder.s is not None:
            self.labrecorder.Stop_Recorder()
        # Stop the eyetracker if connected`
        #if self.eyetracker and self.eyetracker.device is not None:
        #    self.eyetracker.stop_recording()
        if hasattr(self, 'display_widget') and self.display_widget is not None:
            self.display_widget.stopped = True
            self.display_widget.close()
        time.sleep(2)
        self.parent.open_secondary_gui(Qt.Unchecked, self.log_queue, label_stream=None)
        self.label_stream = None  # Reset the label stream after stopping

    #Pauses the display window and the mirror display window
    def pause_display_window(self):
        self.display_widget.pause_trial()
        self.mirror_display_widget.pause_trial()

    #Resumes the display window and the mirror display window
    def resume_display_window(self):
        self.display_widget.resume_trial()
        self.mirror_display_widget.resume_trial()

    # Function to enable the pause and resume buttons(So they are not greyed out)
    def enable_pause_resume_buttons(self):
        self.pause_button.setEnabled(True)
        self.resume_button.setEnabled(True)

    def send_message(self, message_dict):
        if self.client:
            # If this is a client, send the message to the server
            try:
                self.connection.sendall((json.dumps(message_dict) + "\n").encode('utf-8'))
            except Exception as e:
                logging.info(f"Error sending message: {e}")
                # Don't call send_message here to avoid infinite recursion



    def on_next_button_clicked(self):
        if hasattr(self, 'display_widget') and self.display_widget is not None:
            QMetaObject.invokeMethod(self.display_widget, "proceed_from_next_button", Qt.QueuedConnection)

class InstructionFrame(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(18)

        # --- Card-like background for instructions ---
        card = QFrame(self)
        card.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 2px solid #bc85fa;
                border-radius: 18px;
                padding: 24px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(24)
        layout.addWidget(card, stretch=1)

        # --- Multi-page instructions ---
        self.stacked = QStackedWidget(card)
        card_layout.addWidget(self.stacked)

        self.pages = []
        self.add_instruction_page(
            "<h2>👋 Welcome to the Experiment GUI!</h2>"
            "<p>This guide will walk you through the process of running an experiment using the Experiment Graphical User Interface.</p>"
            "<ul>"
            "<li>You can exit this guide at any time by clicking your desired test or the 'Hide Instructions' button.</li>"
            "<li>Use the <b>Next</b> button below to continue.</li>"
            "</ul>"
        )
        self.add_instruction_page(
            "<h2>🧭 Navigation Overview</h2>"
            "<ul>"
            "<li><b>Sidebar:</b> Select different experimental tests and modalities.</li>"
            "<li><b>Instructions Button:</b> Open/close this guide.</li>"
            "<li><b>Latency Checker:</b> Measure network latency (see next page).</li>"
            "<li><b>Stimulus Order Management:</b> View and edit the order of stimuli for each test.</li>"
            "<li><b>Main Area:</b> Controls and status for the selected experiment.</li>"
            "</ul>"
            "<p>Use the <b>Start</b>, <b>Stop</b>, <b>Pause</b>, <b>Resume</b>, and <b>Next</b> buttons to control the experiment flow.</p>"
        )
        self.add_instruction_page(
            "<h2>🕹️ Button Functions</h2>"
            "<ul>"
            "<li><b>Start:</b> Begins the selected test.</li>"
            "<li><b>Stop:</b> Ends the current test and saves all data from connected devices.</li>"
            "<li><b>Pause:</b> Temporarily halts the test.</li>"
            "<li><b>Resume:</b> Continues a paused test.</li>"
            "<li><b>Next:</b> Displays instructions for the participant to interact with the tactile box (only for tactile tests).</li>"
            "</ul>"
            "<p><b>Display/VR/Viewing Booth:</b> Select the output mode for the experiment. Only one may be selected at a time:</p>"
            "<ul>"
            "<li>🖥️ <b>Display:</b> Shows the 2D experiment on the main screen.</li>"
            "<li>🕶️ <b>VR:</b> Activates the VR headset for a 3D experience.</li>"
            "<li>🔬 <b>Viewing Booth:</b> Uses the viewing booth for the experiment.</li>"
            "</ul>"
        )
        self.add_instruction_page(
            "<h2>⏱️ Latency Checker</h2>"
            "<ol>"
            "<li>Click the <b>Latency Checker</b> button in the sidebar.</li>"
            "<li>Click <b>Start Latency Test</b> to begin measuring.</li>"
            "<li>The average latency will be displayed after the test completes.</li>"
            "<li>Verify the latency is within acceptable limits (typically below <b>2 ms</b>).</li>"
            "</ol>"
            "<p><i>The Latency Checker runs for 5 seconds, sending 10 pings per second, and displays the average latency for 50 total pings.</i></p>"
        )
        self.add_instruction_page(
            "<h2>🗂️ Stimulus Order Management Frame</h2>"
            "<ul>"
            "<li>🔽 <b>Test Picker (Top Dropdown):</b><br>"
            "Select which test's stimulus order you want to view or edit.</li><br>"
            "<li>🖼️ <b>Current Order Window:</b><br>"
            "Shows the current working order of images for the selected test.<br>"
            "You can drag and drop images to rearrange their order.</li><br>"
            "<li>🖱️ <b>Drag and Drop:</b><br>"
            "Click and drag images within the list to change their presentation order.</li><br>"
            "<li>📁 <b>Available Assets:</b><br>"
            "Shows all images that can be added to the current test.<br>"
            "Select an asset and click <b>Add Selected Asset</b> to add it to the working order.</li><br>"
            "<li>➕ <b>Add Assets:</b><br>"
            "Use the <b>Add Selected Asset</b> button to insert the chosen asset into the current order.</li><br>"
            "<li>🗑️ <b>Delete Assets:</b><br>"
            "Select an image in the current order and click <b>Delete Selected Stimulus</b> to remove it.</li><br>"
            "<li>📄 <b>Import from CSV/XLSX:</b><br>"
            "Use <b>Import Order from CSV</b> to load a custom order from a CSV or Excel file.<br>"
            "The file should list image names in the desired order (one per row).</li><br>"
            "<li>🔄 <b>Reset Order:</b><br>"
            "Click <b>Reset Working Order</b> to revert to the original order for the selected test.</li><br>"
            "<li>✅ <b>Apply Order:</b><br>"
            "Click <b>Apply Custom Order</b> to save your changes. This order will be used during the experiment.</li><br>"
            "<li>🎲 <b>Randomizer & Repetitions:</b><br>"
            "Use the randomization options to shuffle cues and/or set how many times each image appears.<br>"
            "Click <b>Randomize Now</b> to apply these settings to the working order.</li>"
            "</ul>"
            "<p><b>Remember:</b> Changes are only used in the experiment after you click <b>Apply Custom Order</b>.</p>"
        )        
        self.add_instruction_page(
            "<h2>🧪 Running a Test</h2>"
            "<ol>"
            "<li>Select the desired test from the sidebar.</li>"
            "<li>Ensure all required external devices are connected in the Control Window.</li>"
            "<li>Choose the display mode (<b>Display</b>, <b>VR</b>, or <b>Viewing Booth</b>).</li>"
            "<li>Click <b>Start</b> to begin.</li>"
            "<li>Follow on-screen prompts and monitor the status indicators.</li>"
            "<li>Click <b>Stop</b> to end and save the test.</li>"
            "</ol>"
            "<p><b>Tip:</b> For tactile tests, wait for the experimenter to switch the object before pressing <b>Next</b>.</p>"
        )
        self.add_instruction_page(
            "<h2>🛠️ Troubleshooting & Tips</h2>"
            "<ul>"
            "<li>If a warning appears for any device, check the connection in the Control Window and try again.</li>"
            "<li>Use the latency check to verify network responsiveness.</li>"
            "<li>For further help, consult the experiment protocol or contact the lead researcher.</li>"
            "<li>Always ensure participant safety and comfort.</li>"
            "</ul>"
            "<p>Click <b>Continue</b> to exit this guide and proceed to the first test.</p>"
        )

        # --- Navigation Buttons ---
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(18)
        self.prev_button = QPushButton("← Previous")
        self.prev_button.setFont(QFont("Segoe UI", 16))
        self.prev_button.setStyleSheet("""
            QPushButton {
                background-color: #42A5F5;
                color: white;
                border-radius: 8px;
                padding: 12px 32px;
                font-size: 18px;
                min-width: 120px;
                min-height: 48px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.prev_button.setMinimumHeight(48)
        self.prev_button.clicked.connect(self.prev_page)
        nav_layout.addWidget(self.prev_button)

        self.page_label = QLabel()
        self.page_label.setAlignment(Qt.AlignCenter)
        self.page_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
        self.page_label.setMinimumHeight(48)
        self.page_label.setStyleSheet("""
            QLabel {
                padding: 12px 32px;
                color: #333;
                background: #e3e3e3;
                border-radius: 8px;
                font-size: 20px;
            }
        """)
        nav_layout.addWidget(self.page_label, stretch=1)

        self.next_button = QPushButton("Next →")
        self.next_button.setFont(QFont("Segoe UI", 16))
        self.next_button.setStyleSheet("""
            QPushButton {
                background-color: #42A5F5;
                color: white;
                border-radius: 8px;
                padding: 12px 32px;
                font-size: 18px;
                min-width: 120px;
                min-height: 48px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.next_button.setMinimumHeight(48)
        self.next_button.clicked.connect(self.next_page)
        nav_layout.addWidget(self.next_button)

        card_layout.addLayout(nav_layout)

        continue_button = QPushButton("Continue to Experiment")
        continue_button.setFont(QFont("Segoe UI", 18, QFont.Bold))
        continue_button.setStyleSheet("""
            QPushButton {
                background-color: #7E57C2;
                color: white;
                border-radius: 8px;
                padding: 12px 32px;
                font-size: 20px;
                min-width: 160px;
                min-height: 48px;
            }
            QPushButton:hover {
                background-color: #512da8;
            }
        """)
        continue_button.setMinimumHeight(48)
        continue_button.clicked.connect(parent.show_first_test_frame)
        card_layout.addWidget(continue_button, alignment=Qt.AlignCenter)
        continue_button.setVisible(False)
        self.continue_button = continue_button
        self.update_nav_buttons()

    def add_instruction_page(self, html_text):
        label = QLabel()
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignTop)
        label.setFont(QFont("Segoe UI", 15))
        label.setMargin(20)
        label.setText(html_text)
        label.setTextFormat(Qt.RichText)
        self.stacked.addWidget(label)
        self.pages.append(label)

    def next_page(self):
        idx = self.stacked.currentIndex()
        if idx < self.stacked.count() - 1:
            self.stacked.setCurrentIndex(idx + 1)
        self.update_nav_buttons()

    def prev_page(self):
        idx = self.stacked.currentIndex()
        if idx > 0:
            self.stacked.setCurrentIndex(idx - 1)
        self.update_nav_buttons()

    def update_nav_buttons(self):
        idx = self.stacked.currentIndex()
        total = self.stacked.count()
        self.prev_button.setEnabled(idx > 0)
        if idx == total - 1:
            self.next_button.setVisible(False)
            self.prev_button.setVisible(True)
            self.continue_button.setVisible(True)
        elif idx == 0:
            self.next_button.setVisible(True)
            self.prev_button.setVisible(False)
        else:
            self.next_button.setVisible(True)
            self.prev_button.setVisible(True)
            self.continue_button.setVisible(False)
        self.page_label.setText(f"Page {idx + 1} of {total}")

class LatencyChecker(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(18)

        title = QLabel("Latency Checker")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.latency_label = QLabel("Latency: Not checked")
        self.latency_label.setAlignment(Qt.AlignCenter)
        self.latency_label.setFont(QFont("Segoe UI", 12))
        layout.addWidget(self.latency_label)

        self.status_label = QLabel("Host Status: Unknown")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Segoe UI", 12))
        layout.addWidget(self.status_label)

        latency_button = QPushButton("Check Latency")
        latency_button.setFont(QFont("Segoe UI", 16))
        latency_button.setStyleSheet("""
            QPushButton {
                background-color: #42A5F5;
                color: white;
                border-radius: 8px;
                padding: 12px 32px;
                font-size: 18px;
                min-width: 160px;
                min-height: 48px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        latency_button.setMinimumHeight(48)
        latency_button.clicked.connect(self.send_latency_ping)
        layout.addWidget(latency_button, alignment=Qt.AlignCenter)
        self.latency_button = latency_button

    def send_latency_ping(self):
        if hasattr(self.parent, "start_latency_test"):
            self.parent.start_latency_test()

    def update_latency(self, latency_ms, count=None, avg=None):
        if avg is not None:
            self.latency_label.setText(f"Average Latency: {avg:.2f} ms ({count} samples)")
        else:
            self.latency_label.setText(f"Latency: {latency_ms:.2f} ms")

    def update_status(self, status_text):
        self.status_label.setText(f"Host Status: {status_text}")

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    # Create the application instance
    app = QApplication(sys.argv)

    # Create an instance of the GUI
    window = GUI()
    window.show()

    # Execute the application
    sys.exit(app.exec_())