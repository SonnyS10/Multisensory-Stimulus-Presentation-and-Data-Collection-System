# Installation and Setup Guide

## Prerequisites

### System Requirements
- Python 3.8 or higher
- Operating System: Windows 10+, Linux, or macOS
- Memory: 8GB RAM minimum, 16GB recommended
- Storage: 2GB free space

### Hardware Requirements (Optional)
- HTC VIVE Pro Eye VR headset (for VR experiments)
- EMOTIV EPOC Flex (32-channel EEG system)
- Eyelink 1000 Plus eye tracker
- Custom tactile presentation system
- Arduino-controlled hardware (for turntable control)

## Installation Steps

### 1. Clone the Repository
```bash
git clone https://github.com/SonnyS10/Multisensory-Stimulus-Presentation-and-Data-Collection-System.git
cd Multisensory-Stimulus-Presentation-and-Data-Collection-System
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

Or install the package:
```bash
pip install -e .
```

### 3. Configuration Setup

#### Basic Configuration
The system uses a configuration file located at `eeg_stimulus_project/config/settings.yaml`. This file contains all configurable settings for the system.

Key configuration sections:
- **paths**: File and directory paths (automatically set to relative paths)
- **network**: Network and hardware connection settings
- **hardware**: Hardware-specific settings (EEG, eye tracker, tactile system)
- **experiment**: Experiment parameters and test types

#### Hardware-Specific Configuration

##### EEG System (EMOTIV)
1. Install EMOTIV Pro software
2. Install LabRecorder from the Lab Streaming Layer (LSL) project
3. Update the configuration:
   ```yaml
   platform:
     windows:
       labrecorder_path: "C:\\Path\\To\\LabRecorder.exe"
   ```

##### Eye Tracker (Eyelink)
1. Install SR Research Eyelink software
2. Install Pupil Labs software if using Pupil Labs hardware
3. Configure network settings in `settings.yaml`

##### Tactile System
1. Set up SSH access to the tactile control computer
2. Update tactile system configuration:
   ```yaml
   network:
     tactile_system:
       host: "YOUR_TACTILE_SYSTEM_IP"
       username: "YOUR_USERNAME"
       password: "YOUR_PASSWORD"  # Consider using environment variables
   ```

### 4. Directory Structure Setup

The application will automatically create the following directories:
- `eeg_stimulus_project/saved_data/` - Experiment data storage
- `eeg_stimulus_project/assets/Images/` - Stimulus images
- Log files in the project root

### 5. Asset Setup

#### Default Images
Default stimulus images are included in `eeg_stimulus_project/assets/Images/`.

#### Custom Images
To add custom stimulus images:
1. Create folders for your image categories
2. Use the GUI to import custom image folders
3. The system supports common image formats (JPG, PNG, BMP, etc.)

## Running the Application

### Windows
1. Double-click `eeg_stimulus_project/utils/run_eeg_stimulus.bat`
2. Or run from command line:
   ```cmd
   cd /path/to/project
   python -m eeg_stimulus_project.main.main
   ```

### Linux/Mac
1. Run the shell script:
   ```bash
   ./eeg_stimulus_project/utils/run_eeg_stimulus.sh
   ```
2. Or run from command line:
   ```bash
   cd /path/to/project
   python3 -m eeg_stimulus_project.main.main
   ```

### Package Installation
If you installed the package with pip:
```bash
eeg-stimulus
```

## Network Setup (Multi-Computer Experiments)

### Host Computer Setup
1. Configure firewall to allow connections on port 9999
2. Run the application and select "Host" mode
3. Note the IP address displayed

### Client Computer Setup
1. Run the application and select "Client" mode
2. Enter the host computer's IP address
3. Ensure both computers are on the same network

## Hardware Integration

### EEG System Integration
1. Start LabRecorder before running the application
2. Ensure EEG device is connected and streaming
3. Use the "Connect LabRecorder" button in the control window

### Eye Tracker Integration
1. Calibrate the eye tracker according to manufacturer instructions
2. Ensure LSL streams are available
3. Use the "Connect Eye Tracker" button in the control window

### Tactile System Integration
1. Ensure SSH access to the tactile control computer
2. Verify the remote Python environment is set up
3. The system will automatically connect when needed

## Troubleshooting

### Common Issues

#### Import Errors
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version compatibility (3.8+)

#### Connection Issues
- Verify network connectivity between computers
- Check firewall settings (port 9999)
- Ensure LabRecorder is running and accessible

#### Hardware Issues
- Verify hardware connections and power
- Check device-specific software is running
- Review log files for error messages

#### Path Issues
- The system now uses relative paths automatically
- Check that the project structure is intact
- Verify write permissions for data directories

### Log Files
Check the following log files for debugging:
- `app.log` - Main application log
- Console output for real-time debugging

### Configuration Validation
The system will use default values if configuration files are missing or invalid.

## Environment Variables (Optional)

For enhanced security, you can use environment variables for sensitive information:

```bash
# Windows
set TACTILE_PASSWORD=your_password

# Linux/Mac
export TACTILE_PASSWORD=your_password
```

Then update the configuration to use environment variables:
```yaml
network:
  tactile_system:
    password: "${TACTILE_PASSWORD}"
```

## Development Setup

### For Developers
1. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

2. Run tests:
   ```bash
   python -m pytest tests/
   ```

3. Follow the development guidelines in `DEVELOPER_DOCUMENTATION.md`

## Support

For issues and support:
1. Check the troubleshooting section above
2. Review the developer documentation
3. Check the project's GitHub issues
4. Contact the development team

## License

This project is licensed under the MIT License. See the LICENSE file for details.