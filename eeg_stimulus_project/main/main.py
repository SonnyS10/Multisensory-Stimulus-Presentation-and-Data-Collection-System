import sys
sys.path.append('\\Users\\cpl4168\\Documents\\Paid Research\\Software-for-Paid-Research-')
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit
import os
from multiprocessing import Manager, Process, Queue
import socket
import threading
import logging
from logging.handlers import QueueListener

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

def get_test_lists():
    passive_tests = [
        'Unisensory Neutral Visual',
        'Unisensory Alcohol Visual',
        'Multisensory Neutral Visual & Olfactory',
        'Multisensory Alcohol Visual & Olfactory',
        'Multisensory Neutral Visual, Tactile & Olfactory',
        'Multisensory Alcohol Visual, Tactile & Olfactory'
    ]
    stroop_tests = [
        'Stroop Multisensory Alcohol (Visual & Tactile)',
        'Stroop Multisensory Neutral (Visual & Tactile)',
        'Stroop Multisensory Alcohol (Visual & Olfactory)',
        'Stroop Multisensory Neutral (Visual & Olfactory)'
    ]
    return passive_tests, stroop_tests

def create_data_dirs(subject_id, test_number):
    base_dir = os.path.join('eeg_stimulus_project', 'saved_data', f'subject_{subject_id}', f'test_{test_number}')
    os.makedirs(base_dir, exist_ok=True)
    passive_tests, stroop_tests = get_test_lists()
    selected_tests = passive_tests if test_number == '1' else stroop_tests
    for test in selected_tests:
        test_dir = os.path.join(base_dir, test)
        os.makedirs(test_dir, exist_ok=True)
        file_path = os.path.join(test_dir, 'data.csv')
        if os.path.exists(file_path):
            with open(file_path, 'w') as file:
                file.truncate(0)
    return base_dir

def init_shared_resources():
    manager = Manager()
    shared_status = manager.dict()
    shared_status['lab_recorder_connected'] = False
    shared_status['eyetracker_connected'] = False
    log_queue = Queue()
    return manager, shared_status, log_queue

def run_control_window_host(connection, shared_status, log_queue, base_dir, test_number, host):
    from eeg_stimulus_project.gui.control_window import ControlWindow
    app = QApplication(sys.argv)
    window = ControlWindow(connection, shared_status, log_queue, base_dir, test_number, host)
    window.show()
    sys.exit(app.exec_())

def run_main_gui_client(connection, shared_status, log_queue, base_dir, test_number, client):
    from eeg_stimulus_project.gui.main_gui import GUI
    app = QApplication(sys.argv)
    window = GUI(connection, shared_status, log_queue, base_dir, test_number, client)
    window.show()
    sys.exit(app.exec_())

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Subject Information")
        self.setGeometry(100, 100, 400, 300)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # --- Host Section ---
        self.subject_id_label = QLabel("Subject ID:", self)
        self.subject_id_input = QLineEdit(self)
        self.test_number_label = QLabel("Test Number (1 or 2):", self)
        self.test_number_input = QLineEdit(self)
        self.start_as_host_button = QPushButton("Start as Host", self)
        self.start_as_host_button.clicked.connect(lambda: self.start_experiment(client=False, host=True))

        layout.addWidget(self.subject_id_label)
        layout.addWidget(self.subject_id_input)
        layout.addWidget(self.test_number_label)
        layout.addWidget(self.test_number_input)
        layout.addWidget(self.start_as_host_button)

        # --- Client Section ---
        self.host_ip_label = QLabel("Host IP (for Client):", self)
        self.host_ip_input = QLineEdit(self)
        self.host_ip_input.setText("169.254.37.25")
        self.start_as_client_button = QPushButton("Start as Client", self)
        self.start_as_client_button.clicked.connect(lambda: self.start_experiment(client=True, host=False))

        layout.addWidget(self.host_ip_label)
        layout.addWidget(self.host_ip_input)
        layout.addWidget(self.start_as_client_button)

        # --- Optional: Both Section ---
        self.start_button = QPushButton("Start with No Host/Client", self)
        self.start_button.clicked.connect(lambda: self.start_experiment(client=False, host=False))
        layout.addWidget(self.start_button)

        # Processes and state
        self.gui_process = None
        self.control_process = None
        self.manager = None
        self.shared_status = None
        self.connection = None  # Store socket connection
        self.client_connected = False

    def start_experiment(self, client=False, host=False):
        self.start_button.setEnabled(False)
        self.start_as_host_button.setEnabled(False)
        self.start_as_client_button.setEnabled(False)

        # Only require subject_id and test_number for host or both
        subject_id = self.subject_id_input.text() if host or (not host and not client) else None
        test_number = self.test_number_input.text() if host or (not host and not client) else None

        # Only require host_ip for client
        host_ip = self.host_ip_input.text().strip() if client else None

        # Networking setup
        if host:
            if not subject_id or test_number not in ['1', '2']:
                logging.info("Please enter a valid Subject ID and Test Number (1 or 2).")
                self._reset_buttons()
                return
            threading.Thread(target=self.start_server, daemon=True).start()
        elif client:
            if not host_ip:
                logging.info("Please enter the Host IP for client mode.")
                self._reset_buttons()
                return
            if not self.connect_to_host(host_ip):
                logging.info("Could not connect to host. Check IP and network.")
                self._reset_buttons()
                return
            # Directory and shared resources for client
            base_dir = None
            self.manager, self.shared_status, log_queue = init_shared_resources()
            self.gui_process = Process(target=run_main_gui_client, args=(self.connection, self.shared_status, log_queue, base_dir, test_number, True)) # client=True
            self.gui_process.start()
        else:
            # Both: local experiment
            if not subject_id or test_number not in ['1', '2']:
                logging.info("Please enter a valid Subject ID and Test Number (1 or 2).")
                self._reset_buttons()
                return
            base_dir = create_data_dirs(subject_id, test_number)
            self.manager, self.shared_status, log_queue = init_shared_resources()
            # Your GUI log handler, e.g., QTextEditLogger, or just StreamHandler for console
            #gui_log_handler = logging.StreamHandler()  # Or your custom handler
            #listener = QueueListener(log_queue, gui_log_handler)
            #listener.start()
            self.control_process = Process(target=run_control_window_host, args=(self.connection, self.shared_status, log_queue, base_dir, test_number, False)) # host=False
            self.gui_process = Process(target=run_main_gui_client, args=(self.connection, self.shared_status, log_queue, base_dir, test_number, False)) # client=False
            self.control_process.start()
            self.gui_process.start()

    def _reset_buttons(self):
        self.start_as_host_button.setEnabled(True)
        self.start_button.setEnabled(True)
        self.start_as_client_button.setEnabled(True)

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

if __name__ == "__main__":
    # Create the application and main window, then run the application
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


