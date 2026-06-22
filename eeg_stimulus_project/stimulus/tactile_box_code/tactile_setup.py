import paramiko
import threading
import subprocess
import queue
import time
import socket
import json
import sys
import datetime
import os
import shlex
import logging
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QTextEdit, QLabel, QSpinBox, QDesktopWidget
from PyQt5.QtCore import QTimer
from eeg_stimulus_project.lsl.labels import LSLTactileStream

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from eeg_stimulus_project.config import config

# SSH connection info - load from configuration
def get_ssh_config():
    """Get SSH configuration from settings."""
    return {
        'host': config.get('network.tactile_system.host', '10.115.9.73'),
        'username': config.get('network.tactile_system.username', 'benja'),
        'password': config.get('network.tactile_system.password', 'neuro'),
        'data_port': config.get('network.tactile_system.data_port', 5007),
        'venv_activate': config.get('network.tactile_system.venv_activate', 'source ~/Desktop/bin/activate'),
        'script_path': config.get('network.tactile_system.script_path', 'python ~/forcereadwithzero.py')
    }

# Get SSH configuration
ssh_config = get_ssh_config()
ssh_host = ssh_config['host']
ssh_user = ssh_config['username']
ssh_password = ssh_config['password']
remote_venv_activate = ssh_config['venv_activate']
remote_script = ssh_config['script_path']

TACTILE_LOCAL_PORT = config.get('network.tactile_local_port', 9998)

ssh_client = None
remote_channel = None
output_queue = queue.Queue()


def get_remote_script_pattern(script_command):
    """Extract the remote script filename so we can safely stop stale instances."""
    try:
        parts = shlex.split(script_command)
        if not parts:
            return "forcereadwithzero.py"
        last_token = parts[-1]
        script_name = os.path.basename(last_token)
        return script_name or "forcereadwithzero.py"
    except Exception:
        return "forcereadwithzero.py"

def start_remote_script(local_script_callback): 
    startup_event = threading.Event()
    startup_state = {"ok": False, "error": "Timed out while starting remote script."}

    def task():
        global ssh_client, remote_channel
        try:
            ssh_config = get_ssh_config()
            ssh_host = ssh_config['host']
            ssh_user = ssh_config['username']
            ssh_password = ssh_config['password']
            data_port = ssh_config['data_port']
            remote_venv_activate = ssh_config['venv_activate']
            remote_script = ssh_config['script_path']

            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(ssh_host, username=ssh_user, password=ssh_password)

            script_pattern = get_remote_script_pattern(remote_script)
            quoted_pattern = shlex.quote(script_pattern)
            quoted_password = shlex.quote(ssh_password)
            cleanup_by_port_command = (
                f"if command -v lsof >/dev/null 2>&1; then "
                f"for pid in $(lsof -t -iTCP:{data_port} -sTCP:LISTEN 2>/dev/null); do "
                f"kill \"$pid\" >/dev/null 2>&1 || true; "
                f"done; "
                f"elif command -v fuser >/dev/null 2>&1; then "
                f"fuser -k {data_port}/tcp >/dev/null 2>&1 || true; "
                f"fi"
            )
            cleanup_by_port_sudo_command = (
                f"if command -v sudo >/dev/null 2>&1 && command -v fuser >/dev/null 2>&1; then "
                f"echo {quoted_password} | sudo -S -p '' fuser -k {data_port}/tcp >/dev/null 2>&1 || true; "
                f"fi"
            )
            cleanup_by_name_command = (
                f"for pid in $(pgrep -f {quoted_pattern} 2>/dev/null); do "
                f"[ \"$pid\" != \"$$\" ] && kill \"$pid\" >/dev/null 2>&1 || true; "
                f"done"
            )
            launch_command = (
                f"{cleanup_by_port_command}; "
                f"{cleanup_by_name_command}; "
                f"{cleanup_by_port_sudo_command}; "
                f"sleep 0.5; "
                f"{remote_venv_activate} && {remote_script}"
            )
            remote_command = f"bash -lc {shlex.quote(launch_command)}"
            remote_channel = ssh_client.get_transport().open_session()
            remote_channel.get_pty()
            remote_channel.exec_command(remote_command)

            # If the channel exits immediately, startup failed and local socket should not start.
            time.sleep(1.0)
            if remote_channel.exit_status_ready():
                exit_status = remote_channel.recv_exit_status()
                early_output = ""
                if remote_channel.recv_ready():
                    early_output += remote_channel.recv(4096).decode(errors="replace")
                if remote_channel.recv_stderr_ready():
                    early_output += remote_channel.recv_stderr(4096).decode(errors="replace")
                startup_state["ok"] = False
                if early_output.strip():
                    startup_state["error"] = f"Remote script exited immediately with status {exit_status}. Output: {early_output.strip()}"
                else:
                    startup_state["error"] = f"Remote script exited immediately with status {exit_status}."
                startup_event.set()
            else:
                startup_state["ok"] = True
                startup_event.set()


            while True:
                if remote_channel.recv_ready():
                    data = remote_channel.recv(1024).decode()
                    output_queue.put(data)
                if remote_channel.recv_stderr_ready():
                    err_data = remote_channel.recv_stderr(1024).decode()
                    output_queue.put(err_data)
                if remote_channel.exit_status_ready():
                    exit_status = remote_channel.recv_exit_status()
                    if exit_status != 0:
                        output_queue.put(f"[ERROR] Remote script exited with status {exit_status}. If you see 'Address already in use', wait 5-10 seconds and start again.\n")
                    break

            ssh_client.close()
            output_queue.put("[INFO] Remote script ended.\n")
        except Exception as e:
            startup_state["ok"] = False
            startup_state["error"] = f"Failed to start remote script on host {ssh_host}: {e}"
            startup_event.set()
            output_queue.put(f"[ERROR] Failed to start remote script: {e}\n")

    threading.Thread(target=task, daemon=True).start()
    print("Attempting to remote in to the Raspberry Pi...")
    startup_event.wait(timeout=15)
    if startup_state["ok"]:
        output_queue.put("[INFO] Remote script startup confirmed. Starting local data client...\n")
        local_script_callback()
    else:
        output_queue.put(f"[ERROR] {startup_state['error']}\n")

def stop_remote_script():
    global remote_channel, ssh_client
    if remote_channel is not None:
        try:
            remote_channel.close()
        except Exception:
            pass  # Ignore errors if already closed

    # Best-effort remote cleanup in case the script remains running after channel close.
    try:
        if ssh_client is not None and ssh_client.get_transport() and ssh_client.get_transport().is_active():
            ssh_config = get_ssh_config()
            script_pattern = get_remote_script_pattern(ssh_config['script_path'])
            data_port = ssh_config['data_port']
            quoted_password = shlex.quote(ssh_config['password'])
            cleanup_cmd = (
                f"pkill -f {shlex.quote(script_pattern)} >/dev/null 2>&1 || true; "
                f"if command -v lsof >/dev/null 2>&1; then "
                f"for pid in $(lsof -t -iTCP:{data_port} -sTCP:LISTEN 2>/dev/null); do "
                f"kill \"$pid\" >/dev/null 2>&1 || true; "
                f"done; "
                f"elif command -v fuser >/dev/null 2>&1; then "
                f"fuser -k {data_port}/tcp >/dev/null 2>&1 || true; "
                f"fi; "
                f"if command -v sudo >/dev/null 2>&1 && command -v fuser >/dev/null 2>&1; then "
                f"echo {quoted_password} | sudo -S -p '' fuser -k {data_port}/tcp >/dev/null 2>&1 || true; "
                f"fi"
            )
            ssh_client.exec_command(f"bash -lc {shlex.quote(cleanup_cmd)}")
    except Exception:
        pass

    output_queue.put("[INFO] Remote script manually stopped.\n")

class RemoteScriptGUI(QMainWindow):
    def __init__(self, shared_status, connection=None):
        super().__init__()
        self.shared_status = shared_status
        #self.connection = connection
        self.setWindowTitle("Remote Script Controller")

        # Get screen geometry and set to top right quarter
        screen = QDesktopWidget().screenGeometry()
        width = screen.width() // 2
        height = screen.height() // 2
        x = 0
        y = screen.height() - height
        self.setGeometry(x, y, width, height)

        # Load hardware configuration
        hardware_config = config.get('hardware.tactile', {})
        self.threshold = hardware_config.get('threshold', 200)
        self.last_force = 0
        self.baseline_force = hardware_config.get('baseline_force', 0)
        self.force_history = []
        self.rezero_time = hardware_config.get('rezero_time', 2)  # seconds
        self.rezero_threshold = hardware_config.get('rezero_threshold', 50)  # force units
        self.last_rezero_time = time.time()

        self.lsl_enabled = self.shared_status['lsl_enabled']
        self.touch_detection_armed = self.shared_status.get('touch_detection_armed', False)

        # Timer to sync arm state with shared_status (cross-process / cross-window)
        self.sync_timer = QTimer()
        self.sync_timer.timeout.connect(self.sync_touch_detection_state)
        self.sync_timer.start(200)  # Check every 200 ms

        # Persistent socket for label sending
        self.label_sock = None
        self.label_sock_lock = threading.Lock()
        self.last_touch_state = False  # For edge detection

        # Connect to control window for label sending
        #threading.Thread(target=self.connect_label_socket, daemon=True).start()

        # Start a thread to listen for control messages
        #threading.Thread(target=self.listen_for_control, daemon=True).start()

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.status_label = QLabel("Status: Ready")
        layout.addWidget(self.status_label)

        self.force_label = QLabel("Current Force: 0")
        layout.addWidget(self.force_label)

        self.threshold_box = QSpinBox()
        self.threshold_box.setRange(0, 2047)
        self.threshold_box.setValue(self.threshold)
        self.threshold_box.setPrefix("Threshold: ")
        self.threshold_box.valueChanged.connect(self.set_threshold)
        layout.addWidget(self.threshold_box)

        self.start_button = QPushButton("Start Remote Script")
        self.start_button.clicked.connect(self.start_script)
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop Remote Script")
        self.stop_button.clicked.connect(self.stop_script)
        layout.addWidget(self.stop_button)

        self.output_box = QTextEdit()
        self.output_box.setReadOnly(True)
        layout.addWidget(self.output_box)

        # Timer to update output from queue
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_output)
        self.timer.start(300)

        self.connected = False

        self.lsl_tactile_stream = LSLTactileStream()

    #def connect_label_socket(self):
    #    """Establish a persistent connection to the control window for label sending."""
    #    while self.label_sock is None:
    #        try:
    #            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #            sock.connect(('localhost', 9999))  # Use the correct port for control_window
    #            self.label_sock = sock
    #            print("Connected to control window for label sending.")
    #        except Exception as e:
    #            print(f"Label socket connection failed, retrying: {e}")
    #            time.sleep(0.5)

    def set_threshold(self, value):
        self.threshold = value

    def set_baseline(self):
        self.baseline_force = self.last_force
        self.status_label.setText(f"Baseline set to {self.baseline_force}")

    def start_script(self):
        self.status_label.setText("Status: Starting remote script...")
        threading.Thread(target=lambda: start_remote_script(self.start_local_script), daemon=True).start()
        #start_remote_script(on_success=lambda: self.send_label_to_control("tactile_started"))

    def start_local_script(self):
        """Connect to the Pi force stream and feed parsed samples into output_queue."""
        ssh_config = get_ssh_config()
        remote_host = ssh_config['host']
        port = ssh_config['data_port']
        output_file = config.get_absolute_path('paths.tactile_data_file')

        def read_socket():
            buffer = ""
            try:
                sock = None
                last_error = None
                for _ in range(20):
                    try:
                        sock = socket.create_connection((remote_host, port), timeout=2)
                        break
                    except OSError as exc:
                        last_error = exc
                        time.sleep(0.5)

                if sock is None:
                    raise ConnectionError(
                        f"Could not connect to tactile data socket {remote_host}:{port}. "
                        f"Last error: {last_error}"
                    )

                logging.info(f"[TACTILE] Connected to force stream at {remote_host}:{port}")
                self.send_label_to_control("tactile_connected")

                with sock, open(output_file, "ab") as handle:
                    while True:
                        data = sock.recv(1024)
                        if not data:
                            logging.warning("[TACTILE] Force stream closed by remote host.")
                            break
                        handle.write(data)
                        buffer += data.decode(errors="replace")
                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            line = line.strip()
                            if line:
                                output_queue.put(line + "\n")
            except KeyboardInterrupt:
                logging.info("[TACTILE] Force stream reader stopped by user.")
            except Exception as exc:
                msg = f"[ERROR] Local tactile data connection failed: {exc}\n"
                output_queue.put(msg)
                logging.error(msg.strip())

        threading.Thread(target=read_socket, daemon=True).start()

    def stop_script(self):
        self.status_label.setText("Status: Stopping remote script...")
        stop_remote_script()

    def update_output(self):
        while not output_queue.empty():
            data = output_queue.get()
            if data.startswith("[ERROR]") or data.startswith("[INFO]"):
                self.output_box.append(data.strip())
                self.output_box.moveCursor(self.output_box.textCursor().End)
                continue

            self.output_box.append(data.strip())
            self.output_box.moveCursor(self.output_box.textCursor().End)
            for line in data.strip().splitlines():
                if "," in line:
                    self._process_force_line(line)

    def _process_force_line(self, line):
        try:
            parts = line.split(",")
            if len(parts) != 2:
                return
            _timestamp, force = float(parts[0]), int(parts[1])
            self.last_force = force
            adjusted_force = self.last_force - self.baseline_force
            touched = adjusted_force > self.threshold
            touched_int = int(touched)

            self.lsl_tactile_stream.push_touch(touched_int)
            self.force_label.setText(
                f"Current Force: {force} (Adj: {adjusted_force}, Thr: {self.threshold})"
            )

            armed = bool(self.shared_status.get('touch_detection_armed', False))

            if touched and not self.last_touch_state:
                logging.info(
                    "[TACTILE] THRESHOLD CROSSED force=%s adj=%s threshold=%s armed=%s",
                    force, adjusted_force, self.threshold, armed,
                )
                if armed:
                    self.send_label_to_control("tactile_touch")
                    self.status_label.setText("Status: Force exceeds threshold — touch sent!")
                else:
                    logging.warning(
                        "[TACTILE] Touch ignored: detection NOT armed "
                        "(waiting for touch instruction / touchbox_lsl_true)."
                    )
                    self.status_label.setText(
                        f"Status: Threshold crossed but NOT armed (adj={adjusted_force})"
                    )
            elif not touched:
                self.status_label.setText("Status: Waiting for touch...")

            self.last_touch_state = touched

            now = time.time()
            self.force_history.append((now, force))
            self.force_history = [
                (t, f) for t, f in self.force_history if now - t <= self.rezero_time
            ]
            forces = [f for t, f in self.force_history]
            if forces:
                min_force = min(forces)
                max_force = max(forces)
                if (
                    (max_force - min_force) < self.rezero_threshold
                    and (now - self.last_rezero_time) > self.rezero_time
                ):
                    self.baseline_force = force
                    self.last_rezero_time = now
                    logging.info("[TACTILE] Auto re-zeroed baseline to %s", force)
                    self.status_label.setText(f"Auto re-zeroed at {force}")
        except Exception as exc:
            logging.debug("[TACTILE] Skipped unparsable force line %r: %s", line, exc)

    #def listen_for_control(self):
    #    # Listen on a local port for control messages
    #    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #    sock.bind(('localhost', 9999))  # Pick a free port
    #    sock.listen(1)
    #    while True:
    #        conn, addr = sock.accept()
    #        with conn:
    #            data = conn.recv(1024).decode()
    #            try:
    #                msg = json.loads(data)
    #                action = msg.get("action")
    #                if action == "set_lsl_enabled":
    #                    self.lsl_enabled = msg.get("enabled", True)
    #                    self.status_label.setText(f"LSL enabled: {self.lsl_enabled}")
    #                elif action == "touchbox_lsl_true":
    #                    self.lsl_enabled = True
    #                    self.status_label.setText("LSL enabled: True")
    #                    print("LSL enabled from control window.")
    #            except Exception as e:
    #                print("Error parsing control message:", e)

    def send_label_to_control(self, label):
        """Send a tactile event to the control window on the dedicated local port."""
        msg = {"action": label}
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2.0)
            sock.connect(('localhost', TACTILE_LOCAL_PORT))
            sock.sendall((json.dumps(msg) + "\n").encode('utf-8'))
            sock.close()
            logging.info("[TACTILE] Sent to control window (port %s): %s", TACTILE_LOCAL_PORT, msg)
        except Exception as exc:
            logging.error(
                "[TACTILE] Could not send %s to control window on port %s: %s",
                label, TACTILE_LOCAL_PORT, exc,
            )

    def sync_touch_detection_state(self):
        armed = bool(self.shared_status.get('touch_detection_armed', False))
        lsl = bool(self.shared_status.get('lsl_enabled', False))
        if self.touch_detection_armed != armed:
            self.touch_detection_armed = armed
            logging.info("[TACTILE] touch_detection_armed -> %s", armed)
            self.status_label.setText(f"Touch detection armed: {armed}")
        if self.lsl_enabled != lsl:
            self.lsl_enabled = lsl

def run_tactile_setup(shared_status, connection):
    app = QApplication(sys.argv)
    window = RemoteScriptGUI(shared_status, connection)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    from multiprocessing import Manager
    app = QApplication(sys.argv)
    manager = Manager()
    shared_status = manager.dict()
    shared_status['lsl_enabled'] = False
    shared_status['touch_detection_armed'] = False
    shared_status['pending_touch_advance'] = False
    window = RemoteScriptGUI(shared_status)
    window.show()
    sys.exit(app.exec_())
