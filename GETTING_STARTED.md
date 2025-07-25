# Getting Started Guide
## Multisensory Stimulus Presentation and Data Collection System

This guide will walk you through setting up and running your first experiment with the Multisensory Stimulus Presentation and Data Collection System, starting from just a GitHub repository link.

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Installation](#installation)
3. [First-Time Setup](#first-time-setup)
4. [Running Your First Test](#running-your-first-test)
5. [Basic Operation](#basic-operation)
6. [Troubleshooting](#troubleshooting)
7. [Next Steps](#next-steps)

---

## System Requirements

### Minimum Requirements
- **Operating System**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 18.04+)
- **Python**: Version 3.8 or higher
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB free space for software and initial data
- **Network**: Internet connection for initial setup

### Recommended Hardware (Optional)
- **EEG System**: EMOTIV EPOC Flex (32-channel)
- **Eye Tracker**: Eyelink 1000 Plus or Pupil Labs
- **VR Headset**: HTC VIVE Pro Eye
- **Custom Hardware**: Tactile stimulation system, olfactory delivery system

### Software Dependencies
The following will be installed automatically:
- PyQt5 (GUI framework)
- NumPy, Pandas (data handling)
- Matplotlib (visualization)
- PyLSL (Lab Streaming Layer)
- Paramiko (SSH connectivity)
- Additional dependencies (see requirements.txt)

---

## Installation

### Step 1: Install Python
If you don't have Python installed:

**Windows:**
1. Download Python from [python.org](https://www.python.org/downloads/)
2. **Important**: Check "Add Python to PATH" during installation
3. Verify installation by opening Command Prompt and typing: `python --version`

**macOS:**
```bash
# Using Homebrew (recommended)
brew install python

# Or download from python.org
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

### Step 2: Clone the Repository
Open a terminal/command prompt and run:

```bash
# Clone the repository
git clone https://github.com/SonnyS10/Multisensory-Stimulus-Presentation-and-Data-Collection-System.git

# Navigate to the project directory
cd Multisensory-Stimulus-Presentation-and-Data-Collection-System
```

### Step 3: Create a Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### Step 4: Install Dependencies
```bash
# Install all required packages
pip install -r requirements.txt
```

### Step 5: Verify Installation
```bash
# Test that the main module can be imported
python -c "import eeg_stimulus_project; print('Installation successful!')"
```

---

## First-Time Setup

### 1. Configuration
The system uses a configuration file for settings. The default configuration should work for basic testing:

```bash
# View the configuration file
cat eeg_stimulus_project/config/settings.yaml
```

For now, the default settings are sufficient. Advanced configuration is covered in the [Data Collection Host Guide](DATA_COLLECTION_HOST_GUIDE.md).

### 2. Test Data Directory
The system will automatically create data directories when you run experiments. Default location:
- **Windows**: `eeg_stimulus_project/saved_data/`
- **macOS/Linux**: `eeg_stimulus_project/saved_data/`

### 3. Default Assets
The system includes default images for testing. Custom assets can be imported later through the GUI.

---

## Running Your First Test

### Quick Start (Developer Mode)
The easiest way to test the system is using Developer Mode, which runs everything on one computer:

#### 1. **Launch the Application**

There are three main ways to launch the application:

**a. Using the Terminal/Command Prompt**
1. Open your terminal or command prompt
2. Navigate to the project directory:
   ```bash
   cd Multisensory-Stimulus-Presentation-and-Data-Collection-System
   ```
3. Activate your virtual environment (if using one):
   ```bash
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```
4. Run the application:
   ```bash
   python -m eeg_stimulus_project.main.main
   ```

**b. Using the .bat File (Windows Only)**
1. Navigate to the project directory in File Explorer
2. Go to the `eeg_stimulus_project/utils/` folder
3. Double-click on `run_eeg_stimulus.bat`
4. The batch file will:
   - Automatically detect your Python installation (system or conda)
   - Install any missing dependencies
   - Launch the application
5. Follow the on-screen prompts to select your Python environment if multiple are available

**c. Creating a Desktop Shortcut with Custom Brain Icon**
1. **Create the shortcut**:
   - Right-click on your desktop and select "New" → "Shortcut"
   - Browse to your project directory and select `eeg_stimulus_project/utils/run_eeg_stimulus.bat`
   - Click "Next" and give it a name like "EEG Stimulus Application"
   - Click "Finish"

2. **Set the custom brain icon**:
   - Right-click on the newly created shortcut and select "Properties"
   - Click on the "Change Icon..." button
   - Click "Browse..." and navigate to `eeg_stimulus_project/utils/Brain_icon.ico`
   - Select the brain icon and click "OK"
   - Click "OK" again to apply the changes

3. **Launch the application**:
   - Double-click the desktop shortcut to start the application
   - The custom brain icon will be visible both on the desktop and in the taskbar

#### 2. **Fill in Subject Information**:
   - Subject ID: Enter a test ID (e.g., "test001")
   - Test Number: Enter "1" for passive viewing test

#### 3. **Start Developer Mode**:
   - Click the green "Developer Mode" button
   - Two windows will open:
     - **Control Window**: For managing the experiment
     - **Experiment Window**: For running the actual experiment

#### 4. **Navigate to a Test**:
   - In the Experiment Window, use the sidebar to select a test
   - Try "Unisensory Neutral Visual" first

#### 5. **Run a Simple Test**:
   - Check the "Start Display" checkbox in the test frame
   - A stimulus presentation window will open
   - Click through the experiment to see how it works

### Understanding the Interface

**Main Launcher Window:**
- **Subject Information**: Required for data organization
- **Experiment Mode**: Choose how to run the system
- **Custom Assets**: Optional image folders for personalized experiments

**Control Window (Host):**
- Monitor experiment status
- Connect to hardware systems
- View system logs
- Control recording systems

**Experiment Window:**
- Navigate between different test conditions
- Control stimulus presentation
- Monitor experiment progress
- Access instructions and utilities

---

## Basic Operation

### Experiment Types
The system supports two main experiment types:

**Test 1 - Passive Viewing Experiments:**
- Unisensory Neutral Visual
- Unisensory Alcohol Visual
- Multisensory Neutral Visual & Olfactory
- Multisensory Alcohol Visual & Olfactory
- Multisensory Neutral Visual, Tactile & Olfactory
- Multisensory Alcohol Visual, Tactile & Olfactory

**Test 2 - Stroop Task Experiments:**
- Stroop Multisensory Alcohol (Visual & Tactile)
- Stroop Multisensory Neutral (Visual & Tactile)
- Stroop Multisensory Alcohol (Visual & Olfactory)
- Stroop Multisensory Neutral (Visual & Olfactory)

### Navigation
- **Sidebar**: Click test names to switch between conditions
- **Instructions**: Toggle experiment instructions on/off
- **Stimulus Order**: Configure stimulus presentation sequences
- **Latency Checker**: Test system responsiveness (for distributed setups)

### Data Collection
- Data is automatically saved in organized directories
- Each subject gets a unique folder
- Each test type gets its own subdirectory
- Behavioral data is saved as CSV files
- EEG and other physiological data is coordinated via LSL

---

## Troubleshooting

### Common Issues

**1. "Module not found" errors:**
```bash
# Make sure you're in the right directory
pwd  # Should show the project root

# Reinstall dependencies
pip install -r requirements.txt
```

**2. "Permission denied" errors:**
```bash
# On macOS/Linux, you might need:
chmod +x eeg_stimulus_project/utils/run_eeg_stimulus.sh
```

**3. PyQt5 display issues:**
```bash
# On Linux, you might need:
sudo apt install python3-pyqt5
```

**4. LSL library not found:**
```bash
# This is normal if you don't have LSL hardware
# The software will still run for basic testing
```

### Getting Help
1. Check the console output for error messages
2. Look at the log files in the application directory
3. Refer to the [Troubleshooting section](TROUBLESHOOTING.md) for specific hardware issues
4. Check the GitHub issues for known problems

---

## Next Steps

### For Researchers
- Read the [Experimenter Client Guide](EXPERIMENTER_CLIENT_GUIDE.md)
- Learn about [Data Collection Host Setup](DATA_COLLECTION_HOST_GUIDE.md)
- Explore [Hardware Integration](HARDWARE_SETUP.md)

### For Developers
- Review the [Developer Documentation](DEVELOPER_DOCUMENTATION.md)
- Understand the [System Architecture](DEVELOPER_DOCUMENTATION.md#system-architecture)
- Learn about [Adding New Features](DEVELOPER_DOCUMENTATION.md#adding-new-features)

### For System Administrators
- Set up [Network Configuration](DATA_COLLECTION_HOST_GUIDE.md#network-setup)
- Configure [Hardware Systems](HARDWARE_SETUP.md)
- Plan [Data Storage and Backup](DATA_COLLECTION_HOST_GUIDE.md#data-management)

---

## Quick Reference

### Essential Commands
```bash
# Start the application
python -m eeg_stimulus_project.main.main

# Check installation
python -c "import eeg_stimulus_project; print('OK')"

# View logs (if issues occur)
tail -f app.log
```

### Important Files
- `eeg_stimulus_project/config/settings.yaml` - Configuration
- `eeg_stimulus_project/saved_data/` - Experiment data
- `requirements.txt` - Python dependencies
- `app.log` - Application logs

### Default Network Settings
- **Host Port**: 9999
- **Default Host IP**: 169.254.37.25 (update as needed)

---

**Congratulations!** You've successfully set up the Multisensory Stimulus Presentation and Data Collection System. You're now ready to run experiments and collect data.

For questions or issues, please refer to the specific guides for your use case or check the project's GitHub repository for support.