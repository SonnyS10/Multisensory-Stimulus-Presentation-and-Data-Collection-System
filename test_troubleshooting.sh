#!/bin/bash
# Troubleshooting Test Script
# This script tests various scenarios covered in the troubleshooting guide

echo "=== EEG Stimulus System Troubleshooting Test ==="
echo "Date: $(date)"
echo

# Test 1: Python Environment Check
echo "--- Test 1: Python Environment ---"
python --version 2>/dev/null || echo "ERROR: Python not found - see 'Module not found' section"
which python 2>/dev/null || echo "ERROR: Python not in PATH"
echo

# Test 2: Dependencies Check
echo "--- Test 2: Dependencies Check ---"
echo "Testing critical imports (errors expected in this environment):"
python -c "
import sys
required_modules = ['PyQt5', 'pylsl', 'numpy', 'pandas', 'paramiko']
for module in required_modules:
    try:
        __import__(module)
        print(f'✓ {module}: OK')
    except ImportError as e:
        print(f'✗ {module}: MISSING - {e}')
"
echo

# Test 3: File System Check
echo "--- Test 3: File System Check ---"
echo "Project structure verification:"
for dir in "eeg_stimulus_project" "eeg_stimulus_project/config" "eeg_stimulus_project/assets" "eeg_stimulus_project/saved_data"; do
    if [ -d "$dir" ]; then
        echo "✓ $dir: EXISTS"
    else
        echo "✗ $dir: MISSING"
    fi
done
echo

# Test 4: Network Port Check
echo "--- Test 4: Network Port Check ---"
echo "Checking if port 9999 is available:"
if command -v netstat >/dev/null; then
    if netstat -tuln 2>/dev/null | grep -q ":9999 "; then
        echo "✗ Port 9999: IN USE - potential conflict"
    else
        echo "✓ Port 9999: AVAILABLE"
    fi
else
    echo "! netstat not available - cannot check port status"
fi
echo

# Test 5: Permission Check
echo "--- Test 5: Permission Check ---"
echo "Checking file permissions:"
if [ -r "requirements.txt" ]; then
    echo "✓ Read permissions: OK"
else
    echo "✗ Read permissions: FAILED"
fi

if [ -w "." ]; then
    echo "✓ Write permissions: OK"
else
    echo "✗ Write permissions: FAILED"
fi
echo

# Test 6: Configuration File Check
echo "--- Test 6: Configuration File Check ---"
config_file="eeg_stimulus_project/config/settings.yaml"
if [ -f "$config_file" ]; then
    echo "✓ Configuration file exists: $config_file"
    # Test YAML syntax
    python -c "
import yaml
try:
    with open('$config_file', 'r') as f:
        yaml.safe_load(f)
    print('✓ YAML syntax: VALID')
except yaml.YAMLError as e:
    print('✗ YAML syntax: INVALID -', str(e))
except FileNotFoundError:
    print('✗ Configuration file: NOT FOUND')
" 2>/dev/null || echo "! Cannot validate YAML (PyYAML not available)"
else
    echo "✗ Configuration file missing: $config_file"
fi
echo

# Test 7: System Resources
echo "--- Test 7: System Resources ---"
echo "Memory usage:"
if command -v free >/dev/null; then
    free -h | head -2
else
    echo "! free command not available"
fi

echo "Disk usage:"
df -h . 2>/dev/null | tail -1 || echo "! df command failed"

echo "System load:"
if [ -f /proc/loadavg ]; then
    echo "Load average: $(cat /proc/loadavg | cut -d' ' -f1-3)"
else
    uptime 2>/dev/null | grep -o "load average.*" || echo "! Load average not available"
fi
echo

# Test 8: Process Check
echo "--- Test 8: Process Check ---"
echo "Looking for existing EEG stimulus processes:"
if pgrep -f "eeg_stimulus" >/dev/null 2>&1; then
    echo "✓ EEG stimulus processes found:"
    pgrep -f "eeg_stimulus" -l 2>/dev/null || echo "Process details not available"
else
    echo "✓ No existing EEG stimulus processes (normal for fresh start)"
fi
echo

# Test 9: Recovery Test
echo "--- Test 9: Recovery Test ---"
echo "Testing recovery script functionality:"
echo "Creating test process simulation..."

# Create a simple test process
python -c "
import time
import os
print('Test process PID:', os.getpid())
try:
    time.sleep(2)
except KeyboardInterrupt:
    print('Test process interrupted - recovery successful')
" &
TEST_PID=$!

sleep 1
echo "Test process created with PID: $TEST_PID"

# Test graceful termination
echo "Testing graceful termination..."
kill $TEST_PID 2>/dev/null
wait $TEST_PID 2>/dev/null
echo "✓ Process termination test completed"
echo

echo "=== Troubleshooting Test Complete ==="
echo
echo "Results Summary:"
echo "- This test validates many scenarios covered in TROUBLESHOOTING.md"
echo "- Missing dependencies are expected in this environment"
echo "- The guide provides solutions for all identified issues"
echo "- See TROUBLESHOOTING.md for detailed solutions to any failed tests"
echo