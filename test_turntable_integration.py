#!/usr/bin/env python3
"""
Test script for turntable integration

This script tests the basic functionality of the turntable integration
without requiring full hardware setup.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_bay_mapping():
    """Test the bay mapping functionality."""
    print("Testing bay mapping...")
    
    from eeg_stimulus_project.stimulus.turn_table_code.bay_mapping import bay_mapper
    
    # Test object mapping
    test_objects = ['beer.jpg', 'wine.png', 'water.jpg', 'unknown_object.jpg']
    
    for obj in test_objects:
        bay = bay_mapper.get_bay_for_object(obj)
        print(f"  {obj} -> Bay {bay + 1 if bay is not None else 'None'}")
    
    # Test custom mapping
    bay_mapper.set_custom_mapping('test_object', 5)
    bay = bay_mapper.get_bay_for_object('test_object')
    print(f"  test_object (custom) -> Bay {bay + 1}")
    
    print("Bay mapping test completed.\n")

def test_import_structure():
    """Test that all imports work correctly."""
    print("Testing import structure...")
    
    try:
        from eeg_stimulus_project.stimulus.turn_table_code.bay_mapping import bay_mapper
        print("  ✓ bay_mapping imported successfully")
    except ImportError as e:
        print(f"  ✗ bay_mapping import failed: {e}")
        return False
    
    try:
        # Test turntable GUI import (might fail without hardware)
        from eeg_stimulus_project.stimulus.turn_table_code.turntable_gui import TurntableWindow
        print("  ✓ turntable_gui imported successfully")
    except ImportError as e:
        print(f"  ⚠ turntable_gui import failed (expected without hardware): {e}")
    
    try:
        from eeg_stimulus_project.stimulus.turn_table_code.auto_turntable_window import AutoTurntableWindow
        print("  ✓ auto_turntable_window imported successfully")
    except ImportError as e:
        print(f"  ✗ auto_turntable_window import failed: {e}")
        return False
    
    print("Import structure test completed.\n")
    return True

def test_asset_integration():
    """Test integration with asset system."""
    print("Testing asset integration...")
    
    # Create mock assets
    class MockAsset:
        def __init__(self, filename):
            self.filename = filename
    
    class MockCravingAsset:
        def __init__(self):
            self.asset_type = 'craving_rating'
    
    # Test asset sequence generation
    from eeg_stimulus_project.stimulus.turn_table_code.bay_mapping import bay_mapper
    
    assets = [
        MockAsset('beer.jpg'),
        MockAsset('wine.jpg'),
        MockCravingAsset(),  # Should be skipped
        MockAsset('water.jpg'),
    ]
    
    bay_sequence = bay_mapper.get_bay_sequence_for_assets(assets)
    print(f"  Assets: {[getattr(a, 'filename', 'craving_rating') for a in assets]}")
    print(f"  Bay sequence: {[b + 1 for b in bay_sequence]}")
    
    print("Asset integration test completed.\n")

def main():
    """Run all tests."""
    print("=== Turntable Integration Tests ===\n")
    
    # Test bay mapping
    test_bay_mapping()
    
    # Test imports
    if not test_import_structure():
        print("Critical import failures detected. Cannot continue.")
        return 1
    
    # Test asset integration
    test_asset_integration()
    
    print("=== All Tests Completed ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())