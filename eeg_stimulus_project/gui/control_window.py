from PyQt5.QtWidgets import QFrame, QVBoxLayout, QStackedWidget, QApplication, QMainWindow, QWidget, QLabel, QPushButton, QLineEdit, QMessageBox, QHBoxLayout, QTextEdit
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QTimer
import os
import sys
import subprocess
import psutil
from pywinauto import Application
import time 
import threading
sys.path.append('\\Users\\cpl4168\\Documents\\Paid Research\\Software-for-Paid-Research-')
from eeg_stimulus_project.utils.labrecorder import LabRecorder

class Tee(object):
    def __init__(self, *streams):
        # streams can be sys.stdout, ControlWindow, or log_queue
        self.streams = streams

    def write(self, data):
        for s in self.streams:
            if hasattr(s, 'put'):
                # It's a Queue
                s.put(data)
            elif hasattr(s, 'write'):
                s.write(data)
                s.flush()

    def flush(self):
        for s in self.streams:
            if hasattr(s, 'flush'):
                s.flush()

class ControlWindow(QMainWindow):
    def __init__(self, shared_status, log_queue=None, base_dir=None, test_number=None):
        super().__init__()
        self.shared_status = shared_status

        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        
        self.base_dir = base_dir
        self.test_number = test_number
        self.setWindowTitle("Control Window")
        self.setGeometry(screen_geometry.width() // 2, 100, screen_geometry.width() // 2, screen_geometry.height()- 150)

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
        self.actichamp_button.clicked.connect(self.start_actichamp)
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
        self.labrecorder_button.clicked.connect(self.start_labrecorder)
        labrecorder_row.addWidget(self.labrecorder_button)
        
        self.labrecorder_connected_text = QLabel("Connected Status:", self)
        labrecorder_row.addWidget(self.labrecorder_connected_text)
        self.labrecorder_connected_icon = QLabel(self)
        self.update_app_status_icon(self.labrecorder_connected_icon, False)
        labrecorder_row.addWidget(self.labrecorder_connected_icon)
        
        self.device_frame_layout.addLayout(labrecorder_row)

        # Eye Tracker status row (button + icons + labels)
        eyetracker_row = QHBoxLayout()
        self.eyetracker_button = QPushButton("Eye Tracker", self)
        #self.eyetracker_button.clicked.connect() # Connect to the eyetracker
        eyetracker_row.addWidget(self.eyetracker_button)
        
        self.eyetracker_connected_text = QLabel("Connected Status:", self)
        eyetracker_row.addWidget(self.eyetracker_connected_text)
        self.eyetracker_connected_icon = QLabel(self)
        self.update_app_status_icon(self.eyetracker_connected_icon, False)
        eyetracker_row.addWidget(self.eyetracker_connected_icon)
        
        self.device_frame_layout.addLayout(eyetracker_row)

        # Touch Box status row (button + icons + labels)
        touchbox_row = QHBoxLayout()
        self.touchbox_button = QPushButton("Touchbox", self)
        #self.touchbox_button.clicked.connect() # Connect to the touchbox
        touchbox_row.addWidget(self.touchbox_button)
        
        self.touchbox_connected_text = QLabel("Connected Status:", self)
        touchbox_row.addWidget(self.touchbox_connected_text)
        self.touchbox_connected_icon = QLabel(self)
        self.update_app_status_icon(self.touchbox_connected_icon, False)
        touchbox_row.addWidget(self.touchbox_connected_icon)
        
        self.device_frame_layout.addLayout(touchbox_row)

        # VR status row (button + icons + labels)
        vr_row = QHBoxLayout()
        self.vr_button = QPushButton("Virtual Reality", self)
        #self.vr_button.clicked.connect() # Connect to the VR device
        vr_row.addWidget(self.vr_button)
        
        self.vr_connected_text = QLabel("Connected Status:", self)
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
        
        self.turntable_connected_text = QLabel("Connected Status:", self)
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
        
        self.olfactory_connected_text = QLabel("Connected Status:", self)
        olfactory_row.addWidget(self.olfactory_connected_text)
        self.olfactory_connected_icon = QLabel(self)
        self.update_app_status_icon(self.olfactory_connected_icon, False)
        olfactory_row.addWidget(self.olfactory_connected_icon)
        
        self.device_frame_layout.addLayout(olfactory_row)
        
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

        # Process for the applications
        self.actichamp_process = None
        self.labrecorder_process = None
        self.eyetracker_process = None
        self.touchbox_process = None
        self.vr_process = None
        self.turntable_process = None
        self.olfactory_process = None

        #self.actichamp_timer = QTimer(self)
        #self.actichamp_timer.timeout.connect(self.check_actichamp_status)
        #self.actichamp_timer.start(5000)
        
        #self.labrecorder_timer = QTimer(self)
        #self.labrecorder_timer.timeout.connect(self.check_labrecorder_status)
        #self.labrecorder_timer.start(5000)

        #self.actichamp_linked = False

        self.labrecorder = None
        self.lab_recorder_connected = False

        self.log_queue = log_queue

        # Start a thread to listen to the log queue and print messages in the QTextEdit
        if self.log_queue is not None:
            self.log_thread = threading.Thread(target=self.listen_to_log_queue, daemon=True)
            self.log_thread.start()

        self.original_stdout = sys.stdout
        sys.stdout = Tee(sys.stdout, self, self.log_queue)

    def listen_to_log_queue(self):
        while True:
            try:
                msg = self.log_queue.get()
                if msg == "STOP":
                    break
                self.write(msg)
            except Exception as e:
                self.write(f"Log queue error: {e}\n")

    def write(self, msg):
        # Append message to QTextEdit in a thread-safe way
        def append():
            self.log_text_edit.moveCursor(self.log_text_edit.textCursor().End)
            self.log_text_edit.insertPlainText(msg)
            self.log_text_edit.moveCursor(self.log_text_edit.textCursor().End)
        if self.log_text_edit.thread() == QApplication.instance().thread():
            append()
        else:
            QApplication.instance().postEvent(
                self.log_text_edit,
                type(QEvent)(),
                lambda: append()
            )

    def start_actichamp(self):
        """
        Start the Actichamp application.
        """
        try:
            self.actichamp_process = subprocess.Popen(["C:\\Vision\\actiCHamp-1.15.1-win32\\actiCHamp.exe"])
            print("Actichamp started.")
            print("Attempting Link with the Actichamp Device")
            time.sleep(2)  # Wait for the application to start
            self.link_actichamp()  # Link to the Actichamp device
        except Exception as e:
            print(f"Failed to start Actichamp: {e}")
        # Update icon after a short delay to allow process to start
        #QTimer.singleShot(1000, self.check_actichamp_status)

    def link_actichamp(self):
        try:
            app = Application(backend="uia").connect(title_re="actiCHamp Connector")
            window_spec = app.window(title_re="actiCHamp Connector")
            link_button = window_spec.child_window(title="Link", control_type="Button")
            link_button.wait('enabled', timeout=5)
            link_button.click_input()
            time.sleep(5)  # Wait for the linking process to complete
            print('Actichamp Linked Successfully')
            self.actichamp_linked = True
            self.update_app_status_icon(self.actichamp_linked_icon, True)
        except Exception as e:
            print(f"Failed to link Actichamp: {e}")
            self.actichamp_linked = False
            self.update_app_status_icon(self.actichamp_linked_icon, False)

    #Start the LabRecorder application.
    def start_labrecorder(self):
        try:
            self.labrecorder_process = subprocess.Popen(["cmd.exe", "/C", "start", "cmd.exe", "/K", "C:\\Vision\\LabRecorder\\LabRecorder.exe"])
            print("LabRecorder opened.")
            QTimer.singleShot(5000, self.connect_labrecorder)  # Wait 5 seconds before connecting
        except Exception as e:
            print(f"Failed to open LabRecorder: {e}")
        #QTimer.singleShot(1000, self.check_labrecorder_status)

    #Connect to the LabRecorder application.
    def connect_labrecorder(self):
        try:
            self.labrecorder = LabRecorder(self.base_dir)
            self.shared_status['lab_recorder_connected'] = True
            print("Connected to LabRecorder.")
        except Exception as e:
            self.shared_status['lab_recorder_connected'] = False
            print(f"Failed to connect to LabRecorder: {e}")
        self.update_app_status_icon(self.labrecorder_connected_icon, self.shared_status['lab_recorder_connected'])
        
    #Update the application status icon to show a red or green light.
    def update_app_status_icon(self, icon_label, is_green):
        pixmap = QPixmap(20, 20)
        pixmap.fill(Qt.green if is_green else Qt.red)
        icon_label.setPixmap(pixmap)

    def flush(self):
        # Needed for compatibility with sys.stdout redirection
        pass

    #def is_process_running(self, process_name):
    #    for proc in psutil.process_iter(['name', 'exe', 'cmdline']):
    #        try:
    #            if process_name.lower() in proc.info['name'].lower():
    #                return True
    #        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
    #            pass
    #    return False
    #
    #def check_actichamp_status(self):
    #    running = self.is_process_running("actiCHamp.exe")
    #    self.update_app_status_icon(self.actichamp_status_icon, running)

    #def check_labrecorder_status(self):
    #    connected = self.shared_status.get('lab_recorder_connected', False)
    #    self.update_app_status_icon(self.labrecorder_connected_icon, connected)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ControlWindow()
    window.show()
    sys.exit(app.exec_())