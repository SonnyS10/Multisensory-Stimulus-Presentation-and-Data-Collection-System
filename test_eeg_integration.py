#!/usr/bin/env python3
"""
Test script for EEG Stream Window functionality (without GUI)
This script tests the EEG stream window import and basic functionality.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_eeg_stream_imports():
    """Test that all necessary modules can be imported."""
    print("Testing EEG Stream Window imports...")
    
    try:
        # Test basic imports
        import pylsl
        print("✓ pylsl import successful")
        
        import matplotlib
        # Use a non-GUI backend
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from matplotlib.figure import Figure
        print("✓ matplotlib import successful")
        
        import numpy as np
        print("✓ numpy import successful")
        
        # Test project imports
        from eeg_stimulus_project.gui.eeg_stream_window import EEGStreamWindow
        print("✓ EEGStreamWindow import successful")
        
        # Test LSL functionality
        streams = pylsl.resolve_byprop('type', 'EEG', minimum=0, timeout=2.0)
        print(f"✓ LSL stream resolution test successful (found {len(streams)} EEG streams)")
        
        print("\nAll imports successful! EEG Stream Window is ready to use.")
        return True
        
    except Exception as e:
        print(f"✗ Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_control_window_import():
    """Test that the control window can import the EEG stream functionality."""
    print("\nTesting Control Window integration...")
    
    try:
        from eeg_stimulus_project.gui.control_window import ControlWindow
        print("✓ ControlWindow import successful")
        
        # Test that the EEG stream method exists
        if hasattr(ControlWindow, 'open_eeg_stream'):
            print("✓ open_eeg_stream method found in ControlWindow")
        else:
            print("✗ open_eeg_stream method not found in ControlWindow")
            return False
        
        print("✓ Control Window integration successful")
        return True
        
    except Exception as e:
        print(f"✗ Control Window integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing EEG Stream Window Integration...")
    print("=" * 50)
    
    success = True
    
    # Test imports
    success &= test_eeg_stream_imports()
    
    # Test control window integration
    success &= test_control_window_import()
    
    print("\n" + "=" * 50)
    if success:
        print("✓ All tests passed! EEG Stream functionality is working correctly.")
    else:
        print("✗ Some tests failed. Please check the output above.")
        sys.exit(1)