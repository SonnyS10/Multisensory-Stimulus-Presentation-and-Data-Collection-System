# Data Collection (Host) Side Management Guide
## Multisensory Stimulus Presentation and Data Collection System

This guide provides comprehensive instructions for researchers and technicians operating the host computer in the distributed experiment system. The host computer serves as the central data collection hub, managing hardware systems, coordinating with client computers, and ensuring proper data storage and synchronization.

## Table of Contents
1. [Overview](#overview)
2. [System Setup](#system-setup)
3. [Hardware Integration](#hardware-integration)
4. [Network Configuration](#network-configuration)
5. [Data Management](#data-management)
6. [Running Experiments](#running-experiments)
7. [Monitoring and Quality Control](#monitoring-and-quality-control)
8. [Troubleshooting](#troubleshooting)
9. [Maintenance and Best Practices](#maintenance-and-best-practices)

---

## Overview

### Role of the Host Computer
The host computer serves as the **central data collection and coordination hub** for distributed experiments. It is typically located in a control room or technical area, separate from the participant. Primary responsibilities include:

- **Data Collection Coordination**: Managing all data streams from multiple sources
- **Hardware System Management**: Controlling EEG, eye tracking, and other recording equipment
- **Network Server Operations**: Accepting connections from client computers
- **Data Storage and Organization**: Ensuring proper data archival and backup
- **Real-time Monitoring**: Overseeing experiment progress and data quality
- **Synchronization**: Coordinating timing between all system components

### Host vs. Client Architecture
- **Host (Data Collection Computer)**: Central hub managing data, hardware, and coordination
- **Client (Experimenter Computer)**: Handles stimulus presentation and participant interaction
- **Communication**: Real-time TCP/IP network communication ensures system synchronization
- **Data Flow**: All data streams converge at the host for synchronized storage

---

## System Setup

### 1. Hardware Requirements

**Minimum Requirements:**
- **CPU**: Intel i7 or AMD Ryzen 7 (8+ cores recommended)
- **RAM**: 16GB minimum, 32GB recommended for complex experiments
- **Storage**: 500GB SSD for system, 2TB+ for data storage
- **Network**: Gigabit Ethernet (primary), WiFi (backup)
- **OS**: Windows 10/11 Pro, Ubuntu 20.04+, or macOS 10.15+

**Recommended Hardware:**
- **Workstation-class CPU**: For real-time data processing
- **ECC RAM**: For data integrity in long experiments
- **RAID Storage**: For data redundancy and performance
- **Multiple Network Interfaces**: Separate networks for data and control
- **Uninterruptible Power Supply (UPS)**: Prevent data loss during power issues

### 2. Software Installation

**Core System Setup:**
```bash
# Clone the repository
git clone https://github.com/SonnyS10/Multisensory-Stimulus-Presentation-and-Data-Collection-System.git
cd Multisensory-Stimulus-Presentation-and-Data-Collection-System

# Create dedicated virtual environment
python -m venv host_env
source host_env/bin/activate  # Linux/macOS
# host_env\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

**Additional Software Requirements:**
- **LabRecorder**: For EEG data collection (download separately)
- **LSL Applications**: Lab Streaming Layer tools and utilities
- **Hardware-Specific Software**: Drivers for EEG, eye tracking, etc.
- **SSH Client**: For tactile system communication (usually built-in)

### 3. Directory Structure Setup
Create organized directories for data management:

```bash
# Create data directory structure
mkdir -p data_collection/{raw_data,processed_data,backups,logs,configs}
mkdir -p data_collection/raw_data/{eeg,eyetracking,behavioral,tactile}
mkdir -p data_collection/logs/{system,experiments,hardware}
```

**Recommended Directory Structure:**
```
data_collection/
├── raw_data/
│   ├── eeg/           # EEG recordings (XDF files)
│   ├── eyetracking/   # Eye tracking data
│   ├── behavioral/    # Response data (CSV files)
│   ├── tactile/       # Tactile sensor data
│   └── synchronized/  # Cross-referenced data files
├── processed_data/    # Analysis-ready datasets
├── backups/          # Regular data backups
├── logs/             # System and experiment logs
└── configs/          # Configuration snapshots
```

---

## Hardware Integration

### 1. EEG System Setup (EMOTIV EPOC Flex)

**Prerequisites:**
- EMOTIV Pro software installed and licensed
- EEG headset properly fitted and connected
- LabRecorder installed and configured

**Connection Procedure:**
1. **Start EMOTIV Pro**:
   - Launch EMOTIV Pro software
   - Connect and test EEG headset
   - Verify all channels are receiving good signals
   - Configure sampling rate (typically 256 Hz)

2. **Launch LabRecorder**:
   - Start LabRecorder application
   - Configure recording settings:
     - File location: `data_collection/raw_data/eeg/`
     - File naming: Include participant ID and timestamp
     - Streams: Select EMOTIV and marker streams

3. **Test Integration**:
   - Verify EEG data stream appears in LabRecorder
   - Test event marker reception from experiment system
   - Confirm data quality and synchronization

**Configuration in Host System:**
```python
# In the control window, click "Connect LabRecorder"
# System will establish connection on port 22345
# Monitor connection status in shared_status['lab_recorder_connected']
```

### 2. Eye Tracking Integration

**Supported Systems:**
- **Eyelink 1000 Plus**: Industry standard research eye tracker
- **Pupil Labs**: Open-source eye tracking system
- **HTC VIVE Pro Eye**: VR-integrated eye tracking

**Setup Procedure:**
1. **Hardware Calibration**:
   - Follow manufacturer's calibration procedures
   - Ensure participant positioning is optimal
   - Verify tracking accuracy meets research standards

2. **Software Integration**:
   - Start eye tracking software
   - Configure LSL streaming (if supported)
   - Test data stream reception at host computer

3. **System Integration**:
   ```python
   # In control window, click "Connect Eye Tracker"
   # System will attempt to establish connection
   # Monitor status via shared_status['eyetracker_connected']
   ```

### 3. Tactile System Setup

**Hardware Components:**
- Remote tactile stimulation system
- Force sensors for response detection
- Network-connected control computer

**Connection Configuration:**
The tactile system requires SSH connection to a remote computer:

**Network Setup:**
```yaml
# In eeg_stimulus_project/config/settings.yaml
network:
  tactile_system:
    host: "10.115.12.225"      # Tactile system IP
    username: "your_username"   # SSH username
    password: "your_password"   # SSH password (consider key-based auth)
    script_path: "~/forcereadwithzero.py"
    venv_path: "~/Desktop/bin/activate"
```

**Connection Procedure:**
1. **Verify Network Access**:
   ```bash
   ping 10.115.12.225
   ssh username@10.115.12.225
   ```

2. **Test Tactile System**:
   - SSH into tactile control computer
   - Run tactile control script manually
   - Verify force sensor readings

3. **Integrate with Host**:
   - Use "Connect Tactile System" in control window
   - Monitor connection via shared_status['tactile_connected']
   - Test stimulus delivery and response detection

### 4. Additional Hardware Systems

**VR System (HTC VIVE Pro Eye):**
- Install SteamVR and VIVE software
- Configure room-scale tracking
- Test VR display and eye tracking integration

**Audio Systems:**
- Configure audio output for stimulus presentation
- Test audio synchronization with visual stimuli
- Ensure audio levels are appropriate for experiments

**Custom Hardware:**
- Document any additional hardware integrations
- Create hardware-specific configuration files
- Test integration with main experiment system

---

## Network Configuration

### 1. Network Architecture

**Recommended Network Setup:**
```
[Host Computer] ---- [Ethernet Switch] ---- [Client Computer(s)]
     |                       |
[EEG System]           [Tactile System]
     |                       |
[Eye Tracker]          [Additional Hardware]
```

**IP Address Planning:**
- **Host Computer**: Static IP (e.g., 192.168.1.100)
- **Client Computer**: Static IP (e.g., 192.168.1.101)
- **Hardware Systems**: Static IPs on same subnet
- **Tactile System**: May be on different subnet (e.g., 10.115.12.x)

### 2. Firewall Configuration

**Host Computer Firewall Settings:**
```bash
# Windows Firewall
# Allow inbound connections on port 9999 for client communication
# Allow inbound connections on port 22345 for LabRecorder

# Linux iptables
sudo ufw allow 9999/tcp   # Client connections
sudo ufw allow 22345/tcp  # LabRecorder
sudo ufw allow ssh       # Remote management
```

**Network Security:**
- Use dedicated experiment network (isolated from internet)
- Change default passwords on all systems
- Consider VPN for remote access
- Regular security updates for all systems

### 3. Connection Management

**Starting Host Server:**
1. **Launch Application**:
   ```bash
   python -m eeg_stimulus_project.main.main
   ```

2. **Configure Host Mode**:
   - Enter participant information (Subject ID, Test Number)
   - Click "Start as Data Collection Computer (Host)"
   - System will start listening on port 9999

3. **Wait for Client Connection**:
   - Monitor console for "Waiting for client" message
   - Provide IP address to experimenter/client operator
   - Confirm connection establishment

**Client Connection Monitoring:**
- Monitor connection status in real-time
- Automatic reconnection handling for temporary disconnections
- Log all connection events for troubleshooting

---

## Data Management

### 1. Data Organization Structure

**Automatic Directory Creation:**
The system automatically creates organized directories for each participant:

```
saved_data/
└── subject_[ID]/
    ├── test_1/                    # Passive viewing experiments
    │   ├── Unisensory_Neutral_Visual/
    │   │   ├── data.csv          # Behavioral data
    │   │   └── eeg_data.xdf      # EEG recording
    │   ├── Multisensory_Alcohol_Visual_Olfactory/
    │   └── [other test conditions]/
    └── test_2/                    # Stroop task experiments
        ├── Stroop_Multisensory_Alcohol_Visual_Tactile/
        └── [other test conditions]/
```

### 2. Data Types and Formats

**Behavioral Data (CSV):**
- User responses and reaction times
- Stimulus presentation logs
- Event timing information
- Experimental condition metadata

**Physiological Data (XDF):**
- EEG signals from all channels
- Event markers synchronized with stimuli
- Timestamp information for analysis
- Hardware status and quality metrics

**Eye Tracking Data:**
- Gaze position coordinates
- Pupil diameter measurements
- Fixation and saccade events
- Calibration quality metrics

**Tactile Data:**
- Force sensor readings
- Stimulus delivery confirmations
- Response detection events
- System status information

### 3. Data Backup and Archival

**Real-time Backup:**
```bash
# Set up automatic backup during experiments
rsync -av saved_data/ backup_drive/saved_data/
```

**Daily Backup Procedures:**
1. **Verify Data Integrity**:
   - Check all data files are complete
   - Verify file sizes and timestamps
   - Test file readability

2. **Create Backup Copies**:
   - Copy to external storage device
   - Upload to secure cloud storage (if permitted)
   - Create redundant local copies

3. **Document Data Status**:
   - Log successful backups
   - Note any data quality issues
   - Track participant completion status

---

## Running Experiments

### 1. Pre-Experiment Checklist

**System Preparation:**
- [ ] All hardware systems connected and tested
- [ ] Network connectivity verified
- [ ] LabRecorder configured and ready
- [ ] Data directories created and accessible
- [ ] Backup systems prepared
- [ ] Emergency procedures reviewed

**Software Preparation:**
- [ ] Host application launched and listening
- [ ] All hardware connections established
- [ ] LSL streams verified and running
- [ ] Configuration settings confirmed
- [ ] Log files initialized

**Coordination:**
- [ ] Communication established with experimenter/client
- [ ] Participant information confirmed
- [ ] Experiment protocol reviewed
- [ ] Emergency contact information available

### 2. Experiment Session Management

**Starting a Session:**
1. **Launch Host Application**:
   ```bash
   python -m eeg_stimulus_project.main.main
   ```

2. **Enter Participant Information**:
   - Subject ID: Unique identifier for the participant
   - Test Number: 1 (passive) or 2 (stroop)
   - Verify information accuracy

3. **Start Host Mode**:
   - Click "Start as Data Collection Computer (Host)"
   - System creates data directories automatically
   - Begins listening for client connections

4. **Hardware Connection Sequence**:
   - **LabRecorder**: Click "Connect LabRecorder" button
   - **Eye Tracker**: Click "Connect Eye Tracker" button  
   - **Tactile System**: Click "Connect Tactile System" button
   - Monitor connection status for each system

**During Experiment Execution:**
- **Monitor Control Window**: Watch for status updates and errors
- **Observe Data Streams**: Verify continuous data collection
- **Client Communication**: Maintain contact with experimenter
- **Quality Control**: Monitor data quality indicators
- **Emergency Response**: Ready to intervene if issues arise

### 3. Experiment Coordination

**Client Connection Management:**
- Accept client connections when experimenter is ready
- Monitor connection stability throughout session
- Handle reconnections if network issues occur
- Coordinate timing between multiple clients (if applicable)

**Hardware Synchronization:**
- Ensure all systems are recording simultaneously
- Monitor LSL stream synchronization
- Verify event marker delivery across systems
- Handle hardware-specific timing requirements

**Real-time Monitoring:**
- **EEG Quality**: Monitor signal quality and artifacts
- **Eye Tracking**: Verify tracking accuracy and calibration
- **Behavioral Data**: Observe response patterns for anomalies
- **System Performance**: Monitor CPU, memory, and disk usage

---

## Monitoring and Quality Control

### 1. Real-time Data Quality Monitoring

**EEG Signal Quality:**
- Monitor electrode impedances in real-time
- Watch for movement artifacts and electrical interference
- Verify continuous data streaming
- Alert experimenter to quality issues

**Eye Tracking Accuracy:**
- Monitor tracking stability and accuracy
- Watch for calibration drift
- Verify pupil detection quality
- Re-calibrate if necessary

**Behavioral Data Integrity:**
- Monitor response timing and patterns
- Verify stimulus-response synchronization
- Check for missing or anomalous data
- Document any irregularities

### 2. System Health Monitoring

**Performance Metrics:**
```bash
# Monitor system resources during experiments
top -p $(pgrep -f "eeg_stimulus")
iostat -x 1        # Disk I/O monitoring
netstat -i         # Network interface statistics
```

**Critical Indicators:**
- **CPU Usage**: Should remain below 80% during experiments
- **Memory Usage**: Monitor for memory leaks in long sessions
- **Disk Space**: Ensure adequate space for data collection
- **Network Latency**: Monitor client-host communication delays

### 3. Error Detection and Response

**Automated Error Detection:**
- Connection timeouts and failures
- Hardware disconnections
- Data corruption or missing files
- Excessive system resource usage

**Manual Quality Checks:**
- Visual inspection of data streams
- Participant behavior observations
- Hardware status verification
- Network communication stability

**Response Procedures:**
1. **Immediate Assessment**: Determine severity and impact
2. **Communication**: Alert experimenter if intervention needed
3. **Documentation**: Log all issues with timestamps
4. **Recovery**: Implement appropriate recovery procedures
5. **Prevention**: Adjust procedures to prevent recurrence

---

## Troubleshooting

### 1. Hardware Connection Issues

**EEG System Problems:**
```
Issue: LabRecorder not connecting
Solutions:
1. Verify EMOTIV Pro is running and streaming
2. Check port 22345 availability
3. Restart LabRecorder application
4. Verify LSL library installation
5. Check firewall settings

Issue: Poor EEG signal quality
Solutions:
1. Check electrode contact and impedances
2. Verify proper headset placement
3. Minimize electrical interference sources
4. Re-apply electrode gel if needed
5. Check cable connections
```

**Eye Tracking Problems:**
```
Issue: Eye tracker not responding
Solutions:
1. Verify eye tracking software is running
2. Check USB/network connections
3. Re-calibrate tracking system
4. Verify participant positioning
5. Restart eye tracking software

Issue: Poor tracking accuracy
Solutions:
1. Recalibrate the system
2. Adjust lighting conditions
3. Check for reflections or obstructions
4. Verify participant head positioning
5. Clean tracker lenses if applicable
```

**Tactile System Issues:**
```
Issue: SSH connection failed
Solutions:
1. Verify network connectivity to tactile system
2. Check SSH credentials and permissions
3. Verify tactile system is powered and ready
4. Test manual SSH connection
5. Check firewall settings on tactile system

Issue: Force sensor not responding
Solutions:
1. Check sensor connections and power
2. Verify calibration and baseline settings
3. Test sensor manually on tactile system
4. Check for mechanical obstructions
5. Restart tactile control software
```

### 2. Network and Communication Issues

**Client Connection Problems:**
```
Issue: Client cannot connect to host
Solutions:
1. Verify host is listening on correct port (9999)
2. Check network connectivity between computers
3. Verify firewall settings on both computers
4. Ensure both computers are on same network
5. Try alternative network connection (WiFi/Ethernet)

Issue: Connection drops during experiment
Solutions:
1. Check network stability and bandwidth
2. Verify power management settings
3. Monitor for network congestion
4. Use ethernet instead of WiFi if possible
5. Implement automatic reconnection procedures
```

### 3. Data Collection Issues

**Data Integrity Problems:**
```
Issue: Missing or corrupted data files
Solutions:
1. Check disk space and permissions
2. Verify data directory structure
3. Monitor for hardware failures
4. Implement redundant data storage
5. Regular backup verification

Issue: Synchronization problems
Solutions:
1. Verify LSL system clock synchronization
2. Check event marker delivery
3. Monitor timestamp accuracy
4. Restart LSL applications if needed
5. Verify hardware timing settings
```

### 4. Emergency Procedures

**Critical System Failure:**
1. **Immediate Actions**:
   - Stop data collection safely
   - Secure any collected data
   - Communicate with experimenter immediately
   - Document failure conditions

2. **Data Recovery**:
   - Assess data integrity and completeness
   - Recover from backup systems if available
   - Document data loss or corruption
   - Plan data collection resumption

3. **System Recovery**:
   - Identify and resolve root cause
   - Test all systems before resuming
   - Update procedures to prevent recurrence
   - Report incidents for system improvement

---

## Maintenance and Best Practices

### 1. Regular Maintenance Tasks

**Daily Tasks:**
- [ ] Verify system startup and connectivity
- [ ] Check available disk space
- [ ] Test hardware connections
- [ ] Review and clear log files
- [ ] Backup critical data

**Weekly Tasks:**
- [ ] Update system software and drivers
- [ ] Check hardware calibration
- [ ] Verify backup integrity
- [ ] Clean and maintain hardware
- [ ] Review experiment protocols

**Monthly Tasks:**
- [ ] Comprehensive system testing
- [ ] Hardware maintenance and calibration
- [ ] Data archival and cleanup
- [ ] Security updates and patches
- [ ] Performance optimization

### 2. Documentation and Record Keeping

**Experiment Logs:**
- Maintain detailed records of all experimental sessions
- Document any issues or anomalies
- Track participant information (anonymized)
- Record system configuration changes

**Technical Documentation:**
- Keep hardware manuals and specifications
- Document network configuration
- Maintain software version records
- Update troubleshooting procedures

**Quality Assurance:**
- Regular data quality audits
- System performance monitoring
- Backup verification procedures
- Staff training and certification

### 3. System Optimization

**Performance Tuning:**
- Optimize data collection parameters
- Configure system for real-time performance
- Monitor and adjust resource allocation
- Implement efficient data storage strategies

**Scalability Planning:**
- Plan for increased data volumes
- Consider multi-participant experiments
- Prepare for additional hardware integration
- Design flexible configuration systems

**Security Measures:**
- Regular security assessments
- Access control and authentication
- Data encryption for sensitive information
- Network security monitoring

---

## Advanced Configuration

### 1. Multi-Client Experiments
For experiments requiring multiple client computers:

**Network Configuration:**
- Configure host to accept multiple connections
- Implement client identification and coordination
- Synchronize stimulus presentation across clients
- Manage data collection from multiple sources

**Data Management:**
- Coordinate data streams from multiple clients
- Implement cross-client synchronization
- Manage complex experimental designs
- Ensure data integrity across all clients

### 2. Custom Hardware Integration

**Adding New Hardware:**
1. **Driver Installation**: Install hardware-specific drivers
2. **LSL Integration**: Configure LSL streaming if supported
3. **System Integration**: Modify host software for new hardware
4. **Testing**: Comprehensive testing with existing systems

**Configuration Management:**
- Create hardware-specific configuration files
- Document integration procedures
- Test compatibility with existing systems
- Implement error handling for new hardware

### 3. Advanced Data Processing

**Real-time Processing:**
- Implement real-time data analysis
- Configure automatic data quality assessment
- Set up real-time feedback systems
- Monitor experimental progress automatically

**Integration with Analysis Tools:**
- Configure automatic data export
- Set up integration with MATLAB/Python analysis
- Implement standardized data formats
- Create analysis pipeline automation

---

This comprehensive guide provides the essential information for successfully operating the data collection (host) side of the Multisensory Stimulus Presentation and Data Collection System. For specific technical issues or advanced configurations, consult the developer documentation and work with the technical support team to ensure optimal system performance.