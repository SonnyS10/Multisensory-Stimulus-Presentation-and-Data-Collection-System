# Experimenter (Client) Side Management Guide
## Multisensory Stimulus Presentation and Data Collection System

This guide provides comprehensive instructions for researchers and experimenters who will be operating the client-side of the distributed experiment system. The client computer handles stimulus presentation and participant interaction while connecting to a host computer for data collection coordination.

## Table of Contents
1. [Overview](#overview)
2. [Pre-Experiment Setup](#pre-experiment-setup)
3. [Connecting to Host](#connecting-to-host)
4. [Experiment Configuration](#experiment-configuration)
5. [Running Experiments](#running-experiments)
6. [Participant Management](#participant-management)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

---

## Overview

### Role of the Client Computer
The client computer serves as the **experiment presentation system** and is typically located in the experimental room with the participant. Its primary responsibilities include:

- **Stimulus Presentation**: Displaying visual stimuli to participants
- **Participant Interaction**: Collecting behavioral responses and user inputs
- **Custom Asset Management**: Loading personalized images and stimuli
- **Experiment Flow Control**: Managing the sequence and timing of experimental trials
- **Network Communication**: Coordinating with the host computer for data synchronization

### Client vs. Host Distinction
- **Client (Experimenter Computer)**: Handles stimulus presentation and participant interaction
- **Host (Data Collection Computer)**: Manages data storage, hardware connections, and overall experiment coordination
- **Communication**: Real-time network communication ensures synchronized data collection

---

## Pre-Experiment Setup

### 1. System Requirements
**Minimum Requirements:**
- Windows 10/11, macOS 10.15+, or Linux
- Python 3.8+ with all dependencies installed
- 4GB RAM, 8GB recommended
- Reliable network connection to host computer
- Display capable of running experiment stimuli

**Recommended Hardware:**
- High-resolution monitor for stimulus presentation
- Secondary monitor for experimenter controls
- Backup network connection (ethernet + WiFi)
- Uninterruptible Power Supply (UPS)

### 2. Software Installation
```bash
# Clone and install the system (if not already done)
git clone https://github.com/SonnyS10/Multisensory-Stimulus-Presentation-and-Data-Collection-System.git
cd Multisensory-Stimulus-Presentation-and-Data-Collection-System
pip install -r requirements.txt
```

### 3. Network Configuration
**Essential Information Needed:**
- Host computer IP address (obtain from data collection team)
- Network configuration (same subnet as host)
- Firewall settings (ensure port 9999 is accessible)

**Network Testing:**
```bash
# Test connectivity to host computer
ping [HOST_IP_ADDRESS]

# Test port accessibility (if available)
telnet [HOST_IP_ADDRESS] 9999
```

### 4. Asset Preparation
The client computer can use custom images for personalized experiments:

**Preparing Custom Assets:**
1. **Alcohol Images Folder**:
   - Create a folder with alcohol-related images
   - Supported formats: JPG, PNG
   - Recommended resolution: 1920x1080 or higher
   - File naming: Descriptive names (e.g., "beer_brand_A.jpg")

2. **Non-Alcohol Images Folder**:
   - Create a folder with control/neutral images
   - Match the format and resolution of alcohol images
   - Consider visual complexity and color balance

**Folder Structure Example:**
```
experiment_assets/
├── alcohol_images/
│   ├── beer_heineken.jpg
│   ├── wine_cabernet.jpg
│   └── cocktail_martini.jpg
└── neutral_images/
    ├── soda_cola.jpg
    ├── juice_orange.jpg
    └── water_bottle.jpg
```

---

## Connecting to Host

### 1. Obtaining Host Information
Before starting experiments, coordinate with the data collection team to obtain:
- **Host IP Address**: The network address of the data collection computer
- **Experiment Schedule**: Timing and coordination of experiment sessions
- **Hardware Status**: Confirmation that all recording systems are operational

### 2. Starting the Client Application
1. **Launch the Application**:
   ```bash
   python -m eeg_stimulus_project.main.main
   ```

2. **Configure Connection Settings**:
   - In the "Experimenter Computer (Client)" section
   - Enter the Host IP address provided by the data collection team
   - Default port is 9999 (usually doesn't need to be changed)

3. **Import Custom Assets (Optional)**:
   - Click "Browse" next to "Alcohol Images Folder"
   - Select your prepared alcohol images folder
   - Click "Browse" next to "Non-Alcohol Images Folder"  
   - Select your prepared neutral images folder
   - Leave blank to use default system images

4. **Connect to Host**:
   - Click "Start Experimenter Computer (Client)"
   - Wait for connection confirmation
   - The experiment window will open once connected

### 3. Connection Troubleshooting
**Common Connection Issues:**

**"Connection Refused" Error:**
- Verify the host IP address is correct
- Ensure the host computer is running and waiting for connections
- Check that both computers are on the same network

**"Network Unreachable" Error:**
- Verify network connectivity between computers
- Check firewall settings on both computers
- Ensure port 9999 is not blocked

**"Connection Timeout" Error:**
- Host computer may not be ready
- Coordinate with data collection team
- Verify host computer is in "waiting for client" state

---

## Experiment Configuration

### 1. Understanding the Client Interface
Once connected, the client interface provides:

**Sidebar Navigation:**
- **Test Categories**: Passive viewing vs. Stroop tasks
- **Individual Tests**: Specific stimulus combinations
- **Utility Functions**: Instructions, stimulus order, latency testing

**Main Content Area:**
- **Test Frames**: Configuration and controls for each experiment type
- **Display Controls**: Start/stop stimulus presentation
- **Status Indicators**: Connection and hardware status
- **Participant Instructions**: Built-in instruction displays

### 2. Experiment Types Available

**Passive Viewing Tests (Test 1):**
- Participants observe stimuli without active responses
- Six different sensory combinations available
- Focus on measuring physiological responses (EEG, eye tracking)
- Typical duration: 5-10 minutes per condition

**Stroop Task Tests (Test 2):**
- Participants actively respond to stimuli
- Four different sensory combinations available
- Measures reaction times and accuracy
- Typical duration: 10-15 minutes per condition

### 3. Stimulus Order Configuration
Access via the "Stimulus Order" button in the sidebar:

**Randomization Settings:**
- **Enable Randomization**: Randomize stimulus presentation order
- **Seed Value**: For reproducible randomization sequences
- **Custom Orders**: Predefined stimulus sequences for specific experiments

**Repetition Settings:**
- **Number of Repetitions**: How many times each stimulus is presented
- **Inter-stimulus Intervals**: Time between stimulus presentations
- **Break Intervals**: Scheduled breaks during longer experiments

---

## Running Experiments

### 1. Pre-Experiment Checklist
Before starting each experimental session:

**Technical Preparation:**
- [ ] Client computer connected to host
- [ ] Network connection stable
- [ ] Custom assets loaded (if applicable)
- [ ] Display settings optimized for stimulus presentation
- [ ] Backup systems ready (power, network)

**Coordination with Host:**
- [ ] Confirm all recording systems are active
- [ ] Verify participant information is entered on host
- [ ] Ensure data directories are prepared
- [ ] Test communication between client and host

**Participant Preparation:**
- [ ] Participant briefed on experiment procedures
- [ ] Consent forms completed
- [ ] Hardware setup complete (EEG, eye tracking, etc.)
- [ ] Participant positioned correctly for stimulus viewing

### 2. Starting an Experiment Session

**Step 1: Select Test Condition**
- Use the sidebar to navigate to the desired test
- For first-time participants, start with "Instructions"
- Read through participant instructions together

**Step 2: Configure Test Parameters**
- Access "Stimulus Order" if custom sequences are needed
- Verify randomization settings are appropriate
- Check repetition settings match experimental protocol

**Step 3: Initialize Stimulus Presentation**
- In the selected test frame, check "Start Display"
- A stimulus presentation window will open
- A mirrored view appears in the main interface for monitoring

**Step 4: Monitor Experiment Progress**
- Watch the mirrored display to track experiment progress
- Observe participant for comfort and compliance
- Be ready to pause or stop if issues arise

### 3. During Experiment Execution

**Monitoring Responsibilities:**
- **Participant Comfort**: Watch for signs of fatigue or discomfort
- **Technical Issues**: Monitor for display problems or system errors
- **Data Quality**: Observe response patterns for anomalies
- **Communication**: Maintain contact with data collection team

**Available Controls:**
- **Pause/Resume**: Temporarily halt experiment if needed
- **Stop**: End experiment session early if necessary
- **Emergency Communication**: Direct communication with host computer

### 4. Between Experiments
When switching between different test conditions:

**Data Coordination:**
- Ensure previous test data is properly saved
- Confirm with host that data collection is complete
- Allow time for system reset between conditions

**Participant Management:**
- Provide breaks as needed between test blocks
- Check participant comfort and readiness
- Review instructions for new test conditions

---

## Participant Management

### 1. Participant Instructions
The system includes built-in instruction displays:

**Accessing Instructions:**
- Click "Show Instructions" in the sidebar
- Instructions are tailored to each experiment type
- Review instructions with participants before starting

**Customizing Instructions:**
- Instructions can be modified for specific experimental protocols
- Work with the development team for custom instruction sets
- Consider language and accessibility requirements

### 2. Participant Comfort and Safety

**Visual Comfort:**
- Adjust display brightness appropriately
- Ensure comfortable viewing distance
- Watch for signs of eye strain or fatigue
- Provide breaks every 15-20 minutes for longer sessions

**Physical Comfort:**
- Ensure proper seating and posture
- Minimize movement restrictions from recording equipment
- Maintain comfortable room temperature
- Provide hydration during longer sessions

**Psychological Comfort:**
- Explain experiment procedures clearly
- Emphasize voluntary participation
- Provide reassurance about recording equipment
- Respect participant questions and concerns

### 3. Managing Different Participant Populations

**Age Considerations:**
- **Children**: Shorter sessions, simplified instructions, parental consent
- **Elderly**: Larger fonts, slower pace, frequent breaks
- **Young Adults**: Standard protocols typically appropriate

**Accessibility Considerations:**
- **Visual Impairments**: Coordinate with development team for accommodations
- **Motor Impairments**: Adapt response collection methods
- **Cognitive Considerations**: Simplify instructions, provide additional support

---

## Troubleshooting

### 1. Common Technical Issues

**Display Problems:**
```
Issue: Stimulus window doesn't appear
Solutions:
1. Check "Start Display" checkbox is enabled
2. Verify connection to host computer
3. Try switching to different test condition
4. Restart client application if necessary
```

**Connection Issues:**
```
Issue: Lost connection to host
Solutions:
1. Check network connectivity
2. Coordinate with host operator for reconnection
3. Verify host computer is still running
4. Restart client application and reconnect
```

**Performance Issues:**
```
Issue: Slow or jerky stimulus presentation
Solutions:
1. Close unnecessary applications
2. Check system resource usage
3. Verify network bandwidth
4. Consider reducing stimulus complexity
```

### 2. Participant-Related Issues

**Participant Discomfort:**
- **Immediate Response**: Stop stimulus presentation if needed
- **Assessment**: Determine cause of discomfort
- **Solutions**: Adjust lighting, position, or take break
- **Documentation**: Record any issues for future reference

**Technical Difficulties with Responses:**
- **Input Problems**: Verify response collection systems
- **Timing Issues**: Check synchronization with host
- **Data Quality**: Monitor response patterns for anomalies

### 3. Emergency Procedures

**Immediate Experiment Stop:**
1. Uncheck "Start Display" to stop stimulus presentation
2. Inform participant that experiment is paused
3. Communicate with host operator immediately
4. Document reason for emergency stop

**System Failure:**
1. Ensure participant safety and comfort
2. Contact host operator via alternative communication
3. Follow institutional emergency procedures
4. Document technical issues for system improvement

---

## Best Practices

### 1. Preparation and Planning

**Session Preparation:**
- Arrive early to test all systems
- Coordinate timing with data collection team
- Prepare backup plans for technical issues
- Review experimental protocols beforehand

**Documentation:**
- Keep detailed logs of each session
- Note any technical issues or anomalies
- Record participant feedback and observations
- Maintain participant confidentiality

### 2. Communication

**With Data Collection Team:**
- Establish clear communication protocols
- Regular check-ins during experiments
- Immediate notification of any issues
- Post-session debriefing

**With Participants:**
- Clear, friendly communication
- Professional but approachable manner
- Respect for participant concerns
- Prompt response to questions

### 3. Quality Assurance

**Technical Quality:**
- Regular system checks and maintenance
- Backup procedures for critical components
- Version control for experimental protocols
- Data integrity verification

**Experimental Quality:**
- Consistent experimental procedures
- Standardized participant interactions
- Environmental control (lighting, noise, temperature)
- Adherence to research protocols

---

## Advanced Features

### 1. Custom Stimulus Sequences
For specialized experiments:
- Work with development team to create custom stimulus orders
- Test custom sequences thoroughly before participant sessions
- Document custom configurations for reproducibility

### 2. Multi-Session Experiments
For longitudinal studies:
- Coordinate participant scheduling with data collection team
- Maintain consistent experimental conditions across sessions
- Track participant progress and any changes in responses

### 3. Integration with External Systems
For specialized hardware:
- Coordinate with technical team for additional hardware integration
- Test all systems thoroughly before participant sessions
- Maintain backup procedures for critical components

---

This guide provides the essential information for successfully operating the experimenter (client) side of the Multisensory Stimulus Presentation and Data Collection System. For additional support or questions about specific experimental protocols, consult with the data collection team and refer to the developer documentation for technical details.