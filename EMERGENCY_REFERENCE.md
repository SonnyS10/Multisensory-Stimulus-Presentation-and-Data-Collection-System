# 🆘 Emergency Quick Reference Card

**Print this page and keep it accessible during experiments**

## 🚨 IMMEDIATE EMERGENCY ACTIONS

### Participant Distress/Emergency
1. **STOP STIMULI**: Uncheck "Start Display" or press Ctrl+Alt+Q
2. **Remove hardware**: VR headset, tactile devices
3. **Participant safety**: Check wellbeing, follow institutional procedures
4. **Document**: Note time and circumstances

### Complete System Failure
1. **Participant first**: Ensure safety, remove stimulation
2. **Preserve data**: Don't force-close, let auto-save complete
3. **Note time**: Record exact failure time for data recovery
4. **Alert team**: Use backup communication if needed

## 🔧 QUICK DIAGNOSTIC COMMANDS

### Check System Status
```bash
# Run system health check
./test_troubleshooting.sh

# Check processes
ps aux | grep eeg_stimulus

# Check memory and disk
free -h && df -h

# Check network
ping [HOST_IP]
netstat -tuln | grep 9999
```

### Emergency Recovery
```bash
# Stop all processes
pkill -f "eeg_stimulus"

# Clean restart
cd /path/to/project
python -m eeg_stimulus_project.main.main
```

## 🌐 NETWORK ISSUES

### Host Cannot Start
- **Port busy**: `netstat -tuln | grep 9999` then `kill [PID]`
- **Firewall**: `sudo ufw allow 9999/tcp`

### Client Cannot Connect  
- **Check IP**: Get host IP with `hostname -I`
- **Test connection**: `ping [HOST_IP]` and `telnet [HOST_IP] 9999`
- **Firewall**: Allow app through Windows Defender

### Connection Drops
- **Switch to ethernet** from WiFi
- **Check cables** and power management settings

## 🖥️ HARDWARE ISSUES

### EEG (EMOTIV/LabRecorder)
1. **Check EMOTIV Pro**: Must be running with good signals
2. **Restart LabRecorder**: Close and reopen application
3. **Verify port**: `netstat -an | grep 22345`
4. **Check electrodes**: Impedance and contact quality

### Eye Tracker
1. **Restart software**: Eyelink/Pupil Labs applications
2. **Recalibrate**: Run calibration sequence
3. **Check positioning**: Participant head position and distance

### Tactile System
1. **Test SSH**: `ssh username@10.115.12.225`
2. **Check network**: `ping 10.115.12.225`
3. **Verify credentials**: Username/password in config

## 💾 DATA ISSUES

### Data Not Saving
```bash
# Check disk space
df -h

# Check permissions
ls -la eeg_stimulus_project/saved_data/

# Fix permissions
chmod -R 755 eeg_stimulus_project/saved_data/
```

### Missing Data Files
```bash
# Look for backups
find . -name "*.csv.bak" -o -name "*.xdf.tmp"

# Check data directory
ls -la eeg_stimulus_project/saved_data/subject_*/
```

## 🐛 SOFTWARE CRASHES

### Application Freeze
```bash
# Check resources
top

# Find process ID
ps aux | grep python

# Graceful kill
kill [PID]

# Force kill if needed
kill -9 [PID]
```

### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Check virtual environment
which python
```

## 📞 EMERGENCY CONTACTS

**During Failures:**
- Technical Support: ________________
- System Administrator: ________________  
- Research Supervisor: ________________
- IT Help Desk: ________________

**Hardware Support:**
- EMOTIV Support: ________________
- Eye Tracker Support: ________________
- Network/IT: ________________

## 📋 INCIDENT DOCUMENTATION

**Record for every incident:**
- [ ] Date and time of failure
- [ ] What was happening when it failed
- [ ] Error messages (exact text)
- [ ] Which systems were affected
- [ ] Steps taken to recover
- [ ] Data status (saved/lost/partial)
- [ ] Participant impact

## 📖 DETAILED HELP

**For complete troubleshooting procedures:**
- **Main Guide**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Setup Help**: [GETTING_STARTED.md](GETTING_STARTED.md)  
- **Technical Details**: [DEVELOPER_DOCUMENTATION.md](DEVELOPER_DOCUMENTATION.md)
- **Application Logs**: Check `app.log` file in project directory

---
**Last Updated**: [Current Date] | **Version**: 1.0  
**Keep this reference accessible during all experimental sessions**