import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QMessageBox, QFileDialog, QGroupBox, QSizePolicy, QSpacerItem, QCheckBox
)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt
from multiprocessing import Manager, Process, Queue
import socket
import threading
import logging
from logging.handlers import QueueListener

# Import configuration manager
from eeg_stimulus_project.config import config


# Set up logging for the application
def setup_logging():
    """Setup logging using configuration settings."""
    log_level = config.get('logging.level', 'INFO')
    log_format = config.get('logging.format', '%(asctime)s %(levelname)s %(message)s')
    log_file = config.get_absolute_path('paths.log_file')
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format=log_format,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

# Initialize logging
setup_logging()

# Returns lists of passive and stroop test names
def get_test_lists():
    # Get test types from configuration
    passive_tests = config.get('experiment.test_types.passive', [
        'Unisensory Neutral Visual',
        'Unisensory Alcohol Visual',
        'Multisensory Neutral Visual & Olfactory',
        'Multisensory Alcohol Visual & Olfactory',
        'Multisensory Neutral Visual, Tactile & Olfactory',
        'Multisensory Alcohol Visual, Tactile & Olfactory'
    ])
    stroop_tests = config.get('experiment.test_types.stroop', [
        'Stroop Multisensory Alcohol (Visual & Tactile)',
        'Stroop Multisensory Neutral (Visual & Tactile)',
        'Stroop Multisensory Alcohol (Visual & Olfactory)',
        'Stroop Multisensory Neutral (Visual & Olfactory)'
    ])
    return passive_tests, stroop_tests

# Creates the data directories for a subject and test, and clears any existing data.csv files
def create_data_dirs(subject_id, test_number):
    # Get data directory from configuration
    data_dir = config.get_absolute_path('paths.data_directory')
    base_dir = data_dir / f'subject_{subject_id}' / f'test_{test_number}'
    base_dir.mkdir(parents=True, exist_ok=True)
    
    passive_tests, stroop_tests = get_test_lists()
    selected_tests = passive_tests if test_number == '1' else stroop_tests
    for test in selected_tests:
        test_dir = base_dir / test
        test_dir.mkdir(parents=True, exist_ok=True)
        
        # Clear existing data.csv files
        csv_file = test_dir / 'data.csv'
        if csv_file.exists():
            csv_file.unlink()
    
    return str(base_dir)

# Initializes shared resources for multiprocessing (status dict and log queue)
def init_shared_resources():
    manager = Manager()
    shared_status = manager.dict()
    shared_status['lab_recorder_connected'] = False
    shared_status['eyetracker_connected'] = False
    shared_status['lsl_enabled'] = False
    shared_status['tactile_connected'] = False
    log_queue = Queue()
    return manager, shared_status, log_queue

# Launches the control window process (host)
def run_control_window_host(connection, shared_status, log_queue, base_dir, test_number, host):
    from eeg_stimulus_project.gui.control_window import ControlWindow
    app = QApplication(sys.argv)
    window = ControlWindow(connection, shared_status, log_queue, base_dir, test_number, host)
    window.show()
    sys.exit(app.exec_())

# Launches the main GUI process (client or local)
def run_main_gui_client(connection, shared_status, log_queue, base_dir, test_number, client, alcohol_folder=None, non_alcohol_folder=None, randomize_cues=None, seed=None):
    from eeg_stimulus_project.gui.main_gui import GUI
    app = QApplication(sys.argv)
    window = GUI(connection, shared_status, log_queue, base_dir, test_number, client, alcohol_folder, non_alcohol_folder, randomize_cues, seed)
    window.show()
    sys.exit(app.exec_())

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Subject Information")
        self.setFixedSize(1000, 700)  # Set a fixed size (width, height)
        # self.setMinimumSize(600, 480)  # Or use this for a minimum size

        # Center the window on the screen
        qr = self.frameGeometry()
        cp = QApplication.desktop().screen().rect().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        # Main widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(18)

        # --- Subject Section ---
        subject_group = QGroupBox("Subject Information")
        subject_layout = QVBoxLayout(subject_group)
        subject_layout.setSpacing(8)

        self.subject_id_label = QLabel("Subject ID:")
        self.subject_id_label.setFont(QFont("Segoe UI", 11))
        self.subject_id_input = QLineEdit()
        self.subject_id_input.setFont(QFont("Segoe UI", 11))
        self.subject_id_input.setPlaceholderText("Enter subject ID...")

        self.test_number_label = QLabel("Test Number (1 or 2):")
        self.test_number_label.setFont(QFont("Segoe UI", 11))
        self.test_number_input = QLineEdit()
        self.test_number_input.setFont(QFont("Segoe UI", 11))
        self.test_number_input.setPlaceholderText("1 or 2")

        subject_layout.addWidget(self.subject_id_label)
        subject_layout.addWidget(self.subject_id_input)
        subject_layout.addWidget(self.test_number_label)
        subject_layout.addWidget(self.test_number_input)

        # --- Host/Client Section ---
        host_group = QGroupBox("Experiment Mode")
        host_layout = QHBoxLayout(host_group)
        host_layout.setSpacing(12)

        self.start_as_host_button = QPushButton("Start as Host")
        self.start_as_host_button.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.start_as_host_button.setStyleSheet("background-color: #7E57C2; color: white; padding: 6px 18px; border-radius: 6px;")
        self.start_as_host_button.clicked.connect(lambda: self.start_experiment(client=False, host=True))

        self.start_button = QPushButton("Start Local")
        self.start_button.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.start_button.setStyleSheet("background-color: #26A69A; color: white; padding: 6px 18px; border-radius: 6px;")
        self.start_button.clicked.connect(lambda: self.start_experiment(client=False, host=False))

        host_layout.addWidget(self.start_as_host_button)
        host_layout.addWidget(self.start_button)

        # --- Client Section ---
        client_group = QGroupBox("Client Connection")
        client_layout = QHBoxLayout(client_group)
        client_layout.setSpacing(8)

        self.host_ip_label = QLabel("Host IP:")
        self.host_ip_label.setFont(QFont("Segoe UI", 11))
        self.host_ip_input = QLineEdit()
        self.host_ip_input.setFont(QFont("Segoe UI", 11))
        self.host_ip_input.setText("169.254.37.25")
        self.host_ip_input.setPlaceholderText("Enter host IP...")

        self.start_as_client_button = QPushButton("Start as Client")
        self.start_as_client_button.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.start_as_client_button.setStyleSheet("background-color: #42A5F5; color: white; padding: 6px 18px; border-radius: 6px;")
        self.start_as_client_button.clicked.connect(lambda: self.start_experiment(client=True, host=False))

        client_layout.addWidget(self.host_ip_label)
        client_layout.addWidget(self.host_ip_input)
        client_layout.addWidget(self.start_as_client_button)

        # --- Asset Import Section ---
        asset_group = QGroupBox("Import Custom Assets (Optional)")
        asset_layout = QVBoxLayout(asset_group)
        asset_layout.setSpacing(8)

        # Alcohol
        alcohol_row = QHBoxLayout()
        self.alcohol_folder_label = QLabel("Alcohol Images Folder:")
        self.alcohol_folder_label.setFont(QFont("Segoe UI", 10))
        self.alcohol_folder_input = QLineEdit()
        self.alcohol_folder_input.setFont(QFont("Segoe UI", 10))
        self.alcohol_folder_input.setPlaceholderText("Leave blank to use default")
        self.alcohol_folder_browse = QPushButton("Browse")
        self.alcohol_folder_browse.setFont(QFont("Segoe UI", 10))
        self.alcohol_folder_browse.clicked.connect(self.browse_alcohol_folder)
        alcohol_row.addWidget(self.alcohol_folder_label)
        alcohol_row.addWidget(self.alcohol_folder_input)
        alcohol_row.addWidget(self.alcohol_folder_browse)

        # Non-Alcohol
        non_alcohol_row = QHBoxLayout()
        self.non_alcohol_folder_label = QLabel("Non-Alcohol Images Folder:")
        self.non_alcohol_folder_label.setFont(QFont("Segoe UI", 10))
        self.non_alcohol_folder_input = QLineEdit()
        self.non_alcohol_folder_input.setFont(QFont("Segoe UI", 10))
        self.non_alcohol_folder_input.setPlaceholderText("Leave blank to use default")
        self.non_alcohol_folder_browse = QPushButton("Browse")
        self.non_alcohol_folder_browse.setFont(QFont("Segoe UI", 10))
        self.non_alcohol_folder_browse.clicked.connect(self.browse_non_alcohol_folder)
        non_alcohol_row.addWidget(self.non_alcohol_folder_label)
        non_alcohol_row.addWidget(self.non_alcohol_folder_input)
        non_alcohol_row.addWidget(self.non_alcohol_folder_browse)

        asset_layout.addLayout(alcohol_row)
        asset_layout.addLayout(non_alcohol_row)

        # Randomizer
        randomizer_row = QHBoxLayout()
        self.randomize_checkbox = QCheckBox("Randomize Alcohol/Non-Alcohol Cues")
        self.randomize_checkbox.setFont(QFont("Segoe UI", 10))
        self.seed_label = QLabel("Seed(1-10000):")
        self.seed_label.setFont(QFont("Segoe UI", 10))
        self.seed_input = QLineEdit()
        self.seed_input.setFont(QFont("Segoe UI", 10))
        self.seed_input.setPlaceholderText("Leave blank for random")
        randomizer_row.addWidget(self.randomize_checkbox)
        randomizer_row.addWidget(self.seed_label)
        randomizer_row.addWidget(self.seed_input)
        asset_layout.addLayout(randomizer_row)

        # --- Documentation Section ---
        documentation_group = QGroupBox("Documentation")
        documentation_layout = QVBoxLayout(documentation_group)
        documentation_layout.setSpacing(8)

        # Placeholder label for future documentation
        documentation_label = QLabel("Documentation and usage instructions will appear here in the future.")
        documentation_label.setFont(QFont("Segoe UI", 10))
        documentation_label.setWordWrap(True)
        documentation_layout.addWidget(documentation_label)

        # --- Add all groups to main layout ---
        main_layout.addWidget(subject_group)
        main_layout.addWidget(host_group)
        main_layout.addWidget(client_group)
        main_layout.addWidget(asset_group)
        main_layout.addWidget(documentation_group)  # <-- Add this line
        main_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Store processes and state
        self.gui_process = None
        self.control_process = None
        self.manager = None
        self.shared_status = None
        self.connection = None
        self.client_connected = False

    # Main logic for starting the experiment in host, client, or both/local mode
    def start_experiment(self, client=False, host=False):
        # Disable buttons to prevent double starts
        self.start_button.setEnabled(False)
        self.start_as_host_button.setEnabled(False)
        self.start_as_client_button.setEnabled(False)

        # Get folder paths for images
        alcohol_folder = self.alcohol_folder_input.text().strip()
        non_alcohol_folder = self.non_alcohol_folder_input.text().strip()

        # Get user input values
        subject_id = self.subject_id_input.text() if host or (not host and not client) else None
        test_number = self.test_number_input.text() if host or (not host and not client) else None
        host_ip = self.host_ip_input.text().strip() if client else None

        #Randomization settings
        randomize_cues = self.randomize_checkbox.isChecked()
        seed_text = self.seed_input.text().strip()
        seed = int(seed_text) if seed_text.isdigit() else seed_text if seed_text else None

        # Host or local mode: require subject info
        if host:
            if not subject_id or test_number not in ['1', '2']:
                QMessageBox.critical(self, "Error", "Please enter a valid Subject ID and Test Number (1 or 2).")
                self._reset_buttons()
                return
            threading.Thread(target=self.start_server, daemon=True).start()  # Start server in background thread
        # Client mode: require host IP and connect
        elif client:
            if not host_ip:
                QMessageBox.critical(self, "Error", "Please enter the Host IP for client mode.")
                self._reset_buttons()
                return
            if not self.connect_to_host(host_ip):
                logging.info("Could not connect to host. Check IP and network.")
                self._reset_buttons()
                return
            # Directory and shared resources for client (base_dir is None for client)
            base_dir = None
            self.manager, self.shared_status, log_queue = init_shared_resources()
            self.gui_process = Process(target=run_main_gui_client, args=(self.connection, self.shared_status, log_queue, base_dir, test_number, True)) # client=True
            self.gui_process.start()
        else:
            # Both: local experiment (host and client on same machine)
            if not subject_id or test_number not in ['1', '2']:
                logging.info("Please enter a valid Subject ID and Test Number (1 or 2).")
                self._reset_buttons()
                return
            base_dir = create_data_dirs(subject_id, test_number)
            self.manager, self.shared_status, log_queue = init_shared_resources()
            # Start control and GUI processes
            self.control_process = Process(target=run_control_window_host, args=(self.connection, self.shared_status, log_queue, base_dir, test_number, False)) # host=False
            self.gui_process = Process(
                target=run_main_gui_client,
                args=(self.connection, self.shared_status, log_queue, base_dir, test_number, False, alcohol_folder, non_alcohol_folder, randomize_cues, seed)
            ) # client=False
            self.control_process.start()
            self.gui_process.start()

    # Re-enable buttons after an error or experiment end
    def _reset_buttons(self):
        self.start_as_host_button.setEnabled(True)
        self.start_button.setEnabled(True)
        self.start_as_client_button.setEnabled(True)

    # Starts the server socket for host mode and waits for a client connection
    def start_server(self):
        HOST = '0.0.0.0'
        PORT = 9999
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.bind((HOST, PORT))
            server_socket.listen(1)
            logging.info(f"Host: Waiting for client on port {PORT}...")
            conn, addr = server_socket.accept()
            logging.info(f"Host: Connected by {addr}")
            self.connection = conn  # Save for later use
            self.client_connected = True

            # Start a thread to monitor client connection
            threading.Thread(target=self.monitor_client_connection, daemon=True).start()

            # Only create directories and processes after connection
            subject_id = self.subject_id_input.text()
            test_number = self.test_number_input.text()
            base_dir = create_data_dirs(subject_id, test_number)
            self.manager, self.shared_status, log_queue = init_shared_resources()

            # Start the control window process only after connection
            self.control_process = Process(
                target=run_control_window_host,
                args=(self.connection, self.shared_status, log_queue, base_dir, test_number, True)  # host=True
            )
            self.control_process.start()
        except Exception as e:
            logging.info(f"Host: Server error: {e}")

    # Connects to the host from the client
    def connect_to_host(self, host_ip):
        PORT = 9999
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host_ip, PORT))
            logging.info("Client: Connected to host.")
            self.connection = s  # Save for later use
            return True
        except Exception as e:
            logging.info(f"Client: Connection error: {e}")
            return False

    # Handles closing the main window and terminating child processes
    def closeEvent(self, event):
        if getattr(self, "client_connected", False):
            logging.info("Cannot close host while client is connected. Please close the client first.")
            event.ignore()
            return
        if self.gui_process is not None:
            self.gui_process.terminate()
            self.gui_process.join()
        if self.control_process is not None:
            self.control_process.terminate()
            self.control_process.join()
        event.accept()

    # Monitors the client connection in a background thread
    def monitor_client_connection(self):
        try:
            while True:
                data = self.connection.recv(1)
                if not data:
                    break
        except Exception:
            pass
        logging.info("Client disconnected.")
        self.client_connected = False

    def browse_alcohol_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Alcohol Images Folder")
        if folder:
            self.alcohol_folder_input.setText(folder)

    def browse_non_alcohol_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Non-Alcohol Images Folder")
        if folder:
            self.non_alcohol_folder_input.setText(folder)

    def randomize_cues(self):
        randomize_cues = self.randomize_checkbox.isChecked()
        seed_text = self.seed_input.text().strip()
        seed = int(seed_text) if seed_text.isdigit() else seed_text if seed_text else None

def main():
    """Main entry point for the EEG Stimulus Project."""
    # Create the application and main window, then run the application
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()


