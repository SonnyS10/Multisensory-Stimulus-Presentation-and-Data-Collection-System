import sys
sys.path.append('\\Users\\cpl4168\\Documents\\Paid Research\\Software-for-Paid-Research-')
from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel, QPushButton, QCheckBox, QApplication, QMessageBox
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QMetaObject, Qt
import time
import json
import threading
from eeg_stimulus_project.gui.sidebar import Sidebar
from eeg_stimulus_project.gui.main_frame import MainFrame
from eeg_stimulus_project.gui.display_window import DisplayWindow, MirroredDisplayWindow
from eeg_stimulus_project.data.data_saving import Save_Data
from eeg_stimulus_project.utils.labrecorder import LabRecorder
from eeg_stimulus_project.utils.pupil_labs import PupilLabs
from eeg_stimulus_project.lsl.labels import LSLLabelStream
import logging
from logging.handlers import QueueHandler


class GUI(QMainWindow):
    def __init__(self, connection, shared_status, log_queue, base_dir, test_number, client=False, alcohol_folder=None, non_alcohol_folder=None):
        super().__init__()
        self.shared_status = shared_status
        self.connection = connection
        self.client = client
        self.log_queue = log_queue
        self.alcohol_folder = alcohol_folder
        self.non_alcohol_folder = non_alcohol_folder
        
        if connection is not None:
            self.start_listener()

        # Set up logging
        self.setup_logging(log_queue)

        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()

        self.base_dir = base_dir
        self.test_number = test_number
        self.setWindowTitle("Experiment Control Window")
        self.setGeometry(0, 100, screen_geometry.width() // 2, screen_geometry.height() - 150)
        self.setMinimumSize(800, 600)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QHBoxLayout(self.central_widget)
        
        self.sidebar = Sidebar(self)
        self.main_layout.addWidget(self.sidebar)
        
        self.main_frame = MainFrame(self)
        self.main_layout.addWidget(self.main_frame)
        
        self.stacked_widget = self.main_frame.stacked_widget
        
        #Passive Test Frames
        self.unisensory_neutral_visual = self.create_frame("Unisensory Neutral Visual", is_stroop_test=False)
        self.unisensory_alcohol_visual = self.create_frame("Unisensory Alcohol Visual", is_stroop_test=False)
        self.multisensory_neutral_visual_olfactory = self.create_frame("Multisensory Neutral Visual & Olfactory", is_stroop_test=False)
        self.multisensory_alcohol_visual_olfactory = self.create_frame("Multisensory Alcohol Visual & Olfactory", is_stroop_test=False)
        self.multisensory_neutral_visual_tactile_olfactory = self.create_frame("Multisensory Neutral Visual, Tactile & Olfactory", is_stroop_test=False)
        self.multisensory_alcohol_visual_tactile_olfactory = self.create_frame("Multisensory Alcohol Visual, Tactile & Olfactory", is_stroop_test=False)
        
        #Stroop Test Frames
        self.multisensory_alcohol_visual_tactile = self.create_frame("Stroop Multisensory Alcohol (Visual & Tactile)", is_stroop_test=True)
        self.multisensory_neutral_visual_tactile = self.create_frame("Stroop Multisensory Neutral (Visual & Tactile)", is_stroop_test=True)
        self.multisensory_alcohol_visual_olfactory2 = self.create_frame("Stroop Multisensory Alcohol (Visual & Olfactory)", is_stroop_test=True)
        self.multisensory_neutral_visual_olfactory2 = self.create_frame("Stroop Multisensory Neutral (Visual & Olfactory)", is_stroop_test=True)

        # Instructions Frame
        self.instruction_frame = InstructionFrame(self)
        
        # Add new frames to stacked_widget
        #IN THE FUTURE WE ADD A BEGINNING FRAME THAT HAS INTSRUCTIONS
        self.stacked_widget.addWidget(self.unisensory_neutral_visual)
        self.stacked_widget.addWidget(self.unisensory_alcohol_visual)
        self.stacked_widget.addWidget(self.multisensory_neutral_visual_olfactory)
        self.stacked_widget.addWidget(self.multisensory_alcohol_visual_olfactory)
        self.stacked_widget.addWidget(self.multisensory_neutral_visual_tactile_olfactory)
        self.stacked_widget.addWidget(self.multisensory_alcohol_visual_tactile_olfactory)
        self.stacked_widget.addWidget(self.multisensory_alcohol_visual_tactile)
        self.stacked_widget.addWidget(self.multisensory_neutral_visual_tactile)
        self.stacked_widget.addWidget(self.multisensory_alcohol_visual_olfactory2)
        self.stacked_widget.addWidget(self.multisensory_neutral_visual_olfactory2)
        self.stacked_widget.addWidget(self.instruction_frame)
        
        self.stacked_widget.setCurrentWidget(self.instruction_frame)

        self._latency_test_active = False
        self._latency_rtts = []
        self._latency_test_count = 0
        
    #Functions to show different frames
    def create_frame(self, title, is_stroop_test=False):
        return Frame(self, title, self.connection, is_stroop_test, self.shared_status, self.base_dir, self.test_number, self.client, self.log_queue)
    
    def show_unisensory_neutral_visual(self):
        self.stacked_widget.setCurrentWidget(self.unisensory_neutral_visual)
    
    def show_unisensory_alcohol_visual(self):
        self.stacked_widget.setCurrentWidget(self.unisensory_alcohol_visual)
    
    def show_multisensory_neutral_visual_olfactory(self):
        self.stacked_widget.setCurrentWidget(self.multisensory_neutral_visual_olfactory)
    
    def show_multisensory_alcohol_visual_olfactory(self):
        self.stacked_widget.setCurrentWidget(self.multisensory_alcohol_visual_olfactory)
    
    def show_multisensory_neutral_visual_tactile_olfactory(self):
        self.stacked_widget.setCurrentWidget(self.multisensory_neutral_visual_tactile_olfactory)
    
    def show_multisensory_alcohol_visual_tactile_olfactory(self):
        self.stacked_widget.setCurrentWidget(self.multisensory_alcohol_visual_tactile_olfactory)
    
    def show_multisensory_alcohol_visual_tactile(self):
        self.stacked_widget.setCurrentWidget(self.multisensory_alcohol_visual_tactile)
    
    def show_multisensory_neutral_visual_tactile(self):
        self.stacked_widget.setCurrentWidget(self.multisensory_neutral_visual_tactile)
    
    def show_multisensory_alcohol_visual_olfactory2(self):
        self.stacked_widget.setCurrentWidget(self.multisensory_alcohol_visual_olfactory2)
    
    def show_multisensory_neutral_visual_olfactory2(self):
        self.stacked_widget.setCurrentWidget(self.multisensory_neutral_visual_olfactory2)

    def show_instruction_frame(self):
        self.stacked_widget.setCurrentWidget(self.instruction_frame)

    def show_first_test_frame(self):
        self.stacked_widget.setCurrentWidget(self.unisensory_neutral_visual)
    
    # Function to open the secondary GUI and its mirror widget in the middle frame.
    # This function is called when the checkbox is checked/unchecked
    def open_secondary_gui(self, state, log_queue, label_stream, eyetracker=None, shared_status=None):
        def any_display_widget_open():
            # Check all frames for an open display_widget
            frames = [
                self.unisensory_neutral_visual,
                self.unisensory_alcohol_visual,
                self.multisensory_neutral_visual_olfactory,
                self.multisensory_alcohol_visual_olfactory,
                self.multisensory_neutral_visual_tactile_olfactory,
                self.multisensory_alcohol_visual_tactile_olfactory,
                self.multisensory_alcohol_visual_tactile,
                self.multisensory_neutral_visual_tactile,
                self.multisensory_alcohol_visual_olfactory2,
                self.multisensory_neutral_visual_olfactory2,
            ]
            return any(getattr(f, 'display_widget', None) is not None for f in frames)

        current_frame = self.stacked_widget.currentWidget()  # Get the active Frame
        if state == Qt.Checked:
            if any_display_widget_open():
                logging.info("A display widget is already open in another frame. Not creating a new one.")
                return
            if not hasattr(current_frame, 'display_widget') or current_frame.display_widget is None:
                current_test = self.get_current_test()
                # Create both widgets
                current_frame.display_widget = DisplayWindow(
                    self.connection, log_queue, label_stream, current_frame, current_test,
                    self.base_dir, self.test_number, eyetracker=eyetracker, shared_status=shared_status, client=self.client,
                    alcohol_folder=self.alcohol_folder,
                    non_alcohol_folder=self.non_alcohol_folder
                )
                current_frame.display_widget.experiment_started.connect(current_frame.enable_pause_resume_buttons)
                current_frame.mirror_display_widget = MirroredDisplayWindow(current_frame, current_test=current_test)
                current_frame.display_widget.set_mirror(current_frame.mirror_display_widget)
                # Add both to the middle_frame layout
                middle_layout = current_frame.middle_frame.layout()  # Or however you access the layout
                middle_layout.addWidget(current_frame.mirror_display_widget)
                middle_layout.setStretchFactor(current_frame.mirror_display_widget, 1)  # Optional, ensures it gets all available space
                # Show the main display as a window
                current_frame.display_widget.show()
            else:
                logging.info("Display widget already exists, not creating a new one.")
        else:
            #Remove/hide the widgets when the stop button is pressed
            if hasattr(current_frame, 'display_widget') and current_frame.display_widget is not None:
                current_frame.display_widget.setParent(None)
                current_frame.display_widget = None
            if hasattr(current_frame, 'mirror_display_widget') and current_frame.mirror_display_widget is not None:
                current_frame.mirror_display_widget.setParent(None)
                current_frame.mirror_display_widget = None

    #A function to get the current test name
    def get_current_test(self):
        current_widget = self.stacked_widget.currentWidget()
        if current_widget == self.unisensory_neutral_visual:
            return 'Unisensory Neutral Visual'
        elif current_widget == self.unisensory_alcohol_visual:
            return 'Unisensory Alcohol Visual'
        elif current_widget == self.multisensory_neutral_visual_olfactory:
            return 'Multisensory Neutral Visual & Olfactory'
        elif current_widget == self.multisensory_alcohol_visual_olfactory:
            return 'Multisensory Alcohol Visual & Olfactory'
        elif current_widget == self.multisensory_neutral_visual_tactile_olfactory:
            return 'Multisensory Neutral Visual, Tactile & Olfactory'
        elif current_widget == self.multisensory_alcohol_visual_tactile_olfactory:
            return 'Multisensory Alcohol Visual, Tactile & Olfactory'
        elif current_widget == self.multisensory_alcohol_visual_tactile:
            return 'Stroop Multisensory Alcohol (Visual & Tactile)'
        elif current_widget == self.multisensory_neutral_visual_tactile:
            return 'Stroop Multisensory Neutral (Visual & Tactile)'
        elif current_widget == self.multisensory_alcohol_visual_olfactory2:
            return 'Stroop Multisensory Alcohol (Visual & Olfactory)'
        elif current_widget == self.multisensory_neutral_visual_olfactory2:
            return 'Stroop Multisensory Neutral (Visual & Olfactory)'
        else:
            return None

    def start_latency_test(self):
        if self._latency_test_active:
            return  # Already running
        self._latency_test_active = True
        self._latency_rtts = []
        self._latency_test_count = 0
        self.instruction_frame.latency_label.setText("Measuring latency...")
        def ping_loop():
            start_time = time.time()
            while time.time() - start_time < 5.0:
                self.send_latency_ping(single_test=False)
                time.sleep(.1)  # 10 pings per second
            # After 5 seconds, show average
            self._latency_test_active = False
            if self._latency_rtts:
                avg = sum(self._latency_rtts) / len(self._latency_rtts)
                self.instruction_frame.update_latency(0, count=len(self._latency_rtts), avg=avg)
            else:
                self.instruction_frame.latency_label.setText("No latency samples received.")
        threading.Thread(target=ping_loop, daemon=True).start()

    def send_latency_ping(self, single_test=True):
        if self.connection:
            self._ping_time = time.time()
            msg = {"action": "latency_ping", "timestamp": self._ping_time}
            try:
                self.connection.sendall((json.dumps(msg) + "\n").encode('utf-8'))
            except Exception as e:
                logging.info(f"Error sending ping: {e}")
            if single_test:
                self._latency_test_active = False  # For single ping

    def handle_latency_pong(self, pong_msg):
        pong_time = time.time()
        sent_time = pong_msg.get("timestamp")
        if sent_time:
            rtt = pong_time - sent_time
            latency_ms = rtt * 1000
            if self._latency_test_active:
                self._latency_rtts.append(latency_ms)
                self._latency_test_count += 1
            else:
                self.instruction_frame.update_latency(latency_ms)

    def start_listener(self):
        def listen():
            buffer = ""
            while True:
                try:
                    data = self.connection.recv(4096).decode('utf-8')
                    if not data:
                        break
                    buffer += data
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        if not line.strip():
                            continue
                        msg = json.loads(line)
                        if msg.get("action") == "latency_pong":
                            self.handle_latency_pong(msg)
                        elif msg.get("action") == "host_status":
                            status = msg.get("status", "Unknown")
                            self.instruction_frame.update_status(status)
                        elif msg.get("action") == "object_touched":
                            current_frame = self.stacked_widget.currentWidget()
                            if hasattr(current_frame, 'display_widget') and current_frame.display_widget is not None:
                                QMetaObject.invokeMethod(current_frame.display_widget, "end_touch_instruction_and_advance", Qt.QueuedConnection)
                except Exception as e:
                    logging.info(f"Listener error: {e}")
                    break
        threading.Thread(target=listen, daemon=True).start()

    def setup_logging(self, log_queue):
        queue_handler = QueueHandler(log_queue)
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        logger.handlers = []  # Remove other handlers
        logger.addHandler(queue_handler)
        
class Frame(QFrame):
    def __init__(self, parent, title, connection, is_stroop_test=False, shared_status=None, base_dir=None, test_number=None, client=False, log_queue=None):
        super().__init__(parent)

        self.shared_status = shared_status
        self.base_dir = base_dir
        self.test_number = test_number
        self.labrecorder = None
        self.label_stream = None
        self.eyetracker = None
        self.connection = connection
        self.client = client
        self.log_queue = log_queue
        
        self.layout = QVBoxLayout(self)
        
        top_frame = QFrame(self)
        top_frame.setStyleSheet(f"background-color: rgb(146, 63, 179);")
        top_frame.setMaximumHeight(140)
        self.layout.addWidget(top_frame)
        
        top_layout = QVBoxLayout(top_frame)
        
        header = QLabel(title, self)
        header.setFont(QFont("Helvetica", 17, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet(f"background-color: rgb(146, 63, 179);")
        top_layout.addWidget(header)
        
        # Middle frame with the EEG graph or display windows
        self.middle_frame = QFrame(self)
        self.middle_frame.setStyleSheet(f"background-color: #CBC3E3;")
        self.middle_frame.setMinimumHeight(490)
        self.layout.addWidget(self.middle_frame)

        self.middle_frame.setLayout(QHBoxLayout())
        
        # Save parent reference for later use
        self.parent = parent

        #If the test is a stroop test, add these buttons and checkboxes
        if is_stroop_test:
            button_layout = QHBoxLayout()
            top_layout.addLayout(button_layout)

            self.start_button = QPushButton("Start", self)
            self.start_button.clicked.connect(self.start_button_clicked)
            button_layout.addWidget(self.start_button)

            stop_button = QPushButton("Stop", self)
            stop_button.clicked.connect(self.stop_button_clicked_stroop)  # <-- update this line
            button_layout.addWidget(stop_button)

            self.pause_button = QPushButton("Pause", self)
            self.pause_button.setEnabled(False)
            self.pause_button.clicked.connect(self.pause_display_window)
            button_layout.addWidget(self.pause_button)

            self.resume_button = QPushButton("Resume", self)
            self.resume_button.setEnabled(False)
            self.resume_button.clicked.connect(self.resume_display_window)
            button_layout.addWidget(self.resume_button)

            self.next_button = QPushButton("Next", self)
            self.next_button.setEnabled(False)  # Initially disabled
            self.next_button.clicked.connect(self.on_next_button_clicked)
            button_layout.addWidget(self.next_button)

            self.display_button = QCheckBox("Display", self)
            button_layout.addWidget(self.display_button)

            bottom_frame = QFrame(self)
            bottom_frame.setStyleSheet(f"background-color: #bc85fa;")
            bottom_frame.setMaximumHeight(70)
            self.layout.addWidget(bottom_frame)

        #I the test is NOT a stroop test(Passive Test), add these buttons and checkboxes
        if not is_stroop_test:
            button_layout = QHBoxLayout()
            top_layout.addLayout(button_layout)

            self.start_button = QPushButton("Start", self)
            self.start_button.clicked.connect(self.start_button_clicked)
            button_layout.addWidget(self.start_button)

            stop_button = QPushButton("Stop", self)
            stop_button.clicked.connect(self.stop_button_clicked_passive)
            button_layout.addWidget(stop_button)

            self.pause_button = QPushButton("Pause", self)  # <-- FIXED
            self.pause_button.setEnabled(False)
            self.pause_button.clicked.connect(self.pause_display_window)
            button_layout.addWidget(self.pause_button)

            self.resume_button = QPushButton("Resume", self)  # <-- FIXED
            self.resume_button.setEnabled(False)
            self.resume_button.clicked.connect(self.resume_display_window)
            button_layout.addWidget(self.resume_button)

            self.next_button = QPushButton("Next", self)
            self.next_button.setEnabled(False)  # Initially disabled
            self.next_button.clicked.connect(self.on_next_button_clicked)
            button_layout.addWidget(self.next_button)

            vr_button = QCheckBox("VR", self)
            button_layout.addWidget(vr_button)
                
            self.display_button = QCheckBox("Display", self)
            button_layout.addWidget(self.display_button)
                
            viewing_booth_button = QCheckBox("Viewing Booth", self)
            button_layout.addWidget(viewing_booth_button)

            bottom_frame = QFrame(self)
            bottom_frame.setStyleSheet(f"background-color: #bc85fa;")
            bottom_frame.setMaximumHeight(70)
            self.layout.addWidget(bottom_frame)

    #Function to handle what happens when the start button is clicked for stroop tests and passive tests when the display button is checked
    #IN THE FUTURE WE NEED TO ADD WHAT HAPPENS WHEN THE OTHER BUTTONS ARE CHECKED(VR, Viewing Booth)
    def start_button_clicked(self):
        # Check if at least one of the checkboxes is checked
        checked = False
        # Defensive: check if the attributes exist (they may not in all test types)
        for attr in ['display_button', 'vr_button', 'viewing_booth_button']:
            btn = getattr(self, attr, None)
            if btn is not None and btn.isChecked():
                checked = True
                break

        if not checked:
            QMessageBox.critical(self, "Error", "Please select at least one display mode (VR, Display, or Viewing Booth) before starting.")
            return

        if hasattr(self, 'display_button') and self.display_button.isChecked():
            self.send_message({"action": "start_button", "test": self.parent.get_current_test()})
            if self.label_stream is None:                
                self.label_stream = LSLLabelStream()
                self.parent.open_secondary_gui(Qt.Checked, self.log_queue, label_stream=self.label_stream, eyetracker=self.eyetracker, shared_status=self.shared_status)
                self.start_button.setEnabled(False)  # Disable the start button after starting the stream
            if self.shared_status.get('lab_recorder_connected', False):
                if self.labrecorder is None or self.labrecorder.s is None:
                    self.labrecorder = LabRecorder(self.base_dir)
                if self.labrecorder and self.labrecorder.s is not None:
                    self.labrecorder.Start_Recorder(self.parent.get_current_test())
                else:
                    logging.info("LabRecorder not connected")
            else:
                logging.info("LabRecorder not connected in Control Window")
        else:
            self.parent.open_secondary_gui(Qt.Unchecked)

    #Function to handle what happens when the stop button is clicked for stroop tests(calls the data_saving file)
    def stop_button_clicked_stroop(self):
        self.send_message({"action": "stop_button", "test": self.parent.get_current_test()})

        save_data = Save_Data(self.base_dir, self.test_number)
        self.start_button.setEnabled(True)  # Re-enable the start button after stopping
        try:
            if hasattr(self, 'display_widget') and self.display_widget is not None:
                save_data.save_data_stroop(
                    self.parent.get_current_test(),
                    self.display_widget.user_data['user_inputs'],
                    self.display_widget.user_data['elapsed_time']
                )
            else:
                logging.info("No display_widget found for saving data.")        
        except Exception as e:
            logging.info(f"Error saving data: {e}")
        # Stop LabRecorder if connected
        if self.labrecorder and self.labrecorder.s is not None:
            self.labrecorder.Stop_Recorder()
        # Stop the eyetracker if connected`
        #if self.eyetracker and self.eyetracker.device is not None:
        #    self.eyetracker.stop_recording()
        if hasattr(self, 'display_widget') and self.display_widget is not None:
            self.display_widget.stopped = True
            self.display_widget.close()  # Close the display widget
        time.sleep(2)  # Give some time for the display widget to stop
        self.parent.open_secondary_gui(Qt.Unchecked, self.log_queue, label_stream=None)

    #Function to handle what happens when the stop button is clicked for passive tests(calls the data_saving file)
    def stop_button_clicked_passive(self):
        self.send_message({"action": "stop_button", "test": self.parent.get_current_test()})

        save_data = Save_Data(self.base_dir, self.test_number)
        self.start_button.setEnabled(True)  # Re-enable the start button after stopping
        try:
            if hasattr(self, 'display_widget') and self.display_widget is not None:
                save_data.save_data_passive(self.parent.get_current_test())
            else:
                logging.info("No display_widget found for saving data.")
        except Exception as e:
            logging.info(f"Error saving data: {e}")
        # Stop LabRecorder if connected
        if self.labrecorder and self.labrecorder.s is not None:
            self.labrecorder.Stop_Recorder()
        # Stop the eyetracker if connected`
        #if self.eyetracker and self.eyetracker.device is not None:
        #    self.eyetracker.stop_recording()
        if hasattr(self, 'display_widget') and self.display_widget is not None:
            self.display_widget.stopped = True
            self.display_widget.close()
        time.sleep(2)
        self.parent.open_secondary_gui(Qt.Unchecked, self.log_queue, label_stream=None)

    #Pauses the display window and the mirror display window
    def pause_display_window(self):
        self.display_widget.pause_trial()
        self.mirror_display_widget.pause_trial()

    #Resumes the display window and the mirror display window
    def resume_display_window(self):
        self.display_widget.resume_trial()
        self.mirror_display_widget.resume_trial()

    # Function to enable the pause and resume buttons(So they are not greyed out)
    def enable_pause_resume_buttons(self):
        self.pause_button.setEnabled(True)
        self.resume_button.setEnabled(True)

    def send_message(self, message_dict):
        if self.client:
            # If this is a client, send the message to the server
            try:
                self.connection.sendall((json.dumps(message_dict) + "\n").encode('utf-8'))
            except Exception as e:
                logging.info(f"Error sending message: {e}")

    def on_next_button_clicked(self):
        if hasattr(self, 'display_widget') and self.display_widget is not None:
            QMetaObject.invokeMethod(self.display_widget, "proceed_from_next_button", Qt.QueuedConnection)

class InstructionFrame(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

        layout = QVBoxLayout(self)
        label = QLabel("Welcome!\n\nPlease read the instructions carefully before starting.\n\n[Your instructions here]")
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignCenter)
        label.setFont(QFont("Arial", 16))
        layout.addWidget(label)

        # Latency check
        self.latency_label = QLabel("Latency: Not checked")
        self.latency_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.latency_label)

        latency_button = QPushButton("Check Latency")
        latency_button.setFont(QFont("Arial", 12))
        latency_button.clicked.connect(self.send_latency_ping)
        layout.addWidget(latency_button, alignment=Qt.AlignCenter)

        # Host status
        self.status_label = QLabel("Host Status: Unknown")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        continue_button = QPushButton("Continue")
        continue_button.setFont(QFont("Arial", 14))
        continue_button.clicked.connect(parent.show_first_test_frame)
        layout.addWidget(continue_button, alignment=Qt.AlignCenter)

    def send_latency_ping(self):
        if hasattr(self.parent, "start_latency_test"):
            self.parent.start_latency_test()
            
    def update_latency(self, latency_ms, count=None, avg=None):
        if avg is not None:
            self.latency_label.setText(f"Average Latency: {avg:.2f} ms ({count} samples)")
        else:
            self.latency_label.setText(f"Latency: {latency_ms:.2f} ms")
    
    def update_status(self, status_text):
        self.status_label.setText(f"Host Status: {status_text}")

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    # Create the application instance
    app = QApplication(sys.argv)

    # Create an instance of the GUI
    window = GUI()
    window.show()

    # Execute the application
    sys.exit(app.exec_())