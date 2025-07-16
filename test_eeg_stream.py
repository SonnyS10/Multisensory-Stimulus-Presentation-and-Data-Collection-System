#!/usr/bin/env python3
"""
Test script for EEG Stream Window
This script tests the EEG stream window functionality.
"""

import sys
import os
from pathlib import Path
import time
import threading
import numpy as np
import pylsl

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def create_fake_eeg_stream():
    """Create a fake EEG stream for testing purposes."""
    # Create a stream info
    info = pylsl.StreamInfo(
        name='FakeEEG',
        type='EEG',
        channel_count=32,
        nominal_srate=250,
        channel_format='float32',
        source_id='fake_eeg_001'
    )
    
    # Add channel information
    channels = info.desc().append_child("channels")
    for i in range(32):
        ch = channels.append_child("channel")
        ch.append_child_value("label", f"Ch{i+1}")
        ch.append_child_value("unit", "microvolts")
        ch.append_child_value("type", "EEG")
    
    # Create outlet
    outlet = pylsl.StreamOutlet(info)
    
    print("Created fake EEG stream: FakeEEG")
    print("Channels: 32")
    print("Sample rate: 250 Hz")
    print("Starting data transmission...")
    
    # Send fake data
    sample_rate = 250
    channels = 32
    
    while True:
        # Generate fake EEG data (sinusoidal + noise)
        t = time.time()
        sample = []
        for ch in range(channels):
            # Create different frequency components for each channel
            freq = 1 + ch * 0.5  # Different frequencies for each channel
            signal = 10 * np.sin(2 * np.pi * freq * t) + 5 * np.random.randn()
            sample.append(signal)
        
        # Send sample
        outlet.push_sample(sample)
        
        # Sleep to maintain sample rate
        time.sleep(1.0 / sample_rate)

def test_eeg_stream_window():
    """Test the EEG stream window."""
    try:
        from eeg_stimulus_project.gui.eeg_stream_window import run_eeg_stream_window
        
        # Start fake EEG stream in background
        fake_stream_thread = threading.Thread(target=create_fake_eeg_stream, daemon=True)
        fake_stream_thread.start()
        
        # Wait a bit for stream to start
        time.sleep(2)
        
        # Run the EEG stream window
        run_eeg_stream_window()
        
    except Exception as e:
        print(f"Error testing EEG stream window: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Testing EEG Stream Window...")
    print("This will create a fake EEG stream and open the stream window.")
    print("Press Ctrl+C to stop.")
    
    try:
        test_eeg_stream_window()
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
        sys.exit(0)