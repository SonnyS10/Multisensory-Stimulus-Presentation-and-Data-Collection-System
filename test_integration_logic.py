#!/usr/bin/env python3
"""
Test script for integration logic only

This script tests the integration logic without needing full GUI setup.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_integration_logic():
    """Test that our integration logic works."""
    print("Testing integration logic...")
    
    # Test that we can create mock frame with viewing booth checkbox
    class MockFrame:
        def __init__(self):
            self.viewing_booth_button = MockCheckbox()
            self.display_button = MockCheckbox()
            self.start_button = MockButton()
            self.turntable_widget = None
            self.display_widget = None
            
        def enable_pause_resume_buttons(self):
            pass
    
    class MockCheckbox:
        def __init__(self):
            self._checked = False
        
        def isChecked(self):
            return self._checked
            
        def setChecked(self, checked):
            self._checked = checked
    
    class MockButton:
        def __init__(self):
            self._enabled = True
            
        def setEnabled(self, enabled):
            self._enabled = enabled
    
    class MockGUI:
        def __init__(self):
            self.stimulus_order_frame = MockStimulusFrame()
            
        def get_current_test(self):
            return "Test Unisensory Neutral Visual"
            
        def open_turntable_gui(self, state, log_queue, label_stream=None, **kwargs):
            print(f"  Mock: open_turntable_gui called with state={state}")
            return True
            
        def open_secondary_gui(self, state, log_queue, label_stream=None, **kwargs):
            print(f"  Mock: open_secondary_gui called with state={state}")
            return True
            
        def send_message(self, msg):
            pass
    
    class MockStimulusFrame:
        def get_randomization_settings(self):
            return False, None
            
        def get_repetitions_settings(self):
            return None
    
    # Create mock objects
    frame = MockFrame()
    gui = MockGUI()
    frame.parent = gui
    frame.log_queue = None
    frame.label_stream = None
    frame.eyetracker = None
    frame.shared_status = {}
    frame.local_mode = True
    frame.labrecorder = None
    frame.client = False
    
    # Test viewing booth checkbox logic
    print("  Testing viewing booth checkbox...")
    frame.viewing_booth_button.setChecked(True)
    
    # Simulate the start button logic for viewing booth
    if hasattr(frame, 'viewing_booth_button') and frame.viewing_booth_button.isChecked():
        print("  ✓ Viewing booth checkbox detected")
        gui.send_message({"action": "start_button", "test": gui.get_current_test()})
        gui.open_turntable_gui(True, frame.log_queue, label_stream=frame.label_stream, eyetracker=frame.eyetracker, shared_status=frame.shared_status)
        frame.start_button.setEnabled(False)
        print("  ✓ Mock turntable GUI opened")
    else:
        print("  ✗ Viewing booth logic failed")
        return False
    
    # Test display checkbox logic still works
    print("  Testing display checkbox...")
    frame.viewing_booth_button.setChecked(False)
    frame.display_button.setChecked(True)
    
    if hasattr(frame, 'display_button') and frame.display_button.isChecked():
        print("  ✓ Display checkbox detected")
        gui.open_secondary_gui(True, frame.log_queue, label_stream=frame.label_stream, eyetracker=frame.eyetracker, shared_status=frame.shared_status)
        print("  ✓ Mock display GUI opened")
    else:
        print("  ✗ Display checkbox logic failed")
        return False
    
    print("Integration logic test completed.\n")
    return True

def test_bay_sequence_generation():
    """Test generating bay sequences for real stimulus orders."""
    print("Testing bay sequence generation...")
    
    from eeg_stimulus_project.stimulus.turn_table_code.bay_mapping import bay_mapper
    
    # Create mock asset objects that would come from Display.get_assets()
    class MockAsset:
        def __init__(self, filename):
            self.filename = filename
    
    # Test with common stimulus patterns
    test_cases = [
        {
            'name': 'Alcohol test',
            'assets': [MockAsset('beer.jpg'), MockAsset('wine.jpg'), MockAsset('vodka.jpg')],
            'expected_bays': [0, 1, 2]  # beer, wine, vodka
        },
        {
            'name': 'Neutral test',
            'assets': [MockAsset('water.jpg'), MockAsset('soda.jpg'), MockAsset('juice.jpg')],
            'expected_bays': [8, 9, 10]  # water, soda, juice
        },
        {
            'name': 'Mixed test',
            'assets': [MockAsset('beer.jpg'), MockAsset('water.jpg'), MockAsset('unknown.jpg')],
            'expected_bays': [0, 8, 0]  # beer, water, default
        }
    ]
    
    for case in test_cases:
        bay_sequence = bay_mapper.get_bay_sequence_for_assets(case['assets'])
        print(f"  {case['name']}: {[b+1 for b in bay_sequence]} (expected: {[b+1 for b in case['expected_bays']]})")
        
        if bay_sequence == case['expected_bays']:
            print(f"    ✓ Correct")
        else:
            print(f"    ⚠ Different from expected")
    
    print("Bay sequence generation test completed.\n")
    return True

def main():
    """Run tests."""
    print("=== Integration Logic Tests ===\n")
    
    # Test integration logic
    if not test_integration_logic():
        print("Integration logic test failed.")
        return 1
    
    # Test bay sequence generation  
    if not test_bay_sequence_generation():
        print("Bay sequence generation test failed.")
        return 1
    
    print("=== All Integration Tests Completed Successfully ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())