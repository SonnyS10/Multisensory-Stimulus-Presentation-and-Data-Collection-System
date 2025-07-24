#!/usr/bin/env python3
"""
Test script for main GUI functionality

This script tests if the main GUI can start with turntable integration.
"""

import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import QApplication

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_main_gui_import():
    """Test if main GUI can be imported."""
    print("Testing main GUI import...")
    
    try:
        # Test if we can import the GUI classes
        from eeg_stimulus_project.gui.main_gui import GUI, Frame
        print("  ✓ main_gui imported successfully")
        return True
    except ImportError as e:
        print(f"  ✗ main_gui import failed: {e}")
        return False

def test_gui_creation():
    """Test creating a GUI instance."""
    print("Testing GUI creation...")
    
    try:
        from eeg_stimulus_project.gui.main_gui import GUI
        
        app = QApplication(sys.argv)
        
        # Create GUI instance with minimal parameters
        gui = GUI(
            connection=None,
            shared_status={},
            log_queue=None,
            base_dir="/tmp",
            test_number=1,
            client=False,
            local_mode=True
        )
        
        print("  ✓ GUI instance created successfully")
        
        # Test if viewing booth checkbox exists
        frame = gui.unisensory_neutral_visual
        if hasattr(frame, 'viewing_booth_button'):
            print("  ✓ Viewing booth checkbox found")
        else:
            print("  ⚠ Viewing booth checkbox not found")
        
        gui.close()
        app.quit()
        return True
        
    except Exception as e:
        print(f"  ✗ GUI creation failed: {e}")
        return False

def main():
    """Run tests."""
    print("=== Main GUI Integration Tests ===\n")
    
    # Test imports
    if not test_main_gui_import():
        print("Cannot continue due to import failures.")
        return 1
    
    # Test GUI creation
    if not test_gui_creation():
        print("Cannot continue due to GUI creation failures.")
        return 1
    
    print("\n=== GUI Tests Completed Successfully ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())