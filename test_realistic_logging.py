#!/usr/bin/env python3
"""
Simple test to verify the logging fix works without GUI dependencies.
This test validates the core logging functionality matches the multiprocessing
pattern used in the actual application.
"""

import logging
import multiprocessing as mp
import time
import sys
from pathlib import Path
from logging.handlers import QueueListener

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class TestLogHandler(logging.Handler):
    """Test handler that captures messages."""
    
    def __init__(self):
        super().__init__()
        self.messages = []
    
    def emit(self, record):
        msg = self.format(record)
        self.messages.append(msg)

def simulate_control_window_host(log_queue):
    """Simulates the control window host process from run_control_window_host()."""
    from eeg_stimulus_project.utils.logging_utils import setup_child_process_logging
    
    # Setup logging for child process - this is what happens in run_control_window_host
    setup_child_process_logging(log_queue)
    
    # Generate messages similar to what control_window.py would generate
    logging.info("Control Window: Initializing control window")
    logging.info("Control Window: Setting up device connections")
    logging.warning("Control Window: Device connection warning")
    logging.error("Control Window: Device connection error")

def simulate_main_gui_client(log_queue):
    """Simulates the main GUI client process from run_main_gui_client()."""
    from eeg_stimulus_project.utils.logging_utils import setup_child_process_logging
    
    # Setup logging for child process - this is what happens in run_main_gui_client
    setup_child_process_logging(log_queue)
    
    # Generate messages similar to what main_gui.py would generate
    logging.info("Main GUI: Initializing main GUI")
    logging.info("Main GUI: Loading experiment configuration")
    logging.warning("Main GUI: GUI warning message")
    logging.error("Main GUI: GUI error message")

def test_realistic_multiprocessing():
    """Test the logging system with realistic multiprocessing scenario."""
    print("Testing realistic multiprocessing logging scenario...")
    
    # Create log queue
    log_queue = mp.Queue()
    
    # Create test handler
    test_handler = TestLogHandler()
    test_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    
    # Create and start queue listener (this is what happens in control_window.py)
    listener = QueueListener(log_queue, test_handler)
    listener.start()
    
    try:
        # Start child processes (similar to what happens in main.py)
        control_process = mp.Process(target=simulate_control_window_host, args=(log_queue,))
        gui_process = mp.Process(target=simulate_main_gui_client, args=(log_queue,))
        
        control_process.start()
        gui_process.start()
        
        control_process.join()
        gui_process.join()
        
        # Give time for queue processing
        time.sleep(0.5)
        
        # Check captured messages
        messages = test_handler.messages
        print(f"Total messages captured: {len(messages)}")
        
        # Print messages for verification
        print("\nCaptured messages:")
        for i, msg in enumerate(messages, 1):
            print(f"{i}: {msg}")
        
        # Expected: 4 messages from control_window + 4 from main_gui = 8 total
        expected_count = 8
        
        if len(messages) == expected_count:
            print(f"\n✅ Correct number of messages captured ({expected_count})")
            
            # Check for duplicates by message content
            message_contents = []
            for msg in messages:
                # Extract the message part (after timestamp and level)
                parts = msg.split(' ', 2)
                if len(parts) >= 3:
                    message_contents.append(parts[2])
            
            unique_messages = set(message_contents)
            
            if len(unique_messages) == len(message_contents):
                print("✅ No duplicate messages found")
                return True
            else:
                print(f"❌ Found {len(message_contents) - len(unique_messages)} duplicate messages")
                
                # Show duplicates
                from collections import Counter
                message_counts = Counter(message_contents)
                duplicates = {msg: count for msg, count in message_counts.items() if count > 1}
                
                print("Duplicate messages:")
                for msg, count in duplicates.items():
                    print(f"  '{msg}' appears {count} times")
                
                return False
        else:
            print(f"❌ Expected {expected_count} messages, got {len(messages)}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        listener.stop()

def main():
    """Run the realistic multiprocessing test."""
    print("EEG Stimulus Project - Realistic Multiprocessing Logging Test")
    print("=" * 65)
    
    # Run the test
    if test_realistic_multiprocessing():
        print("\n🎉 Realistic multiprocessing test passed! No duplicate messages.")
        return 0
    else:
        print("\n❌ Realistic multiprocessing test failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())