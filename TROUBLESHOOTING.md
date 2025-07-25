# Troubleshooting Guide
## Multisensory Stimulus Presentation and Data Collection System

This comprehensive troubleshooting guide identifies potential failure points in the software system and provides step-by-step solutions for common problems. The guide is organized by failure type and severity level.

## Table of Contents
1. [Emergency Procedures](#emergency-procedures)
2. [Application Startup Failures](#application-startup-failures)
3. [Network Communication Issues](#network-communication-issues)
4. [Hardware Connection Problems](#hardware-connection-problems)
5. [Data Collection Failures](#data-collection-failures)
6. [Software Crashes and Hangs](#software-crashes-and-hangs)
7. [Configuration and Setup Issues](#configuration-and-setup-issues)
8. [Performance Problems](#performance-problems)
9. [Diagnostic Tools and Procedures](#diagnostic-tools-and-procedures)
10. [Recovery and Prevention](#recovery-and-prevention)

---

## Emergency Procedures

### 🚨 CRITICAL: Complete System Failure During Experiment

**Immediate Actions (First 60 seconds):**
1. **Ensure participant safety**
   - Stop all stimulus presentation immediately
   - Check participant comfort and wellbeing
   - Remove or pause any ongoing stimulation (VR, tactile, olfactory)

2. **Preserve collected data**
   - Do NOT force-close applications immediately
   - Check if auto-save is in progress
   - Note the approximate time of failure for data recovery

3. **Emergency communication**
   - Alert all team members immediately
   - Use backup communication if network is down
   - Document the exact circumstances of the failure

**Recovery Steps:**
1. **Assess system state**
   ```bash
   # Check if processes are still running
   ps aux | grep "eeg_stimulus"
   ps aux | grep "python"
   
   # Check system resources
   top
   df -h  # Check disk space
   ```

2. **Attempt graceful recovery**
   - Try to save any open data files
   - Close applications in reverse order (client first, then host)
   - Check network connections

3. **Emergency shutdown if necessary**
   - Only if system is completely unresponsive
   - Document all steps taken for post-incident analysis

### 🚨 Participant Emergency

**If participant shows distress during experiment:**
1. **Immediate response**
   - Press `Ctrl+Alt+Q` (emergency stop if implemented)
   - Uncheck "Start Display" to stop stimulus presentation
   - Remove VR headset or turn away from display

2. **System actions**
   - Keep data collection systems running if possible
   - Mark the incident in experiment logs
   - Follow institutional emergency procedures

---

## Application Startup Failures

### Issue: "Module not found" or Import Errors

**Symptoms:**
```
ImportError: No module named 'PyQt5'
ModuleNotFoundError: No module named 'eeg_stimulus_project'
```

**Diagnosis:**
```bash
# Check Python version
python --version

# Check if in correct directory
pwd

# Verify virtual environment
which python
pip list
```

**Solutions:**
1. **Verify Python environment**
   ```bash
   # Activate virtual environment if using one
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   
   # Reinstall dependencies
   pip install -r requirements.txt
   ```

2. **Fix Python path issues**
   ```bash
   # Add project to PYTHONPATH
   export PYTHONPATH="${PYTHONPATH}:/path/to/project"
   
   # Or run from project root
   python -m eeg_stimulus_project.main.main
   ```

3. **Check for corrupted installation**
   ```bash
   # Reinstall PyQt5 specifically
   pip uninstall PyQt5 PyQt5-tools
   pip install PyQt5>=5.15.0
   ```

### Issue: "Permission denied" Errors

**Symptoms:**
```
PermissionError: [Errno 13] Permission denied
```

**Solutions:**
1. **Fix file permissions**
   ```bash
   # Make scripts executable
   chmod +x eeg_stimulus_project/utils/run_eeg_stimulus.sh
   
   # Fix directory permissions
   chmod -R 755 eeg_stimulus_project/
   ```

2. **Run with appropriate privileges**
   ```bash
   # For hardware access on Linux
   sudo usermod -a -G dialout $USER  # For serial ports
   sudo usermod -a -G input $USER    # For input devices
   ```

### Issue: Configuration File Errors

**Symptoms:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'config/settings.yaml'
yaml.parser.ParserError: while parsing
```

**Solutions:**
1. **Create missing configuration**
   ```bash
   # Check if config directory exists
   ls eeg_stimulus_project/config/
   
   # Create basic configuration if missing
   mkdir -p eeg_stimulus_project/config
   ```

2. **Fix YAML syntax errors**
   ```bash
   # Validate YAML syntax
   python -c "import yaml; yaml.safe_load(open('eeg_stimulus_project/config/settings.yaml'))"
   ```

---

## Network Communication Issues

### Issue: Host Cannot Start Server

**Symptoms:**
```
Host: Server error: [Errno 98] Address already in use
Host: Server error: [Errno 99] Cannot assign requested address
```

**Diagnosis:**
```bash
# Check if port 9999 is in use
netstat -tulpn | grep 9999
lsof -i :9999

# Check network interface status
ip addr show
ifconfig
```

**Solutions:**
1. **Port already in use**
   ```bash
   # Find and kill process using port 9999
   sudo netstat -tlpn | grep 9999
   sudo kill -9 [PID]
   
   # Or use different port (modify code)
   # Change PORT = 9999 to PORT = 9998 in main.py
   ```

2. **Network interface issues**
   ```bash
   # Restart network service (Linux)
   sudo systemctl restart networking
   
   # Check firewall settings
   sudo ufw status
   sudo ufw allow 9999/tcp
   ```

3. **Multiple host instances**
   ```bash
   # Check for running instances
   ps aux | grep "eeg_stimulus"
   
   # Kill all instances
   pkill -f "eeg_stimulus"
   ```

### Issue: Client Cannot Connect to Host

**Symptoms:**
```
Client: Connection error: [WinError 10060] Connection timeout
Client: Connection error: [Errno 111] Connection refused
Could not connect to host. Check IP and network.
```

**Diagnosis:**
```bash
# Test network connectivity
ping [HOST_IP]

# Test port accessibility
telnet [HOST_IP] 9999
nc -zv [HOST_IP] 9999

# Check routing
traceroute [HOST_IP]
```

**Solutions:**
1. **Verify host IP address**
   ```bash
   # Get correct IP address on host
   hostname -I          # Linux
   ipconfig | findstr "IPv4"  # Windows
   ```

2. **Firewall configuration**
   ```bash
   # Linux/Ubuntu firewall
   sudo ufw allow from [CLIENT_IP] to any port 9999
   
   # Windows: Allow app through Windows Defender Firewall
   # Control Panel > System and Security > Windows Defender Firewall
   ```

3. **Network troubleshooting**
   ```bash
   # Reset network stack (Windows)
   netsh winsock reset
   netsh int ip reset
   
   # Restart network services
   sudo systemctl restart NetworkManager  # Linux
   ```

### Issue: Connection Drops During Experiment

**Symptoms:**
```
Host: Listener crashed: [WinError 10054] Connection forcibly closed
Client disconnected.
Host: Listener crashed: [WinError 10053] Connection aborted
```

**Common Causes:**
- Network instability
- Power management settings
- Antivirus interference
- High CPU/memory usage

**Solutions:**
1. **Network stability**
   ```bash
   # Use ethernet instead of WiFi
   # Check cable connections
   
   # Monitor network quality
   ping -c 100 [HOST_IP]  # Check for packet loss
   ```

2. **Power management**
   ```bash
   # Disable USB power saving (Windows)
   # Device Manager > USB Root Hub > Power Management
   # Uncheck "Allow computer to turn off this device"
   ```

3. **Prioritize network traffic**
   ```bash
   # Set network adapter priority (Windows)
   # Network Connections > Advanced > Advanced Settings
   # Move Ethernet to top of list
   ```

---

## Hardware Connection Problems

### Issue: EEG System (EMOTIV/LabRecorder) Connection Failed

**Symptoms:**
```
Failed to start Actichamp: [WinError 2] The system cannot find the file specified
LabRecorder not connected
Failed to connect to LabRecorder
No EEG streams found
```

**Pre-flight Checklist:**
- [ ] EMOTIV Pro software running
- [ ] EEG headset connected and powered
- [ ] LabRecorder installed and configured
- [ ] Participant wearing headset properly
- [ ] Electrode impedances checked

**Solutions:**
1. **EMOTIV Pro Issues**
   ```bash
   # Check if EMOTIV Pro is running
   ps aux | grep -i emotiv     # Linux
   tasklist | findstr EMOTIV   # Windows
   ```
   - Restart EMOTIV Pro software
   - Check EEG headset connection
   - Verify electrode contact quality

2. **LabRecorder Connection**
   ```bash
   # Check if LabRecorder is listening
   netstat -an | grep 22345
   ```
   - Start LabRecorder manually
   - Configure LSL stream selection
   - Check port 22345 availability

3. **LSL Stream Issues**
   ```bash
   # Test LSL stream availability
   python -c "import pylsl; print(pylsl.resolve_streams())"
   ```
   - Restart LSL applications
   - Check LSL library installation
   - Verify stream names and types

**Advanced Diagnostics:**
```bash
# Check EEG data quality
# Run LSL viewer if available
# Monitor signal quality in EMOTIV Pro
```

### Issue: Eye Tracker Connection Failed

**Symptoms:**
```
Failed to connect to Eye Tracker
Eyetracker not connected in Control Window
Eye tracker connection failed
```

**Supported Systems:**
- Eyelink 1000 Plus
- Pupil Labs
- HTC VIVE Pro Eye

**Solutions:**
1. **Eyelink System**
   - Check USB/Ethernet connection
   - Verify Eyelink software is running
   - Run calibration sequence
   - Check participant positioning

2. **Pupil Labs System**
   ```bash
   # Check Pupil Labs service
   python -c "import pupil_labs_realtime_api; print('OK')"
   ```
   - Start Pupil Capture/Service
   - Verify camera connections
   - Check LSL streaming configuration

3. **HTC VIVE Pro Eye**
   - Check SteamVR status
   - Verify VIVE software installation
   - Test eye tracking in VIVE settings
   - Check headset fit and calibration

### Issue: Tactile System SSH Connection Failed

**Symptoms:**
```
Connected (version 2.0, client OpenSSH_9.2p1)
Authentication (publickey) failed.
Authentication (password) successful!
```

**Network Requirements:**
- SSH access to tactile control computer (10.115.12.225)
- Username and password authentication
- Python environment on remote system

**Solutions:**
1. **SSH Authentication**
   ```bash
   # Test manual SSH connection
   ssh username@10.115.12.225
   
   # Check SSH key configuration
   ssh-keygen -t rsa
   ssh-copy-id username@10.115.12.225
   ```

2. **Network connectivity**
   ```bash
   # Test network connection
   ping 10.115.12.225
   
   # Check SSH port (22)
   nc -zv 10.115.12.225 22
   ```

3. **Remote system setup**
   - Verify Python environment exists
   - Check tactile control script location
   - Test force sensor hardware
   - Verify baseline calibration

**Configuration Check:**
```yaml
# Verify settings in config/settings.yaml
network:
  tactile_system:
    host: "10.115.12.225"
    username: "your_username"
    password: "your_password"
```

---

## Data Collection Failures

### Issue: Data Not Saving

**Symptoms:**
```
No display_widget found for saving data.
FileNotFoundError: [Errno 2] No such file or directory
PermissionError: [Errno 13] Permission denied
```

**Diagnosis:**
```bash
# Check available disk space
df -h

# Check directory permissions
ls -la eeg_stimulus_project/saved_data/

# Check file system status
fsck /dev/[device]  # Linux only if unmounted
```

**Solutions:**
1. **Insufficient disk space**
   ```bash
   # Free up space
   # Move old data to external storage
   # Clean temporary files
   rm -rf /tmp/*
   ```

2. **Permission issues**
   ```bash
   # Fix directory permissions
   chmod -R 755 eeg_stimulus_project/saved_data/
   chown -R $USER eeg_stimulus_project/saved_data/
   ```

3. **Directory structure**
   ```bash
   # Recreate data directories
   mkdir -p eeg_stimulus_project/saved_data
   mkdir -p eeg_stimulus_project/saved_data/subject_test
   ```

### Issue: Data Synchronization Problems

**Symptoms:**
- Mismatched timestamps between data streams
- Missing event markers in data files
- Offset between behavioral and physiological data

**Solutions:**
1. **LSL synchronization**
   ```bash
   # Restart all LSL applications
   # Verify system clock synchronization
   ```

2. **Event marker issues**
   ```bash
   # Check LSL marker stream
   python -c "import pylsl; streams = pylsl.resolve_streams(); print([s.name() for s in streams])"
   ```

3. **Clock drift**
   - Use NTP time synchronization
   - Check system time settings
   - Verify LSL clock accuracy

### Issue: Corrupted Data Files

**Symptoms:**
- Incomplete CSV files
- Corrupted XDF files
- Missing data segments

**Recovery:**
1. **Check backup files**
   ```bash
   # Look for temporary or backup files
   find . -name "*.csv.bak" -o -name "*.xdf.tmp"
   ```

2. **Partial data recovery**
   ```bash
   # Check file integrity
   file [datafile.xdf]
   
   # Attempt partial recovery
   python -c "import pyxdf; data = pyxdf.load_xdf('file.xdf')"
   ```

---

## Software Crashes and Hangs

### Issue: Application Freeze/Hang

**Symptoms:**
- GUI becomes unresponsive
- Application stops responding to input
- High CPU usage with no progress

**Immediate Actions:**
1. **Check system resources**
   ```bash
   # Monitor resource usage
   top
   ps aux | grep python
   
   # Check memory usage
   free -h
   ```

2. **Identify hanging process**
   ```bash
   # Find unresponsive processes
   ps aux | grep -E "(eeg_stimulus|python.*main)"
   
   # Check for zombie processes
   ps aux | grep "<defunct>"
   ```

**Recovery:**
1. **Graceful termination attempt**
   ```bash
   # Send SIGTERM first
   kill [PID]
   
   # Wait 10 seconds, then force kill
   sleep 10
   kill -9 [PID]
   ```

2. **Clean restart**
   ```bash
   # Kill all related processes
   pkill -f "eeg_stimulus"
   
   # Clear shared memory
   ipcrm -a  # Use with caution
   ```

### Issue: Memory Leaks

**Symptoms:**
```
MemoryError
System becomes sluggish over time
Increasing RAM usage without corresponding workload
```

**Monitoring:**
```bash
# Monitor memory usage over time
watch -n 1 'ps aux | grep python | head -20'

# Check for memory leaks
valgrind --tool=memcheck python -m eeg_stimulus_project.main.main
```

**Solutions:**
1. **Restart application regularly**
   - For long experiments, schedule breaks
   - Restart between experiment blocks

2. **Resource cleanup**
   ```python
   # Add to application code
   import gc
   gc.collect()  # Force garbage collection
   ```

### Issue: Python/PyQt5 Crashes

**Symptoms:**
```
Segmentation fault (core dumped)
QWidget: Must construct a QApplication before a QWidget
Fatal Python error: Segmentation fault
```

**Solutions:**
1. **PyQt5 version conflicts**
   ```bash
   # Reinstall PyQt5
   pip uninstall PyQt5 PyQt5-tools
   pip install PyQt5==5.15.7
   ```

2. **Threading issues**
   - Check for Qt operations in non-main threads
   - Verify signal/slot connections
   - Use QTimer for periodic tasks

3. **System compatibility**
   ```bash
   # Check system compatibility
   ldd $(python -c "import PyQt5.QtCore; print(PyQt5.QtCore.__file__)")
   ```

---

## Configuration and Setup Issues

### Issue: Invalid Configuration Settings

**Symptoms:**
```
yaml.parser.ParserError: while parsing
KeyError: 'missing_config_key'
Configuration validation failed
```

**Solutions:**
1. **YAML syntax validation**
   ```bash
   # Check YAML syntax
   python -c "import yaml; yaml.safe_load(open('eeg_stimulus_project/config/settings.yaml'))"
   ```

2. **Reset to defaults**
   ```bash
   # Backup current config
   cp eeg_stimulus_project/config/settings.yaml settings.yaml.bak
   
   # Create minimal config
   cat > eeg_stimulus_project/config/settings.yaml << EOF
   experiment:
     default_settings: true
   network:
     host_port: 9999
   EOF
   ```

### Issue: Path and Directory Problems

**Symptoms:**
```
FileNotFoundError: No such file or directory
Invalid path configuration
Cannot access asset directory
```

**Solutions:**
1. **Verify all paths**
   ```bash
   # Check critical directories
   ls eeg_stimulus_project/assets/
   ls eeg_stimulus_project/saved_data/
   ls eeg_stimulus_project/config/
   ```

2. **Use absolute paths if needed**
   ```bash
   # Get absolute path
   realpath eeg_stimulus_project/
   ```

### Issue: Asset Loading Problems

**Symptoms:**
```
Cannot load image assets
Invalid image format
Asset directory not found
```

**Solutions:**
1. **Verify asset formats**
   ```bash
   # Check image formats
   file eeg_stimulus_project/assets/Images/*.jpg
   
   # List supported formats
   python -c "from PIL import Image; print(Image.registered_extensions())"
   ```

2. **Reset asset directories**
   ```bash
   # Restore default assets
   git checkout -- eeg_stimulus_project/assets/
   ```

---

## Performance Problems

### Issue: Slow Stimulus Presentation

**Symptoms:**
- Delayed visual stimuli
- Jerky or stuttering display
- High latency between trigger and display

**Diagnosis:**
```bash
# Check system performance
top
iostat -x 1

# Monitor GPU usage (if available)
nvidia-smi  # NVIDIA GPUs
```

**Solutions:**
1. **Display optimization**
   - Close unnecessary applications
   - Disable desktop effects
   - Set high-performance power mode

2. **Hardware acceleration**
   ```bash
   # Check OpenGL support
   glxinfo | grep -i opengl
   
   # Verify graphics drivers
   lspci | grep -i vga
   ```

3. **Process priority**
   ```bash
   # Run with higher priority
   nice -n -10 python -m eeg_stimulus_project.main.main
   ```

### Issue: Network Latency

**Symptoms:**
- Delayed communication between host/client
- Event markers out of sync
- Slow response to commands

**Solutions:**
1. **Network optimization**
   ```bash
   # Check network latency
   ping -c 100 [HOST_IP]
   
   # Use ethernet instead of WiFi
   # Check for network congestion
   ```

2. **Buffer optimization**
   - Increase network buffer sizes
   - Reduce network polling intervals
   - Optimize data packet sizes

---

## Diagnostic Tools and Procedures

### System Health Check Script

```bash
#!/bin/bash
# Save as: check_system_health.sh

echo "=== System Health Check ==="
echo "Date: $(date)"
echo

echo "--- Python Environment ---"
python --version
which python
echo

echo "--- Required Packages ---"
python -c "
try:
    import PyQt5; print('PyQt5: OK')
except: print('PyQt5: MISSING')
try:
    import pylsl; print('pylsl: OK')
except: print('pylsl: MISSING')
try:
    import numpy; print('numpy: OK')
except: print('numpy: MISSING')
"
echo

echo "--- System Resources ---"
echo "Memory:"
free -h
echo "Disk Space:"
df -h /
echo "CPU Load:"
uptime
echo

echo "--- Network Status ---"
echo "Network Interfaces:"
ip addr show | grep -E "(inet|UP|DOWN)"
echo "Port 9999 Status:"
netstat -tuln | grep 9999 || echo "Port 9999 not in use"
echo

echo "--- Process Check ---"
echo "EEG Stimulus Processes:"
ps aux | grep -E "(eeg_stimulus|main.py)" | grep -v grep || echo "No EEG processes running"
echo

echo "=== Health Check Complete ==="
```

### Log Analysis Tools

```bash
# Monitor logs in real-time
tail -f app.log

# Search for error patterns
grep -E "(ERROR|FAILED|Exception)" app.log

# Count connection events
grep -c "Connected" app.log
grep -c "disconnected" app.log

# Find performance issues
grep -E "(timeout|slow|lag|delay)" app.log
```

### Hardware Diagnostic Commands

```bash
# Check USB devices (for hardware)
lsusb

# Check serial ports
ls -la /dev/tty*

# Check audio devices
aplay -l
pacmd list-sources

# Check graphics
xrandr  # Linux display info
```

---

## Recovery and Prevention

### Automated Recovery Procedures

**Create a recovery script:**
```bash
#!/bin/bash
# Save as: emergency_recovery.sh

echo "Starting emergency recovery..."

# Stop all related processes
echo "Stopping processes..."
pkill -f "eeg_stimulus"
pkill -f "python.*main"

# Wait for cleanup
sleep 5

# Clear shared resources
echo "Cleaning shared resources..."
# Add any specific cleanup commands

# Check system state
echo "Checking system state..."
./check_system_health.sh

# Restart if needed
read -p "Restart application? (y/n): " restart
if [[ $restart == "y" ]]; then
    echo "Restarting application..."
    cd /path/to/project
    python -m eeg_stimulus_project.main.main
fi
```

### Prevention Strategies

1. **Regular System Maintenance**
   ```bash
   # Daily checks
   - Monitor disk space
   - Check log files for errors
   - Verify network connectivity
   - Test hardware connections
   
   # Weekly maintenance
   - Update system software
   - Clean temporary files
   - Backup critical data
   - Test recovery procedures
   ```

2. **Monitoring Setup**
   ```bash
   # Set up automated monitoring
   crontab -e
   
   # Add these lines:
   # Check disk space every hour
   0 * * * * df -h / | awk 'NR==2{if($5+0 > 85) print "Disk usage high: "$5}' | mail -s "Disk Alert" admin@example.com
   
   # Check processes every 15 minutes
   */15 * * * * pgrep -f "eeg_stimulus" > /dev/null || echo "EEG process not running" | mail -s "Process Alert" admin@example.com
   ```

3. **Backup Strategies**
   ```bash
   # Automated data backup
   rsync -av --progress eeg_stimulus_project/saved_data/ /backup/location/
   
   # Configuration backup
   tar -czf config_backup_$(date +%Y%m%d).tar.gz eeg_stimulus_project/config/
   ```

### Best Practices for Stable Operation

1. **Environment Preparation**
   - Use dedicated computers for data collection
   - Minimize running applications during experiments
   - Disable automatic updates during experiment periods
   - Use UPS (Uninterruptible Power Supply) for critical systems

2. **Network Stability**
   - Use wired ethernet connections when possible
   - Set up dedicated experiment network
   - Configure static IP addresses
   - Test network stability before each session

3. **Hardware Maintenance**
   - Regular calibration of all sensors
   - Check cable connections and wear
   - Monitor hardware temperatures
   - Keep firmware and drivers updated

4. **Software Hygiene**
   - Regular testing of all system components
   - Version control for configuration changes
   - Standardized installation procedures
   - Regular backup and recovery testing

---

## Emergency Contact Information

**During System Failures:**
1. **Technical Support**: [Add contact information]
2. **System Administrator**: [Add contact information]
3. **IT Help Desk**: [Add contact information]
4. **Research Supervisor**: [Add contact information]

**Hardware Vendor Support:**
- **EMOTIV Support**: [Contact information]
- **Eye Tracker Support**: [Contact information]
- **Network/IT Support**: [Contact information]

---

## Appendix: Common Error Codes

### Network Error Codes
- `10054`: Connection forcibly closed by remote host
- `10053`: Connection aborted by software
- `10060`: Connection timeout
- `10061`: Connection refused
- `111`: Connection refused (Linux)
- `98`: Address already in use (Linux)

### System Error Codes
- `ENOENT (2)`: No such file or directory
- `EACCES (13)`: Permission denied
- `EEXIST (17)`: File already exists
- `ENOSPC (28)`: No space left on device

### Application-Specific Messages
- `LabRecorder not connected`: EEG system not ready
- `Eyetracker not connected`: Eye tracking system not ready
- `Client disconnected`: Network communication lost
- `Authentication failed`: SSH credentials incorrect

---

**Document Version**: 1.0  
**Last Updated**: [Current Date]  
**Maintained By**: System Development Team  
**Review Schedule**: After each major incident or monthly

This troubleshooting guide should be updated based on new failure modes discovered during system operation. Please report any new issues or solutions to the development team for inclusion in future versions.