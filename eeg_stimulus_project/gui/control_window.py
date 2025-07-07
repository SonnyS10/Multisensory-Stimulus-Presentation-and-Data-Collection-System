from PyQt5.QtWidgets import QFrame, QVBoxLayout, QApplication, QMainWindow, QWidget, QLabel, QPushButton, QHBoxLayout, QTextEdit
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QTimer, QMetaObject, pyqtSignal, QObject
import sys
import subprocess
from pywinauto import Application
import time 
import threading
import json
import traceback
import logging 
import os
from logging.handlers import QueueListener #QueueHandler
import socket

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

sys.path.append('\\Users\\cpl4168\\Documents\\Paid Research\\Software-for-Paid-Research-')
from eeg_stimulus_project.utils.labrecorder import LabRecorder
from eeg_stimulus_project.utils.pupil_labs import PupilLabs
from eeg_stimulus_project.lsl.labels import LSLLabelStream


class ControlWindow(QMainWindow):
    def __init__(self, connection, shared_status, log_queue, base_dir=None, test_number=None, host=False):
        super().__init__()
        self.shared_status = shared_status
        self.connection = connection

        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        
        self.base_dir = base_dir
        self.test_number = test_number
        self.label_stream = None
        self.labrecorder = None
        self.lab_recorder_connected = False
        self.eyetracker = None
        self.current_test = None
        self.log_queue = log_queue
        self.host = host
        
        #self.setup_logging(log_queue)

        # Set the window title and size (half of the screen width and full height)
        self.setWindowTitle("Control Window")
        self.setGeometry(screen_geometry.width() // 2, 100, screen_geometry.width() // 2, screen_geometry.height()- 150)

        # Create the central widget and layout
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        # --- DEVICE FRAME ---
        self.device_frame = QFrame(self.central_widget)
        self.device_frame.setMinimumWidth(800)  # Set minimum width to 800
        self.device_frame_layout = QVBoxLayout(self.device_frame)
        self.device_frame_layout.setAlignment(Qt.AlignTop)
        self.device_frame_layout.setContentsMargins(10, 10, 10, 10)

        # Actichamp status row (button + icons + labels)
        actichamp_row = QHBoxLayout()
        self.actichamp_button = QPushButton("Actichamp", self)
        self.actichamp_button.clicked.connect(lambda: threading.Thread(target=self.start_actichamp, daemon=True).start())
        actichamp_row.addWidget(self.actichamp_button)
        
        self.actichamp_linked_text = QLabel("Linked Status:", self)
        actichamp_row.addWidget(self.actichamp_linked_text)
        self.actichamp_linked_icon = QLabel(self)
        self.update_app_status_icon(self.actichamp_linked_icon, False)
        actichamp_row.addWidget(self.actichamp_linked_icon)

        self.device_frame_layout.addLayout(actichamp_row)
        
        # LabRecorder status row (button + icons + labels)
        labrecorder_row = QHBoxLayout()
        self.labrecorder_button = QPushButton("LabRecorder", self)
        self.labrecorder_button.clicked.connect(lambda: threading.Thread(target=self.start_labrecorder, daemon=True).start())
        labrecorder_row.addWidget(self.labrecorder_button)
        
        self.labrecorder_connected_text = QLabel("Connection Status:", self)
        labrecorder_row.addWidget(self.labrecorder_connected_text)
        self.labrecorder_connected_icon = QLabel(self)
        self.update_app_status_icon(self.labrecorder_connected_icon, False)
        labrecorder_row.addWidget(self.labrecorder_connected_icon)
        
        self.device_frame_layout.addLayout(labrecorder_row)

        # Eye Tracker status row (button + icons + labels)
        eyetracker_row = QHBoxLayout()
        self.eyetracker_button = QPushButton("Eye Tracker", self)
        self.eyetracker_button.clicked.connect(self.connect_eyetracker) # Connect to the eyetracker
        eyetracker_row.addWidget(self.eyetracker_button)
        
        self.eyetracker_connected_text = QLabel("Connection Status:", self)
        eyetracker_row.addWidget(self.eyetracker_connected_text)
        self.eyetracker_connected_icon = QLabel(self)
        self.update_app_status_icon(self.eyetracker_connected_icon, False)
        eyetracker_row.addWidget(self.eyetracker_connected_icon)
        
        self.device_frame_layout.addLayout(eyetracker_row)

        # Touch Box status row (button + icons + labels)
        touchbox_row = QHBoxLayout()
        self.touchbox_button = QPushButton("Touchbox", self)
        self.touchbox_button.clicked.connect(self.open_tactile_box)  # Connect to the touchbox
        touchbox_row.addWidget(self.touchbox_button)
        
        self.touchbox_connected_text = QLabel("Connection Status:", self)
        touchbox_row.addWidget(self.touchbox_connected_text)
        self.touchbox_connected_icon = QLabel(self)
        self.update_app_status_icon(self.touchbox_connected_icon, False)
        touchbox_row.addWidget(self.touchbox_connected_icon)

        self.lsl_touch_label = QLabel("LSL stream ready for Touch:", self)
        touchbox_row.addWidget(self.lsl_touch_label)
        self.lsl_touch_icon = QLabel(self)
        self.update_app_status_icon(self.lsl_touch_icon, False)  # Start as red
        touchbox_row.addWidget(self.lsl_touch_icon)

        self.device_frame_layout.addLayout(touchbox_row)

        # VR status row (button + icons + labels)
        vr_row = QHBoxLayout()
        self.vr_button = QPushButton("Virtual Reality", self)
        #self.vr_button.clicked.connect() # Connect to the VR device
        vr_row.addWidget(self.vr_button)
        
        self.vr_connected_text = QLabel("Connection Status:", self)
        vr_row.addWidget(self.vr_connected_text)
        self.vr_connected_icon = QLabel(self)
        self.update_app_status_icon(self.vr_connected_icon, False)
        vr_row.addWidget(self.vr_connected_icon)
        
        self.device_frame_layout.addLayout(vr_row)

        # Turntable status row (button + icons + labels)
        turntable_row = QHBoxLayout()
        self.turntable_button = QPushButton("Turntable", self)
        #self.turntable_button.clicked.connect() # Connect to the turntable
        turntable_row.addWidget(self.turntable_button)
        
        self.turntable_connected_text = QLabel("Connection Status:", self)
        turntable_row.addWidget(self.turntable_connected_text)
        self.turntable_connected_icon = QLabel(self)
        self.update_app_status_icon(self.turntable_connected_icon, False)
        turntable_row.addWidget(self.turntable_connected_icon)
        
        self.device_frame_layout.addLayout(turntable_row)

        # Olfactory Sysytem status row (button + icons + labels)
        olfactory_row = QHBoxLayout()
        self.olfactory_button = QPushButton("Olfactory System", self)
        #self.olfactory_button.clicked.connect() # Connect to the olfactory
        olfactory_row.addWidget(self.olfactory_button)
        
        self.olfactory_connected_text = QLabel("Connection Status:", self)
        olfactory_row.addWidget(self.olfactory_connected_text)
        self.olfactory_connected_icon = QLabel(self)
        self.update_app_status_icon(self.olfactory_connected_icon, False)
        olfactory_row.addWidget(self.olfactory_connected_icon)
        
        self.device_frame_layout.addLayout(olfactory_row)

        # TO MAYBE BE IMPLEMENTED LATER
        # LSL Status
        #self.lsl_status_label = QLabel("LSL Status:", self)
        #layout.addWidget(self.lsl_status_label)
        #self.lsl_status_icon = QLabel(self)
        #self.update_lsl_status_icon(False)
        #layout.addWidget(self.lsl_status_icon)
        
        # --- MAIN LAYOUT ---
        self.control_layout = QVBoxLayout(self.central_widget)
        self.control_layout.setAlignment(Qt.AlignTop)
        self.control_layout.addWidget(self.device_frame)

        # --- LOG TEXT EDITOR ---
        self.log_text_edit = QTextEdit(self)
        self.log_text_edit.setReadOnly(True)
        self.log_text_edit.setMinimumHeight(150)
        self.control_layout.addWidget(QLabel("Log Output:", self))
        self.control_layout.addWidget(self.log_text_edit)

        log_handler = QTextEditLogger(self.log_text_edit)
        log_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
        logging.getLogger().addHandler(log_handler)

        if log_queue is not None:
            self.queue_listener = QueueListener(log_queue, log_handler)
            self.queue_listener.start()
            
        # Process for the applications
        self.actichamp_process = None
        self.labrecorder_process = None
        self.eyetracker_process = None
        self.touchbox_process = None
        self.vr_process = None
        self.turntable_process = None
        self.olfactory_process = None

        # Start a thread to listen to the log queue and print messages in the QTextEdit
        #if self.log_queue is not None:
        #   self.log_thread = threading.Thread(target=self.listen_to_log_queue, daemon=True)
        #   self.log_thread.start()

        if self.host:
            # If this is the host, start listening for commands from the client
            if self.connection is not None:
                self.connection_thread = threading.Thread(target=self.host_command_listener, daemon=True)
                self.connection_thread.start()

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
                self.actichamp_process = subprocess.Popen(["C:\\Vision\\actiCHamp-1.15.1-win32\\actiCHamp.exe"])
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
                self.labrecorder_process = subprocess.Popen(["cmd.exe", "/C", "start", "cmd.exe", "/K", "C:\\Vision\\LabRecorder\\LabRecorder.exe"])
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
            self.labrecorder = LabRecorder(self.base_dir)
            if self.labrecorder.s is not None:
                self.shared_status['lab_recorder_connected'] = True
                logging.info("Connected to LabRecorder.")
            else:
                raise Exception()
        except Exception:
            self.shared_status['lab_recorder_connected'] = False
        self.update_app_status_icon(self.labrecorder_connected_icon, self.shared_status['lab_recorder_connected'])

    #Connect to the Pupil Labs Eye Tracker.
    def connect_eyetracker(self):
        try:
            self.eyetracker = PupilLabs()
            time.sleep(2)  # Wait for the Pupil Labs device to initialize
            if self.eyetracker.device is not None:
                self.shared_status['eyetracker_connected'] = True
                logging.info("Connected to Eye Tracker.")
                self.eyetracker.estimate_time_offset()  # Estimate time offset
            else:
                raise Exception()
        except Exception:
            logging.info(f"Failed to connect to Eye Tracker")
            self.shared_status['eyetracker_connected'] = False
        self.update_app_status_icon(self.eyetracker_connected_icon, self.shared_status['eyetracker_connected'])
        
    def open_tactile_box(self):
        # Path to your tactile_setup.py
        script_path = os.path.join(
            "c:/Users/srs1520/Documents/Paid Research/Software-for-Paid-Research-/eeg_stimulus_project/stimulus/tactile_box_code/tactile_setup.py"
        )
        # Use sys.executable to ensure the same Python interpreter is used
        subprocess.Popen([sys.executable, script_path])

    #Update the application connection/linkage status icon to show a red or green light.
    def update_app_status_icon(self, icon_label, is_green):
        pixmap = QPixmap(20, 20)
        pixmap.fill(Qt.green if is_green else Qt.red)
        icon_label.setPixmap(pixmap)

    def flush(self):
        # Needed for compatibility with sys.stdout redirection
        pass

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
                        logging.info(f'Host: Received line: {repr(line)}')
                        if not line.strip():
                            continue
                        try:
                            if not line.startswith("{"):
                                line = "{" + line
                            if not line.endswith("}"):
                                line = line + "}"
                            message = json.loads(line)
                            action = message.get("action")
                            if action == "start_button":
                                test_name = message.get("test", None)
                                if test_name:
                                    self.current_test = test_name  # Store for use in start_test
                                self.start_test()
                                logging.info("Host: Starting test...")
                                pass
                            elif action == "stop_button":
                                self.stop_test()
                                logging.info("Host: Stopping test...")
                                pass
                            elif action == "label":
                                label = message.get("label", None)
                                self.label_push(label)
                                logging.info(f"Host: Pushing label: {label}")
                                pass
                            elif action == "latency_ping":
                                pong = {"action": "latency_pong", "timestamp": message.get("timestamp")}
                                self.connection.sendall((json.dumps(pong) + "\n").encode('utf-8'))
                            elif action == "touchbox_lsl_true":
                                self.update_app_status_icon(self.lsl_touch_icon, True)
                                self.send_lsl_control("touchbox_lsl_true")
                            elif action == "touchbox_lsl_false":
                                self.update_app_status_icon(self.lsl_touch_icon, False)
                                self.send_lsl_control("touchbox_lsl_false")
                            # ...other actions...
                        except Exception as e:
                            logging.info(f"Host: Error processing command: {e}")
                            traceback.print_exc()
                except Exception as e:
                    logging.info(f"Host: Error handling command: {e}")
                    traceback.print_exc()
        except Exception as e:
            logging.info(f"Host: Listener crashed: {e}")
            traceback.print_exc()

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
        #print(f"Label pushed: {label}")

    def send_lsl_control(self, action):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('localhost', 9999))
            msg = {"action": action}
            sock.sendall(json.dumps(msg).encode())
            sock.close()
        except Exception as e:
            logging.info(f"Could not send LSL control message: {e}")
        
    # To send status updates, periodically or on change:
        #status_msg = {
        #    "action": "host_status",
        #    "status": f"LabRecorder: {'Connected' if self.shared_status['lab_recorder_connected'] else 'Not Connected'}, "
        #              f"Eyetracker: {'Connected' if self.shared_status['eyetracker_connected'] else 'Not Connected'}"
        #}
        #self.connection.sendall((json.dumps(status_msg) + "\n").encode('utf-8'))

    # TO MAYBE BE IMPLEMENTED LATER

    #def setup_logging(self, log_queue):
    #    queue_handler = QueueHandler(log_queue)
    #    logger = logging.getLogger()
    #    logger.setLevel(logging.INFO)
    #    logger.handlers = []
    #    logger.addHandler(queue_handler)

    '''
    def init_lsl(self):
        """
        Initialize LSL and update the status icon.
        """
        try:
            if LSL.init_lsl_stream() == True:  # Call the LSL initialization method
                self.update_lsl_status_icon(True)
                self.start_button.setEnabled(True)
                self.retry_button.setEnabled(False)
            else:
                self.show_error_message("Failed to initialize LSL: No stream found.")
                self.update_lsl_status_icon(False)
                self.start_button.setEnabled(True)
                self.retry_button.setEnabled(True)
        except Exception as e:
            self.show_error_message(f"Failed to initialize LSL because of an Error: {str(e)}")
            self.update_lsl_status_icon(False)
            self.start_button.setEnabled(False)
            self.retry_button.setEnabled(True)

    def update_lsl_status_icon(self, is_streaming):
        """
        Update the LSL status icon to show a red or green light.
        """
        pixmap = QPixmap(20, 20)
        pixmap.fill(Qt.green if is_streaming else Qt.red)
        self.lsl_status_icon.setPixmap(pixmap)

    def show_error_message(self, message):
        """
        Show an error message in a popup dialog.
        """
        error_dialog = QMessageBox(self)
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setWindowTitle("Error")
        error_dialog.setText(message)
        error_dialog.exec_()
    '''

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ControlWindow()
    window.show()
    sys.exit(app.exec_())