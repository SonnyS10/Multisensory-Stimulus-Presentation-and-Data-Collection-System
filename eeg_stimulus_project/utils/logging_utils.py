"""
Logging utilities for the EEG Stimulus Project.
Provides centralized logging configuration for multiprocessing environments.
"""

import logging
import sys
import json
import socket
import threading
from logging.handlers import QueueHandler
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from eeg_stimulus_project.config import config


class NetworkLogHandler(logging.Handler):
    """
    A logging handler that sends log messages over a network connection.
    Used for client-server logging in distributed setups.
    """
    
    def __init__(self, connection):
        """
        Initialize the network log handler.
        
        Args:
            connection: Socket connection to send log messages through
        """
        super().__init__()
        self.connection = connection
        self.lock = threading.Lock()
    
    def emit(self, record):
        """
        Send a log record over the network connection.
        
        Args:
            record: LogRecord to send
        """
        try:
            # Format the log message
            formatted_msg = self.format(record)
            
            # Create a log message packet
            log_packet = {
                'type': 'log_message',
                'timestamp': record.created,
                'level': record.levelname,
                'message': formatted_msg,
                'logger': record.name,
                'filename': record.filename,
                'lineno': record.lineno
            }
            
            # Convert to JSON and send
            json_msg = json.dumps(log_packet) + '\n'
            
            with self.lock:
                if self.connection:
                    try:
                        self.connection.send(json_msg.encode('utf-8'))
                    except (ConnectionResetError, BrokenPipeError, OSError):
                        # Connection lost, disable this handler
                        self.connection = None
                        
        except Exception as e:
            # Don't let logging errors crash the application
            # Could consider writing to stderr or a backup log file
            print(f"NetworkLogHandler error: {e}", file=sys.stderr)
    
    def close(self):
        """Close the network connection."""
        if self.connection:
            with self.lock:
                self.connection = None
        super().close()


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


def setup_child_process_logging(log_queue, network_connection=None):
    """
    Setup logging configuration specifically for child processes.
    This ensures that log messages from child processes are sent to the queue only.
    Child processes should NOT write directly to file/console to avoid duplication.
    
    Args:
        log_queue (Queue): Queue for sending log messages to the parent process.
        network_connection (socket, optional): Network connection for sending logs
                                             to remote host in client mode.
    """
    # Get configuration
    log_level = config.get('logging.level', 'INFO')
    log_format = config.get('logging.format', '%(asctime)s %(levelname)s %(message)s')
    
    # Clear any existing handlers
    logger = logging.getLogger()
    logger.handlers.clear()
    
    # For child processes, use the queue handler for local logging
    if log_queue is not None:
        queue_handler = QueueHandler(log_queue)
        # Don't set formatter on queue handler - let the receiving handler format it
        logger.addHandler(queue_handler)
    
    # If we have a network connection (client mode), also send logs to host
    if network_connection is not None:
        network_handler = NetworkLogHandler(network_connection)
        network_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(network_handler)
    
    # Configure logger
    logger.setLevel(getattr(logging, log_level.upper()))
    
    return logger


def setup_main_process_logging():
    """
    Setup logging configuration for the main process.
    This is used when no multiprocessing is involved.
    """
    return setup_logging(log_queue=None)