import socket
import os
import time


class LabRecorder:
    def __init__(self, base_dir):
        self.base_dir = base_dir

        # Creates a connection with the LabRecorder Remote control server
        try:
            self.s = socket.create_connection(("localhost", 22345))
            print("LabRecorder socket connected.")
        except socket.error as e:
            print(f"Could not connect to LabRecorder: {e}")
            self.s = None

        self.check_tcp_port("localhost", 22345)

    # Sends commands to the LabRecorder server to begin recording and assigns a filepath
    def Start_Recorder(self, current_test):
        if not self.s:
            print("No LabRecorder connection.")
            return
        save_dir = os.path.join(self.base_dir, current_test)
        os.makedirs(save_dir, exist_ok=True)
        xdf_path = os.path.join('C:\\Users\\srs1520\\Documents\\Paid Research\\Software-for-Paid-Research-', save_dir)
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