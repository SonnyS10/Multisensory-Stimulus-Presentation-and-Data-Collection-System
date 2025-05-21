import socket
import os


class LabRecorder():
    
    def create_connection(self):
        """
        Create a connection to the LabRecorder server.
        """
        try:
            # Attempt to connect to the LabRecorder server
            self.s = socket.create_connection(("localhost", 22345))
        except socket.error as e:
            print(f"Could not connect to LabRecorder: {e}")
            return False
        return True
    
    def __init__(self, base_dir):
        self.base_dir = base_dir

    def Start_Recorder(self, current_test):
        save_dir = os.path.join(self.base_dir, current_test)
        os.makedirs(save_dir, exist_ok=True)
        xdf_path = os.path.join('C:\\Users\\srs1520\\Documents\\Paid Research\\Software-for-Paid-Research-', save_dir)
        self.s.sendall(b"select all\n")
        #self.s.sendall(b'filename {root:{xdf_path}} {template:eeg_data.xdf}\n'.encode('utf-8'))
        self.s.sendall(f'filename {{root:{xdf_path}\\}} {{template:eeg_data.xdf}}\n'.encode('utf-8'))
        self.s.sendall(b"start\n")
        print(f"LabRecorder started recording: {xdf_path}")

    def Stop_Recorder(self):
        self.s.sendall(b"stop\n")
        print("LabRecorder stopped recording.")