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
# DO NOT MODIFY - Core experiment setup
def start_experiment(self, client=False, host=False):
    # Process creation and management logic
    
# DO NOT MODIFY - Network initialization
def start_server(self):
    # Server socket setup for host mode
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
# DO NOT MODIFY - Hardware initialization
def setup_hardware_connections(self):
    # EEG, eye tracker, and other hardware setup
    
# MODIFY WITH CAUTION - Experiment flow
def run_experiment_sequence(self):
    # Main experiment execution logic
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
# DO NOT MODIFY - Network communication
def handle_client_messages(self):
    # Client message processing
    
# MODIFY WITH CAUTION - Experiment control
def start_experiment_on_client(self):
    # Remote experiment initiation
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
# DO NOT MODIFY - Display initialization
def initialize_display(self):
    # Display setup and calibration
    
# MODIFY WITH CAUTION - Stimulus timing
def present_stimulus(self, stimulus_type, duration):
    # Stimulus presentation logic
```

#### Tactile Stimulus (`stimulus/tactile_box_code/`)

**Purpose**: Control tactile stimulation hardware

**Key Files**:
- `tactile_setup.py`: Hardware interface for tactile stimulation

**Critical Code Sections**:
```python
# DO NOT MODIFY - Hardware communication
def connect_tactile_hardware(self):
    # SSH connection to tactile control system
    
# MODIFY WITH CAUTION - Stimulation parameters
def deliver_tactile_stimulus(self, intensity, duration):
    # Tactile stimulus delivery
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
# DO NOT MODIFY - Data integrity
def save_experiment_data(self, data, metadata):
    # Ensures data consistency and backup
    
# MODIFY WITH CAUTION - File paths
def create_data_directories(self, subject_id, test_number):
    # Directory structure creation
```

### 6. LSL Integration (`lsl/`)

**Purpose**: Lab Streaming Layer integration for data synchronization

**Key Files**:
- `stream_manager.py`: LSL stream management
- `labels.py`: Event labeling system

**Critical Code Sections**:
```python
# DO NOT MODIFY - Stream initialization
def init_lsl_stream(self):
    # LSL stream discovery and setup
    
# MODIFY WITH CAUTION - Event timing
def send_event_marker(self, event_type, timestamp):
    # Event marker transmission
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
- **Lines 69-84**: Process creation and management
- **Lines 310-342**: Server socket setup
- **Lines 360-380**: Process cleanup and termination

#### `gui/main_gui.py`
- **Lines 33-50**: Connection and logging setup
- **Lines 100-150**: Hardware initialization
- **Lines 200-250**: Experiment sequence control

#### `lsl/stream_manager.py`
- **Lines 32-50**: LSL stream discovery
- **Lines 80-120**: Data collection threading
- **Lines 140-160**: Stream synchronization

#### `data/data_saving.py`
- **Lines 15-45**: Data integrity and CSV writing
- **Lines 25-35**: File path construction

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