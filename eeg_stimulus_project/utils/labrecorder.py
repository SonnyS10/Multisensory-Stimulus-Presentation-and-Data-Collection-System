import socket
import os
import time
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from eeg_stimulus_project.config import config


class LabRecorder:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        
        # Get LabRecorder configuration
        labrecorder_host = config.get('hardware.eeg.labrecorder_host', 'localhost')
        labrecorder_port = config.get('network.labrecorder_port', 22345)

        # Creates a connection with the LabRecorder Remote control server
        try:
            self.s = socket.create_connection((labrecorder_host, labrecorder_port))
            print("LabRecorder socket connected.")
        except socket.error as e:
            print(f"Could not connect to LabRecorder: {e}")
            self.s = None

        self.check_tcp_port(labrecorder_host, labrecorder_port)

    # Sends commands to the LabRecorder server to begin recording and assigns a filepath
    def Start_Recorder(self, current_test):
        if not self.s:
            print("No LabRecorder connection.")
            return
        
        # Create save directory using relative path
        save_dir = Path(self.base_dir) / current_test
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # Use the save directory path for recording
        xdf_path = str(save_dir.resolve())
        
        self.s.sendall(b"update\n")
        time.sleep(3)
        self.s.sendall(b"select all\n")
        self.s.sendall(f'filename {{root:{xdf_path}\\}} {{template:eeg_data.xdf}}\n'.encode('utf-8'))
        self.s.sendall(b"start\n")
        print(f"LabRecorder started recording: {xdf_path}")

    # Sends commands to the LabRecorder server to stop recording
    def Stop_Recorder(self):
        if self.s:
            self.s.sendall(b"stop\n")
            print("LabRecorder stopped recording.")

    def check_tcp_port(self, host, port):
            try:
                with socket.create_connection((host, port), timeout=5):
                    print(f"Port {port} on {host} is open and connected.")
            except (socket.timeout, ConnectionRefusedError):
                print(f"Port {port} on {host} is not connected.")
            except Exception as e:
                print(f"An error occurred: {e}")