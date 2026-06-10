import socket
import time
import sys
from pathlib import Path
import datetime
import re
import logging

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from eeg_stimulus_project.config import config

try:
    from pylsl import resolve_streams
except Exception:
    resolve_streams = None


class LabRecorder:
    CONDITION_ALIASES = {
        "Unisensory Neutral Visual": "UNV",
        "Unisensory Alcohol Visual": "UAV",
        "Multisensory Neutral Visual & Olfactory": "MNVO",
        "Multisensory Alcohol Visual & Olfactory": "MAVO",
        "Multisensory Neutral Visual, Tactile & Olfactory": "MNVTO",
        "Multisensory Alcohol Visual, Tactile & Olfactory": "MAVTO",
        "Stroop Multisensory Neutral (Visual & Tactile)": "SMNVT",
        "Stroop Multisensory Alcohol (Visual & Tactile)": "SMAVT",
        "Stroop Multisensory Neutral (Visual & Olfactory)": "SMNVO",
        "Stroop Multisensory Alcohol (Visual & Olfactory)": "SMAVO",
        "Baseline": "BASE",
    }

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

    def _condition_alias(self, current_test):
        alias = self.CONDITION_ALIASES.get(str(current_test))
        if alias:
            return alias
        return self._sanitize_filename_part(current_test, fallback="COND")

    def _build_recording_paths(self, current_test):
        """
        Keep the human-readable condition folder for app data, but give LabRecorder
        a short ASCII-only root/template so its remote filename parser stays stable.
        """
        base_dir = Path(self.base_dir).resolve()
        condition_dir = base_dir / current_test
        condition_dir.mkdir(parents=True, exist_ok=True)

        alias = self._condition_alias(current_test)
        xdf_root = base_dir / "xdf" / alias
        xdf_root.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        subject_str = f"subj_{self._sanitize_filename_part(self.subject_id)}_" if self.subject_id else ""
        filename = f"{subject_str}{alias}_{timestamp}.xdf"
        xdf_path = xdf_root / filename

        # Defensive path containment check before sending anything to LabRecorder.
        xdf_path.resolve().relative_to(base_dir)

        return {
            "condition_dir": condition_dir,
            "alias": alias,
            "xdf_root": xdf_root,
            "filename": filename,
            "xdf_path": xdf_path,
        }

    def _send_command(self, command):
        if not self.s:
            raise ConnectionError("No LabRecorder connection.")
        if not command.endswith("\n"):
            command += "\n"
        self.s.sendall(command.encode("utf-8"))

    def _wait_for_recording_file(self, xdf_path, timeout=1.5, interval=0.25):
        deadline = time.time() + timeout
        last_size = None
        while time.time() < deadline:
            if xdf_path.exists():
                size = xdf_path.stat().st_size
                if size > 0:
                    return {"exists": True, "size": size, "warning": None}
                last_size = size
            time.sleep(interval)

        if xdf_path.exists():
            size = xdf_path.stat().st_size
            warning = f"LabRecorder output exists but is still zero bytes after start: {xdf_path}"
            return {"exists": True, "size": size, "warning": warning}

        warning = f"LabRecorder output has not appeared after start: {xdf_path}"
        return {"exists": False, "size": last_size, "warning": warning}

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

            recording_paths = self._build_recording_paths(current_test)
            alias = recording_paths["alias"]
            xdf_root = recording_paths["xdf_root"].resolve()
            filename = recording_paths["filename"]
            xdf_path = recording_paths["xdf_path"].resolve()

            streams = self._get_visible_lsl_streams()
            if streams is not None and len(streams) == 0:
                error = "No LSL streams visible to LabRecorder at start time."
                print(error)
                return {"ok": False, "path": str(xdf_path), "error": error, "stream_count": 0}

            # Reset any previous recording state before selecting streams. LabRecorder tolerates
            # stop when idle and it prevents stale zero-byte sessions from carrying forward.
            self._send_command("stop")
            time.sleep(0.25)
            self._send_command("update")
            time.sleep(3)
            self._send_command("select all")
            filename_command = f"filename {{root:{xdf_root}}} {{template:{filename}}}"
            stream_count = len(streams) if streams is not None else None
            target_message = (
                f"LabRecorder target: root={xdf_root}, template={filename}, "
                f"path={xdf_path}, condition_alias={alias}, stream_count={stream_count}"
            )
            logging.info(target_message)
            print(target_message)
            self._send_command(filename_command)
            self._send_command("start")

            file_check = self._wait_for_recording_file(xdf_path)
            if file_check.get("warning"):
                logging.warning(file_check["warning"])
                print(f"WARNING: {file_check['warning']}")

            self.last_xdf_path = str(xdf_path)
            self.is_recording = True
            if stream_count is None:
                print(f"LabRecorder started recording: {xdf_path}")
            else:
                print(f"LabRecorder started recording: {xdf_path} ({stream_count} LSL streams visible)")
            return {
                "ok": True,
                "path": str(xdf_path),
                "error": None,
                "stream_count": stream_count,
                "condition_alias": alias,
                "file_check": file_check,
            }
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
