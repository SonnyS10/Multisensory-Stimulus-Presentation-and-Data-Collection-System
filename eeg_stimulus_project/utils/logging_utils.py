"""
Logging utilities for the EEG Stimulus Project.
Provides centralized logging configuration for multiprocessing environments.
"""

import logging
import sys
from logging.handlers import QueueHandler
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from eeg_stimulus_project.config import config


def setup_logging(log_queue=None):
    """
    Setup logging configuration for both main process and child processes.
    
    Args:
        log_queue (Queue, optional): Queue for multiprocessing log handling.
                                   If provided, messages will be sent to this queue.
                                   
    Note:
        This function is primarily for main process logging.
        Child processes should use setup_child_process_logging() instead.
    """
    # Get configuration
    log_level = config.get('logging.level', 'INFO')
    log_format = config.get('logging.format', '%(asctime)s %(levelname)s %(message)s')
    log_file = config.get_absolute_path('paths.log_file')
    
    # Clear any existing handlers
    logger = logging.getLogger()
    logger.handlers.clear()
    
    # Create handlers
    handlers = []
    
    # File handler (always add for main process)
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter(log_format))
    handlers.append(file_handler)
    
    # Console handler (always add for main process)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    handlers.append(console_handler)
    
    # Queue handler for multiprocessing (if specified)
    if log_queue is not None:
        queue_handler = QueueHandler(log_queue)
        # Don't set formatter on queue handler - let the receiving handler format it
        handlers.append(queue_handler)
    
    # Configure logger
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Add all handlers
    for handler in handlers:
        logger.addHandler(handler)
    
    return logger


def setup_child_process_logging(log_queue):
    """
    Setup logging configuration specifically for child processes.
    This ensures that log messages from child processes are sent to the queue only.
    Child processes should NOT write directly to file/console to avoid duplication.
    
    Args:
        log_queue (Queue): Queue for sending log messages to the parent process.
    """
    # Get configuration
    log_level = config.get('logging.level', 'INFO')
    
    # Clear any existing handlers
    logger = logging.getLogger()
    logger.handlers.clear()
    
    # For child processes, ONLY use the queue handler
    # The queue listener will handle the actual logging to file/console
    if log_queue is not None:
        queue_handler = QueueHandler(log_queue)
        # Don't set formatter on queue handler - let the receiving handler format it
        logger.addHandler(queue_handler)
    
    # Configure logger
    logger.setLevel(getattr(logging, log_level.upper()))
    
    return logger


def setup_main_process_logging():
    """
    Setup logging configuration for the main process.
    This is used when no multiprocessing is involved.
    """
    return setup_logging(log_queue=None)