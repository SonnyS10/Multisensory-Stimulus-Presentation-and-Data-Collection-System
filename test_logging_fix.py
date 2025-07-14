#!/usr/bin/env python3
"""
Test script to verify the logging fix prevents duplicate messages.
"""

import logging
import multiprocessing as mp
import time
import io
import sys
from pathlib import Path
from logging.handlers import QueueListener

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_child_process_logging(log_queue):
    """Test function that runs in a child process and generates log messages."""
    from eeg_stimulus_project.utils.logging_utils import setup_child_process_logging
    
    # Setup logging for child process
    setup_child_process_logging(log_queue)
    
    # Generate test messages
    logging.info("Test message 1 from child process")
    logging.warning("Test warning from child process")
    logging.error("Test error from child process")
    
    # Sleep to ensure messages are processed
    time.sleep(0.1)

def test_main_process_logging():
    """Test function that generates log messages in the main process."""
    from eeg_stimulus_project.utils.logging_utils import setup_main_process_logging
    
    # Setup logging for main process
    setup_main_process_logging()
    
    # Generate test messages
    logging.info("Test message 1 from main process")
    logging.warning("Test warning from main process")
    logging.error("Test error from main process")

def test_logging_duplication():
    """Test that logging does not cause duplication in multiprocessing context."""
    print("Testing logging duplication fix...")
    
    # Create a queue for inter-process communication
    log_queue = mp.Queue()
    
    # Capture console output to check for duplicates
    console_output = io.StringIO()
    
    # Create a simple console handler to capture output
    console_handler = logging.StreamHandler(console_output)
    console_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    
    # Create and start the queue listener
    listener = QueueListener(log_queue, console_handler)
    listener.start()
    
    try:
        # Start child process that will send messages to queue
        child_process = mp.Process(target=test_child_process_logging, args=(log_queue,))
        child_process.start()
        child_process.join()
        
        # Give some time for queue processing
        time.sleep(0.5)
        
        # Get the output and check for duplicates
        output = console_output.getvalue()
        lines = output.strip().split('\n')
        
        # Filter out empty lines
        lines = [line for line in lines if line.strip()]
        
        print(f"Total log lines captured: {len(lines)}")
        print("Captured output:")
        for i, line in enumerate(lines, 1):
            print(f"{i}: {line}")
        
        # Check for duplicate messages
        message_counts = {}
        for line in lines:
            # Extract the message part (after timestamp and level)
            parts = line.split(' ', 2)
            if len(parts) >= 3:
                message = parts[2]
                message_counts[message] = message_counts.get(message, 0) + 1
        
        # Check if any message appears more than once
        duplicates = {msg: count for msg, count in message_counts.items() if count > 1}
        
        if duplicates:
            print(f"\n❌ DUPLICATE MESSAGES FOUND:")
            for msg, count in duplicates.items():
                print(f"  '{msg}' appears {count} times")
            return False
        else:
            print("\n✅ No duplicate messages found!")
            return True
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        listener.stop()

def main():
    """Run the logging test."""
    print("EEG Stimulus Project - Logging Duplication Fix Test")
    print("=" * 60)
    
    # Test that configuration works
    try:
        from eeg_stimulus_project.config import config
        print("✅ Configuration loaded successfully")
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        return 1
    
    # Test main process logging
    try:
        test_main_process_logging()
        print("✅ Main process logging test passed")
    except Exception as e:
        print(f"❌ Main process logging test failed: {e}")
        return 1
    
    # Test multiprocessing logging for duplicates
    if test_logging_duplication():
        print("\n🎉 All logging tests passed! No duplicate messages detected.")
        return 0
    else:
        print("\n❌ Logging duplication test failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())