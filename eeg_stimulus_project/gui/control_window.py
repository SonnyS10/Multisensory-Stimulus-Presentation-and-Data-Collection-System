from PyQt5.QtWidgets import QFrame, QVBoxLayout, QApplication, QMainWindow, QWidget, QLabel, QPushButton, QHBoxLayout, QTextEdit, QStackedWidget, QDialog, QLineEdit, QMessageBox
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt, QTimer, QMetaObject, pyqtSignal, QObject
import sys
import subprocess
import time 
import threading
import json
import traceback
import logging 
import os
import platform
from pathlib import Path
from logging.handlers import QueueListener #QueueHandler
import socket
from multiprocessing import Process, Manager

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from eeg_stimulus_project.config import config

# Platform-specific imports
if platform.system() == 'Windows':
    try:
        from pywinauto import Application
    except ImportError:
        print("pywinauto not available - Windows automation features disabled")
        Application = None
else:
    Application = None

class QTextEditLogger(logging.Handler, QObject):
    append_text = pyqtSignal(str)

    def __init__(self, text_edit):
        logging.Handler.__init__(self)
        QObject.__init__(self)
        self.text_edit = text_edit
        self.append_text.connect(self._append)

    def emit(self, record):
        msg = self.format(record)
        self.append_text.emit(msg)

    def _append(self, msg):
        self.text_edit.moveCursor(self.text_edit.textCursor().End)
        self.text_edit.insertPlainText(msg + '\n')
        self.text_edit.moveCursor(self.text_edit.textCursor().End)

def excepthook(type, value, tb):
    logging.info("Uncaught exception:", value)
    traceback.print_exception(type, value, tb)

sys.excepthook = excepthook

# Import utility modules
from eeg_stimulus_project.utils.labrecorder import LabRecorder
from eeg_stimulus_project.utils.eye_tracking_software import PupilLabs
from eeg_stimulus_project.lsl.labels import LSLLabelStream


class ControlWindow(QMainWindow):
    def __init__(self, connection, shared_status, log_queue, base_dir=None, test_number=None, host=False, subject_id=None):
        super().__init__()
        self.shared_status = shared_status
        self.connection = connection

        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        
        self.base_dir = base_dir
        self.test_number = test_number
        self.subject_id = subject_id
        self.label_stream = None
        self.labrecorder = None
        self.lab_recorder_connected = False
        self.eyetracker = None
        self.current_test = None
        self.log_queue = log_queue
        self.host = host

        # --- Window Aesthetics ---
        self.setWindowTitle("Control Window")
        self.setGeometry(screen_geometry.width() // 2, 100, screen_geometry.width() // 2, screen_geometry.height() - 150)
        self.setMinimumSize(900, 700)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5fa;
            }
        """)

        # --- Central Widget & Main Layout ---
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.control_layout = QVBoxLayout(self.central_widget)
        self.control_layout.setAlignment(Qt.AlignTop)
        self.control_layout.setContentsMargins(24, 24, 24, 24)
        self.control_layout.setSpacing(18)

        # --- DEVICE FRAME ---
        self.device_frame = QFrame(self.central_widget)
        self.device_frame.setMinimumWidth(800)
        self.device_frame.setStyleSheet("""
            QFrame {
                background-color: #ede7f6;
                border-radius: 16px;
                border: 1.5px solid #bc85fa;
            }
        """)
        self.device_frame_layout = QVBoxLayout(self.device_frame)
        self.device_frame_layout.setAlignment(Qt.AlignTop)
        self.device_frame_layout.setContentsMargins(18, 18, 18, 18)
        self.device_frame_layout.setSpacing(14)

        # --- Device Rows Helper ---
        def device_row(button_text, button_func, status_text, icon_ref, extra_widgets=None):
            row = QHBoxLayout()
            row.setSpacing(10)
            btn = QPushButton(button_text, self)
            btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #7E57C2;
                    color: white;
                    border-radius: 8px;
                    padding: 8px 22px;
                }
                QPushButton:hover {
                    background-color: #512da8;
                }
            """)
            if button_func:
                btn.clicked.connect(button_func)
            row.addWidget(btn)
            label = QLabel(status_text, self)
            label.setFont(QFont("Segoe UI", 11))
            row.addWidget(label)
            # --- Status Bar (fills vertical space) ---
            status_bar = QFrame(self)
            status_bar.setFixedWidth(120)
            status_bar.setMinimumHeight(32)
            status_bar.setMaximumHeight(40)
            status_bar.setStyleSheet("""
                QFrame {
                    border-radius: 7px;
                    background-color: #d32f2f; /* Default to red */
                }
            """)
            row.addWidget(status_bar)
            if extra_widgets:
                for w in extra_widgets:
                    row.addWidget(w)
            return row, status_bar

        # --- Actichamp Row ---
        actichamp_row, self.actichamp_linked_icon = device_row(
            "Actichamp",
            lambda: threading.Thread(target=self.start_actichamp, daemon=True).start(),
            "Linked Status:",
            "actichamp_linked_icon"
        )
        self.device_frame_layout.addLayout(actichamp_row)

        # --- LabRecorder Row ---
        labrecorder_row, self.labrecorder_connected_icon = device_row(
            "LabRecorder",
            lambda: threading.Thread(target=self.start_labrecorder, daemon=True).start(),
            "Connection Status:",
            "labrecorder_connected_icon"
        )
        self.device_frame_layout.addLayout(labrecorder_row)

        # --- Eye Tracker Row ---
        eyetracker_row, self.eyetracker_connected_icon = device_row(
            "Eye Tracker",
            self.connect_eyetracker,
            "Connection Status:",
            "eyetracker_connected_icon"
        )
        self.device_frame_layout.addLayout(eyetracker_row)

        # --- Touch Box Row ---
        lsl_touch_label = QLabel("LSL stream ready for Touch:", self)
        lsl_touch_label.setFont(QFont("Segoe UI", 11))
        self.lsl_touch_icon = QFrame(self)
        self.lsl_touch_icon.setFixedWidth(120)
        self.lsl_touch_icon.setMinimumHeight(32)
        self.lsl_touch_icon.setMaximumHeight(40)
        self.lsl_touch_icon.setStyleSheet("""
            QFrame {
                border-radius: 7px;
                background-color: #d32f2f; /* Default to red */
            }
        """)
        touchbox_row, self.touchbox_connected_icon = device_row(
            "Tactile Box",
            self.open_tactile_box,
            "Connection Status:",
            "touchbox_connected_icon",
            extra_widgets=[lsl_touch_label, self.lsl_touch_icon]
        )
        self.device_frame_layout.addLayout(touchbox_row)

        # --- VR Row ---
        vr_row, self.vr_connected_icon = device_row(
            "Virtual Reality",
            None,  # Add function if needed
            "Connection Status:",
            "vr_connected_icon"
        )
        self.device_frame_layout.addLayout(vr_row)

        # --- Turntable Row ---
        turntable_row, self.turntable_connected_icon = device_row(
            "Turntable",
            self.connect_turntable,
            "Connection Status:",
            "turntable_connected_icon"
        )
        self.device_frame_layout.addLayout(turntable_row)

        # --- Olfactory Row ---
        olfactory_row, self.olfactory_connected_icon = device_row(
            "Olfactory System",
            self.connect_olfactory,
            "Connection Status:",
            "olfactory_connected_icon"
        )
        self.device_frame_layout.addLayout(olfactory_row)

        # --- Olfactory Validation Button ---
        validate_olfactory_btn = QPushButton("Validate Ports", self)
        validate_olfactory_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        validate_olfactory_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border-radius: 8px;
                padding: 8px 22px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        validate_olfactory_btn.clicked.connect(self.validate_olfactory_ports)
        olfactory_validation_row = QHBoxLayout()
        olfactory_validation_row.addWidget(validate_olfactory_btn)
        olfactory_validation_row.addStretch()
        self.device_frame_layout.addLayout(olfactory_validation_row)

        # --- EEG Stream Row ---
        eeg_stream_row, self.eeg_stream_connected_icon = device_row(
            "EEG Stream",
            self.open_eeg_stream,
            "Stream Status:",
            "eeg_stream_connected_icon"
        )
        self.device_frame_layout.addLayout(eeg_stream_row)


        # --- Add Device Frame to Main Layout ---
        self.control_layout.addWidget(self.device_frame)

        # --- LOG TEXT EDITOR ---
        log_label = QLabel("Log Output:", self)
        log_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.control_layout.addWidget(log_label)

        self.log_text_edit = QTextEdit(self)
        self.log_text_edit.setReadOnly(True)
        self.log_text_edit.setMinimumHeight(150)
        self.log_text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #fff;
                border-radius: 10px;
                border: 1px solid #bc85fa;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 26px;
            }
        """)
        self.control_layout.addWidget(self.log_text_edit)

        logger = logging.getLogger()
        #logger.handlers = []  # Remove all existing handlers

        log_handler = QTextEditLogger(self.log_text_edit)
        log_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))

        if log_queue is not None:
            self.queue_listener = QueueListener(log_queue, log_handler)
            self.queue_listener.start()
        else:
            logger.addHandler(log_handler)

        # Process for the applications
        self.actichamp_process = None
        self.labrecorder_process = None
        self.eyetracker_process = None
        self.touchbox_process = None
        self.vr_process = None
        self.turntable_process = None
        self.olfactory_process = None
        self.eeg_stream_process = None

        if self.host:
            # If this is the host, start listening for commands from the client
            if self.connection is not None:
                self.connection_thread = threading.Thread(target=self.host_command_listener, daemon=True)
                self.connection_thread.start()

        self.start_tactile_listener()

        # --- Control Instructions ---
        self.instructions_frame = ControlInstructionsFrame(self)
        self.control_layout.addWidget(self.instructions_frame)
        self.instructions_frame.setVisible(False)  # Hide instructions by default

        # --- Show/Hide Instructions Button ---
        self.toggle_instructions_button = QPushButton("Show Instructions", self)
        self.toggle_instructions_button.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.toggle_instructions_button.setStyleSheet("""
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
        self.toggle_instructions_button.setMinimumHeight(48)
        self.toggle_instructions_button.clicked.connect(self.toggle_instructions)
        self.control_layout.addWidget(self.toggle_instructions_button, alignment=Qt.AlignCenter)

        self.label_log = []

    def toggle_instructions(self):
        if self.instructions_frame.isVisible():
            self.instructions_frame.setVisible(False)
            self.toggle_instructions_button.setText("Show Instructions")
        else:
            self.instructions_frame.setVisible(True)
            self.toggle_instructions_button.setText("Hide Instructions")

    # Redirect terminal outputs to the log queue
    def listen_to_log_queue(self):
        while True:
            try:
                msg = self.log_queue.get()
                if msg == "STOP":
                    break
                self.write(msg)
            except Exception as e:
                self.write(f"Log queue error: {e}\n")

    # Append message to QTextEdit in a thread-safe way
    def write(self, msg):
        def append():
            self.log_text_edit.moveCursor(self.log_text_edit.textCursor().End)
            self.log_text_edit.insertPlainText(msg)
            self.log_text_edit.moveCursor(self.log_text_edit.textCursor().End)
        if self.log_text_edit.thread() == QApplication.instance().thread():
            append()
        else:
            QMetaObject.invokeMethod(self.log_text_edit, append(), Qt.QueuedConnection)

    # Start the Actichamp application and automatically link to the EEG stream.
    def start_actichamp(self):
        def worker():
            try:
                # Get actichamp path from configuration based on platform
                current_platform = platform.system().lower()
                platform_config = config.get(f'platform.{current_platform}', {})
                
                if current_platform == 'windows':
                    actichamp_path = platform_config.get('actichamp_path', 'C:\\Vision\\actiCHamp-1.15.1-win32\\actiCHamp.exe')
                    self.actichamp_process = subprocess.Popen([actichamp_path])
                else:
                    logging.info("Actichamp not supported on this platform")
                    return
                    
                logging.info("Actichamp started.")
                logging.info("Attempting Link with the Actichamp Device")
                time.sleep(2)  # Wait for the application to start
                self.link_actichamp()
            except Exception as e:
                logging.info(f"Failed to start Actichamp: {e}")
                traceback.print_exc()
        threading.Thread(target=worker, daemon=True).start()

    # Link to the EEG stream through the Actichamp application.
    def link_actichamp(self):
        try:
            app = Application(backend="uia").connect(title_re="actiCHamp Connector")
            window_spec = app.window(title_re="actiCHamp Connector")
            link_button = window_spec.child_window(title="Link", control_type="Button")
            link_button.wait('enabled', timeout=5)
            link_button.click_input()
            time.sleep(5)  # Wait for the linking process to complete
            if window_spec.child_window(title="Unlink", control_type="Button").exists():
                logging.info('Actichamp Linked Successfully')
                self.actichamp_linked = True
                self.update_app_status_icon(self.actichamp_linked_icon, True)
            else:
                raise Exception("Actichamp linking failed")
        except Exception as e:
            logging.info(f"Failed to link Actichamp: {e}")
            self.actichamp_linked = False
            self.update_app_status_icon(self.actichamp_linked_icon, False)

    #Start the LabRecorder application.
    def start_labrecorder(self):
        def worker():
            try:
                # Get labrecorder path from configuration based on platform
                current_platform = platform.system().lower()
                platform_config = config.get(f'platform.{current_platform}', {})
                labrecorder_path = platform_config.get('labrecorder_path', 'labrecorder')
                
                if current_platform == 'windows':
                    self.labrecorder_process = subprocess.Popen(["cmd.exe", "/C", "start", "cmd.exe", "/K", labrecorder_path])
                else:
                    # For Linux/Mac, try to start labrecorder directly
                    self.labrecorder_process = subprocess.Popen([labrecorder_path])
                    
                logging.info("LabRecorder opened.")
                time.sleep(5)  # Wait for the application to start
                self.connect_labrecorder()  # Connect to LabRecorder after it has started
            except Exception as e:
                logging.info(f"Failed to open LabRecorder: {e}")
                traceback.print_exc()
        threading.Thread(target=worker, daemon=True).start()

    #Connect the LabRecorder application to the Actichamp stream.
    def connect_labrecorder(self):
        try:
            self.labrecorder = LabRecorder(self.base_dir, subject_id=self.subject_id)
            if self.labrecorder.s is not None:
                self.shared_status['lab_recorder_connected'] = True
                logging.info("Connected to LabRecorder.")
                self.connection.sendall((json.dumps({"action": "labrecorder_connected"}) + "\n").encode('utf-8'))
            else:
                raise Exception()
        except Exception:
            self.shared_status['lab_recorder_connected'] = False
        self.update_app_status_icon(self.labrecorder_connected_icon, self.shared_status['lab_recorder_connected'])

    #Connect to the Pupil Labs Eye Tracker.
    def connect_eyetracker(self):
        default_ip = "10.117.25.116"
        dialog = EyeTrackerIPDialog(default_ip, self)
        if dialog.exec_() == QDialog.Accepted:
            ip = dialog.get_ip()
            try:
                self.eyetracker = PupilLabs(ip_address=ip)
                time.sleep(2)  # Wait for the Pupil Labs device to initialize
                if self.eyetracker.device is not None:
                    self.shared_status['eyetracker_connected'] = True
                    self.connection.sendall((json.dumps({"action": "eyetracker_connected"}) + "\n").encode('utf-8'))
                    logging.info("Connected to Eye Tracker.")
                    self.eyetracker.estimate_time_offset()  # Estimate time offset
                else:
                    raise Exception()
            except Exception:
                logging.info(f"Failed to connect to Eye Tracker")
                self.shared_status['eyetracker_connected'] = False
        self.update_app_status_icon(self.eyetracker_connected_icon, self.shared_status['eyetracker_connected'])
        
    def open_tactile_box(self):
        from eeg_stimulus_project.stimulus.tactile_box_code import tactile_setup
        self.tactile_process = Process(target=tactile_setup.run_tactile_setup, args=(self.shared_status, self.connection))
        self.tactile_process.start()

    def connect_olfactory(self):
        if self.connection:
            msg = {"action": "connect_olfactory"}
            self.connection.sendall((json.dumps(msg) + "\n").encode('utf-8'))

    def validate_olfactory_ports(self):
        """Validate and test olfactory ports to ensure correct assignment."""
        # Initial confirmation dialog
        reply = QMessageBox.question(
            self,
            "Olfactory Port Validation",
            "Ready to test run the olfactory system to make sure that the scents are correctly assigned?\n\n"
            "This will dispense scents and ask you to confirm they are correct.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            return
        
        # Start validation process
        self.validation_state = {
            'testing_scent': 1,
            'ports_swapped': False,
            'step': 'dispense'  # State: 'dispense', 'await_response', 'swap_test'
        }
        
        self._run_validation_step()
    
    def _run_validation_step(self):
        """Execute the current validation step."""
        state = self.validation_state
        scent_num = state['testing_scent']
        
        if state['step'] == 'dispense':
            # Trigger the scent
            logging.info(f"Dispensing scent {scent_num}...")
            msg = {"action": "trigger_scent", "scent_number": scent_num}
            try:
                self.connection.sendall((json.dumps(msg) + "\n").encode('utf-8'))
            except Exception as e:
                logging.error(f"Failed to send scent trigger: {e}")
                return
            
            # Schedule stop
            QTimer.singleShot(6000, self._stop_scent_and_ask)
        
        elif state['step'] == 'await_response':
            # Ask user if scent was correct
            swapped_text = " (after swapping ports)" if state['ports_swapped'] else ""
            reply = QMessageBox.question(
                self,
                f"Scent {scent_num} Test",
                f"Was scent {scent_num} correctly dispensed{swapped_text}?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Success! Check if we're done
                if scent_num == 1 and not state['ports_swapped']:
                    # Test scent 5 next
                    state['testing_scent'] = 5
                    state['step'] = 'dispense'
                    QTimer.singleShot(500, self._run_validation_step)
                else:
                    # All tests passed
                    QMessageBox.information(
                        self,
                        "Validation Complete",
                        "Olfactory port validation successful!\n\n"
                        f"Ports are correctly assigned. {'(Ports were swapped)' if state['ports_swapped'] else ''}"
                    )
                    logging.info(f"Olfactory validation complete. Ports swapped: {state['ports_swapped']}")
            else:
                # User says it was wrong
                if not state['ports_swapped']:
                    # Swap ports and retry same scent
                    state['ports_swapped'] = True
                    logging.info(f"Swapping ports and retrying scent {scent_num}...")
                    msg = {"action": "swap_olfactory_ports"}
                    try:
                        self.connection.sendall((json.dumps(msg) + "\n").encode('utf-8'))
                    except Exception as e:
                        logging.error(f"Failed to send port swap command: {e}")
                        return
                    
                    # Wait a moment then retry
                    state['step'] = 'dispense'
                    QTimer.singleShot(500, self._run_validation_step)
                else:
                    # Already swapped once, still wrong - user needs to check hardware
                    QMessageBox.critical(
                        self,
                        "Validation Failed",
                        "Scent dispensing is not working correctly even after swapping ports.\n\n"
                        "Please check:\n"
                        "1. Arduino connections\n"
                        "2. Scent cartridge placement\n"
                        "3. Serial port configuration\n\n"
                        "Contact technical support if the problem persists."
                    )
                    logging.error("Olfactory validation failed - hardware issue suspected")
    
    def _stop_scent_and_ask(self):
        """Stop the currently dispensing scent and ask user for feedback."""
        scent_num = self.validation_state['testing_scent']
        
        # Stop the scent
        msg = {"action": "stop_scent", "scent_number": scent_num}
        try:
            self.connection.sendall((json.dumps(msg) + "\n").encode('utf-8'))
        except Exception as e:
            logging.error(f"Failed to send scent stop command: {e}")
        
        logging.info(f"Scent {scent_num} dispensing stopped.")
        
        # Move to response step
        self.validation_state['step'] = 'await_response'
        self._run_validation_step()

    def connect_turntable(self):
        if self.connection:
            msg = {"action": "connect_turntable"}
            self.connection.sendall((json.dumps(msg) + "\n").encode('utf-8'))

    def open_eeg_stream(self):
        """Open the EEG stream window in a separate process."""
        try:
            from Old_Code.eeg_stream_window import run_eeg_stream_window
            self.eeg_stream_process = Process(target=run_eeg_stream_window)
            self.eeg_stream_process.start()
            self.update_app_status_icon(self.eeg_stream_connected_icon, True)
            logging.info("EEG Stream window opened")
        except Exception as e:
            logging.error(f"Failed to open EEG Stream window: {e}")
            self.update_app_status_icon(self.eeg_stream_connected_icon, False)

    #Update the application connection/linkage status icon to show a red or green light.
    def update_app_status_icon(self, bar_widget, is_green):
        # Fill the bar with green or red
        color = "#43a047" if is_green else "#b82c2c"
        bar_widget.setStyleSheet(f"""
            QFrame {{
                border-radius: 7px;
                background-color: {color};
            }}
        """)

    def flush(self):
        # Needed for compatibility with sys.stdout redirection
        pass

    def handle_network_log_message(self, message):
        """
        Handle a log message received from the network (client).
        Display it in the log text widget with a prefix to identify it as from client.
        
        Args:
            message: Dictionary containing log message data
        """
        try:
            # Extract log information
            formatted_msg = message.get('message', '')
            level = message.get('level', 'INFO')
            timestamp = message.get('timestamp', '')
            
            # Add a prefix to identify this as a client log message
            client_msg = f"[CLIENT] {formatted_msg}"
            
            # Create a log record and display it
            # We'll use the existing log handler to ensure consistent formatting
            if hasattr(self, 'log_text_edit'):
                # Use QMetaObject to ensure thread safety when updating UI
                QMetaObject.invokeMethod(
                    self.log_text_edit,
                    'append',
                    Qt.QueuedConnection,
                    client_msg
                )
            
        except Exception as e:
            logging.error(f"Error handling network log message: {e}")

    def host_command_listener(self):
        logging.info("Host: Listening for commands...")
        buffer = ''
        try:
            while True:
                data = self.connection.recv(4096).decode('utf-8')
                if not data:
                    break
                try:
                    buffer += data
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        #logging.info(f'Host: Received line: {repr(line)}')
                        if not line.strip():
                            continue
                        try:
                            if not line.startswith("{"):
                                line = "{" + line
                            if not line.endswith("}"):
                                line = line + "}"
                            message = json.loads(line)
                            
                            # Handle different message types
                            msg_type = message.get("type")
                            action = message.get("action")
                            
                            if msg_type == "log_message":
                                # This is a log message from the client
                                self.handle_network_log_message(message)
                            elif action == "start_button":
                                test_name = message.get("test", None)
                                if test_name:
                                    self.current_test = test_name  # Store for use in start_test
                                self.start_test()
                                logging.info("Host: Starting test...")
                                pass
                            elif action == "stop_button":
                                self.stop_test()
                                logging.info("Host: Stopping test...")
                                self.save_label_log()
                                pass
                            elif action == "label":
                                label = message.get("label", None)
                                self.label_push(label)
                                if self.eyetracker and self.eyetracker.device is not None:
                                    self.eyetracker.send_marker(label)
                                #logging.info(f"Host: Pushing label: {label}")
                                pass
                            elif action == "latency_ping":
                                pong = {"action": "latency_pong", "timestamp": message.get("timestamp")}
                                self.connection.sendall((json.dumps(pong) + "\n").encode('utf-8'))
                            elif action == "touchbox_lsl_true":
                                self.update_app_status_icon(self.lsl_touch_icon, True)
                                self.shared_status['lsl_enabled'] = True
                                #self.send_lsl_control("touchbox_lsl_true")
                            elif action == "crave":
                                self.craving_response = message.get("crave", None)
                                logging.info(f"Host: Received craving response: {self.craving_response}")
                                self.label_push(f"craving_rating_{self.craving_response}")
                            elif action == "client_log":
                                # Handle log messages from client
                                log_message = message.get("message", "")
                                logging.info(f"[CLIENT] {log_message}")
                                #timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                                #self.label_log.append((label, timestamp))
                            elif action == "olfactory_connected":
                                self.update_app_status_icon(self.olfactory_connected_icon, message.get("success", False))
                                self.shared_status['olfactory_connected'] = message.get("success", False)
                            elif action == "turntable_connected":
                                self.update_app_status_icon(self.turntable_connected_icon, message.get("success", False))
                                self.shared_status['turntable_connected'] = message.get("success", False)
                        except Exception as e:
                            logging.info(f"Host: Error processing command: {e}")
                            traceback.print_exc()
                except Exception as e:
                    logging.info(f"Host: Error handling command: {e}")
                    traceback.print_exc()
        except Exception as e:
            logging.info(f"Host: Listener crashed: {e}")
            traceback.print_exc()

    def start_tactile_listener(self):
        def tactile_listener():
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('localhost', 9999))
            sock.listen(5)
            #print("Label listener started on port 9999")
            while True:
                conn, addr = sock.accept()
                with conn:
                    data = b""
                    while True:
                        chunk = conn.recv(4096)
                        if not chunk:
                            break
                        data += chunk
                    try:
                        msg = json.loads(data.decode('utf-8').strip())
                        if msg.get("action") == "tactile_connected":
                            label = "tactile_connected"
                            logging.info(f"Received label: {label}")
                            self.label_push(label)
                            logging.info(f"Host: Pushing label: {label}")
                            self.update_app_status_icon(self.touchbox_connected_icon, True)
                            self.shared_status['tactile_connected'] = True
                            self.connection.sendall((json.dumps({"action": "tactile_connected"}) + "\n").encode('utf-8'))
                        if msg.get("action") == "tactile_touch":
                            label = "tactile_touch"
                            logging.info(f"Received label: {label}")
                            self.label_push(label)
                            logging.info(f"Host: Pushing label: {label}")
                            self.connection.sendall((json.dumps({"action": "object_touched"}) + "\n").encode('utf-8'))
                            self.update_app_status_icon(self.lsl_touch_icon, False)
                    except Exception as e:
                        print(f"Error handling label message: {e}")
        threading.Thread(target=tactile_listener, daemon=True).start()

    def send_olfactory_command(scent_number):
        # Send scent_number to olfactory system (via socket, REST, etc.)
        pass

    def start_test(self):
        if self.label_stream is None:
            self.label_stream = LSLLabelStream()

        if self.labrecorder and self.labrecorder.s is not None:
            test_name = self.current_test if self.current_test else "default_test"
            self.labrecorder.Start_Recorder(test_name)
        else:
            logging.info("LabRecorder not connected")

        #if self.eyetracker is None or self.eyetracker.device is None:
        #    self.eyetracker = PupilLabs()
        if self.eyetracker and self.eyetracker.device is not None:
            self.eyetracker.start_recording()
        else:
            logging.info("Eyetracker not connected")

    def stop_test(self):
        # Stop LabRecorder if connected
        if self.labrecorder and self.labrecorder.s is not None:
            self.labrecorder.Stop_Recorder()
        # Stop the eyetracker if connected`
        if self.eyetracker and self.eyetracker.device is not None:
            self.eyetracker.stop_recording()

    def label_push(self, label):
        """
        Push a label to the LSL stream.
        """
        if self.label_stream is None:
            self.label_stream = LSLLabelStream()
        self.label_stream.push_label(label)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        self.label_log.append((label, timestamp))
        #print(f"Label pushed: {label}")
        
    def save_label_log(self):
        # Determine the test directory
        test_dir = os.path.join(self.base_dir, self.current_test)
        os.makedirs(test_dir, exist_ok=True)
        log_path = os.path.join(test_dir, "label_timestamps.txt")
        with open(log_path, "w", encoding="utf-8") as f:
            for label, timestamp in self.label_log:
                f.write(f"{timestamp}\t{label}\n")

class ControlInstructionsFrame(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(18)

        # --- Multi-page instructions ---
        self.stacked = QStackedWidget(self)
        layout.addWidget(self.stacked)

        self.pages = []
        self.add_instruction_page(
            "Welcome to the Control Window!\n\n"
            "This guide explains how to use the Control Window to manage device connections and monitor experiment progress.\n\n"
            "Click 'Next' to continue."
        )
        self.add_instruction_page(
            "Device Buttons & Status Icons:\n\n"
            "- Each row represents a device (Actichamp, LabRecorder, Eye Tracker, Tactile Box, VR, Turntable, Olfactory System).\n"
            "- The button on each row will attempt to connect or launch the corresponding device/software.\n"
            "- The red/green icon next to each device shows its connection status:\n"
            "    • Red = Not connected\n"
            "    • Green = Connected\n"
            "- Some devices (like Tactile Box) have additional indicators for LSL stream readiness.\n"
            "    • This icon turns green when the experiment is ready to receive tactile input via LSL to continue.\n"
        )
        self.add_instruction_page(
            "How to Use:\n\n"
            "1. Click each device's button to connect or launch its software.\n"
            "2. Watch the status icon to confirm successful connection (icon turns green).\n"
            "   Note: The Tactile Box will require you to manually connect by clicking the 'Start Remote Script' button after it has been launched.\n"
            "3. If a device fails to connect, check cables, power, and software, then try again."
        )
        self.add_instruction_page(
            "Monitoring Progress & Errors:\n\n"
            "- The Log Output panel at the bottom displays real-time status updates, progress messages, and any errors.\n"
            "- Always watch the log for confirmation of device connections and troubleshooting information.\n"
            "- If you see an error, follow the instructions in the log or consult the experiment protocol."
        )
        self.add_instruction_page(
            "Tips & Troubleshooting:\n\n"
            "- If a device does not connect, restart its software and check all connections.\n"
            "- Ensure all devices are powered on and properly configured before starting the experiment.\n"
            "- For the Tactile Box, it may require you to start the remote script multiple times before it connects.\n"
            "    • If it still does not connect, try closing the application and relaunching it before messing with the hardware.\n"
            "- For persistent issues, refer to the experiment documentation or contact technical support.\n"
            "- You can close these instructions at any time and return to the main Control Window."
        )

        # --- Navigation Buttons ---
        nav_layout = QHBoxLayout()
        self.prev_button = QPushButton("Previous")
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

        self.next_button = QPushButton("Next")
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

        layout.addLayout(nav_layout)
        self.update_nav_buttons()

    def add_instruction_page(self, text):
        label = QLabel(text)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignTop)
        label.setFont(QFont("Segoe UI", 15))
        label.setMargin(20)
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
        self.next_button.setEnabled(idx < total - 1)
        self.prev_button.setVisible(idx > 0)
        self.next_button.setVisible(idx < total - 1)
        self.page_label.setText(f"Page {idx + 1} of {total}")

    def hide_instructions(self):
        self.setVisible(False)

class EyeTrackerIPDialog(QDialog):
    def __init__(self, current_ip, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Confirm Eye Tracker IP Address")
        self.setModal(True)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Please confirm the Eye Tracker IP address:"))
        self.ip_edit = QLineEdit(current_ip)
        layout.addWidget(self.ip_edit)
        btn_layout = QHBoxLayout()
        self.confirm_btn = QPushButton("Confirm")
        self.cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(self.confirm_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        self.confirm_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

    def get_ip(self):
        return self.ip_edit.text()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ControlWindow()
    window.show()
    sys.exit(app.exec_())