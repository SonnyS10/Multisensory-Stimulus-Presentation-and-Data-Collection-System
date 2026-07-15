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
        "Stroop Practice Neutral (Visual & Tactile)": "SPNVT",
        "Stroop Practice Neutral (Visual & Olfactory)": "SPNVO",
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
        self.recording_xdf_path = None
        self.final_xdf_path = None
        self.recording_xdf_root = None
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
        Write the XDF straight into the human-readable condition folder. The filename
        keeps a short ASCII-only alias so LabRecorder's remote filename parser stays
        stable; the root path uses the full condition name (no '{'/'}' chars, which are
        the only ones that would break the {root:...} command syntax), so no post-stop
        move is required.
        """
        base_dir = Path(self.base_dir).resolve()
        condition_dir = base_dir / current_test
        condition_dir.mkdir(parents=True, exist_ok=True)

        alias = self._condition_alias(current_test)
        xdf_root = condition_dir

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        subject_str = f"subj_{self._sanitize_filename_part(self.subject_id)}_" if self.subject_id else ""
        filename = f"{subject_str}{alias}_{timestamp}.xdf"
        xdf_path = xdf_root / filename
        final_xdf_path = xdf_path

        # Defensive path containment check before sending anything to LabRecorder.
        xdf_path.resolve().relative_to(base_dir)
        final_xdf_path.resolve().relative_to(base_dir)

        return {
            "condition_dir": condition_dir,
            "alias": alias,
            "xdf_root": xdf_root,
            "filename": filename,
            "xdf_path": xdf_path,
            "final_xdf_path": final_xdf_path,
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

    def _cleanup_empty_recording_dirs(self):
        for path_value in (self.recording_xdf_root,):
            if not path_value:
                continue
            path = Path(path_value)
            try:
                path.rmdir()
                parent = path.parent
                if parent.name == "_labrecorder_tmp":
                    parent.rmdir()
            except OSError:
                pass

    def _move_finished_xdf_to_test_folder(self):
        if not self.recording_xdf_path or not self.final_xdf_path:
            return {"path": self.last_xdf_path, "moved": False, "warning": None}

        source = Path(self.recording_xdf_path)
        destination = Path(self.final_xdf_path)

        for _ in range(20):
            if source.exists():
                break
            time.sleep(0.25)

        # The file is now written straight into the condition folder, so source and
        # destination are the same path: just confirm it landed and skip the move.
        if source.resolve() == destination.resolve():
            if source.exists():
                self.last_xdf_path = str(destination)
                message = f"LabRecorder XDF saved to test folder: {destination}"
                logging.info(message)
                print(message)
                return {"path": str(destination), "moved": False, "warning": None}
            warning = (
                f"LabRecorder XDF not found in test folder after stop "
                f"(LabRecorder may have rejected the path): {destination}"
            )
            logging.warning(warning)
            print(f"WARNING: {warning}")
            return {"path": str(destination), "moved": False, "warning": warning}

        if not source.exists():
            warning = f"Could not move XDF into test folder because the source file was not found: {source}"
            logging.warning(warning)
            print(f"WARNING: {warning}")
            return {"path": str(destination), "moved": False, "warning": warning}

        destination.parent.mkdir(parents=True, exist_ok=True)
        last_error = None
        try:
            for _ in range(20):
                try:
                    source.replace(destination)
                    self.last_xdf_path = str(destination)
                    self._cleanup_empty_recording_dirs()
                    message = f"LabRecorder XDF moved to test folder: {destination}"
                    logging.info(message)
                    print(message)
                    return {"path": str(destination), "moved": True, "warning": None}
                except PermissionError as e:
                    last_error = e
                    time.sleep(0.25)
        except Exception as e:
            last_error = e

        warning = f"Could not move XDF into test folder: {last_error}"
        logging.warning(warning)
        print(f"WARNING: {warning}")
        return {"path": str(source), "moved": False, "warning": warning}

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
            final_xdf_path = recording_paths["final_xdf_path"].resolve()

            streams = self._get_visible_lsl_streams()
            if streams is not None and len(streams) == 0:
                error = "No LSL streams visible to LabRecorder at start time."
                print(error)
                return {"ok": False, "path": str(final_xdf_path), "error": error, "stream_count": 0}

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
                f"recording_path={xdf_path}, final_path={final_xdf_path}, "
                f"condition_alias={alias}, stream_count={stream_count}"
            )
            logging.info(target_message)
            print(target_message)
            self._send_command(filename_command)
            self._send_command("start")

            file_check = self._wait_for_recording_file(xdf_path)
            if file_check.get("warning"):
                logging.warning(file_check["warning"])
                print(f"WARNING: {file_check['warning']}")

            self.recording_xdf_path = str(xdf_path)
            self.final_xdf_path = str(final_xdf_path)
            self.recording_xdf_root = str(xdf_root)
            self.last_xdf_path = str(final_xdf_path)
            self.is_recording = True
            if stream_count is None:
                print(f"LabRecorder started recording: {xdf_path}")
            else:
                print(f"LabRecorder started recording: {xdf_path} ({stream_count} LSL streams visible)")
            return {
                "ok": True,
                "path": str(final_xdf_path),
                "error": None,
                "stream_count": stream_count,
                "condition_alias": alias,
                "recording_path": str(xdf_path),
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
            move_result = self._move_finished_xdf_to_test_folder()
            print("LabRecorder stopped recording.")
            return {
                "ok": True,
                "path": move_result.get("path", self.last_xdf_path),
                "error": None,
                "warning": move_result.get("warning"),
                "moved": move_result.get("moved", False),
            }
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
