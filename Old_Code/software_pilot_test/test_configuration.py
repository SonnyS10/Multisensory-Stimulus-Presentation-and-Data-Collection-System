#!/usr/bin/env python3
"""
Test script to verify the portable configuration system works correctly.
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_configuration():
    """Test that the configuration system works properly."""
    print("Testing EEG Stimulus Project Configuration System...")
    
    try:
        from eeg_stimulus_project.config import config
        print("✓ Configuration module imported successfully")
        
        # Test basic configuration access
        host_port = config.get('network.host_port')
        print(f"✓ Network host port: {host_port}")
        
        # Test path configuration
        data_dir = config.get_absolute_path('paths.data_directory')
        print(f"✓ Data directory: {data_dir}")
        
        # Test hardware configuration
        threshold = config.get('hardware.tactile.threshold')
        print(f"✓ Tactile threshold: {threshold}")
        
        # Test experiment configuration
        passive_tests = config.get('experiment.test_types.passive')
        print(f"✓ Passive tests available: {len(passive_tests)}")
        
        # Test platform configuration
        platform_config = config.get('platform.windows')
        print(f"✓ Windows platform configuration loaded: {platform_config is not None}")
        
        print("\nAll configuration tests passed! ✓")
        return True
        
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_imports():
    """Test that key modules can be imported without GUI dependencies."""
    print("\nTesting module imports...")
    
    try:
        # Test configuration
        from eeg_stimulus_project.config import config
        print("✓ Configuration module")
        
        # Test that the configuration system works
        if config._config is not None:
            print("✓ Configuration loaded successfully")
        else:
            print("✗ Configuration not loaded")
            return False
            
        print("\nAll import tests passed! ✓")
        return True
        
    except Exception as e:
        print(f"✗ Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_paths():
    """Test that paths are properly resolved."""
    print("\nTesting path resolution...")
    
    try:
        from eeg_stimulus_project.config import config
        
        # Test data directory creation
        data_dir = config.get_absolute_path('paths.data_directory')
        data_dir.mkdir(parents=True, exist_ok=True)
        print(f"✓ Data directory created: {data_dir}")
        
        # Test assets directory
        assets_dir = config.get_absolute_path('paths.assets_directory')
        print(f"✓ Assets directory: {assets_dir}")
        
        # Test relative path handling
        relative_path = config.get_path('paths.log_file', relative_to_project_root=False)
        print(f"✓ Relative path: {relative_path}")
        
        print("\nAll path tests passed! ✓")
        return True
        
    except Exception as e:
        print(f"✗ Path test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("EEG Stimulus Project - Configuration System Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_configuration,
        test_paths
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1
            
    print("\n" + "=" * 50)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! The repository is ready for deployment.")
        return 0
    else:
        print("❌ Some tests failed. Please check the configuration.")
        return 1

if __name__ == "__main__":
    sys.exit(main())