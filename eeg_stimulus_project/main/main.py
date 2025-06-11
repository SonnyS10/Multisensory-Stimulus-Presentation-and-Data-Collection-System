import sys
sys.path.append('\\Users\\cpl4168\\Documents\\Paid Research\\Software-for-Paid-Research-')
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit
import os
from multiprocessing import Manager, Process
import socket
import threading

class Tee(object):
    def __init__(self, *streams):
        # streams can be sys.stdout, ControlWindow, or log_queue
        self.streams = streams

    def write(self, data):
        for s in self.streams:
            if hasattr(s, 'put'):

                s.put(data)
            elif hasattr(s, 'write'):
                s.write(data)
                s.flush()

    def flush(self):
        for s in self.streams:
            if hasattr(s, 'flush'):
                s.flush()

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
                print("Please enter a valid Subject ID and Test Number (1 or 2).")
                self.start_as_host_button.setEnabled(True)
                self.start_button.setEnabled(True)
                self.start_as_client_button.setEnabled(True)
                return
            threading.Thread(target=self.start_server, daemon=True).start()
        elif client:
            if not host_ip:
                print("Please enter the Host IP for client mode.")
                self.start_as_client_button.setEnabled(True)
                self.start_button.setEnabled(True)
                self.start_as_host_button.setEnabled(True)
                return
            if not self.connect_to_host(host_ip):
                print("Could not connect to host. Check IP and network.")
                self.start_as_client_button.setEnabled(True)
                self.start_button.setEnabled(True)
                self.start_as_host_button.setEnabled(True)
                return

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
            'Stroop Multisensory Alcohol (Visual & Tactile)',
            'Stroop Multisensory Neutral (Visual & Tactile)',
            'Stroop Multisensory Alcohol (Visual & Olfactory)',
            'Stroop Multisensory Neutral (Visual & Olfactory)'
        ]
        # Select the appropriate tests based on the test number
        # IN THE FUTURE, WE SHOULD MAKE THIS DAY NUMBER INSTEAD OF TEST NUMBER 
        # AND WHICHEVER TESTS ARE DONE ON THAT DAY GET RECORDED INTO THEIR RESPECTIVE FOLDERS
        # For now, we will just use test number
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
        # Create the Manager and shared_status dict
        from multiprocessing import Queue
        log_queue = Queue()
        self.manager = Manager()
        self.shared_status = self.manager.dict()
        self.shared_status['lab_recorder_connected'] = False
        self.shared_status['eyetracker_connected'] = False
        if not client and not host:
            # Run both
            self.control_process = Process(target=run_control_window_host, args=(self.connection, self.shared_status, log_queue, base_dir, test_number))
            self.gui_process = Process(target=run_main_gui_client, args=(self.connection, self.shared_status, log_queue, base_dir, test_number))
            self.control_process.start()
            self.gui_process.start()
        #elif host:
        #    # Only control panel
        #    self.control_process = Process(target=run_control_window_host, args=(self.connection, self.shared_status, log_queue, base_dir, test_number))
        #    self.control_process.start()
        elif client:
            # Only main GUI
            self.gui_process = Process(target=run_main_gui_client, args=(self.connection, self.shared_status, log_queue, base_dir, test_number))
            self.gui_process.start()

    def start_server(self):
        HOST = '0.0.0.0'
        PORT = 9999
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.bind((HOST, PORT))
            server_socket.listen(1)
            print(f"Host: Waiting for client on port {PORT}...")
            conn, addr = server_socket.accept()
            print(f"Host: Connected by {addr}")
            self.connection = conn  # Save for later use

            # Only create directories and processes after connection
            subject_id = self.subject_id_input.text()
            test_number = self.test_number_input.text()
            base_dir = os.path.join('eeg_stimulus_project', 'saved_data', f'subject_{subject_id}', f'test_{test_number}')
            os.makedirs(base_dir, exist_ok=True)

            from multiprocessing import Queue
            log_queue = Queue()

            self.manager = Manager()
            self.shared_status = self.manager.dict()
            self.shared_status['lab_recorder_connected'] = False
            self.shared_status['eyetracker_connected'] = False

            # Start the control window process only after connection
            self.control_process = Process(
                target=run_control_window_host,
                args=(conn, self.shared_status, log_queue, base_dir, test_number)
            )
            self.control_process.start()
        except Exception as e:
            print(f"Host: Server error: {e}")

    def connect_to_host(self, host_ip):
        PORT = 9999
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host_ip, PORT))
            print("Client: Connected to host.")
            self.connection = s  # Save for later use
            return True
        except Exception as e:
            print(f"Client: Connection error: {e}")
            return False

    def closeEvent(self, event):
        if self.gui_process is not None:
            self.gui_process.terminate()
            self.gui_process.join()
        if self.control_process is not None:
            self.control_process.terminate()
            self.control_process.join()
        event.accept()

def run_control_window(shared_status, log_queue, base_dir, test_number):
    from eeg_stimulus_project.gui.control_window import ControlWindow
    app = QApplication(sys.argv)
    window = ControlWindow(shared_status, log_queue, base_dir, test_number)
    window.show()
    sys.exit(app.exec_())

def run_main_gui(shared_status, log_queue, base_dir, test_number):
    from eeg_stimulus_project.gui.main_gui import GUI
    sys.stdout = Tee(sys.stdout, log_queue)
    app = QApplication(sys.argv)
    window = GUI(shared_status, base_dir, test_number)  # If you want to use log_queue in GUI, add it to the constructor
    window.show()
    sys.exit(app.exec_())

def run_control_window_host(connection, shared_status, log_queue, base_dir, test_number):
    from eeg_stimulus_project.gui.control_window import ControlWindow
    app = QApplication(sys.argv)
    window = ControlWindow(connection, shared_status, log_queue, base_dir, test_number)
    window.show()
    sys.exit(app.exec_())

def run_main_gui_client(connection, shared_status, log_queue, base_dir, test_number):
    from eeg_stimulus_project.gui.main_gui import GUI
    sys.stdout = Tee(sys.stdout, log_queue)
    app = QApplication(sys.argv)
    window = GUI(connection, shared_status, base_dir, test_number)  # If you want to use log_queue in GUI, add it to the constructor
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    # Create the application and main window, then run the application
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


