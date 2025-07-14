# Multisensory Stimulus Presentation and Data Collection System

A portable, cross-platform software system for presenting and synchronizing multisensory stimuli (visual, tactile, olfactory) while collecting EEG, eye tracking, and behavioral data.

## Quick Start

### Installation
```bash
# Clone the repository
git clone https://github.com/SonnyS10/Multisensory-Stimulus-Presentation-and-Data-Collection-System.git
cd Multisensory-Stimulus-Presentation-and-Data-Collection-System

# Install dependencies
pip install -r requirements.txt

# Run the application
python -m eeg_stimulus_project.main.main
```

### For Windows Users
Double-click `eeg_stimulus_project/utils/run_eeg_stimulus.bat`

### For Linux/Mac Users
```bash
./eeg_stimulus_project/utils/run_eeg_stimulus.sh
```

## Key Features

✅ **Cross-Platform Compatibility**: Works on Windows, Linux, and macOS
✅ **Portable Configuration**: No hardcoded paths - works on any computer
✅ **Multi-modal Stimulus Presentation**: Visual, tactile, and olfactory stimuli
✅ **Real-time Data Collection**: EEG, eye tracking, and behavioral responses
✅ **Distributed Architecture**: Host/client setup for multi-computer experiments
✅ **Synchronization**: Lab Streaming Layer (LSL) for precise timing
✅ **Easy Setup**: Automated installation and configuration

## System Requirements

### Software Requirements
- Python 3.8 or higher
- PyQt5 for GUI
- PyLSL for data streaming
- Additional dependencies listed in `requirements.txt`

### Hardware Components (Optional)
- HTC VIVE Pro Eye VR headset
- EMOTIV EPOC Flex (32-channel EEG)
- Eyelink 1000 Plus eye tracker
- Custom odor delivery system
- Custom tactile presentation box
- Arduino-controlled viewing booth

## Project Structure

```
Multisensory-Stimulus-Presentation-and-Data-Collection-System/
├── eeg_stimulus_project/           # Main project package
│   ├── main/                       # Application entry point
│   │   └── main.py                 # Main GUI launcher
│   ├── config/                     # Configuration system
│   │   ├── settings.yaml           # Main configuration file
│   │   └── config_manager.py       # Configuration management
│   ├── gui/                        # User interface components
│   ├── stimulus/                   # Stimulus presentation modules
│   ├── data/                       # Data handling modules
│   ├── lsl/                        # Lab Streaming Layer integration
│   ├── utils/                      # Utility modules
│   └── assets/                     # Asset management
├── requirements.txt                # Python dependencies
├── setup.py                       # Package installation
├── INSTALLATION.md                # Detailed setup guide
├── DEVELOPER_DOCUMENTATION.md     # Developer documentation
└── README.md                      # This file
```

## Configuration

The system uses a centralized configuration file (`eeg_stimulus_project/config/settings.yaml`) that allows customization of:

- **File paths**: All paths are relative to the project root
- **Network settings**: Host/client communication and hardware connections
- **Hardware configuration**: EEG, eye tracker, and tactile system settings
- **Experiment parameters**: Test types, timing, and data collection settings
- **Platform-specific settings**: Windows, Linux, and macOS configurations

### Key Configuration Sections

```yaml
# File and directory paths (automatically relative to project root)
paths:
  data_directory: "eeg_stimulus_project/saved_data"
  assets_directory: "eeg_stimulus_project/assets"

# Network configuration
network:
  host_port: 9999
  tactile_system:
    host: "10.115.12.225"
    username: "your_username"
    password: "your_password"

# Hardware settings
hardware:
  eeg:
    device_type: "EMOTIV"
    sampling_rate: 256
  tactile:
    threshold: 500
```

## Multi-Computer Setup

### Host Computer
1. Run the application
2. Select "Host" mode
3. Configure firewall to allow port 9999
4. Share the IP address with client computers

### Client Computer
1. Run the application
2. Select "Client" mode
3. Enter the host computer's IP address
4. Connect and synchronize with the host

## Data Collection

The system collects and synchronizes:
- **EEG data**: Via EMOTIV Pro and LabRecorder
- **Eye tracking**: Via Eyelink or Pupil Labs
- **Behavioral responses**: User inputs and reaction times
- **Stimulus timing**: Precise event markers via LSL
- **Tactile feedback**: Force sensor data

All data is automatically saved to organized directories with timestamps and metadata.

## Hardware Integration

### EEG System (EMOTIV)
- Start LabRecorder before running the application
- Connect EEG device and ensure streaming
- Use "Connect LabRecorder" in the control window

### Eye Tracker (Eyelink/Pupil Labs)
- Calibrate according to manufacturer instructions
- Ensure LSL streams are available
- Use "Connect Eye Tracker" in the control window

### Tactile System
- Configure SSH access in `settings.yaml`
- Ensure remote Python environment is set up
- System connects automatically when needed

## Development

### Setting Up Development Environment
```bash
# Install in development mode
pip install -e .

# Run tests
python test_configuration.py

# Follow development guidelines
# See DEVELOPER_DOCUMENTATION.md for detailed information
```

### Key Development Guidelines
- Use the centralized configuration system
- Maintain cross-platform compatibility
- Follow the existing code structure
- Test on multiple platforms when possible

## Troubleshooting

### Common Issues
1. **Import errors**: Install dependencies with `pip install -r requirements.txt`
2. **Connection issues**: Check firewall settings and network connectivity
3. **Hardware issues**: Verify device connections and driver installations
4. **Path issues**: The system now uses relative paths automatically

### Getting Help
- Check `INSTALLATION.md` for detailed setup instructions
- Review `DEVELOPER_DOCUMENTATION.md` for technical details
- Check the project's GitHub issues
- View log files for debugging information

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

We welcome contributions! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Acknowledgments

- Research team for system requirements and testing
- Open source communities for the underlying technologies
- Hardware manufacturers for integration support

---

**Note**: This system has been refactored to be fully portable and cross-platform compatible. All hardcoded paths have been removed and replaced with a flexible configuration system.
