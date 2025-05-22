from PyQt5.QtWidgets import QFrame, QVBoxLayout, QStackedWidget, QApplication, QMainWindow, QWidget, QLabel, QPushButton, QLineEdit, QMessageBox, QHBoxLayout
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QTimer
import os
import sys
import subprocess
import psutil
from pywinauto import Application
import time 
sys.path.append('\\Users\\srs1520\\Documents\\Paid Research\\Software-for-Paid-Research-')
from eeg_stimulus_project.utils.labrecorder import LabRecorder
from eeg_stimulus_project.utils.device_manager import DeviceManager

class ControlWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Control Window")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.control_layout = QVBoxLayout(self.central_widget)
        self.control_layout.setAlignment(Qt.AlignTop)

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

        self.control_layout.addLayout(actichamp_row)
        
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
        
        self.control_layout.addLayout(labrecorder_row)

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
        
        self.control_layout.addLayout(eyetracker_row)

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
        
        self.control_layout.addLayout(touchbox_row)

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
        
        self.control_layout.addLayout(vr_row)

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
        
        self.control_layout.addLayout(turntable_row)

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
        
        self.control_layout.addLayout(olfactory_row)
        
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
        #self.labrecorder_connected = False
        
        self.base_dir = os.environ.get('BASE_DIR', '')

        self.labrecorder = None
        self.lab_recorder_connected = False

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
            self.connect_labrecorder()
        except Exception as e:
            print(f"Failed to open LabRecorder: {e}")
        #QTimer.singleShot(1000, self.check_labrecorder_status)

    #Connect to the LabRecorder application.
    def connect_labrecorder(self):
        try:
            DeviceManager.labrecorder = LabRecorder(self.base_dir)
            if DeviceManager.labrecorder.s is None:
                raise Exception()
            DeviceManager.lab_recorder_connected = True
            print("Connected to LabRecorder.")
        except Exception as e:
            DeviceManager.lab_recorder_connected = False
        self.update_app_status_icon(self.labrecorder_connected_icon, DeviceManager.lab_recorder_connected)
        
    #Update the application status icon to show a red or green light.
    def update_app_status_icon(self, icon_label, is_green):
        pixmap = QPixmap(20, 20)
        pixmap.fill(Qt.green if is_green else Qt.red)
        icon_label.setPixmap(pixmap)

    '''
    def is_process_running(self, process_name):
        for proc in psutil.process_iter(['name', 'exe', 'cmdline']):
            try:
                if process_name.lower() in proc.info['name'].lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False

    def check_actichamp_status(self):
        running = self.is_process_running("actiCHamp.exe")
        self.update_app_status_icon(self.actichamp_status_icon, running)

    def check_labrecorder_status(self):
        running = self.is_process_running("LabRecorder.exe")
        self.update_app_status_icon(self.labrecorder_status_icon, running)
    '''

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ControlWindow()
    window.show()
    sys.exit(app.exec_())