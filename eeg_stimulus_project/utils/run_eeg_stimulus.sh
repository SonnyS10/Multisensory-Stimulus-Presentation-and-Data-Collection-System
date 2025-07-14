#!/bin/bash

# EEG Stimulus Project Launcher
# This script launches the EEG Stimulus Project on Linux/Mac
# Usage: ./run_eeg_stimulus.sh

# Get the directory containing this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Navigate to the project root (two levels up from utils directory)
cd "$SCRIPT_DIR/../.."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed or not in PATH"
    exit 1
fi

# Launch the application
python3 -m eeg_stimulus_project.main.main

# Keep the terminal open if there are any errors
echo "Press Enter to exit..."
read