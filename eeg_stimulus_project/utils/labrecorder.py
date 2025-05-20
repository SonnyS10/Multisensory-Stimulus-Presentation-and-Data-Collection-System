import socket
import os


class LabRecorder():
    s = socket.create_connection(("localhost", 22345))
    def __init__(self, base_dir):
        self.base_dir = base_dir

    def Start_Recorder(self, current_test):
        save_dir = os.path.join(self.base_dir, current_test)
        os.makedirs(save_dir, exist_ok=True)
        xdf_path = os.path.join(save_dir, "eeg_data.xdf")
        self.s.sendall(b"select all\n")
        self.s.sendall(f'filename "{xdf_path}"\n'.encode('utf-8'))
        self.s.sendall(b"start\n")
        print(f"LabRecorder started recording: {xdf_path}")

    def Stop_Recorder(self):
        self.s.sendall(b"stop\n")
        print("LabRecorder stopped recording.")