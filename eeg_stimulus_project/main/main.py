"""
EEG Stimulus Project - Main Application Entry Point

This module serves as the primary entry point for the Multisensory Stimulus Presentation 
and Data Collection System. It handles application initialization, experiment mode selection,
and coordination between distributed system components.

Key Features:
- Host/Client architecture for distributed experiments
- Multiprocessing for GUI and control window separation
- Asset import and management
- Network communication setup
- Cross-platform compatibility

Author: Research Team
Last Modified: 2024
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path for proper module imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# PyQt5 imports for GUI components
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QMessageBox, QFileDialog, QGroupBox, QSizePolicy, 
    QSpacerItem, QCheckBox
)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt

# System and communication imports
from multiprocessing import Manager, Process, Queue
import socket
import threading
import logging
from logging.handlers import QueueListener

# Import configuration manager for centralized settings
from eeg_stimulus_project.config import config

# Import logging utilities for consistent logging across processes
from eeg_stimulus_project.utils.logging_utils import setup_main_process_logging

# Initialize logging system for the main process
setup_main_process_logging()

def get_test_lists():
    """
    Retrieves the lists of available test types from configuration.
    
    This function gets the predefined passive and stroop test types that can be
    used in experiments. These test types define different stimulus combinations
    for multisensory research.
    
    Returns:
        tuple: A tuple containing two lists:
            - passive_tests (list): Tests for passive viewing experiments (Test 1)
            - stroop_tests (list): Tests for stroop task experiments (Test 2)
    
    Note:
        Test types can be customized in the configuration file under
        experiment.test_types.passive and experiment.test_types.stroop
    """
    # Get test types from configuration with default fallbacks
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

def create_data_dirs(subject_id, test_number):
    """
    Creates the directory structure for storing experiment data.
    
    This function sets up organized directories for each subject and test number,
    creating subdirectories for each test type. It also clears any existing
    data.csv files to prevent data contamination between experiment runs.
    
    Args:
        subject_id (str): Unique identifier for the research subject
        test_number (str): Test number ('1' for passive, '2' for stroop)
    
    Returns:
        str: Absolute path to the created base directory for the subject/test
    
    Directory Structure Created:
        data_directory/
        └── subject_{subject_id}/
            └── test_{test_number}/
                ├── {test_type_1}/
                ├── {test_type_2}/
                └── ...
    
    Note:
        - Removes existing data.csv files to prevent data conflicts
        - Creates directories recursively if they don't exist
        - Uses configuration-based data directory paths
    """
    # Get data directory from configuration (supports cross-platform paths)
    data_dir = config.get_absolute_path('paths.data_directory')
    base_dir = data_dir / f'subject_{subject_id}' / f'test_{test_number}'
    base_dir.mkdir(parents=True, exist_ok=True)
    
    # Get the appropriate test list based on test number
    passive_tests, stroop_tests = get_test_lists()
    selected_tests = passive_tests if test_number == '1' else stroop_tests
    
    # Create subdirectories for each test type and clear existing data
    for test in selected_tests:
        test_dir = base_dir / test
        test_dir.mkdir(parents=True, exist_ok=True)
        
        # Clear existing data.csv files to prevent data contamination
        csv_file = test_dir / 'data.csv'
        if csv_file.exists():
            csv_file.unlink()
    
    return str(base_dir)

def init_shared_resources():
    """
    Initializes shared resources for multiprocessing communication.
    
    Sets up a multiprocessing Manager to create shared resources that can be
    accessed by multiple processes. This includes a shared status dictionary
    for hardware connection states and a log queue for centralized logging.
    
    Returns:
        tuple: A tuple containing:
            - manager (multiprocessing.Manager): Manager for shared objects
            - shared_status (dict): Dictionary tracking hardware connection status
            - log_queue (Queue): Queue for centralized logging across processes
    
    Shared Status Keys:
        - lab_recorder_connected (bool): EEG system connection status
        - eyetracker_connected (bool): Eye tracker connection status
        - lsl_enabled (bool): Lab Streaming Layer status
        - tactile_connected (bool): Tactile system connection status
    
    Note:
        This function is critical for distributed experiment coordination
        and should not be modified without understanding multiprocessing implications.
    """
    # Create multiprocessing manager for shared resources
    manager = Manager()
    
    # Initialize shared status dictionary with hardware connection states
    shared_status = manager.dict()
    shared_status['lab_recorder_connected'] = False
    shared_status['eyetracker_connected'] = False
    shared_status['lsl_enabled'] = False
    shared_status['tactile_connected'] = False
    
    # Create log queue for centralized logging across processes
    log_queue = Queue()
    
    return manager, shared_status, log_queue

def run_control_window_host(connection, shared_status, log_queue, base_dir, test_number, host, subject_id):
    """
    Launches the control window process for host mode operation.
    
    This function creates a separate process to run the control window, which
    manages experiment coordination, hardware connections, and data collection
    monitoring in host mode.
    
    Args:
        connection: Network connection object for client communication
        shared_status (dict): Shared dictionary for hardware status tracking
        log_queue (Queue): Queue for centralized logging
        base_dir (str): Base directory path for data storage
        test_number (str): Test number ('1' or '2')
        host (bool): Flag indicating if this is running in host mode
    
    Note:
        This function runs in a separate process and includes its own
        QApplication instance. It will not return until the window is closed.
        
    Process Safety:
        - Sets up child process logging
        - Imports modules within process to avoid pickling issues
        - Properly configures Qt application for subprocess
    """
    # Import modules within the process to avoid multiprocessing issues
    from eeg_stimulus_project.utils.logging_utils import setup_child_process_logging
    from eeg_stimulus_project.gui.control_window import ControlWindow
    
    # Setup logging for this child process
    setup_child_process_logging(log_queue)
    
    # Create Qt application for this process
    app = QApplication(sys.argv)
    
    # Create and show the control window
    window = ControlWindow(connection, shared_status, log_queue, base_dir, test_number, host, subject_id)
    window.show()
    
    # Run the application event loop (blocks until window closes)
    sys.exit(app.exec_())

def run_main_gui_client(connection, shared_status, log_queue, base_dir, test_number, client, alcohol_folder=None, non_alcohol_folder=None):
    """
    Launches the main GUI process for client or local mode operation.
    
    This function creates a separate process to run the main experiment GUI,
    which handles stimulus presentation, user interactions, and experiment
    flow management.
    
    Args:
        connection: Network connection object (None for local mode)
        shared_status (dict): Shared dictionary for hardware status tracking
        log_queue (Queue): Queue for centralized logging
        base_dir (str): Base directory path for data storage (None for client)
        test_number (str): Test number ('1' or '2')
        client (bool): Flag indicating if this is running in client mode
        alcohol_folder (str, optional): Path to custom alcohol images folder
        non_alcohol_folder (str, optional): Path to custom non-alcohol images folder
    
    Note:
        This function runs in a separate process and includes its own
        QApplication instance. The client parameter determines whether
        network logging is enabled.
        
    Asset Management:
        - alcohol_folder and non_alcohol_folder allow custom asset imports
        - If None, default assets from the project are used
        - Paths should be absolute for cross-platform compatibility
    
    Process Safety:
        - Sets up child process logging with optional network connection
        - Imports modules within process to avoid pickling issues
        - Properly configures Qt application for subprocess
    """
    # Import modules within the process to avoid multiprocessing issues
    from eeg_stimulus_project.utils.logging_utils import setup_child_process_logging
    from eeg_stimulus_project.gui.main_gui import GUI
    
    # Setup logging for this child process
    # If this is a client, pass the connection for network logging
    network_connection = connection if client else None
    setup_child_process_logging(log_queue, network_connection)
    
    # Create Qt application for this process
    app = QApplication(sys.argv)
    
    # Create and show the main GUI window
    window = GUI(connection, shared_status, log_queue, base_dir, test_number, client, alcohol_folder, non_alcohol_folder)
    window.show()
    
    # Run the application event loop (blocks until window closes)
    sys.exit(app.exec_())

class MainWindow(QMainWindow):
    """
    Main application window for the EEG Stimulus Project launcher.
    
    This class provides the primary user interface for configuring and launching
    experiments in different modes (host, client, or local). It handles:
    - Subject information input
    - Experiment mode selection
    - Network configuration for distributed experiments
    - Asset import for custom stimuli
    - Process management for multiprocessing architecture
    
    The window allows users to:
    1. Enter subject information (ID and test number)
    2. Choose between host, client, or developer modes
    3. Configure network settings for client connections
    4. Import custom image assets for experiments
    5. Launch appropriate processes based on selected mode
    
    Attributes:
        gui_process (Process): Process running the main GUI
        control_process (Process): Process running the control window
        manager (Manager): Multiprocessing manager for shared resources
        shared_status (dict): Shared status dictionary across processes
        connection: Network connection for client/host communication
        client_connected (bool): Flag tracking client connection status
    """
    
    def __init__(self):
        """
        Initialize the main launcher window with all UI components.
        
        Sets up the complete user interface including:
        - Subject information input fields
        - Mode selection buttons (host/client/developer)
        - Network configuration section
        - Asset import controls
        - Window properties and layout
        
        The window is designed with a fixed size and centered on screen
        for consistent user experience across platforms.
        """
        super().__init__()
        
        # Set window properties
        self.setWindowTitle(" Multisensory Stimulus Presentation and Data Collection System")
        self.setFixedSize(1000, 700)  # Fixed size for consistent layout
        
        # Center the window on the screen
        qr = self.frameGeometry()
        cp = QApplication.desktop().screen().rect().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        # Create main widget and layout with appropriate spacing
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(18)

        # --- Subject Information Section ---
        # This section collects essential information for data organization
        # Only required for host/data collection computers
        subject_group = QGroupBox("Subject Information: Only Fill this out if you are on the Data Collection Computer (Host)")
        subject_layout = QVBoxLayout(subject_group)
        subject_layout.setSpacing(8)

        # Subject ID input field
        self.subject_id_label = QLabel("Subject ID:")
        self.subject_id_label.setFont(QFont("Segoe UI", 11))
        self.subject_id_input = QLineEdit()
        self.subject_id_input.setFont(QFont("Segoe UI", 11))
        self.subject_id_input.setPlaceholderText("Enter subject ID...")

        # Test number selection (1 for passive viewing, 2 for stroop task)
        self.test_number_label = QLabel("Test Number: 1(Passive Viewing) or 2(Stroop Task)")
        self.test_number_label.setFont(QFont("Segoe UI", 11))
        self.test_number_input = QLineEdit()
        self.test_number_input.setFont(QFont("Segoe UI", 11))
        self.test_number_input.setPlaceholderText("1 or 2")

        # Add subject information widgets to layout
        subject_layout.addWidget(self.subject_id_label)
        subject_layout.addWidget(self.subject_id_input)
        subject_layout.addWidget(self.test_number_label)
        subject_layout.addWidget(self.test_number_input)

        # --- Experiment Mode Selection Section ---
        # Provides buttons for different operational modes
        host_group = QGroupBox("Experiment Mode")
        host_layout = QHBoxLayout(host_group)
        host_layout.setSpacing(12)

        # Host mode button - for data collection computers
        # Starts server and waits for client connections
        self.start_as_host_button = QPushButton("Start as Data Collection Computer (Host)")
        self.start_as_host_button.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.start_as_host_button.setStyleSheet("background-color: #7E57C2; color: white; padding: 6px 18px; border-radius: 6px;")
        self.start_as_host_button.clicked.connect(lambda: self.start_experiment(client=False, host=True))

        # Developer mode button - for local testing and development
        # Runs both host and client on same machine
        self.start_button = QPushButton("Developer Mode")
        self.start_button.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.start_button.setStyleSheet("background-color: #26A69A; color: white; padding: 6px 18px; border-radius: 6px;")
        self.start_button.clicked.connect(lambda: self.start_experiment(client=False, host=False))

        # Add mode selection buttons to layout
        host_layout.addWidget(self.start_as_host_button)
        host_layout.addWidget(self.start_button)

        # --- Client Mode Configuration Section ---
        # For computers that will present stimuli while connecting to a host
        client_group = QGroupBox("Experimenter Computer (Client)")
        client_layout = QHBoxLayout(client_group)
        client_layout.setSpacing(8)

        # Host IP address input for client connections
        self.host_ip_label = QLabel("Host IP:")
        self.host_ip_label.setFont(QFont("Segoe UI", 11))
        self.host_ip_input = QLineEdit()
        self.host_ip_input.setFont(QFont("Segoe UI", 11))
        self.host_ip_input.setText("169.254.37.25")  # Default IP address
        self.host_ip_input.setPlaceholderText("Enter host IP...")

        # Client mode startup button
        # Connects to specified host IP for distributed experiments
        self.start_as_client_button = QPushButton("Start Experimenter Computer (Client)")
        self.start_as_client_button.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.start_as_client_button.setStyleSheet("background-color: #42A5F5; color: white; padding: 6px 18px; border-radius: 6px;")
        self.start_as_client_button.clicked.connect(lambda: self.start_experiment(client=True, host=False))

        # Add client configuration widgets to layout
        client_layout.addWidget(self.host_ip_label)
        client_layout.addWidget(self.host_ip_input)
        client_layout.addWidget(self.start_as_client_button)

        # --- Custom Asset Import Section ---
        # Allows importing custom image folders for personalized experiments
        # Optional feature primarily used by client computers
        asset_group = QGroupBox("Import Custom Assets (Optional: For the Client Only)")
        asset_layout = QVBoxLayout(asset_group)
        asset_layout.setSpacing(8)

        # Alcohol images folder selection
        alcohol_row = QHBoxLayout()
        self.alcohol_folder_label = QLabel("Alcohol Images Folder:")
        self.alcohol_folder_label.setFont(QFont("Segoe UI", 10))
        self.alcohol_folder_input = QLineEdit()
        self.alcohol_folder_input.setFont(QFont("Segoe UI", 10))
        self.alcohol_folder_input.setPlaceholderText("Leave blank to use default")
        self.alcohol_folder_browse = QPushButton("Browse")
        self.alcohol_folder_browse.setFont(QFont("Segoe UI", 10))
        self.alcohol_folder_browse.clicked.connect(self.browse_alcohol_folder)
        
        # Add alcohol folder widgets to horizontal layout
        alcohol_row.addWidget(self.alcohol_folder_label)
        alcohol_row.addWidget(self.alcohol_folder_input)
        alcohol_row.addWidget(self.alcohol_folder_browse)

        # Non-alcohol images folder selection
        non_alcohol_row = QHBoxLayout()
        self.non_alcohol_folder_label = QLabel("Non-Alcohol Images Folder:")
        self.non_alcohol_folder_label.setFont(QFont("Segoe UI", 10))
        self.non_alcohol_folder_input = QLineEdit()
        self.non_alcohol_folder_input.setFont(QFont("Segoe UI", 10))
        self.non_alcohol_folder_input.setPlaceholderText("Leave blank to use default")
        self.non_alcohol_folder_browse = QPushButton("Browse")
        self.non_alcohol_folder_browse.setFont(QFont("Segoe UI", 10))
        self.non_alcohol_folder_browse.clicked.connect(self.browse_non_alcohol_folder)
        
        # Add non-alcohol folder widgets to horizontal layout
        non_alcohol_row.addWidget(self.non_alcohol_folder_label)
        non_alcohol_row.addWidget(self.non_alcohol_folder_input)
        non_alcohol_row.addWidget(self.non_alcohol_folder_browse)

        # Add both folder selection rows to asset layout
        asset_layout.addLayout(alcohol_row)
        asset_layout.addLayout(non_alcohol_row)

        # --- Documentation Section ---
        # Placeholder for future documentation integration
        documentation_group = QGroupBox("Documentation")
        documentation_layout = QVBoxLayout(documentation_group)
        documentation_layout.setSpacing(8)

        # Placeholder label for future documentation links or information
        documentation_label = QLabel("Documentation and usage instructions will appear here in the future.")
        documentation_label.setFont(QFont("Segoe UI", 10))
        documentation_label.setWordWrap(True)
        documentation_layout.addWidget(documentation_label)

        # --- Assemble Main Layout ---
        # Add all sections to the main vertical layout
        main_layout.addWidget(subject_group)
        main_layout.addWidget(host_group)
        main_layout.addWidget(client_group)
        main_layout.addWidget(asset_group)
        main_layout.addWidget(documentation_group)
        # Add expandable spacer to push content to top
        main_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # --- Initialize Process Management Variables ---
        # Store references to child processes and shared resources
        self.gui_process = None          # Process running the main GUI
        self.control_process = None      # Process running the control window
        self.manager = None              # Multiprocessing manager
        self.shared_status = None        # Shared status dictionary
        self.connection = None           # Network connection object
        self.client_connected = False    # Flag for client connection status

    def start_experiment(self, client=False, host=False):
        """
        Main logic for starting experiments in different modes.
        
        This method coordinates the startup process for different experiment modes:
        - Host mode: Starts server and waits for client connections
        - Client mode: Connects to host and starts experiment GUI
        - Developer mode: Runs both host and client on same machine
        
        Args:
            client (bool): True if starting in client mode
            host (bool): True if starting in host mode
            
        Process Flow:
        1. Disable buttons to prevent multiple starts
        2. Validate required input based on mode
        3. Initialize network connections if needed
        4. Create data directories (host/local mode only)
        5. Start appropriate processes based on mode
        
        Mode Behaviors:
        - Host: Starts server thread, waits for client, then starts control window
        - Client: Connects to host, starts GUI process only
        - Developer: Creates both control and GUI processes locally
        
        Note:
            This method handles the complex coordination between distributed
            processes and should be modified carefully to maintain proper
            process lifecycle management.
        """
        # Disable all mode buttons to prevent multiple simultaneous starts
        self.start_button.setEnabled(False)
        self.start_as_host_button.setEnabled(False)
        self.start_as_client_button.setEnabled(False)

        # Get asset folder paths (convert to absolute paths for consistency)
        alcohol_folder = os.path.abspath(self.alcohol_folder_input.text().strip())
        non_alcohol_folder = os.path.abspath(self.non_alcohol_folder_input.text().strip())

        # Get user input values (only required for host/local modes)
        subject_id = self.subject_id_input.text() if host or (not host and not client) else None
        test_number = self.test_number_input.text() if host or (not host and not client) else None
        host_ip = self.host_ip_input.text().strip() if client else None

        # HOST MODE: Set up server and wait for client connections
        if host:
            # Validate required subject information for data organization
            if not subject_id or test_number not in ['1', '2']:
                QMessageBox.critical(self, "Error", "Please enter a valid Subject ID and Test Number (1 or 2).")
                self._reset_buttons()
                return
            # Start server in background thread to avoid blocking UI
            threading.Thread(target=self.start_server, daemon=True).start()
            
        # CLIENT MODE: Connect to host and start experiment GUI
        elif client:
            # Validate host IP address is provided
            if not host_ip:
                QMessageBox.critical(self, "Error", "Please enter the Host IP for client mode.")
                self._reset_buttons()
                return
            # Attempt to connect to the specified host
            if not self.connect_to_host(host_ip):
                logging.info("Could not connect to host. Check IP and network.")
                self._reset_buttons()
                return
            # Initialize shared resources for client mode
            base_dir = None  # Client doesn't manage data directories
            self.manager, self.shared_status, log_queue = init_shared_resources()
            # Start GUI process for client mode
            self.gui_process = Process(target=run_main_gui_client, 
                                     args=(self.connection, self.shared_status, log_queue, 
                                           base_dir, test_number, True, alcohol_folder, non_alcohol_folder))
            self.gui_process.start()
            
        # DEVELOPER MODE: Run both host and client on same machine
        else:
            # Both: local experiment (host and client on same machine)
            self.local_mode = True
            if not subject_id or test_number not in ['1', '2']:
                logging.info("Please enter a valid Subject ID and Test Number (1 or 2).")
                self._reset_buttons()
                return
            # Create data directory structure for local experiment
            base_dir = create_data_dirs(subject_id, test_number)
            # Initialize shared resources for local multiprocessing
            self.manager, self.shared_status, log_queue = init_shared_resources()
            
            # Start both control window and GUI processes locally
            self.control_process = Process(target=run_control_window_host, 
                                         args=(self.connection, self.shared_status, log_queue, 
                                               base_dir, test_number, False, subject_id))  # host=False for local
            self.gui_process = Process(target=run_main_gui_client,
                                     args=(self.connection, self.shared_status, log_queue, 
                                           base_dir, test_number, False, alcohol_folder, non_alcohol_folder, self.local_mode) )  # client=False for local
            
            # Start both processes
            self.control_process.start()
            self.gui_process.start()

    def _reset_buttons(self):
        """
        Re-enable mode selection buttons after an error or experiment end.
        
        This method restores the UI to its initial state by enabling all
        mode selection buttons. Called when:
        - Input validation fails
        - Network connection fails
        - Experiment terminates
        - Error conditions occur
        
        Ensures users can restart experiments or try different modes
        after resolving issues.
        """
        self.start_as_host_button.setEnabled(True)
        self.start_button.setEnabled(True)
        self.start_as_client_button.setEnabled(True)

    def start_server(self):
        """
        Starts the server socket for host mode and waits for client connections.
        
        This method sets up a TCP server on port 9999 and waits for a client
        to connect. Once connected, it:
        1. Establishes the connection and stores it
        2. Starts monitoring the client connection
        3. Creates data directories based on subject information
        4. Initializes shared resources for multiprocessing
        5. Starts the control window process
        
        Network Configuration:
        - Host: 0.0.0.0 (listens on all interfaces)
        - Port: 9999 (default, can be configured)
        - Protocol: TCP
        
        Error Handling:
        - Logs connection errors
        - Handles socket binding failures
        - Manages client disconnection gracefully
        
        Note:
            This method runs in a background thread to avoid blocking the UI.
            The server will only accept one client connection at a time.
        """
        # Network configuration (these should eventually move to config file)
        HOST = '0.0.0.0'  # Listen on all available interfaces
        PORT = 9999       # Standard port for this application
        
        try:
            # Create and configure server socket
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.bind((HOST, PORT))
            server_socket.listen(1)  # Accept only one client connection
            
            logging.info(f"Host: Waiting for client on port {PORT}...")
            
            # Block until client connects (this is why we're in a thread)
            conn, addr = server_socket.accept()
            logging.info(f"Host: Connected by {addr}")
            
            # Store connection for communication with client
            self.connection = conn
            self.client_connected = True

            # Start monitoring client connection in background thread
            threading.Thread(target=self.monitor_client_connection, daemon=True).start()

            # Now that client is connected, set up experiment environment
            subject_id = self.subject_id_input.text()
            test_number = self.test_number_input.text()
            
            # Create data directory structure for this experiment
            base_dir = create_data_dirs(subject_id, test_number)
            
            # Initialize shared resources for multiprocessing
            self.manager, self.shared_status, log_queue = init_shared_resources()

            # Start the control window process (host manages data collection)
            self.control_process = Process(
                target=run_control_window_host,
                args=(self.connection, self.shared_status, log_queue, base_dir, test_number, True, subject_id)  # host=True
            )
            self.control_process.start()
            
        except Exception as e:
            logging.info(f"Host: Server error: {e}")

    def connect_to_host(self, host_ip):
        """
        Establishes client connection to the specified host.
        
        This method attempts to connect to a host computer running the server
        component of the experiment system. Used in client mode to establish
        communication for distributed experiments.
        
        Args:
            host_ip (str): IP address of the host computer
            
        Returns:
            bool: True if connection successful, False otherwise
            
        Connection Process:
        1. Create TCP socket
        2. Attempt connection to host_ip:9999
        3. Store connection object for later communication
        4. Log connection status
        
        Error Handling:
        - Network unreachable
        - Host not responding
        - Port blocked by firewall
        - Invalid IP address format
        
        Note:
            Uses the same port (9999) as the server for consistency.
            Connection object is stored in self.connection for later use.
        """
        PORT = 9999  # Must match the port used by server
        
        try:
            # Create client socket and attempt connection
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host_ip, PORT))
            
            logging.info("Client: Connected to host.")
            self.connection = s  # Store connection for later communication
            return True
            
        except Exception as e:
            logging.info(f"Client: Connection error: {e}")
            return False

    def closeEvent(self, event):
        """
        Handles application shutdown and process cleanup.
        
        This method is called when the user attempts to close the main window.
        It ensures proper cleanup of child processes and network connections
        to prevent orphaned processes or hanging connections.
        
        Args:
            event (QCloseEvent): The close event from Qt
            
        Cleanup Process:
        1. Check if client is connected (prevent host from closing prematurely)
        2. Terminate GUI process if running
        3. Terminate control process if running
        4. Wait for processes to finish (join)
        5. Accept or ignore the close event
        
        Safety Measures:
        - Prevents host from closing while client is connected
        - Ensures all child processes are properly terminated
        - Prevents zombie processes and resource leaks
        
        Note:
            Process termination is forceful but safe since processes
            are designed to handle termination gracefully.
        """
        # Prevent host from closing while client is still connected
        # This ensures proper experiment coordination
        if getattr(self, "client_connected", False):
            logging.info("Cannot close host while client is connected. Please close the client first.")
            event.ignore()  # Don't close the window
            return
        
        # Clean up GUI process if it exists
        if self.gui_process is not None:
            self.gui_process.terminate()  # Forcefully terminate
            self.gui_process.join()       # Wait for termination to complete
        
        # Clean up control process if it exists  
        if self.control_process is not None:
            self.control_process.terminate()  # Forcefully terminate
            self.control_process.join()       # Wait for termination to complete
        
        # Accept the close event (allow window to close)
        event.accept()

    def monitor_client_connection(self):
        """
        Monitors the client connection in a background thread.
        
        This method runs continuously to detect when a client disconnects
        from the host. It helps maintain accurate connection state and
        allows proper cleanup when clients disconnect unexpectedly.
        
        Monitoring Process:
        1. Continuously attempt to receive data from client
        2. If no data received, client has disconnected
        3. Update connection status flag
        4. Log disconnection event
        
        Thread Safety:
        - Runs in daemon thread (dies with main process)
        - Uses exception handling for clean disconnection detection
        - Updates shared state safely
        
        Note:
            This is a blocking operation which is why it runs in a
            separate thread. The recv(1) call will block until data
            is available or the connection is closed.
        """
        try:
            # Continuously monitor connection by attempting to receive data
            while True:
                data = self.connection.recv(1)  # Try to receive 1 byte
                if not data:  # No data means client disconnected
                    break
        except Exception:
            # Exception indicates connection was closed or network error
            pass
        
        # Update connection status and log disconnection
        logging.info("Client disconnected.")
        self.client_connected = False

    def browse_alcohol_folder(self):
        """
        Opens file dialog to select alcohol images folder.
        
        Allows users to browse and select a custom folder containing
        alcohol-related images for use in experiments. If selected,
        the path is populated in the alcohol folder input field.
        
        File Dialog Configuration:
        - Title: "Select Alcohol Images Folder"
        - Mode: Directory selection only
        - Returns: Absolute path to selected directory
        
        Note:
            Selected folder should contain image files (jpg, png, etc.)
            compatible with the experiment system.
        """
        folder = QFileDialog.getExistingDirectory(self, "Select Alcohol Images Folder")
        if folder:
            self.alcohol_folder_input.setText(folder)

    def browse_non_alcohol_folder(self):
        """
        Opens file dialog to select non-alcohol images folder.
        
        Allows users to browse and select a custom folder containing
        non-alcohol-related images for use in experiments. If selected,
        the path is populated in the non-alcohol folder input field.
        
        File Dialog Configuration:
        - Title: "Select Non-Alcohol Images Folder"
        - Mode: Directory selection only
        - Returns: Absolute path to selected directory
        
        Note:
            Selected folder should contain image files (jpg, png, etc.)
            compatible with the experiment system.
        """
        folder = QFileDialog.getExistingDirectory(self, "Select Non-Alcohol Images Folder")
        if folder:
            self.non_alcohol_folder_input.setText(folder)

def main():
    """
    Main entry point for the EEG Stimulus Project application.
    
    This function initializes the Qt application framework and creates
    the main launcher window. It serves as the entry point for all
    experiment modes and handles the complete application lifecycle.
    
    Application Flow:
    1. Create QApplication instance for Qt framework
    2. Create and configure MainWindow
    3. Display the window to user
    4. Enter Qt event loop (blocks until application exits)
    5. Exit with appropriate status code
    
    Usage:
        python -m eeg_stimulus_project.main.main
        
    or:
        python main.py
    
    Exit Codes:
        - 0: Normal application termination
        - Non-zero: Error or abnormal termination
    
    Note:
        This function will not return until the user closes the application
        or an unhandled exception occurs. All experiment coordination
        happens through the MainWindow interface.
    """
    # Create the Qt application instance (required for all GUI operations)
    app = QApplication(sys.argv)
    
    # Create and configure the main launcher window
    window = MainWindow()
    
    # Display the window to the user
    window.show()
    
    # Enter the Qt event loop and exit with appropriate code
    sys.exit(app.exec_())

# Standard Python entry point check
if __name__ == "__main__":
    main()


