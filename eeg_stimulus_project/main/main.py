import sys
sys.path.append('\\Users\\cpl4168\\Documents\\Paid Research\\Software-for-Paid-Research-')
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, QMessageBox, QHBoxLayout
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QTimer
import os
import subprocess
import psutil
from pywinauto import Application
from pywinauto import Desktop
import time 
from eeg_stimulus_project.lsl.stream_manager import LSL  # Import the LSL class from LSL.py

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Subject Information")
        self.setGeometry(100, 100, 400, 300)

        # Create the central widget and set it as the central widget of the main window
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create a vertical layout for the central widget
        layout = QVBoxLayout(central_widget)

        # LSL Status
        #self.lsl_status_label = QLabel("LSL Status:", self)
        #layout.addWidget(self.lsl_status_label)
        #self.lsl_status_icon = QLabel(self)
        #self.update_lsl_status_icon(False)
        #layout.addWidget(self.lsl_status_icon)

        # Subject ID input
        self.subject_id_label = QLabel("Subject ID:", self)
        layout.addWidget(self.subject_id_label)
        self.subject_id_input = QLineEdit(self)
        layout.addWidget(self.subject_id_input)

        # Test number input
        self.test_number_label = QLabel("Test Number (1 or 2):", self)
        layout.addWidget(self.test_number_label)
        self.test_number_input = QLineEdit(self)
        layout.addWidget(self.test_number_input)

        # Start button
        self.start_button = QPushButton("Start", self)
        self.start_button.clicked.connect(self.start_experiment)
        #self.start_button.setEnabled(False)  # Disable until LSL is streaming
        layout.addWidget(self.start_button)

        # Retry LSL button
        self.retry_button = QPushButton("Retry LSL", self)
        self.retry_button.clicked.connect(self.retry_lsl)
        self.retry_button.setEnabled(False)
        layout.addWidget(self.retry_button)

        self.connection_label = QLabel("Click Either Button To Start Its Corresponding Application:", self)
        layout.addWidget(self.connection_label)

        # Actichamp status row (button + icons + labels)
        actichamp_row = QHBoxLayout()
        self.actichamp_button = QPushButton("Actichamp", self)
        self.actichamp_button.clicked.connect(self.start_actichamp)
        actichamp_row.addWidget(self.actichamp_button)

        self.actichamp_status_text = QLabel("Running", self)
        actichamp_row.addWidget(self.actichamp_status_text)
        self.actichamp_status_icon = QLabel(self)
        self.update_app_status_icon(self.actichamp_status_icon, False)
        actichamp_row.addWidget(self.actichamp_status_icon)
        
        self.actichamp_linked_text = QLabel("Linked", self)
        actichamp_row.addWidget(self.actichamp_linked_text)
        self.actichamp_linked_icon = QLabel(self)
        self.update_app_status_icon(self.actichamp_linked_icon, False)
        actichamp_row.addWidget(self.actichamp_linked_icon)

        layout.addLayout(actichamp_row)

        
        '''
        # LabRecorder status row (button + icons + labels)
        labrecorder_row = QHBoxLayout()
        self.labrecorder_button = QPushButton("LabRecorder", self)
        self.labrecorder_button.clicked.connect(self.start_labrecorder)
        labrecorder_row.addWidget(self.labrecorder_button)

        self.labrecorder_status_text = QLabel("Running", self)
        labrecorder_row.addWidget(self.labrecorder_status_text)
        self.labrecorder_status_icon = QLabel(self)
        self.update_app_status_icon(self.labrecorder_status_icon, False)
        labrecorder_row.addWidget(self.labrecorder_status_icon)
        
        self.labrecorder_connected_text = QLabel("Connected", self)
        labrecorder_row.addWidget(self.labrecorder_connected_text)
        self.labrecorder_connected_icon = QLabel(self)
        self.update_app_status_icon(self.labrecorder_connected_icon, False)
        labrecorder_row.addWidget(self.labrecorder_connected_icon)
        
        layout.addLayout(labrecorder_row)
        '''

        # Initialize LSL
        #self.init_lsl()

        # Process for the GUI
        self.actichamp_process = None
        #self.labrecorder_process = None
        self.gui_process = None

        self.actichamp_timer = QTimer(self)
        self.actichamp_timer.timeout.connect(self.check_actichamp_status)
        self.actichamp_timer.start(5000)
        
        #self.labrecorder_timer = QTimer(self)
        #self.labrecorder_timer.timeout.connect(self.check_labrecorder_status)
        #self.labrecorder_timer.start(5000)

        self.actichamp_linked = False
        #self.labrecorder_connected = False

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
        QTimer.singleShot(1000, self.check_actichamp_status)

    def link_actichamp(self):
        try:
            app = Application(backend="uia").connect(title_re="actiCHamp Connector")
            window_spec = app.window(title_re="actiCHamp Connector")
            link_button = window_spec.child_window(title="Link", control_type="Button")
            link_button.wait('enabled', timeout=5)
            link_button.click_input()
            print('Actichamp Linked Successfully')
            self.actichamp_linked = True
            self.update_app_status_icon(self.actichamp_linked_icon, True)
        except Exception as e:
            print(f"Failed to link Actichamp: {e}")
            self.actichamp_linked = False
            self.update_app_status_icon(self.actichamp_linked_icon, False)
        
    '''
    def start_labrecorder(self):
        """
        Start the LabRecorder application.
        """
        try:
            self.labrecorder_process = subprocess.Popen(["cmd.exe", "/C", "start", "cmd.exe", "/K", "C:\\Vision\\LabRecorder\\LabRecorder.exe"])
            print("LabRecorder started.")
        except Exception as e:
            print(f"Failed to start LabRecorder: {e}")
        QTimer.singleShot(1000, self.check_labrecorder_status)
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

    def update_app_status_icon(self, icon_label, is_green):
        """
        Update the application status icon to show a red or green light.
        """
        pixmap = QPixmap(20, 20)
        pixmap.fill(Qt.green if is_green else Qt.red)
        icon_label.setPixmap(pixmap)

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
    def connect_labrecorder(self, base_dir):
        """
        Connect to the LabRecorder by reading the status file written by main_gui.py.
        """
        # Path to the status file in the main folder (where main.py is)
        main_folder = os.path.dirname(os.path.abspath(sys.argv[0]))
        status_file = os.path.join(main_folder, "labrecorder_status.txt")
        self.labrecorder_connected = False

        if os.path.exists(status_file):
            try:
                with open(status_file, "r") as f:
                    status = f.read().strip().lower()
                    self.labrecorder_connected = status == "true"
            except Exception as e:
                print(f"Error reading LabRecorder status file: {e}")
                self.labrecorder_connected = False
        else:
            print("LabRecorder status file not found.")
            self.labrecorder_connected = False

        # Update the icon based on the status
        self.update_app_status_icon(self.labrecorder_connected_icon, self.labrecorder_connected)
        if self.labrecorder_connected:
            print("LabRecorder connected (from file).")
        else:
            print("LabRecorder not connected (from file).")
    '''
    
    def start_experiment(self):
        # Get the subject ID and test number from the input fields
        subject_id = self.subject_id_input.text()
        test_number = self.test_number_input.text()

        # Check if the subject ID and test number are valid
        if subject_id and test_number in ['1', '2']:
            # Create base directory structure
            base_dir = os.path.join('eeg_stimulus_project', 'saved_data', f'subject_{subject_id}', f'test_{test_number}')
            os.makedirs(base_dir, exist_ok=True)

            # List of tests
            passive_tests = [
                'Unisensory Neutral Visual',
                'Unisensory Alcohol Visual',
                'Multisensory Neutral Visual & Olfactory',
                'Multisensory Alcohol Visual & Olfactory',
                'Multisensory Neutral Visual, Tactile & Olfactory',
                'Multisensory Alcohol Visual, Tactile & Olfactory'
            ]

            stroop_tests = [
                'Multisensory Alcohol (Visual & Tactile)',
                'Multisensory Neutral (Visual & Tactile)',
                'Multisensory Alcohol (Visual & Olfactory)',
                'Multisensory Neutral (Visual & Olfactory)'
            ]

            # Select the appropriate tests based on the test number
            if test_number == '1':
                selected_tests = passive_tests
            else:
                selected_tests = stroop_tests

            # Create subdirectories for each selected test and clear the data.csv file if it exists
            for test in selected_tests:
                test_dir = os.path.join(base_dir, test)
                os.makedirs(test_dir, exist_ok=True)
                file_path = os.path.join(test_dir, 'data.csv')
                if os.path.exists(file_path):
                    with open(file_path, 'w') as file:
                        file.truncate(0)

            # Pass the subject ID, test number, and base directory as environment variables
            env = os.environ.copy()
            env['SUBJECT_ID'] = subject_id
            env['TEST_NUMBER'] = test_number
            env['BASE_DIR'] = base_dir

            # Construct the correct path to gui.py
            gui_path = os.path.join(os.path.dirname(__file__), '..', 'gui', 'main_gui.py')

            # Run the GUI script
            self.gui_process = subprocess.Popen([sys.executable, gui_path], env=env)
            #status_file = os.path.join(base_dir, "labrecorder_status.txt")
            #labrecorder_connected = False
            #if os.path.exists(status_file):
            #    with open(status_file, "r") as f:
            #        labrecorder_connected = f.read().strip().lower() == "true"
            #print("LabRecorder connected (from file):", labrecorder_connected)
            # Now you can use labrecorder_connected in main.py as needed        
        else:
            print("Please enter a valid Subject ID and Test Number (1 or 2).")

    def retry_lsl(self):
        """
        Retry LSL initialization and update the status icon.
        """
        self.update_lsl_status_icon(False)
        self.start_button.setEnabled(False)
        self.retry_button.setEnabled(False)
        self.init_lsl()

    def closeEvent(self, event):
        # Terminate GUI process
        if self.gui_process is not None:
            self.gui_process.terminate()
            self.gui_process.wait()
        # Terminate Actichamp process
        #if self.actichamp_process is not None:
        #    self.actichamp_process.terminate()
        #    self.actichamp_process.wait()
        # Terminate LabRecorder process
        #if self.labrecorder_process is not None:
        #    self.labrecorder_process.terminate()
        #    self.labrecorder_process.wait()
        event.accept()

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

if __name__ == "__main__":
    # Create the application and main window, then run the application
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
