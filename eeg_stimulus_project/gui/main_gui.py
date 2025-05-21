import sys
import os
sys.path.append('\\Users\\cpl4168\\Documents\\Paid Research\\Software-for-Paid-Research-')
from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel, QPushButton, QCheckBox
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from sidebar import Sidebar
from main_frame import MainFrame
from display_window import DisplayWindow
from eeg_stimulus_project.data.eeg_graph_widget import EEGGraphWidget
from eeg_stimulus_project.lsl.stream_manager import LSL
from eeg_stimulus_project.data.data_saving import Save_Data
from eeg_stimulus_project.utils.labrecorder import LabRecorder

class GUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Data Collection App")
        self.setGeometry(100, 100, 1100, 700)
        self.setMinimumSize(800, 600)  # Set a minimum size if needed
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QHBoxLayout(self.central_widget)
        
        self.sidebar = Sidebar(self)
        self.main_layout.addWidget(self.sidebar)
        
        self.main_frame = MainFrame(self)
        self.main_layout.addWidget(self.main_frame)
        
        self.stacked_widget = self.main_frame.stacked_widget
        
        self.unisensory_neutral_visual = self.create_frame("Unisensory Neutral Visual", is_stroop_test=False)
        self.unisensory_alcohol_visual = self.create_frame("Unisensory Alcohol Visual", is_stroop_test=False)
        self.multisensory_neutral_visual_olfactory = self.create_frame("Multisensory Neutral Visual & Olfactory", is_stroop_test=False)
        self.multisensory_alcohol_visual_olfactory = self.create_frame("Multisensory Alcohol Visual & Olfactory", is_stroop_test=False)
        self.multisensory_neutral_visual_tactile_olfactory = self.create_frame("Multisensory Neutral Visual, Tactile & Olfactory", is_stroop_test=False)
        self.multisensory_alcohol_visual_tactile_olfactory = self.create_frame("Multisensory Alcohol Visual, Tactile & Olfactory", is_stroop_test=False)
        
        # New frames for Stroop Test
        self.multisensory_alcohol_visual_tactile = self.create_frame("Multisensory Alcohol (Visual & Tactile)", is_stroop_test=True)
        self.multisensory_neutral_visual_tactile = self.create_frame("Multisensory Neutral (Visual & Tactile)", is_stroop_test=True)
        self.multisensory_alcohol_visual_olfactory2 = self.create_frame("Multisensory Alcohol (Visual & Olfactory)", is_stroop_test=True)
        self.multisensory_neutral_visual_olfactory2 = self.create_frame("Multisensory Neutral (Visual & Olfactory)", is_stroop_test=True)
        
        self.stacked_widget.addWidget(self.unisensory_neutral_visual)
        self.stacked_widget.addWidget(self.unisensory_alcohol_visual)
        self.stacked_widget.addWidget(self.multisensory_neutral_visual_olfactory)
        self.stacked_widget.addWidget(self.multisensory_alcohol_visual_olfactory)
        self.stacked_widget.addWidget(self.multisensory_neutral_visual_tactile_olfactory)
        self.stacked_widget.addWidget(self.multisensory_alcohol_visual_tactile_olfactory)
        
        # Add new frames to stacked_widget
        self.stacked_widget.addWidget(self.multisensory_alcohol_visual_tactile)
        self.stacked_widget.addWidget(self.multisensory_neutral_visual_tactile)
        self.stacked_widget.addWidget(self.multisensory_alcohol_visual_olfactory2)
        self.stacked_widget.addWidget(self.multisensory_neutral_visual_olfactory2)
        
        self.stacked_widget.setCurrentWidget(self.unisensory_neutral_visual)
        
        self.labrecorder = None
        self.labrecorder_connected = False
        
    def create_frame(self, title, is_stroop_test=False):
        return Frame(self, title, is_stroop_test)
    
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
    
    # New methods to show new frames
    def show_multisensory_alcohol_visual_tactile(self):
        self.stacked_widget.setCurrentWidget(self.multisensory_alcohol_visual_tactile)
    
    def show_multisensory_neutral_visual_tactile(self):
        self.stacked_widget.setCurrentWidget(self.multisensory_neutral_visual_tactile)
    
    def show_multisensory_alcohol_visual_olfactory2(self):
        self.stacked_widget.setCurrentWidget(self.multisensory_alcohol_visual_olfactory2)
    
    def show_multisensory_neutral_visual_olfactory2(self):
        self.stacked_widget.setCurrentWidget(self.multisensory_neutral_visual_olfactory2)
    
    def open_secondary_gui(self, state):
        if state == Qt.Checked:
            # Only open if not already open
            if not hasattr(self, 'display_window') or self.display_window is None or not self.display_window.isVisible():
                current_test = self.get_current_test()
                self.display_window = DisplayWindow(self, current_test=current_test)
                # When the window is closed, set self.display_window to None
                self.display_window.destroyed.connect(lambda: setattr(self, 'display_window', None))
                self.display_window.show()
        else:
            if hasattr(self, 'display_window') and self.display_window is not None:
                self.display_window.close()
                self.display_window = None
    
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
            return 'Multisensory Alcohol (Visual & Tactile)'
        elif current_widget == self.multisensory_neutral_visual_tactile:
            return 'Multisensory Neutral (Visual & Tactile)'
        elif current_widget == self.multisensory_alcohol_visual_olfactory2:
            return 'Multisensory Alcohol (Visual & Olfactory)'
        elif current_widget == self.multisensory_neutral_visual_olfactory2:
            return 'Multisensory Neutral (Visual & Olfactory)'
        else:
            return None
        
class Frame(QFrame):
    def __init__(self, parent, title, is_stroop_test=False):
        super().__init__(parent)
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
        
        # Middle frame with the EEG graph
        self.middle_frame = QFrame(self)
        self.middle_frame.setStyleSheet(f"background-color: #CBC3E3;")
        self.middle_frame.setMinimumHeight(490)
        self.layout.addWidget(self.middle_frame)

        middle_layout = QVBoxLayout(self.middle_frame)

        # Add EEGGraphWidget to the middle frame
        self.eeg_graph = EEGGraphWidget()
        middle_layout.addWidget(self.eeg_graph)

        # Add navigation buttons for EEG graph
        nav_layout = QHBoxLayout()
        middle_layout.addLayout(nav_layout)

        prev_button = QPushButton("Previous Page", self)
        prev_button.clicked.connect(self.eeg_graph.previous_page)
        nav_layout.addWidget(prev_button)

        next_button = QPushButton("Next Page", self)
        next_button.clicked.connect(self.eeg_graph.next_page)
        nav_layout.addWidget(next_button)
        
        # Save parent reference for later use
        self.parent = parent

        # Read from environment variables
        self.base_dir = os.environ.get('BASE_DIR', '')
        self.test_number = os.environ.get('TEST_NUMBER', '')

        if is_stroop_test:
            button_layout = QHBoxLayout()
            top_layout.addLayout(button_layout)

            start_button = QPushButton("Start", self)
            start_button.clicked.connect(self.start_button_clicked)
            button_layout.addWidget(start_button)

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

            self.display_button = QCheckBox("Display", self)
            button_layout.addWidget(self.display_button)

            bottom_frame = QFrame(self)
            bottom_frame.setStyleSheet(f"background-color: #bc85fa;")
            bottom_frame.setMaximumHeight(70)
            self.layout.addWidget(bottom_frame)

        if not is_stroop_test:
            button_layout = QHBoxLayout()
            top_layout.addLayout(button_layout)

            start_button = QPushButton("Start", self)
            start_button.clicked.connect(self.start_button_clicked)
            button_layout.addWidget(start_button)

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

            bottom_layout = QHBoxLayout(bottom_frame)

            visual_checkbox = QCheckBox("Visual", self)
            bottom_layout.addWidget(visual_checkbox)

            olfactory_checkbox = QCheckBox("Olfactory", self)
            bottom_layout.addWidget(olfactory_checkbox)

            tactile_checkbox = QCheckBox("Tactile", self)
            bottom_layout.addWidget(tactile_checkbox)

            input_keyboard_checkbox = QCheckBox("Input Keyboard", self)
            bottom_layout.addWidget(input_keyboard_checkbox)

            eye_tracker_checkbox = QCheckBox("Eye Tracker", self)
            bottom_layout.addWidget(eye_tracker_checkbox)

    def start_button_clicked(self):
        if self.display_button.isChecked():
            self.parent.open_secondary_gui(Qt.Checked)
            self.parent.display_window.experiment_started.connect(self.enable_pause_resume_buttons)
            #LSL.start_collection()
                # When you want to start recording:
            if self.parent.labrecorder_connected:
                self.parent.labrecorder.Start_Recorder(self.parent.get_current_test())
            else:
                print("LabRecorder connection failed, continuing in test mode.")
        else:
            self.parent.open_secondary_gui(Qt.Unchecked)

    def stop_button_clicked_stroop(self):
        save_data = Save_Data(self.base_dir, self.test_number)
        try:
            save_data.save_data_stroop(self.parent.get_current_test(), self.user_data['user_inputs'], self.user_data['elapsed_time'])
        except Exception as e:
            print(f"Error saving data: {e}")
        # When you want to stop recording:
        if self.parent.labrecorder_connected:
            self.parent.labrecorder.Stop_Recorder()
        self.parent.open_secondary_gui(Qt.Unchecked)

    def stop_button_clicked_passive(self):
        save_data = Save_Data(self.base_dir, self.test_number)
        try:
            save_data.save_data_passive(self.parent.get_current_test())
        except Exception as e:
            print(f"Error saving data: {e}")
        # When you want to stop recording:
        if self.parent.labrecorder_connected:
            self.parent.labrecorder.Stop_Recorder()
        self.parent.open_secondary_gui(Qt.Unchecked)
    
    def pause_display_window(self):
        if hasattr(self.parent, 'display_window') and self.parent.display_window is not None:
            self.parent.display_window.pause_trial()

    def resume_display_window(self):
        if hasattr(self.parent, 'display_window') and self.parent.display_window is not None:
            self.parent.display_window.resume_trial()

    def enable_pause_resume_buttons(self):
        self.pause_button.setEnabled(True)
        self.resume_button.setEnabled(True)

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