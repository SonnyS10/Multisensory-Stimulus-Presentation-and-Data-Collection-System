# EEG Stimulus Project - Developer Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Project Structure](#project-structure)
4. [Core Components](#core-components)
5. [Data Flow](#data-flow)
6. [Key Files and Modules](#key-files-and-modules)
7. [Configuration and Settings](#configuration-and-settings)
8. [Network Architecture](#network-architecture)
9. [Hardware Integration](#hardware-integration)
10. [Development Guidelines](#development-guidelines)
11. [Troubleshooting](#troubleshooting)
12. [Future Enhancements](#future-enhancements)

---

## Project Overview

The EEG Stimulus Project is a comprehensive multisensory research platform designed for synchronized presentation of visual, tactile, and olfactory stimuli while collecting EEG, eye tracking, and behavioral data. This system is built using Python with PyQt5 for the GUI framework and integrates with multiple hardware systems for data collection.

### Key Features
- **Multi-modal Stimulus Presentation**: Visual (VR/screen), tactile, and olfactory stimuli
- **Real-time Data Collection**: EEG, eye tracking, and behavioral responses
- **Distributed Architecture**: Host/client setup for multi-computer experiments
- **Synchronization**: Lab Streaming Layer (LSL) for precise timing
- **Experiment Management**: Automated trial sequencing and data saving
- **Hardware Integration**: Support for HTC VIVE Pro Eye, EMOTIV EEG, Eyelink eye tracker

### Target Users
- **Researchers**: Running multisensory experiments
- **Developers**: Maintaining and extending the system
- **Technicians**: Setting up and troubleshooting hardware

---

## System Architecture

The system follows a modular architecture with clear separation of concerns:

```
┌─────────────────────────────────────────┐
│           Main Application              │
│         (main/main.py)                  │
└─────────────────┬───────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
┌───────▼────────┐  ┌───────▼────────┐
│  Control Window │  │   Main GUI     │
│  (Host Mode)    │  │  (Experiment)  │
└───────┬────────┘  └───────┬────────┘
        │                   │
        └─────────┬─────────┘
                  │
    ┌─────────────▼─────────────┐
    │     Stimulus Modules      │
    │  Visual | Tactile | Olfac │
    └─────────────┬─────────────┘
                  │
    ┌─────────────▼─────────────┐
    │    Data Collection        │
    │  LSL | EEG | Eye Tracker  │
    └───────────────────────────┘
```

### Design Patterns
- **Multiprocessing**: Separate processes for GUI and control
- **Observer Pattern**: Status sharing between components
- **Factory Pattern**: Asset loading and management
- **Command Pattern**: Network communication protocol

---

## Project Structure

```
Software-for-Paid-Research-/
├── eeg_stimulus_project/           # Main project package
│   ├── main/                       # Application entry point
│   │   ├── main.py                 # Main GUI launcher
│   │   └── __init__.py
│   ├── gui/                        # User interface components
│   │   ├── main_gui.py             # Primary experiment interface
│   │   ├── control_window.py       # Host control interface
│   │   ├── sidebar.py              # Navigation sidebar
│   │   ├── main_frame.py           # Main content frame
│   │   ├── display_window.py       # Stimulus display window
│   │   └── __init__.py
│   ├── stimulus/                   # Stimulus presentation modules
│   │   ├── visual/                 # Visual stimulus handling
│   │   │   ├── base_visual.py      # Base visual class
│   │   │   ├── screen.py           # Screen display
│   │   │   ├── vr.py               # VR display
│   │   │   └── real_world.py       # Real-world display
│   │   ├── tactile_box_code/       # Tactile stimulus control
│   │   │   ├── tactile_setup.py    # Tactile hardware interface
│   │   │   └── received_data.txt   # Tactile data log
│   │   ├── turn_table_code/        # Rotational stimulus control
│   │   │   └── turntable_gui.py    # Turntable interface
│   │   ├── olfactory.py            # Olfactory stimulus (placeholder)
│   │   └── __init__.py
│   ├── data/                       # Data handling modules
│   │   ├── data_saving.py          # Data persistence
│   │   ├── eeg_graph_widget.py     # EEG visualization
│   │   └── __init__.py
│   ├── lsl/                        # Lab Streaming Layer integration
│   │   ├── stream_manager.py       # LSL stream management
│   │   ├── labels.py               # Event labeling
│   │   └── __init__.py
│   ├── utils/                      # Utility modules
│   │   ├── labrecorder.py          # EEG recording interface
│   │   ├── Pupil_Labs.py           # Eye tracking integration
│   │   ├── name_changer.py         # File naming utilities
│   │   ├── xdf_file_handler.py     # XDF file processing
│   │   ├── run_eeg_stimulus.bat    # Windows launcher
│   │   └── __init__.py
│   ├── assets/                     # Asset management
│   │   ├── asset_handler.py        # Asset loading logic
│   │   ├── Images/                 # Default image assets
│   │   └── __init__.py
│   ├── config/                     # Configuration files
│   │   └── settings.yaml           # Application settings
│   ├── sync/                       # Synchronization modules
│   │   ├── timestamp_manager.py    # Timing coordination
│   │   └── __init__.py
│   ├── tests/                      # Test modules
│   │   ├── test_gui.py             # GUI testing
│   │   ├── test_lsl.py             # LSL testing
│   │   └── __init__.py
│   └── saved_data/                 # Experiment data storage
├── Old_Code/                       # Legacy code (deprecated)
├── README.md                       # Basic project information
├── app.log                         # Application log file
├── computer_connection_test_*.py   # Network testing utilities
└── .git/                           # Git repository data
```

---

## Core Components

### 1. Application Entry Point (`main/main.py`)

**Purpose**: Primary application launcher and experiment coordinator

**Key Responsibilities**:
- Initialize GUI application
- Handle host/client mode selection
- Manage multiprocessing for distributed experiments
- Setup network connections
- Initialize shared resources

**Critical Code Sections**:
```python
# DO NOT MODIFY - Multiprocessing initialization (lines 60-68)
def init_shared_resources():
    manager = Manager()
    shared_status = manager.dict()
    shared_status['lab_recorder_connected'] = False
    shared_status['eyetracker_connected'] = False
    shared_status['lsl_enabled'] = False
    shared_status['tactile_connected'] = False
    log_queue = Queue()
    return manager, shared_status, log_queue

# DO NOT MODIFY - Process creation (lines 71-76)
def run_control_window_host(connection, shared_status, log_queue, base_dir, test_number, host):
    from eeg_stimulus_project.gui.control_window import ControlWindow
    app = QApplication(sys.argv)
    window = ControlWindow(connection, shared_status, log_queue, base_dir, test_number, host)
    window.show()
    sys.exit(app.exec_())

# DO NOT MODIFY - Network server setup (lines 311-340)
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
        self.connection = conn
        self.client_connected = True
        # Process creation continues...
    except Exception as e:
        logging.info(f"Host: Server error: {e}")

# MODIFY WITH CAUTION - Experiment startup logic (lines 245-300)
def start_experiment(self, client=False, host=False):
    # Button disabling and input validation
    # Process creation based on mode selection
    # Network connection handling
```

**Configuration Points**:
- Subject ID validation
- Test number selection (1 or 2)
- Host IP configuration
- Asset folder selection

### 2. Main GUI (`gui/main_gui.py`)

**Purpose**: Primary experiment interface for stimulus presentation

**Key Responsibilities**:
- Display experiment controls
- Manage stimulus presentation
- Handle user interactions
- Coordinate with hardware systems

**Critical Code Sections**:
```python
# DO NOT MODIFY - GUI initialization and layout (lines 21-100)
def __init__(self, connection, shared_status, log_queue, base_dir, test_number, client=False,
             alcohol_folder=None, non_alcohol_folder=None, randomize_cues=False, seed=None):
    super().__init__()
    self.shared_status = shared_status
    self.connection = connection
    self.client = client
    # GUI component initialization
    self.sidebar = Sidebar(self)
    self.main_frame = MainFrame(self)
    self.stacked_widget = self.main_frame.stacked_widget
    
# DO NOT MODIFY - Network communication listener (lines 268-294)
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
                    # Message handling continues...
            except Exception as e:
                logging.info(f"Listener error: {e}")
                break
    threading.Thread(target=listen, daemon=True).start()

# DO NOT MODIFY - Logging setup (lines 296-301)
def setup_logging(self, log_queue):
    queue_handler = QueueHandler(log_queue)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.handlers = []
    logger.addHandler(queue_handler)
    
# MODIFY WITH CAUTION - Test frame creation (lines 101-104)
def create_frame(self, title, is_stroop_test=False):
    return Frame(self, title, self.connection, is_stroop_test, self.shared_status, 
                 self.base_dir, self.test_number, self.client, self.log_queue)
```

**GUI Components**:
- Sidebar navigation
- Main content frame
- Status indicators
- Hardware connection panels

### 3. Control Window (`gui/control_window.py`)

**Purpose**: Host control interface for managing distributed experiments

**Key Responsibilities**:
- Monitor experiment status
- Control remote clients
- Manage data collection
- Display system logs

**Critical Code Sections**:
```python
# DO NOT MODIFY - Control window initialization (lines 48-100)
def __init__(self, connection, shared_status, log_queue, base_dir=None, test_number=None, host=False):
    super().__init__()
    self.shared_status = shared_status
    self.connection = connection
    self.base_dir = base_dir
    self.test_number = test_number
    self.label_stream = None
    self.labrecorder = None
    self.lab_recorder_connected = False
    self.eyetracker = None
    # GUI layout initialization continues...

# DO NOT MODIFY - Log queue monitoring (lines 263-273)
def listen_to_log_queue(self):
    def worker():
        while True:
            try:
                msg = self.log_queue.get(timeout=1)
                if msg:
                    self.write(msg)
            except:
                pass
    threading.Thread(target=worker, daemon=True).start()

# DO NOT MODIFY - Hardware connection methods (lines 319-359)
def start_labrecorder(self):
    def worker():
        try:
            self.labrecorder = LabRecorder()
            self.labrecorder.start_recording()
            self.shared_status['lab_recorder_connected'] = True
        except Exception as e:
            logging.info(f"LabRecorder error: {e}")
    threading.Thread(target=worker, daemon=True).start()

def connect_eyetracker(self):
    def worker():
        try:
            self.eyetracker = PupilLabs()
            self.eyetracker.connect()
            self.shared_status['eyetracker_connected'] = True
        except Exception as e:
            logging.info(f"Eyetracker error: {e}")
    threading.Thread(target=worker, daemon=True).start()

# MODIFY WITH CAUTION - Host command processing (lines 380+)
def host_command_listener(self):
    # Network command processing for distributed experiments
```

### 4. Stimulus Modules (`stimulus/`)

#### Visual Stimulus (`stimulus/visual/`)

**Purpose**: Handle all visual stimulus presentation

**Key Files**:
- `base_visual.py`: Abstract base class for visual stimuli
- `screen.py`: Traditional screen display
- `vr.py`: VR headset integration
- `real_world.py`: Real-world visual cues

**Critical Code Sections**:
```python
# Note: Visual stimulus modules are currently empty base files
# Implementation needed based on experiment requirements
```

#### Tactile Stimulus (`stimulus/tactile_box_code/`)

**Purpose**: Control tactile stimulation hardware via SSH connection

**Key Files**:
- `tactile_setup.py`: Hardware interface for tactile stimulation

**Critical Code Sections**:
```python
# DO NOT MODIFY - SSH connection setup (lines 24-54)
def start_remote_script(local_script_callback): 
    def task():
        global ssh_client, remote_channel
        try:
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(ssh_host, username=ssh_user, password=ssh_password)
            remote_command = f"{remote_venv_activate} && {remote_script}"
            remote_channel = ssh_client.get_transport().open_session()
            remote_channel.get_pty()
            remote_channel.exec_command(remote_command)
            # Data collection loop continues...
        except Exception as e:
            output_queue.put(f"[ERROR] Failed to start remote script: {e}\n")
    threading.Thread(target=task, daemon=True).start()

# DO NOT MODIFY - Connection termination (lines 55-64)
def stop_remote_script():
    global ssh_client, remote_channel
    if remote_channel:
        remote_channel.close()
    if ssh_client:
        ssh_client.close()

# MODIFY WITH CAUTION - Threshold and baseline settings (lines 153-159)
def set_threshold(self, value):
    # Tactile detection threshold configuration
    
def set_baseline(self):
    # Baseline calibration for tactile system
```

#### Olfactory Stimulus (`stimulus/olfactory.py`)

**Purpose**: Control olfactory stimulus delivery (currently placeholder)

**Development Note**: This module is currently empty and ready for implementation

### 5. Data Collection (`data/`)

**Purpose**: Handle all data collection and storage

**Key Files**:
- `data_saving.py`: Primary data persistence
- `eeg_graph_widget.py`: Real-time EEG visualization

**Critical Code Sections**:
```python
# DO NOT MODIFY - Data saving class initialization (lines 9-12)
class Save_Data():
    def __init__(self, base_dir, test_number):
        self.base_dir = base_dir
        self.test_number = test_number

# DO NOT MODIFY - Stroop test data saving (lines 15-36)
def save_data_stroop(self, current_test, user_inputs, elapsed_time, labrecorder=None):
    test_dir = os.path.join(self.base_dir, current_test)
    os.makedirs(test_dir, exist_ok=True)
    file_path = os.path.join(test_dir, 'data.csv')
    file_exists = os.path.isfile(file_path)
    if file_exists:
        print("File already exists. Deleting the old file.")
        os.remove(file_path)
    with open(file_path, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['User Inputs', 'Elapsed Time'])
        for input, time in zip(user_inputs, elapsed_time):
            writer.writerow([input, time])
    print("Data saved successfully!")

# MODIFY WITH CAUTION - Passive test data saving (lines 38-44)
def save_data_passive(self, current_test, labrecorder=None):
    test_dir = os.path.join(self.base_dir, current_test)
    os.makedirs(test_dir, exist_ok=True)
    print("Data saved successfully!")
```

### 6. LSL Integration (`lsl/`)

**Purpose**: Lab Streaming Layer integration for data synchronization

**Key Files**:
- `stream_manager.py`: LSL stream management
- `labels.py`: Event labeling system

**Critical Code Sections**:
```python
# DO NOT MODIFY - Stream initialization (lines 32-51)
@staticmethod
def init_lsl_stream():
    """
    MUST BE CALLED TO initialize streams, data, timestamp offset, and the collection thread.
    """
    # Variables to hold streams, data, and the collection thread
    LSL.streams = {}
    LSL.collected_data = {}
    for stream_type, enabled in config.SUPPORTED_STREAMS.items():
        if enabled:
            LSL.streams[stream_type] = None
            LSL.collected_data[stream_type] = []
    # Initialize all required streams
    for stream_type in LSL.streams.keys():
        LSL._find_and_initialize_stream(stream_type, checked=False)
    # Check if any streams were found
    if not any(LSL.streams.values()):
        print("No valid LSL streams found.")
        return False

# DO NOT MODIFY - Buffer clearing (lines 53-66)
@staticmethod
def clear_stream_buffers():
    """
    Clears the buffer of each LSL stream to ensure no old data is included in the new collection.
    """
    for stream_type, stream in LSL.streams.items():
        if stream:
            print(f"Clearing buffer for {stream_type} stream...")
            while True:
                sample, timestamp = stream.pull_sample(timeout=0.0)
                if not sample:
                    break
            print(f"{stream_type} stream buffer cleared.")

# MODIFY WITH CAUTION - Data collection control (lines 68-96)
@staticmethod
def start_collection():
    """Function to start data collection."""
    
@staticmethod
def stop_collection(path: str):
    """Function to stop data collection and save data."""

# Event labeling system (labels.py)
def push_label(self, label):
    """Push a label (string) to the LSL stream."""
    if self.outlet:
        self.outlet.push_sample([str(label)])
```

---

## Data Flow

### Experiment Initialization Flow
1. **Application Launch**: `main.py` starts the GUI
2. **Mode Selection**: User chooses host, client, or local mode
3. **Network Setup**: If distributed, establish host/client connection
4. **Hardware Initialization**: Connect to EEG, eye tracker, etc.
5. **Asset Loading**: Load stimulus materials
6. **Experiment Ready**: System prepared for data collection

### Data Collection Flow
1. **Stimulus Trigger**: Experiment begins stimulus presentation
2. **Event Markers**: LSL markers sent for synchronization
3. **Data Streams**: EEG, eye tracking, behavioral data collected
4. **Real-time Processing**: Data buffered and processed
5. **Storage**: Data saved to structured directories
6. **Synchronization**: All data streams time-aligned

### Network Communication Flow
1. **Host Setup**: Host opens listening socket
2. **Client Connection**: Client connects to host
3. **Status Updates**: Shared status dictionary updated
4. **Command Relay**: Host sends commands to client
5. **Data Aggregation**: Host collects data from all sources

---

## Key Files and Modules

### Critical Files (DO NOT MODIFY WITHOUT DEEP UNDERSTANDING)

#### `main/main.py`
- **Lines 60-68**: `init_shared_resources()` - Multiprocessing setup
- **Lines 71-76**: `run_control_window_host()` - Process creation
- **Lines 79-84**: `run_main_gui_client()` - GUI process launch
- **Lines 245-300**: `start_experiment()` - Experiment initialization
- **Lines 311-340**: `start_server()` - Network server setup
- **Lines 343-353**: `connect_to_host()` - Client connection

#### `gui/main_gui.py`
- **Lines 21-100**: `__init__()` - GUI initialization and layout
- **Lines 268-294**: `start_listener()` - Network communication
- **Lines 296-301**: `setup_logging()` - Logging configuration
- **Lines 101-104**: `create_frame()` - Test frame creation

#### `gui/control_window.py`
- **Lines 48-100**: `__init__()` - Control window initialization
- **Lines 263-273**: `listen_to_log_queue()` - Log monitoring
- **Lines 319-332**: `start_labrecorder()` - EEG recording setup
- **Lines 345-359**: `connect_eyetracker()` - Eye tracking setup

#### `lsl/stream_manager.py`
- **Lines 32-51**: `init_lsl_stream()` - Stream discovery
- **Lines 53-66**: `clear_stream_buffers()` - Buffer management
- **Lines 68-84**: `start_collection()` - Data collection start
- **Lines 119-139**: `_find_and_initialize_stream()` - Stream initialization

#### `data/data_saving.py`
- **Lines 15-36**: `save_data_stroop()` - Stroop test data saving
- **Lines 38-44**: `save_data_passive()` - Passive test data saving

#### `stimulus/tactile_box_code/tactile_setup.py`
- **Lines 24-54**: `start_remote_script()` - SSH connection setup
- **Lines 55-64**: `stop_remote_script()` - Connection cleanup

### Utility Files (SAFE TO MODIFY)

#### `assets/asset_handler.py`
- Image loading and randomization
- Custom asset integration
- Asset validation

#### `utils/name_changer.py`
- File naming conventions
- Data organization utilities

#### `config/settings.yaml`
- Application configuration
- Hardware settings
- Experiment parameters

### Test Files (SAFE TO MODIFY)

#### `tests/test_gui.py`
- GUI component testing
- User interaction simulation

#### `tests/test_lsl.py`
- LSL functionality testing
- Data stream validation

---

## Configuration and Settings

### Primary Configuration (`config/settings.yaml`)

**Current Status**: Basic configuration file (mostly empty)

**Recommended Structure**:
```yaml
# Hardware Settings
hardware:
  eeg:
    device_type: "EMOTIV"
    sampling_rate: 256
  eye_tracker:
    device_type: "Eyelink"
    calibration_points: 9
  tactile:
    ssh_host: "10.115.12.225"
    ssh_user: "benja"

# Experiment Settings
experiment:
  default_test_types: ["passive", "stroop"]
  stimulus_duration: 2000  # milliseconds
  inter_stimulus_interval: 1500  # milliseconds

# Network Settings
network:
  host_port: 9999
  timeout: 30

# Data Settings
data:
  base_directory: "saved_data"
  file_formats: ["csv", "xdf"]
```

### Hard-coded Configuration (CRITICAL SECTIONS)

#### Network Configuration
```python
# main/main.py - Lines 312-316
HOST = '0.0.0.0'  # DO NOT CHANGE
PORT = 9999       # CHANGE WITH CAUTION
```

#### Hardware Configuration
```python
# stimulus/tactile_box_code/tactile_setup.py - Lines 14-17
ssh_host = '10.115.12.225'      # HARDWARE DEPENDENT
ssh_user = 'benja'              # HARDWARE DEPENDENT
ssh_password = 'neuro'          # SECURITY SENSITIVE
```

#### Data Paths
```python
# utils/labrecorder.py - Line 27
xdf_path = os.path.join('C:\\Users\\srs1520\\Documents\\...')  # MODIFY FOR DEPLOYMENT
```

---

## Network Architecture

### Host/Client Communication Protocol

#### Connection Setup
1. **Host**: Opens socket on port 9999
2. **Client**: Connects to host IP
3. **Handshake**: Status exchange and validation
4. **Ready State**: Both systems prepared for experiment

#### Message Format
```python
{
    "type": "command|status|data",
    "payload": {
        "action": "start|stop|pause",
        "data": {},
        "timestamp": "2024-01-01T00:00:00Z"
    }
}
```

#### Status Synchronization
- `lab_recorder_connected`: EEG system status
- `eyetracker_connected`: Eye tracker status  
- `lsl_enabled`: LSL system status
- `tactile_connected`: Tactile system status

### Network Troubleshooting

#### Common Issues
1. **Connection Refused**: Check firewall settings
2. **Port in Use**: Verify port 9999 availability
3. **IP Mismatch**: Confirm correct host IP address
4. **Process Hanging**: Check for zombie processes

#### Debugging Steps
```python
# Add to main.py for network debugging
logging.basicConfig(level=logging.DEBUG)
```

---

## Hardware Integration

### EEG Integration (EMOTIV)

#### Connection Process
1. **LabRecorder**: Start external LabRecorder application
2. **Socket Connection**: Connect to port 22345
3. **Stream Discovery**: LSL finds EEG streams
4. **Data Collection**: Real-time EEG data acquisition

#### Configuration Points
- Sampling rate: 256 Hz (hardcoded in LSL)
- Channel count: 32 (EMOTIV EPOC Flex)
- Data format: XDF files via LabRecorder

### Eye Tracking Integration (Eyelink)

#### Connection Process
1. **Pupil Labs**: Initialize eye tracking software
2. **Calibration**: Run calibration sequence
3. **Stream Setup**: Establish LSL stream
4. **Data Sync**: Synchronize with EEG data

#### Configuration Points
- Calibration points: 9-point calibration
- Sampling rate: 1000 Hz
- Data format: Integrated with LSL

### Tactile System Integration

#### Connection Process
1. **SSH Connection**: Connect to tactile control computer
2. **Python Environment**: Activate remote virtual environment
3. **Script Execution**: Run tactile control script
4. **Data Relay**: Receive tactile feedback data

#### Configuration Points
- SSH host: 10.115.12.225 (hardware dependent)
- Remote script: `forcereadwithzero.py`
- Virtual environment: `~/Desktop/bin/activate`

### VR Integration (HTC VIVE Pro Eye)

#### Connection Process
1. **PTVR**: Perception Toolbox for Virtual Reality
2. **Headset Detection**: Verify HTC VIVE connection
3. **Eye Tracking**: Integrated eye tracking setup
4. **Display Setup**: VR stimulus presentation

#### Configuration Points
- Display resolution: Native HTC VIVE resolution
- Refresh rate: 90 Hz
- Eye tracking: Integrated with Eyelink system

---

## Development Guidelines

### Code Style and Standards

#### Python Style
- Follow PEP 8 guidelines
- Use type hints where appropriate
- Document complex functions with docstrings
- Maintain consistent indentation (4 spaces)

#### GUI Development
- Use PyQt5 design patterns
- Implement proper signal/slot connections
- Handle window lifecycle properly
- Ensure thread safety for GUI updates

#### Error Handling
```python
# Preferred error handling pattern
try:
    # Hardware operation
    result = hardware_operation()
except HardwareError as e:
    logging.error(f"Hardware error: {e}")
    # Graceful degradation
except Exception as e:
    logging.error(f"Unexpected error: {e}")
    # Emergency cleanup
```

### Adding New Features

#### New Stimulus Modality
1. Create new file in `stimulus/` directory
2. Inherit from appropriate base class
3. Implement required methods
4. Add to main GUI integration
5. Update configuration system

#### New Hardware Integration
1. Create utility class in `utils/`
2. Implement connection and data methods
3. Add LSL stream if needed
4. Update status sharing system
5. Add hardware monitoring

#### New Data Format
1. Update `data/data_saving.py`
2. Add format validation
3. Update file naming conventions
4. Test data integrity

### Testing Guidelines

#### Unit Testing
- Test individual components in isolation
- Mock hardware dependencies
- Verify data integrity
- Test error conditions

#### Integration Testing
- Test hardware connections
- Verify data flow
- Test network communication
- Validate experiment sequences

#### User Testing
- Test complete experiment workflows
- Verify GUI responsiveness
- Test error recovery
- Validate data output

---

## Troubleshooting

### Common Issues and Solutions

#### Application Won't Start
**Symptoms**: Application crashes on startup
**Causes**: Missing dependencies, hardware not connected
**Solutions**:
1. Check Python environment and dependencies
2. Verify hardware connections
3. Check log files for error messages
4. Test with minimal configuration

#### EEG Connection Issues
**Symptoms**: No EEG data, connection timeouts
**Causes**: LabRecorder not running, LSL streams not found
**Solutions**:
1. Start LabRecorder manually
2. Check LSL stream availability
3. Verify EEG hardware connection
4. Restart LSL system

#### Network Communication Problems
**Symptoms**: Host/client connection fails
**Causes**: Firewall blocking, incorrect IP, port in use
**Solutions**:
1. Check firewall settings
2. Verify IP address configuration
3. Test port availability
4. Check network connectivity

#### Data Saving Errors
**Symptoms**: Data not saved, file permission errors
**Causes**: Insufficient permissions, disk space, path issues
**Solutions**:
1. Check file permissions
2. Verify disk space
3. Test file path validity
4. Check directory structure

### Debug Mode

#### Enable Debug Logging
```python
# Add to main.py
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler()
    ]
)
```

#### Network Debug
```python
# Add network debugging
import socket
def test_connection(host, port):
    try:
        s = socket.create_connection((host, port), timeout=5)
        s.close()
        return True
    except:
        return False
```

#### Hardware Debug
```python
# Test hardware connections
def test_hardware():
    # Test EEG connection
    # Test eye tracker
    # Test tactile system
    # Report status
```

---

## Future Enhancements

### Planned Features

#### 1. Enhanced Configuration System
- Web-based configuration interface
- Real-time parameter adjustment
- Configuration validation
- Template system for common setups

#### 2. Advanced Data Analysis
- Real-time signal processing
- Automated artifact detection
- Statistical analysis tools
- Report generation

#### 3. Improved Hardware Support
- Additional EEG systems
- Multiple eye tracker support
- Enhanced tactile feedback
- Audio stimulus integration

#### 4. User Experience Improvements
- Drag-and-drop experiment design
- Visual experiment flow editor
- Automated hardware detection
- Simplified setup process

### Technical Debt

#### Code Quality Issues
1. **Hard-coded Paths**: Replace with configuration system
2. **Error Handling**: Improve error recovery mechanisms
3. **Documentation**: Add comprehensive docstrings
4. **Testing**: Increase test coverage

#### Architecture Improvements
1. **Modular Design**: Further separate concerns
2. **Plugin System**: Support for custom modules
3. **State Management**: Centralized state handling
4. **Event System**: Improved event handling

---

## GUI Screenshots Placeholders

### Main Application Window
*[Screenshot placeholder: Main launcher window showing subject information, experiment mode selection, and asset import options]*

### Control Window (Host Mode)
*[Screenshot placeholder: Host control interface showing connected clients, experiment status, and system monitoring]*

### Experiment Interface
*[Screenshot placeholder: Main experiment window showing stimulus controls, hardware status, and data collection indicators]*

### Hardware Status Panel
*[Screenshot placeholder: Hardware connection status showing EEG, eye tracker, and tactile system status]*

### Data Collection Interface
*[Screenshot placeholder: Real-time data display showing EEG signals, eye tracking data, and event markers]*

---

## Appendices

### A. File Dependencies

#### Critical Dependencies
- PyQt5: GUI framework
- pylsl: Lab Streaming Layer
- paramiko: SSH connections
- pandas: Data handling
- PIL: Image processing

#### Hardware Dependencies
- LabRecorder: EEG data collection
- Pupil Labs: Eye tracking
- PTVR: VR integration
- Arduino IDE: Turntable control

### B. Network Ports

#### Standard Ports
- 9999: Host/client communication
- 22345: LabRecorder control
- 22: SSH for tactile system

#### Firewall Configuration
- Allow inbound: 9999, 22345
- Allow outbound: 22, 443 (if needed)

### C. Directory Structure Standards

#### Data Organization
```
saved_data/
├── subject_001/
│   ├── test_1/
│   │   ├── Unisensory_Neutral_Visual/
│   │   │   ├── data.csv
│   │   │   └── eeg_data.xdf
│   │   └── ...
│   └── test_2/
│       └── ...
└── ...
```

#### Asset Organization
```
assets/
├── Images/
│   ├── Default/
│   │   ├── Beer.jpg
│   │   └── Stella.jpg
│   └── Personalized/
│       └── custom_images/
└── ...
```

---

**Document Version**: 1.0  
**Last Updated**: [Current Date]  
**Maintained By**: Development Team  
**Review Schedule**: Monthly

---

*This documentation serves as a comprehensive guide for developers working on the EEG Stimulus Project. For questions or clarifications, please contact the development team.*