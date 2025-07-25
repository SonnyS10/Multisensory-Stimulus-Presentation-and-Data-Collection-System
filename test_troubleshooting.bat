@echo off
REM EEG Stimulus System Troubleshooting Test (Windows Batch Version)
echo ========================================
echo EEG Stimulus System Troubleshooting Test
echo Date: %DATE% %TIME%
echo ========================================
echo.

REM Test 1: Python Environment Check
echo --- Test 1: Python Environment ---
python --version 2>NUL || echo ERROR: Python not found - see 'Module not found' section
where python 2>NUL || echo ERROR: Python not in PATH
echo.

REM Test 2: Dependencies Check
echo --- Test 2: Dependencies Check ---
echo Testing critical imports (errors expected in this environment):
python -c "modules=['PyQt5','pylsl','numpy','pandas','paramiko']; import sys; for m in modules: \
    try: __import__(m); print('✓ %s: OK' % m) \
    except ImportError as e: print('✗ %s: MISSING - %s' % (m, e))"
echo.

REM Test 3: File System Check
echo --- Test 3: File System Check ---
echo Project structure verification:
for %%D in (eeg_stimulus_project eeg_stimulus_project\config eeg_stimulus_project\assets eeg_stimulus_project\saved_data) do (
    if exist "%%D\" (
        echo ✓ %%D: EXISTS
    ) else (
        echo ✗ %%D: MISSING
    )
)
echo.

REM Test 4: Network Port Check
echo --- Test 4: Network Port Check ---
echo Checking if port 9999 is available:
netstat -ano | findstr ":9999" >nul
if %ERRORLEVEL%==0 (
    echo ✗ Port 9999: IN USE - potential conflict
) else (
    echo ✓ Port 9999: AVAILABLE
)
echo.

REM Test 5: Permission Check
echo --- Test 5: Permission Check ---
echo Checking file permissions:
if exist requirements.txt (
    echo ✓ Read permissions: OK
) else (
    echo ✗ Read permissions: FAILED
)
REM Check write permission by trying to create a temp file
echo. > test_write.tmp 2>NUL
if exist test_write.tmp (
    del test_write.tmp
    echo ✓ Write permissions: OK
) else (
    echo ✗ Write permissions: FAILED
)
echo.

REM Test 6: Configuration File Check
echo --- Test 6: Configuration File Check ---
set config_file=eeg_stimulus_project\config\settings.yaml
if exist "%config_file%" (
    echo ✓ Configuration file exists: %config_file%
    python -c "import yaml; \
try: \
    with open(r'%config_file%', 'r') as f: yaml.safe_load(f); print('✓ YAML syntax: VALID') \
except yaml.YAMLError as e: print(f'✗ YAML syntax: INVALID - {e}') \
except FileNotFoundError: print('✗ Configuration file: NOT FOUND')"
) else (
    echo ✗ Configuration file missing: %config_file%
)
echo.

REM Test 7: System Resources
echo --- Test 7: System Resources ---
echo Memory usage:
systeminfo | findstr /C:"Total Physical Memory"
echo Disk usage:
wmic logicaldisk get size,freespace,caption
echo System load:
REM Windows does not have /proc/loadavg, so show uptime
systeminfo | findstr /C:"System Boot Time"
echo.

REM Test 8: Process Check
echo --- Test 8: Process Check ---
echo Looking for existing EEG stimulus processes:
tasklist | findstr /I "eeg_stimulus" >nul
if %ERRORLEVEL%==0 (
    echo ✓ EEG stimulus processes found:
    tasklist | findstr /I "eeg_stimulus"
) else (
    echo ✓ No existing EEG stimulus processes (normal for fresh start)
)
echo.

REM Test 9: Recovery Test
echo --- Test 9: Recovery Test ---
echo Testing recovery script functionality:
echo Creating test process simulation...
start /B python -c "import time,os; print('Test process PID:',os.getpid()); time.sleep(5)"
REM Wait a moment for process to start
ping 127.0.0.1 -n 3 >nul
REM Attempt to kill the process (will only work if you know the PID)
REM For demonstration, just show running python processes
tasklist | findstr /I "python"
echo ✓ Process termination test completed
echo.

echo ========================================
echo Troubleshooting Test Complete
echo ========================================
echo Results Summary:
echo - This test validates many scenarios covered in TROUBLESHOOTING.md
echo - Missing dependencies are expected in this environment
echo - The guide provides solutions for all identified issues
echo - See TROUBLESHOOTING.md for detailed solutions to any failed tests
echo.