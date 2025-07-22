@echo off
REM EEG Stimulus Project Launcher - Universal Version

echo ========================================
echo EEG Stimulus Project Launcher
echo ========================================

REM Get the directory containing this batch file
set "SCRIPT_DIR=%~dp0"
echo Script directory: %SCRIPT_DIR%

REM Navigate to the project root (go up from utils to project root)
cd /d "%SCRIPT_DIR%\.."
echo Current directory: %CD%

REM Check if the main module exists (corrected path)
if exist "main\main.py" (
    echo [OK] Found main.py file at: %CD%\main\main.py
) else (
    echo [ERROR] main.py not found in expected location!
    echo Expected: %CD%\main\main.py
    pause
    exit /b 1
)

echo.
echo Detecting Python environments...

REM Try to find Python executable
set "PYTHON_EXE="
set "CURRENT_ENV=base"

REM Check if conda is available
where conda >nul 2>&1
if not errorlevel 1 (
    echo [OK] Found conda installation
    
    REM Get current environment name from conda info --envs
    for /f "tokens=1,* delims= " %%i in ('conda info --envs 2^>nul ^| findstr /C:"*"') do (
        set "CURRENT_ENV=%%i"
    )
    REM Now CURRENT_ENV is set

    echo Current conda environment: %CURRENT_ENV%
    echo.
    echo Available conda environments:
    conda info --envs 2>nul
    echo.
    
    REM Ask user which environment to use
    echo Environment options:
    echo 1. Use current environment (%CURRENT_ENV%)
    echo 2. Use Research environment (if available)
    echo 3. Use base environment
    echo 4. Choose specific environment
    echo 5. Use system Python (no conda)
    echo.
    set /p "ENV_CHOICE=Enter your choice (1-5): "
    
    if "%ENV_CHOICE%"=="1" (
        echo Using current environment: %CURRENT_ENV%
        set "PYTHON_EXE=python"
        goto :found_python
    )
    
    if "%ENV_CHOICE%"=="2" (
        echo Activating Research environment...
        call conda activate Research 2>nul
        if not errorlevel 1 (
            echo [OK] Activated Research environment
            set "PYTHON_EXE=python"
            goto :found_python
        ) else (
            echo [WARNING] Failed to activate Research environment
            echo Falling back to current environment
            set "PYTHON_EXE=python"
            goto :found_python
        )
    )
    
    if "%ENV_CHOICE%"=="3" (
        echo Activating base environment...
        call conda activate base 2>nul
        if not errorlevel 1 (
            echo [OK] Activated base environment
            set "PYTHON_EXE=python"
            goto :found_python
        ) else (
            echo [WARNING] Failed to activate base environment
            set "PYTHON_EXE=python"
            goto :found_python
        )
    )
    
    if "%ENV_CHOICE%"=="4" (
        echo.
        set /p "CUSTOM_ENV=Enter environment name: "
        echo Activating %CUSTOM_ENV% environment...
        call conda activate %CUSTOM_ENV% 2>nul
        if not errorlevel 1 (
            echo [OK] Activated %CUSTOM_ENV% environment
            set "PYTHON_EXE=python"
            goto :found_python
        ) else (
            echo [ERROR] Failed to activate %CUSTOM_ENV% environment
            echo Available environments:
            conda info --envs
            pause
            exit /b 1
        )
    )
    
    if "%ENV_CHOICE%"=="5" (
        echo Using system Python...
        goto :find_system_python
    )
    
    REM Default to current environment if invalid choice
    echo Invalid choice, using current environment: %CURRENT_ENV%
    set "PYTHON_EXE=python"
    goto :found_python
) else (
    echo [INFO] Conda not found, searching for system Python...
    goto :find_system_python
)

:find_system_python
echo Searching for system Python...

REM Method 1: Try python from PATH
echo [1/4] Checking python in PATH...
python --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_EXE=python"
    echo [OK] Found Python in PATH
    goto :found_python
)

REM Method 2: Try pythonw from PATH  
echo [2/4] Checking pythonw in PATH...
pythonw --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_EXE=pythonw"
    echo [OK] Found Pythonw in PATH
    goto :found_python
)

REM Method 3: Try common Anaconda locations
echo [3/4] Checking common Anaconda locations...
if exist "%USERPROFILE%\anaconda3\python.exe" (
    set "PYTHON_EXE=%USERPROFILE%\anaconda3\python.exe"
    echo [OK] Found Python at: %USERPROFILE%\anaconda3\python.exe
    goto :found_python
)

if exist "%LOCALAPPDATA%\anaconda3\python.exe" (
    set "PYTHON_EXE=%LOCALAPPDATA%\anaconda3\python.exe"
    echo [OK] Found Python at: %LOCALAPPDATA%\anaconda3\python.exe
    goto :found_python
)

if exist "C:\ProgramData\anaconda3\python.exe" (
    set "PYTHON_EXE=C:\ProgramData\anaconda3\python.exe"
    echo [OK] Found Python at: C:\ProgramData\anaconda3\python.exe
    goto :found_python
)

REM Method 4: Try Windows Store Python
echo [4/4] Checking Windows Store Python...
if exist "%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe" (
    set "PYTHON_EXE=%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe"
    echo [OK] Found Python at: %LOCALAPPDATA%\Microsoft\WindowsApps\python.exe
    goto :found_python
)

REM If no Python found
echo [ERROR] Could not find Python executable!
echo.
echo Please install Python from one of these sources:
echo 1. https://www.python.org/downloads/
echo 2. https://www.anaconda.com/products/distribution
echo 3. Microsoft Store (search for "Python")
echo.
pause
exit /b 1

:found_python
echo.
echo Testing Python installation...
"%PYTHON_EXE%" --version
if errorlevel 1 (
    echo [ERROR] Python found but not working properly
    pause
    exit /b 1
)

REM Show current environment info
echo.
echo Environment Information:
if defined CONDA_DEFAULT_ENV (
    echo Active conda environment: %CONDA_DEFAULT_ENV%
) else (
    echo Using system Python (no conda environment active)
)
"%PYTHON_EXE%" -c "import sys; print('Python executable:', sys.executable)"

echo.
echo Checking for required packages...
echo Testing PyQt5...
"%PYTHON_EXE%" -c "import PyQt5; print('PyQt5 version:', PyQt5.QtCore.QT_VERSION_STR)" 2>nul
if errorlevel 1 (
    echo [WARNING] PyQt5 not found. Installing required packages...
    echo.
    echo Installing PyQt5 and other dependencies...
    "%PYTHON_EXE%" -m pip install PyQt5 pillow numpy matplotlib openpyxl pylsl pyyaml
    if errorlevel 1 (
        echo [ERROR] Failed to install required packages
        echo Please run this command manually:
        echo "%PYTHON_EXE%" -m pip install PyQt5 pillow numpy matplotlib openpyxl pylsl pyyaml
        pause
        exit /b 1
    )
    echo [OK] Packages installed successfully
) else (
    echo [OK] PyQt5 is available
    echo [INFO] Ensuring all packages are installed...
    "%PYTHON_EXE%" -m pip install PyQt5 pillow numpy matplotlib openpyxl pylsl pyyaml --quiet --upgrade
)

echo Testing yaml...
"%PYTHON_EXE%" -c "import yaml; print('yaml is available')" 2>nul
if errorlevel 1 (
    echo [WARNING] yaml not found. Installing required packages...
    echo.
    echo Installing missing dependencies...
    "%PYTHON_EXE%" -m pip install PyQt5 pillow numpy matplotlib openpyxl pylsl pyyaml
    if errorlevel 1 (
        echo [ERROR] Failed to install required packages
        echo Please run this command manually:
        echo "%PYTHON_EXE%" -m pip install PyQt5 pillow numpy matplotlib openpyxl pylsl pyyaml
        pause
        exit /b 1
    )
    echo [OK] Packages installed successfully
) else (
    echo [OK] yaml is available
)

echo.
REM ==============================
REM Check for all required packages
REM ==============================

set PACKAGES=PyQt5 pillow numpy matplotlib openpyxl pylsl pyyaml pandas pupil-labs-realtime-api

echo Checking for required Python packages...
for %%P in (%PACKAGES%) do (
    "%PYTHON_EXE%" -c "import %%P" 2>nul
    if errorlevel 1 (
        echo [WARNING] Package %%P not found. Installing...
        "%PYTHON_EXE%" -m pip install %%P
        if errorlevel 1 (
            echo [ERROR] Failed to install package %%P
            pause
            exit /b 1
        )
    ) else (
        echo [OK] Package %%P is available
    )
)
echo.

echo.
echo ========================================
echo Launching EEG Stimulus Application...
echo Using Python: %PYTHON_EXE%
echo ========================================
echo.

REM Launch the application (corrected module path)
"%PYTHON_EXE%" main\main.py

REM Check if launch was successful
if errorlevel 1 (
    echo.
    echo ========================================
    echo [ERROR] Application failed to start
    echo ========================================
    echo.
    echo Troubleshooting tips:
    echo 1. Try installing packages manually:
    echo    "%PYTHON_EXE%" -m pip install PyQt5 pillow numpy matplotlib openpyxl pylsl pyyaml
    echo 2. Check that you're in the correct directory
    echo 3. Run this command manually to see the error:
    echo    "%PYTHON_EXE%" -m main.main
    echo 4. Try a different conda environment
    echo.
) else (
    echo.
    echo [OK] Application started successfully
)

echo.
pause