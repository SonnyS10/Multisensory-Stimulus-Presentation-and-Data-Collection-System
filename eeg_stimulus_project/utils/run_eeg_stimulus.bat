@echo off
REM EEG Stimulus Project Launcher
REM This batch file launches the EEG Stimulus Project
REM Usage: run_eeg_stimulus.bat

REM Get the directory containing this batch file
set "SCRIPT_DIR=%~dp0"

REM Navigate to the project root (two levels up from utils directory)
cd /d "%SCRIPT_DIR%\..\.."

REM Launch the application
pythonw -m eeg_stimulus_project.main.main

REM Keep the window open if there are any errors
pause