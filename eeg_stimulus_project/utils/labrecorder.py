import socket
import time
import sys
from pathlib import Path
import datetime
import re

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from eeg_stimulus_project.config import config

try:
    from pylsl import resolve_streams
except Exception:
    resolve_streams = None


class LabRecorder:
    def __init__(self, base_dir, subject_id=None):
        self.base_dir = base_dir
        self.subject_id = subject_id
        self.last_xdf_path = None
        self.is_recording = False
        
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

    def _sanitize_filename_part(self, value, fallback="recording"):
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value)).strip("._-")
        return safe or fallback

    def _send_command(self, command):
        if not self.s:
            raise ConnectionError("No LabRecorder connection.")
        if not command.endswith("\n"):
            command += "\n"
        self.s.sendall(command.encode("utf-8"))

    def _get_visible_lsl_streams(self):
        if resolve_streams is None:
            return None
        return resolve_streams(wait_time=2.0)

    # Sends commands to the LabRecorder server to begin recording and assigns a filepath
    def Start_Recorder(self, current_test):
        if not self.s:
            print("No LabRecorder connection.")
            return {"ok": False, "path": None, "error": "No LabRecorder connection."}

        try:
            current_test = str(current_test or "default_test")

            # Create save directory using relative path
            save_dir = Path(self.base_dir) / current_test
            save_dir.mkdir(parents=True, exist_ok=True)

            # --- Compose filename with subject ID, test name, and timestamp ---
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            subject_str = f"subj_{self._sanitize_filename_part(self.subject_id)}_" if self.subject_id else ""
            test_str = self._sanitize_filename_part(current_test)
            filename = f"{subject_str}{test_str}_{timestamp}.xdf"

            # Use the save directory path for recording
            xdf_path = str(save_dir.resolve() / filename)

            streams = self._get_visible_lsl_streams()
            if streams is not None and len(streams) == 0:
                error = "No LSL streams visible to LabRecorder at start time."
                print(error)
                return {"ok": False, "path": xdf_path, "error": error, "stream_count": 0}

            # Reset any previous recording state before selecting streams. LabRecorder tolerates
            # stop when idle and it prevents stale zero-byte sessions from carrying forward.
            self._send_command("stop")
            time.sleep(0.25)
            self._send_command("update")
            time.sleep(3)
            self._send_command("select all")
            self._send_command(f"filename {{root:{save_dir.resolve()}}} {{template:{filename}}}")
            self._send_command("start")

            self.last_xdf_path = xdf_path
            self.is_recording = True
            stream_count = len(streams) if streams is not None else None
            if stream_count is None:
                print(f"LabRecorder started recording: {xdf_path}")
            else:
                print(f"LabRecorder started recording: {xdf_path} ({stream_count} LSL streams visible)")
            return {"ok": True, "path": xdf_path, "error": None, "stream_count": stream_count}
        except Exception as e:
            self.is_recording = False
            error = f"Failed to start LabRecorder recording: {e}"
            print(error)
            return {"ok": False, "path": None, "error": error, "stream_count": None}

    # Sends commands to the LabRecorder server to stop recording
    def Stop_Recorder(self):
        if not self.s:
            print("No LabRecorder connection.")
            return {"ok": False, "path": self.last_xdf_path, "error": "No LabRecorder connection."}

        try:
            self._send_command("stop")
            self.is_recording = False
            print("LabRecorder stopped recording.")
            return {"ok": True, "path": self.last_xdf_path, "error": None}
        except Exception as e:
            error = f"Failed to stop LabRecorder recording: {e}"
            print(error)
            return {"ok": False, "path": self.last_xdf_path, "error": error}

    def check_tcp_port(self, host, port):
        try:
            with socket.create_connection((host, port), timeout=5):
                print(f"Port {port} on {host} is open and connected.")
        except (socket.timeout, ConnectionRefusedError):
            print(f"Port {port} on {host} is not connected.")
        except Exception as e:
            print(f"An error occurred: {e}")
