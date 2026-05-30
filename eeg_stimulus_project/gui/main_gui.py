import sys
from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel, QPushButton, QCheckBox, QApplication, QMessageBox, QStackedWidget, QDialog, QScrollArea, QSizePolicy
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
from eeg_stimulus_project.utils.eye_tracking_software import PupilLabs
from eeg_stimulus_project.lsl.labels import LSLLabelStream
from eeg_stimulus_project.assets.asset_handler import Display
from eeg_stimulus_project.gui.craving_dialog import CravingRatingDialog
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
        self.olfactory_controller = None

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
        self.baseline_frame = BaselineFrame(self)
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
        self.stacked_widget.addWidget(self.baseline_frame)
        
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

    def start_baseline(self):
        """Toggle to the baseline recording frame."""
        if self.stacked_widget.currentWidget() == self.baseline_frame:
            self.stacked_widget.setCurrentWidget(self.last_test_frame)
        else:
            self.stacked_widget.setCurrentWidget(self.baseline_frame)
            self.sidebar.instructions_button.setText("Show Instructions")

    def update_custom_orders(self, custom_orders):
        """Update the custom orders in the Display class."""
        Display.set_custom_orders(custom_orders)

    
    # Function to open the secondary GUI and its mirror widget in the middle frame.
    # This function is called when the checkbox is checked/unchecked
    def open_secondary_gui(self, state, log_queue, label_stream, eyetracker=None, shared_status=None, baseline_mode=False):
        def any_display_widget_open():
            # Check all frames (including baseline) for an open display_widget
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
                self.baseline_frame,
            ]
            return any(getattr(f, 'display_widget', None) is not None for f in frames)

        current_frame = self.stacked_widget.currentWidget()  # Get the active Frame
        if state == Qt.Checked:
            if any_display_widget_open():
                logging.info("A display widget is already open in another frame. Not creating a new one.")
                self.send_message({"action": "client_log", "message": "A display widget is already open in another frame. Not creating a new one."})
                return
            if not hasattr(current_frame, 'display_widget') or current_frame.display_widget is None:
                if baseline_mode:
                    current_test = "Baseline"
                else:
                    current_test = self.get_current_test()
                # Get randomization and repetitions settings from stimulus_order_frame
                randomize_cues, seed = self.stimulus_order_frame.get_randomization_settings()
                repetitions = self.stimulus_order_frame.get_repetitions_settings()

                scent_numbers = self.stimulus_order_frame.scent_numbers
                
                # Create both widgets
                current_frame.display_widget = DisplayWindow(
                    self.connection, log_queue, label_stream, current_frame, current_test,
                    self.base_dir, self.test_number, eyetracker=eyetracker, shared_status=shared_status, client=self.client,
                    alcohol_folder=self.alcohol_folder,
                    non_alcohol_folder=self.non_alcohol_folder,
                    randomize_cues=randomize_cues,
                    seed=seed,
                    repetitions=repetitions, local_mode=self.local_mode, scent_numbers=scent_numbers,
                    baseline_mode=baseline_mode
                )
                current_frame.display_widget.experiment_started.connect(current_frame.enable_pause_resume_buttons)
                current_frame.mirror_display_widget = MirroredDisplayWindow(current_frame, current_test=current_test, baseline_mode=baseline_mode)
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
                            # Notify turntable window if present and in tactile mode
                            if hasattr(current_frame, 'turntable_window') and current_frame.turntable_window is not None:
                                QMetaObject.invokeMethod(current_frame.turntable_window, "on_object_touched", Qt.QueuedConnection)
                        elif msg.get("action") == "labrecorder_connected":
                            self.labrecorder_connected = True
                            self.shared_status['lab_recorder_connected'] = True
                        elif msg.get("action") == "labrecorder_recording_started":
                            path = msg.get("path", "")
                            stream_count = msg.get("stream_count")
                            stream_text = "unknown" if stream_count is None else str(stream_count)
                            logging.info(f"LabRecorder recording started: {path} ({stream_text} LSL streams visible)")
                        elif msg.get("action") == "labrecorder_recording_failed":
                            error = msg.get("error", "Unknown LabRecorder start error")
                            logging.info(f"LabRecorder recording failed: {error}")
                        elif msg.get("action") == "eyetracker_connected":
                            self.shared_status['eyetracker_connected'] = True
                            self.eyetracker_connected = True
                        elif msg.get("action") == "tactile_connected":
                            self.shared_status['tactile_connected'] = True
                        elif msg.get("action") == "connect_olfactory":
                            from eeg_stimulus_project.stimulus.olfactory.olfactory_controller import OlfactoryController
                            try:
                                self.olfactory_controller = OlfactoryController()
                                if self.olfactory_controller.connect():
                                    logging.info("Olfactory controller connected")
                                    self.shared_status['olfactory_connected'] = True
                                    self.connection.sendall((json.dumps({"action": "olfactory_connected", "success": True}) + "\n").encode('utf-8'))
                                    self.olfactory_controller.close()  # Close immediately after testing connection, will reconnect when needed for stimulus presentation
                                else:
                                    logging.error("Failed to connect olfactory controller")
                                    self.connection.sendall((json.dumps({"action": "olfactory_connected", "success": False}) + "\n").encode('utf-8'))
                            except Exception as e:
                                logging.error(f"Error connecting olfactory: {e}")
                                self.connection.sendall((json.dumps({"action": "olfactory_connected", "success": False}) + "\n").encode('utf-8'))
                            
                        elif msg.get("action") == "trigger_scent":
                            if self.olfactory_controller.connect():
                                time.sleep(2)  # Give some time for the connection to establish
                                scent_number = msg.get("scent_number")
                                self.olfactory_controller.trigger_scent(scent_number)
                        
                        elif msg.get("action") == "stop_scent":
                            if self.olfactory_controller:
                                scent_number = msg.get("scent_number")
                                self.olfactory_controller.stop_scent(scent_number)
                                self.olfactory_controller.close()  # Close after stopping scent, will reconnect when needed for next stimulus presentation
                        
                        elif msg.get("action") == "swap_olfactory_ports":
                            if self.olfactory_controller:
                                self.olfactory_controller.swap_ports()
                                logging.info("Olfactory ports swapped")
                        
                        elif msg.get("action") == "connect_turntable":
                            from eeg_stimulus_project.stimulus.turn_table_code.turntable_controller import TurntableController
                            try:
                                turntable_controller = TurntableController()
                                time.sleep(2)  # Give some time for the turntable controller to initialize
                                response = {"action": "turntable_connected", "success": True}
                                self.shared_status['turntable_connected'] = True
                                self.connection.sendall((json.dumps(response) + "\n").encode('utf-8'))
                            except Exception as e:
                                logging.info(f"Error connecting to turntable: {e}")
                                self.shared_status['turntable_connected'] = False
                                response = {"action": "turntable_connected", "success": False}
                                self.connection.sendall((json.dumps(response) + "\n").encode('utf-8'))
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
    
    def show_craving_rating_dialog(self):
        """Show a manual craving rating dialog."""
        dialog = CravingRatingDialog(self, self.base_dir, self.test_number)
        dialog.exec_()

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
        self.is_stroop_test = is_stroop_test
        self.recording_session_active = False

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
        top_frame.setMaximumHeight(200)
        top_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
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
            QCheckBox::indicator {
                width: 25px;
                height: 25px;
            }
        """

        #If the test is a stroop test, add these buttons and checkboxes
        if is_stroop_test:
            button_layout = QHBoxLayout()
            button_layout.setSpacing(14)
            button_layout.setContentsMargins(0, 0, 0, 0)
            button_layout.setAlignment(Qt.AlignVCenter)
            top_layout.addLayout(button_layout)

            self.start_button = QPushButton("Start", self)
            self.start_button.setStyleSheet(button_style)
            self.start_button.clicked.connect(self.start_button_clicked)
            button_layout.addWidget(self.start_button)

            self.stop_button = QPushButton("Stop", self)
            self.stop_button.setStyleSheet(button_style)
            self.stop_button.clicked.connect(self.stop_button_clicked_stroop)
            button_layout.addWidget(self.stop_button)

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
            button_layout.setContentsMargins(0, 0, 0, 0)
            button_layout.setAlignment(Qt.AlignVCenter)
            top_layout.addLayout(button_layout)

            self.start_button = QPushButton("Start", self)
            self.start_button.setStyleSheet(button_style)
            self.start_button.clicked.connect(self.start_button_clicked)
            button_layout.addWidget(self.start_button)

            self.stop_button = QPushButton("Stop", self)
            self.stop_button.setStyleSheet(button_style)
            self.stop_button.clicked.connect(self.stop_button_clicked_passive)
            button_layout.addWidget(self.stop_button)

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

            self.turntable_button = QCheckBox("Turntable", self)
            self.turntable_button.setStyleSheet(button_style)
            button_layout.addWidget(self.turntable_button)

            bottom_frame = QFrame(self)
            bottom_frame.setStyleSheet("background-color: #bc85fa; border-radius: 8px;")
            bottom_frame.setMaximumHeight(50)
            self.layout.addWidget(bottom_frame)

        for attr in ['start_button', 'stop_button', 'pause_button', 'resume_button', 'next_button', 'display_button', 'vr_button', 'turntable_button']:
            btn = getattr(self, attr, None)
            if btn is not None:
                btn.setStyleSheet(button_style)
                btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
                btn.setMinimumHeight(48)

        checkbox_attrs = ['display_button', 'vr_button', 'turntable_button']
        for attr in checkbox_attrs:
            btn = getattr(self, attr, None)
            if btn is not None:
                btn.stateChanged.connect(lambda state, checked_attr=attr: self.handle_exclusive_checkbox(checked_attr, state))

    def handle_exclusive_checkbox(self, checked_attr, state):
        # Only act if a box was checked
        if state == Qt.Checked:
            for attr in ['display_button', 'vr_button', 'turntable_button']:
                if attr != checked_attr:
                    btn = getattr(self, attr, None)
                    if btn is not None:
                        btn.blockSignals(True)
                        btn.setChecked(False)
                        btn.blockSignals(False)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w = self.width()
        h = self.height()
        if w > 1200 or h > 800:
            font_size = 24
            padding = "18px 40px"
        else:
            font_size = 15
            padding = "8px 22px"
        button_style = f"""
            QPushButton {{
                background-color: #42A5F5;
                color: white;
                border-radius: 8px;
                padding: {padding};
                font-size: {font_size}px;
            }}
            QPushButton:disabled {{
                background-color: #bdbdbd;
                color: #eee;
            }}
            QPushButton:hover {{
                background-color: #1976D2;
            }}
            QCheckBox {{
                font-size: {font_size}px;
                padding: 2px 8px;
            }}
            QCheckBox::indicator {{
                width: {font_size + 10}px;
                height: {font_size + 10}px;
            }}
        """
        # Update styles for all relevant buttons and checkboxes
        for attr in ['start_button', 'stop_button', 'pause_button', 'resume_button', 'next_button', 'display_button', 'vr_button', 'turntable_button']:
            btn = getattr(self, attr, None)
            if btn is not None:
                btn.setStyleSheet(button_style)

    def _start_recording_session(self, current_test):
        if self.recording_session_active:
            return

        if self.client:
            self.send_message({"action": "start_button", "test": current_test})
            self.recording_session_active = True
            return

        if not self.local_mode:
            return

        if self.shared_status.get('lab_recorder_connected', False):
            if self.labrecorder is None or self.labrecorder.s is None:
                self.labrecorder = LabRecorder(self.base_dir)
            if self.labrecorder and self.labrecorder.s is not None:
                result = self.labrecorder.Start_Recorder(current_test)
                if result.get("ok"):
                    stream_count = result.get("stream_count")
                    stream_text = "unknown" if stream_count is None else str(stream_count)
                    logging.info(f"LabRecorder recording started: {result.get('path')} ({stream_text} LSL streams visible)")
                else:
                    logging.info(result.get("error", "Unknown LabRecorder start error"))
            else:
                logging.info("LabRecorder not connected")
                self.send_message({"action": "client_log", "message": "LabRecorder not connected"})
        else:
            logging.info("LabRecorder not connected in Control Window")
            self.send_message({"action": "client_log", "message": "LabRecorder not connected in Control Window"})

        self._push_local_session_marker(f"{current_test} Started")
        self.recording_session_active = True

    def _stop_recording_session(self, current_test):
        if not self.recording_session_active:
            return

        if self.client:
            self.send_message({"action": "stop_button", "test": current_test})
            self.recording_session_active = False
            return

        if self.local_mode:
            self._push_local_session_marker(f"{current_test} Stopped")
            if self.labrecorder and self.labrecorder.s is not None:
                result = self.labrecorder.Stop_Recorder()
                if result.get("ok"):
                    logging.info(f"LabRecorder recording stopped: {result.get('path')}")
                else:
                    logging.info(result.get("error", "Unknown LabRecorder stop error"))
            self.recording_session_active = False

    def _push_local_session_marker(self, label):
        if self.local_mode and self.label_stream is not None:
            self.label_stream.push_label(label)
            logging.info(f"Local session marker pushed: {label}")

    #Function to handle what happens when the start button is clicked for stroop tests and passive tests
    def start_button_clicked(self):
        #print(self.shared_status['lab_recorder_connected'])
        #print(self.shared_status['eyetracker_connected'])
        # Check if at least one of the checkboxes is checked
        checked = False
        # Defensive: check if the attributes exist (they may not in all test types)
        for attr in ['display_button', 'vr_button', 'turntable_button']:
            btn = getattr(self, attr, None)
            if btn is not None and btn.isChecked():
                checked = True
                break

        if not checked:
            QMessageBox.critical(self, "Error", "Please select at least one display mode (VR, Display, or Turntable) before starting.")
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

        # --- Tactile connection check (mandatory for Stroop tactile tests) ---
        current_test = self.parent.get_current_test()
        is_stroop_tactile = current_test in ['Stroop Multisensory Alcohol (Visual & Tactile)', 
                                               'Stroop Multisensory Neutral (Visual & Tactile)']
        is_tactile = "Tactile" in current_test
        
        if is_stroop_tactile and not self.shared_status.get('tactile_connected', False):
            # For Stroop tactile tests, tactile connection is MANDATORY
            QMessageBox.critical(
                self,
                "Tactile Box Required",
                "The tactile box must be connected to run this Stroop test. Please connect the tactile system in the Control Window before starting.",
                QMessageBox.Ok
            )
            return
        elif is_tactile and not self.shared_status.get('tactile_connected', False):
            # For non-Stroop tactile tests, show warning
            reply = QMessageBox.question(
                self,
                "Tactile Box Not Connected",
                "The tactile box is not connected, are you sure you want to proceed?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
            
        # --- Olfactory connection check ---
        is_olfactory = "Olfactory" in current_test
        
        if is_olfactory and not self.shared_status.get('olfactory_connected', False):
            # For olfactory tests, olfactory connection is MANDATORY
            QMessageBox.critical(
                self,
                "Olfactory System Required",
                "The olfactory system must be connected to run this test. Please connect the olfactory system in the Control Window before starting.",
                QMessageBox.Ok
            )
            return

        # --- Turntable connection warning ---
        if not self.is_stroop_test:  # Only show turntable warning for non-Stroop tests since Stroop tests do not require turntable connection
            is_turntable = self.turntable_button.isChecked()
            if is_turntable and not self.shared_status.get('turntable_connected', False):
               reply = QMessageBox.question(
                   self,
                   "Turntable Not Connected",
                   "The turntable is not connected, are you sure you want to proceed?",
                   QMessageBox.Yes | QMessageBox.No,
                   QMessageBox.No
               )
               if reply != QMessageBox.Yes:
                   return

        # --- Test already run warning ---
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

        turntable_selected = hasattr(self, 'turntable_button') and self.turntable_button.isChecked()

        if self.client and not turntable_selected:
            self._start_recording_session(current_test)

        display_selected = hasattr(self, 'display_button') and self.display_button.isChecked()
        if self.local_mode and self.label_stream is None:
            self.label_stream = LSLLabelStream()

        if display_selected:
            if self.local_mode and self.label_stream is None:
                self.label_stream = LSLLabelStream()
            self.parent.open_secondary_gui(Qt.Checked, self.log_queue, label_stream=self.label_stream, eyetracker=self.eyetracker, shared_status=self.shared_status)
        else:
            self.parent.open_secondary_gui(Qt.Unchecked, self.log_queue, label_stream=None)

        if not self.client and not turntable_selected:
            self._start_recording_session(current_test)
        self.start_button.setEnabled(False)

        if not turntable_selected:
            self.tests_run.add(current_test)

        if turntable_selected:
            test_name = self.parent.get_current_test()
            order_frame = self.parent.stimulus_order_frame
            if order_frame.current_test_name == test_name:
                order_frame.sync_working_order_with_ui()
            test_order = (
                order_frame.working_orders.get(test_name)
                or order_frame.custom_orders.get(test_name)
                or order_frame.original_assets.get(test_name)
                or []
            )

            from eeg_stimulus_project.stimulus.turn_table_code.turntable_gui import TurntableWindow, TurntableStimulusItem
            turntable_items = []
            for idx, img in enumerate(test_order):
                filename = getattr(img, 'filename', None)
                if not filename:
                    continue
                display_name = os.path.splitext(os.path.basename(filename))[0]
                scent_number = order_frame.scent_numbers.get(filename)
                turntable_items.append(
                    TurntableStimulusItem(
                        display_name,
                        sequence_number=idx + 1,
                        source_path=filename,
                        scent_number=scent_number,
                    )
                )

            def send_message_from_turntable(msg):
                if self.client:
                    try:
                        self.connection.sendall((json.dumps(msg) + "\n").encode('utf-8'))
                    except Exception as e:
                        logging.info(f"Error sending message: {e}")
                elif self.local_mode and msg.get("action") == "label":
                    if self.label_stream is None:
                        self.label_stream = LSLLabelStream()
                    self.label_stream.push_label(msg.get("label", ""))
                    logging.info(f"Local turntable label pushed: {msg.get('label', '')}")

            def start_turntable_recording():
                self._start_recording_session(test_name)
                self.tests_run.add(test_name)

            def stop_turntable_recording():
                self._stop_recording_session(test_name)

            if "Tactile" in test_name:
                self.turntable_window = TurntableWindow(
                    test_order=turntable_items,
                    object_to_bay={},
                    tactile_mode=True,
                    send_message=send_message_from_turntable,
                    on_sequence_started=start_turntable_recording,
                    on_sequence_stopped=stop_turntable_recording
                )
            else:
                self.turntable_window = TurntableWindow(
                    test_order=turntable_items,
                    object_to_bay={},
                    tactile_mode=False,
                    send_message=send_message_from_turntable,
                    on_sequence_started=start_turntable_recording,
                    on_sequence_stopped=stop_turntable_recording
                )
            self.turntable_window.show()

    #Function to handle what happens when the stop button is clicked for stroop tests(calls the data_saving file)
    def stop_button_clicked_stroop(self):
        # Ask for confirmation before stopping
        reply = QMessageBox.question(
            self,
            "Confirm Stop",
            "Are you sure you want to stop the test? This will save all data from connected devices and end the experiment.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No  # Default to No
        )
        
        if reply == QMessageBox.No:
            return  # Cancel the stop operation
        
        self._stop_recording_session(self.parent.get_current_test())

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
        # LabRecorder is stopped by _stop_recording_session above.
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
        # Ask for confirmation before stopping
        reply = QMessageBox.question(
            self,
            "Confirm Stop",
            "Are you sure you want to stop the test? This will save all data from connected devices and end the experiment.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No  # Default to No
        )
        
        if reply == QMessageBox.No:
            return  # Cancel the stop operation
        
        self._stop_recording_session(self.parent.get_current_test())

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
        # LabRecorder is stopped by _stop_recording_session above.
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
            "<p>This guide walks you through running experiments using the Experiment Graphical User Interface.</p>"
            "<p>This system is designed to manage:</p>"
            "<ul>"
            "<li>Real-time EEG stimulus presentation (visual, olfactory, tactile)</li>"
            "<li>Multi-modal experimental designs (passive viewing and Stroop tasks)</li>"
            "<li>Data collection from multiple synchronized devices</li>"
            "<li>Customizable stimulus orders and parameters</li>"
            "</ul>"
            "<p>You can exit this guide at any time by clicking a test or the 'Hide Instructions' button. Click <b>Next</b> to continue.</p>"
        )
        self.add_instruction_page(
            "<h2>🧭 Interface Overview</h2>"
            "<p><b>Main components of the Experiment GUI:</b></p>"
            "<ul>"
            "<li><b>Sidebar (Left):</b> Lists all 10 available tests organized by type</li>"
            "<li><b>Main Frame (Center):</b> Displays controls for the selected test</li>"
            "<li><b>Universal Buttons (Bottom Left):</b>"
            "<ul>"
            "<li>📋 <b>Instructions:</b> Show/hide this guide</li>"
            "<li>⏱️ <b>Latency Checker:</b> Test network responsiveness</li>"
            "<li>🗂️ <b>Stimulus Order:</b> Customize stimulus presentation</li>"
            "<li>⚖️ <b>Record Baseline:</b> Record 4-minute crosshair baseline</li>"
            "<li>🧬 <b>Manual Craving Rating:</b> Displays the craving rating window</li>"
            "</ul>"
            "</li>"
            "</ul>"
        )
        self.add_instruction_page(
            "<h2>📊 Test Types: Passive vs Stroop</h2>"
            "<p><b>Passive Viewing Tests (6 tests):</b><br>"
            "Participants view stimuli without responding. Ideal for studying automatic responses.</p>"
            "<ul>"
            "<li>Unisensory Neutral/Alcohol Visual</li>"
            "<li>Multisensory Neutral/Alcohol Visual & Olfactory</li>"
            "<li>Multisensory Neutral/Alcohol Visual, Tactile & Olfactory</li>"
            "</ul>"
            "<p><b>Stroop Tests (4 tests):</b><br>"
            "Participants respond to multisensory stimuli conflicts. Ideal for studying cognitive control.</p>"
            "<ul>"
            "<li>Stroop Multisensory Alcohol/Neutral (Visual & Tactile)</li>"
            "<li>Stroop Multisensory Alcohol/Neutral (Visual & Olfactory)</li>"
            "</ul>"
            "<p><b>Key Difference:</b> Passive tests are run through 3 different modes (Display, VR, Turntable); Stroop tests require participant interaction via buttons (Only Display mode).</p>"
        )
        self.add_instruction_page(
            "<h2>🖥️ Display Modes & Device Requirements</h2>"
            "<p><b>Three presentation modes (select only one):</b></p>"
            "<ul>"
            "<li>🖥️ <b>Display:</b> Standard 2D monitor presentation</li>"
            "<li>🕶️ <b>VR:</b> Virtual Reality headset (immersive 3D experience)</li>"
            "<li>🔬 <b>Turntable:</b> Physical stimulus rotation platform</li>"
            "</ul>"
            "<p><b>Device requirements by test:</b></p>"
            "<table border='1' cellpadding='8' cellspacing='0' style='font-size: 26px;'>"
            "<tr><th>Test</th><th>Display</th><th>EEG</th><th>Olfactory</th><th>Tactile</th></tr>"
            "<tr><td>Visual tests</td><td>✓ Required</td><td>✓ Required</td><td>✗</td><td>✗</td></tr>"
            "<tr><td>Olfactory tests</td><td>✓ Required</td><td>✓ Required</td><td>✓ Required</td><td>✗</td></tr>"
            "<tr><td>Tactile tests</td><td>✓ Required</td><td>✓ Required</td><td>✗</td><td>✓ Required</td></tr>"
            "<tr><td>Tactile+Olfactory</td><td>✓ Required</td><td>✓ Required</td><td>✓ Required</td><td>✓ Required</td></tr>"
            "</table>"
        )
        self.add_instruction_page(
            "<h2>🕹️ Control Buttons & Workflows</h2>"
            "<p><b>Test Control Buttons (all tests):</b></p>"
            "<ul>"
            "<li><b>Start:</b> Begins stimulus presentation and data collection</li>"
            "<li><b>Stop:</b> Ends test, saves all EEG/device data</li>"
            "<li><b>Pause/Resume:</b> Temporarily halt and continue (display tests only)</li>"
            "</ul>"
            "<p><b>Stroop-Specific Buttons:</b></p>"
            "<ul>"
            "<li><b>Response Buttons:</b> Participant uses these to indicate congruency/incongruency</li>"
            "<li><b>Next:</b> Advance to next stimulus</li>"
            "</ul>"
            "<p><b>Passive Test Workflow:</b></p>"
            "<ol>"
            "<li>Select display mode (Display/VR/Turntable)</li>"
            "<li>Click Start - stimuli present automatically</li>"
            "<li>Click Stop when complete</li>"
            "</ol>"
            "<p><b>Stroop Test Workflow:</b></p>"
            "<ol>"
            "<li>Select display mode</li>"
            "<li>Click Start</li>"
            "<li>Participant responds to each stimulus</li>"
            "<li>Click Next to advance</li>"
            "<li>Click Stop when complete</li>"
            "</ol>"
        )
        self.add_instruction_page(
            "<h2>⏱️ Latency Checker & Baseline Recording</h2>"
            "<p><b>Latency Checker:</b></p>"
            "<ol>"
            "<li>Click 'Latency Checker' in the sidebar</li>"
            "<li>Click 'Start Latency Test' button</li>"
            "<li>Wait 5 seconds for 50 pings (10 pings/sec)</li>"
            "<li>View average round-trip time (should be &lt;2 ms)</li>"
            "<li>Return to a test when ready</li>"
            "</ol>"
            "<p><b>Baseline Recording:</b></p>"
            "<ol>"
            "<li>Click 'Baseline' in the sidebar</li>"
            "<li>Participant fixates on crosshair for 4 minutes</li>"
            "<li>EEG/device data recorded without stimuli</li>"
            "<li>Establishes resting state baseline</li>"
            "</ol>"
        )
        self.add_instruction_page(
            "<h2>🗂️ Stimulus Order Management</h2>"
            "<p><b>Core Features:</b></p>"
            "<ul>"
            "<li><b>Test Selector:</b> Choose which test to edit</li>"
            "<li><b>Working Order:</b> Drag/drop images to rearrange</li>"
            "<li><b>Available Assets:</b> Browse all images by category (Default/Custom)</li>"
            "<li><b>Add/Delete:</b> Dynamically modify current order</li>"
            "</ul>"
            "<p><b>Advanced Options:</b></p>"
            "<ul>"
            "<li><b>Import from CSV/XLSX:</b> Load predefined stimulus orders</li>"
            "<li><b>Randomize:</b> Shuffle alcohol/non-alcohol cues with optional seed</li>"
            "<li><b>Repetitions:</b> Set how many times each stimulus appears</li>"
            "<li><b>Scent Assignment (Olfactory tests only):</b> Assign scent numbers (1-8) to each odor</li>"
            "</ul>"
            "<p><b>⚠️ Important:</b> Click 'Apply Custom Order' to save changes for use in experiments.</p>"
        )
        self.add_instruction_page(
            "<h2>🧬 Craving Rating & Data Collection</h2>"
            "<p><b>Craving Rating During Experiments:</b></p>"
            "<ul>"
            "<li><b>Craving Rating Asset:</b> Special stimulus that prompts participant to rate cravings (1-7 scale)</li>"
            "<li>Automatically included at end of passive tests</li>"
            "<li>Can be inserted anywhere in stimulus order via Stimulus Order Management</li>"
            "</ul>"
            "<p><b>Manual Craving Rating Button:</b></p>"
            "<ul>"
            "<li>Located in the sidebar (orange button: 'Manual Craving Rating')</li>"
            "<li>Use this to collect craving ratings <b>outside</b> of test runs</li>"
            "<li>Useful for baseline craving measurements or between test blocks</li>"
            "<li>Opens dialog allowing participant to enter craving rating (0-100)</li>"
            "<li>Data saved with timestamp for later analysis</li>"
            "</ul>"
            "<p><b>What Gets Recorded During Tests:</b></p>"
            "<ul>"
            "<li>EEG signals from Actichamp/LabRecorder</li>"
            "<li>Eye tracking data from Pupil Labs</li>"
            "<li>Tactile response timing</li>"
            "<li>Olfactory port activation timing</li>"
            "<li>Stimulus presentation timing via LSL markers</li>"
            "<li>Craving ratings (both asset-based and manual)</li>"
            "<li>Stroop responses and reaction times</li>"
            "</ul>"
            "<p><b>Data Organization:</b> All data saved with timestamp synchronization across devices in the subject's data directory.</p>"
        )
        self.add_instruction_page(
            "<h2>✅ Pre-Experiment Checklist</h2>"
            "<p><b>Before Starting ANY Test:</b></p>"
            "<ul>"
            "<li>✓ All devices connected in Control Window (check green status icons)</li>"
            "<li>✓ LabRecorder and Eye Tracker successfully linked</li>"
            "<li>✓ Latency Checker passes (&lt;2 ms)</li>"
            "<li>✓ Stimulus order reviewed and applied</li>"
            "</ul>"
            "<p><b>For Olfactory Tests ONLY:</b></p>"
            "<ul>"
            "<li>✓ Olfactory system connected in Control Window</li>"
            "<li>✓ Olfactory ports validated via 'Validate Olfactory Ports'</li>"
            "<li>✓ Scent assignments completed (all stimuli have scent numbers 1-8)</li>"
            "</ul>"
            "<p><b>For Tactile Tests ONLY:</b></p>"
            "<ul>"
            "<li>✓ Tactile Box connected (green indicator)</li>"
            "<li>✓ Test objects ready for experimenter</li>"
            "</ul>"
            "<p><b>General Preparation:</b></p>"
            "<ul>"
            "<li>✓ Participant seated comfortably</li>"
            "<li>✓ Display/VR/Turntable mode selected</li>"
            "<li>✓ Instructions explained to participant</li>"
            "<li>✓ Baseline recording completed (optional but recommended)</li>"
            "<li>✓ Data save directory configured</li>"
            "</ul>"
        )
        self.add_instruction_page(
            "<h2>🛠️ Troubleshooting & Common Issues</h2>"
            "<p><b>Device Connection Failures:</b></p>"
            "<ul>"
            "<li> Actichamp won't link → Check Control Window, verify USB connection</li>"
            "<li> LabRecorder fails → Ensure Actichamp linked first, restart LabRecorder</li>"
            "<li> Eye Tracker timeout → Verify IP address, check network connectivity</li>"
            "<li> Tactile Box no LSL → Restart Tactile setup, may require multiple attempts</li>"
            "</ul>"
            "<p><b>Stimulus Order Issues:</b></p>"
            "<ul>"
            "<li> Changes not taking effect → Must click 'Apply Custom Order' to save</li>"
            "<li> Passive test won't start → Max 8 unique stimuli limit - reduce duplicates</li>"
            "<li> Olfactory test blocked → Must assign scents to all assets first</li>"
            "</ul>"
            "<p><b>During Experiment:</b></p>"
            "<ul>"
            "<li> Test stops unexpectedly → Check log in Control Window for errors</li>"
            "<li> Data not saving → Verify base directory and permissions</li>"
            "<li> Latency spike → Network congestion - retry after latency check</li>"
            "</ul>"
            "<p><b>Need Help?</b> Refer to README.md, TROUBLESHOOTING.md, or contact us.</p>"
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
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        label = QLabel()
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignTop)
        label.setFont(QFont("Segoe UI", 15))
        label.setMargin(20)
        label.setText(html_text)
        label.setTextFormat(Qt.RichText)
        scroll.setWidget(label)
        self.stacked.addWidget(scroll)
        self.pages.append(scroll)
    
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

class BaselineFrame(QFrame):
    """Dedicated frame for recording baseline (crosshair for 4 minutes)."""
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.display_widget = None
        self.mirror_display_widget = None
        self.label_stream = None
        self.labrecorder = None
        self.eyetracker = None

        self.setStyleSheet("""
            QFrame {
                background-color: #999999;
                border-radius: 16px;
                border: 1.5px solid #43A047;
            }
        """)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(18)

        # Top frame/header
        top_frame = QFrame(self)
        top_frame.setStyleSheet("""
            QFrame {
                background-color: #43A047;
                border-radius: 12px;
            }
        """)
        top_frame.setMaximumHeight(200)
        top_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout.addWidget(top_frame)

        top_layout = QVBoxLayout(top_frame)
        top_layout.setContentsMargins(15, 15, 15, 15)
        top_layout.setSpacing(8)

        header = QLabel("Baseline Recording", self)
        header.setFont(QFont("Segoe UI", 20, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("color: white;")
        top_layout.addWidget(header)

        description = QLabel("Record a 4-minute baseline EEG with crosshair fixation.", self)
        description.setFont(QFont("Segoe UI", 12))
        description.setAlignment(Qt.AlignCenter)
        description.setStyleSheet("color: #e8f5e9;")
        description.setWordWrap(True)
        top_layout.addWidget(description)

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
        """

        button_layout = QHBoxLayout()
        button_layout.setSpacing(14)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setAlignment(Qt.AlignVCenter)
        top_layout.addLayout(button_layout)

        self.start_button = QPushButton("Start Baseline", self)
        self.start_button.setStyleSheet(button_style)
        self.start_button.clicked.connect(self.start_baseline)
        button_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop Baseline", self)
        self.stop_button.setStyleSheet(button_style)
        self.stop_button.clicked.connect(self.stop_baseline)
        button_layout.addWidget(self.stop_button)

        for btn in [self.start_button, self.stop_button]:
            btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
            btn.setMinimumHeight(48)

        # Middle frame for mirror display
        self.middle_frame = QFrame(self)
        self.middle_frame.setStyleSheet("""
            QFrame {
                background-color: #ede7f6;
                border-radius: 10px;
            }
        """)
        self.middle_frame.setMinimumHeight(420)
        self.middle_frame.setLayout(QHBoxLayout())
        self.layout.addWidget(self.middle_frame)

        bottom_frame = QFrame(self)
        bottom_frame.setStyleSheet("background-color: #43A047; border-radius: 8px;")
        bottom_frame.setMaximumHeight(50)
        self.layout.addWidget(bottom_frame)

    def start_baseline(self):
        """Launch the baseline display window."""
        if self.display_widget is not None:
            QMessageBox.warning(self, "Already Running", "Baseline is already running. Stop it first.")
            return

        # Check if any other frame has a display widget open
        all_frames = [
            self.parent.unisensory_neutral_visual,
            self.parent.unisensory_alcohol_visual,
            self.parent.multisensory_neutral_visual_olfactory,
            self.parent.multisensory_alcohol_visual_olfactory,
            self.parent.multisensory_neutral_visual_tactile_olfactory,
            self.parent.multisensory_alcohol_visual_tactile_olfactory,
            self.parent.multisensory_alcohol_visual_tactile,
            self.parent.multisensory_neutral_visual_tactile,
            self.parent.multisensory_alcohol_visual_olfactory2,
            self.parent.multisensory_neutral_visual_olfactory2,
        ]
        if any(getattr(f, 'display_widget', None) is not None for f in all_frames):
            QMessageBox.warning(self, "Already Running", "A display window is already open. Please stop it first.")
            return

        # Create label stream
        if self.label_stream is None:
            self.label_stream = LSLLabelStream()

        self.parent.send_message({"action": "start_button", "test": "Baseline"})

        # Create display and mirror widgets
        self.display_widget = DisplayWindow(
            self.parent.connection, self.parent.log_queue, self.label_stream, self, "Baseline",
            self.parent.base_dir, self.parent.test_number,
            eyetracker=self.eyetracker,
            shared_status=self.parent.shared_status,
            client=self.parent.client,
            alcohol_folder=self.parent.alcohol_folder,
            non_alcohol_folder=self.parent.non_alcohol_folder,
            local_mode=self.parent.local_mode,
            baseline_mode=True
        )
        self.mirror_display_widget = MirroredDisplayWindow(self, current_test="Baseline", baseline_mode=True)
        self.display_widget.set_mirror(self.mirror_display_widget)

        # Add mirror to middle frame
        middle_layout = self.middle_frame.layout()
        middle_layout.addWidget(self.mirror_display_widget)
        middle_layout.setStretchFactor(self.mirror_display_widget, 1)

        # Show the main display window
        self.display_widget.show()

        # Start LabRecorder if connected
        if self.parent.local_mode and self.parent.shared_status.get('lab_recorder_connected', False):
            if self.labrecorder is None or getattr(self.labrecorder, 's', None) is None:
                self.labrecorder = LabRecorder(self.parent.base_dir)
            if self.labrecorder and self.labrecorder.s is not None:
                result = self.labrecorder.Start_Recorder("Baseline")
                if result.get("ok"):
                    stream_count = result.get("stream_count")
                    stream_text = "unknown" if stream_count is None else str(stream_count)
                    logging.info(f"LabRecorder baseline recording started: {result.get('path')} ({stream_text} LSL streams visible)")
                else:
                    logging.info(result.get("error", "Unknown LabRecorder baseline start error"))

        self.start_button.setEnabled(False)

    def stop_baseline(self):
        """Stop the baseline recording and clean up."""
        self.parent.send_message({"action": "stop_button", "test": "Baseline"})

        # Stop LabRecorder
        if self.labrecorder and getattr(self.labrecorder, 's', None) is not None:
            result = self.labrecorder.Stop_Recorder()
            if result.get("ok"):
                logging.info(f"LabRecorder baseline recording stopped: {result.get('path')}")
            else:
                logging.info(result.get("error", "Unknown LabRecorder baseline stop error"))

        # Close display widget
        if self.display_widget is not None:
            self.display_widget.stopped = True
            self.display_widget.close()
            self.display_widget.setParent(None)
            self.display_widget = None

        # Close mirror widget
        if self.mirror_display_widget is not None:
            self.mirror_display_widget.close()
            self.mirror_display_widget.setParent(None)
            self.mirror_display_widget = None

        self.start_button.setEnabled(True)
        self.label_stream = None

    def send_message(self, message_dict):
        self.parent.send_message(message_dict)


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
