import sys
sys.path.append('C:\\Users\\cpl4168\\Documents\\Paid Research\\Software-for-Paid-Research-')
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QMainWindow, QWidget, QVBoxLayout, QStackedLayout, QSizePolicy, QPushButton
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt, QTimer, QEvent, pyqtSignal
from eeg_stimulus_project.stimulus.Display import Display
from eeg_stimulus_project.data.data_saving import Save_Data
from eeg_stimulus_project.lsl.labels import LSLLabelStream
from eeg_stimulus_project.utils.pupil_labs import PupilLabs
import os
import threading

#This is the class that creates the mirror display window that resides in the main display window to be used by the experimenter to make sure the experiment is running correctly
#It contains the same layout and functionality as the main display window, but it is not interactive
#It is used to show the experimenter what the subject is seeing
class MirroredDisplayWindow(QWidget):
    def __init__(self, parent=None, current_test=None):
        super().__init__(parent)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  

        self.current_test = current_test

        self.stacked_layout = QStackedLayout(self)

        # Overlay widget
        self.overlay_widget = QWidget()
        self.overlay_layout = QVBoxLayout(self.overlay_widget)
        self.overlay_widget.setStyleSheet("background-color: white;")
        self.overlay_widget.setGeometry(0, 0, 700, 650)

        self.instructions_label = QLabel(
            "Directions: [Your directions here]\n\nPress the SPACE BAR to begin the experiment.",
            self.overlay_widget
        )
        self.instructions_label.setFont(QFont("Arial", 18))
        self.instructions_label.setAlignment(Qt.AlignCenter)
        self.overlay_layout.addWidget(self.instructions_label)

        self.countdown_label = QLabel("", self.overlay_widget)
        self.countdown_label.setFont(QFont("Arial", 36, QFont.Bold))
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.setVisible(False)
        self.overlay_layout.addWidget(self.countdown_label)

        # Main experiment widget
        self.experiment_widget = QWidget()
        self.experiment_layout = QVBoxLayout(self.experiment_widget)

        bottom_frame = QFrame(self.experiment_widget)
        bottom_frame.setStyleSheet("background-color: #FFFFFF;")
        bottom_layout = QHBoxLayout(bottom_frame)
        self.image_label = QLabel(self.experiment_widget)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        bottom_layout.addWidget(self.image_label)
        self.experiment_layout.addWidget(bottom_frame)

        self.timer_label = QLabel("00:00:00", self.experiment_widget)
        self.timer_label.setFont(QFont("Arial", 20))
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setMaximumHeight(50)
        self.experiment_layout.addWidget(self.timer_label)

        self.stacked_layout.addWidget(self.overlay_widget)      # index 0
        self.stacked_layout.addWidget(self.experiment_widget)   # index 1

        self.stacked_layout.setCurrentIndex(0)

        self.paused = False

    #Method to update the mirror image
    def set_pixmap(self, pixmap):
        if pixmap:
            scaled_pixmap = pixmap.scaled(
                self.image_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
            self.set_overlay_visible(False)  # <-- Switch to experiment view
        else:
            self.image_label.clear()

    #Method to update the mirror text        
    def set_instruction_text(self, text=None, font=None):
        if text is None:
            text = "Press the 'Y' key if congruent.\nPress the 'N' key if incongruent."
        self.image_label.clear()
        self.instructions_label.setText(text)
        self.instructions_label.setAlignment(Qt.AlignCenter)
        self.instructions_label.setVisible(True)
        self.countdown_label.setVisible(False)  # <-- Hide countdown label
        label_height = self.instructions_label.height()
        if font is None:
            font_size = max(8, int(label_height * 0.04))
            font = QFont("Arial", font_size, QFont.Bold)
        self.instructions_label.setFont(font)
        self.set_overlay_visible(True)

    #Method to set the timer text
    def set_timer(self, text):
        self.timer_label.setText(text)

    #Method to set the overlay visibility
    def set_overlay_visible(self, visible):
        self.stacked_layout.setCurrentIndex(0 if visible else 1)

    #Method to set the countdown text
    def set_countdown(self, text, visible=True):
        self.countdown_label.setText(text)
        self.countdown_label.setVisible(visible)

    #Method to start the countdown only called from the DisplayWindow
    def start_countdown(self):
        self.instructions_label.setVisible(False)
        self.countdown_label.setVisible(True)
        self.countdown_seconds = 3
        self.countdown_label.setText(str(self.countdown_seconds))
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.countdown_timer.start(1000)

    #Method to update the countdown
    def update_countdown(self):
        self.countdown_seconds -= 1
        if self.countdown_seconds > 0:
            self.countdown_label.setText(str(self.countdown_seconds))
        else:
            self.countdown_timer.stop()
            self.countdown_label.setText("Go!")
            QTimer.singleShot(1000, self.begin_experiment)

    #Method to show the instruction for the next image
    def show_instruction_for_next_image(self, text=None, font=None):
        self.set_instruction_text(text, font)
        self.set_pixmap(None)

    #Method to show the image
    def begin_experiment(self):
        self.stacked_layout.setCurrentIndex(1)

    #Method to pause the trial, this method is called from the DisplayWindow when the trial is paused
    def pause_trial(self, event=None):
        self.paused = True

    #Method to resume the trial, this method is called from the DisplayWindow when the trial is resumed
    def resume_trial(self, event=None):
        self.paused = False
        
    def end_screen(self):
        # Create a new widget for the end screen
        end_widget = QWidget()
        end_widget.setStyleSheet("background-color: white;")
        end_layout = QVBoxLayout(end_widget)
        end_layout.setAlignment(Qt.AlignCenter)  # Center contents

        # Add a label with the end message
        end_label = QLabel("Test has ended.\n Please wait for the experimenter to close the test.", end_widget)
        end_label.setFont(QFont("Arial", 22))
        end_label.setAlignment(Qt.AlignCenter)
        end_layout.addWidget(end_label, alignment=Qt.AlignCenter)

        # Make the end_widget fill the mirrored window
        end_widget.setMinimumSize(self.size())
        end_widget.setMaximumSize(self.size())

        self.stacked_layout.addWidget(end_widget)
        self.stacked_layout.setCurrentWidget(end_widget)

#This is the main display window that contains the experiment and the logic to make the mirror display function 
#It is the main window that the subject sees and interacts with
class DisplayWindow(QMainWindow):
    experiment_started = pyqtSignal()

    def __init__(self, label_stream, parent=None, current_test=None, base_dir=None, test_number=None, eyetracker=None, shared_status=None):
        super().__init__(parent)
        
        self.shared_status = shared_status if shared_status else {'eyetracker_connected': False}
        self.eyetracker = eyetracker
        self.label_stream = label_stream if label_stream else LSLLabelStream()

        if self.shared_status.get('eyetracker_connected', False):
            # Eye tracker is connected, uses same instance of eye tracker or creates a new one if needed
            if self.eyetracker is None or self.eyetracker.device is None:
                self.eyetracker = PupilLabs()
            if self.eyetracker and self.eyetracker.device is not None:
                self.eyetracker.start_recording()
            else:
                print("Eyetracker not connected1")
        else:
            print("Eyetracker not connected2")

        #threads = [
        #    threading.Thread(target=self.set_eyetracker(self.eyetracker)),
        #]
#
        #for t in threads:
        #    t.start()
#
        #for t in threads:
        #    t.join()
     
        self.current_label = None

        self.current_test = current_test
        self.base_dir = base_dir
        self.test_number = test_number

        self.setWindowTitle("Display App")
        self.setGeometry(100, 100, 700, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.stacked_layout = QStackedLayout(central_widget)

        self.overlay_widget = QWidget()
        self.overlay_layout = QVBoxLayout(self.overlay_widget)
        self.overlay_widget.setStyleSheet("background-color: white;")
        self.overlay_widget.setGeometry(0, 0, 700, 650)

        #This is the overlay that shows the instructions for the experiment that the subject sees
        #IN THE FUTURE THIS SHOULD BE DIFFERENT FOR EACH TEST
        self.instructions_label = QLabel("Directions: [Your directions here]\n\nPress the SPACE BAR to begin the experiment.", self.overlay_widget)
        self.instructions_label.setFont(QFont("Arial", 18))
        self.instructions_label.setAlignment(Qt.AlignCenter)
        self.overlay_layout.addWidget(self.instructions_label)

        self.countdown_label = QLabel("", self.overlay_widget)
        self.countdown_label.setFont(QFont("Arial", 36, QFont.Bold))
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.setVisible(False)
        self.overlay_layout.addWidget(self.countdown_label)

        # Main experiment widget
        self.experiment_widget = QWidget()
        self.experiment_layout = QVBoxLayout(self.experiment_widget)

        # Bottom frame with the image
        bottom_frame = QFrame(self.experiment_widget)
        bottom_frame.setStyleSheet("background-color: #FFFFFF;")
        bottom_layout = QHBoxLayout(bottom_frame)
        self.image_label = QLabel(self.experiment_widget)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        bottom_layout.addWidget(self.image_label)
        self.experiment_layout.addWidget(bottom_frame)

        # Timer label
        self.timer_label = QLabel("00:00:00", self.experiment_widget)
        self.timer_label.setFont(QFont("Arial", 20))
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setMaximumHeight(50)
        self.experiment_layout.addWidget(self.timer_label)

        # Add both widgets to the stacked layout
        self.stacked_layout.addWidget(self.overlay_widget)      # index 0
        self.stacked_layout.addWidget(self.experiment_widget)   # index 1

        # Show overlay first
        self.stacked_layout.setCurrentIndex(0)

        # Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.elapsed_time = 0

        # Passive Transition timer
        self.image_transition_timer = QTimer(self)
        self.image_transition_timer.setSingleShot(True)
        self.image_transition_timer.timeout.connect(self._on_image_transition)

        # Stroop Transition timer
        self.stroop_transition_timer = QTimer(self)
        self.stroop_transition_timer.setSingleShot(True)
        self.stroop_transition_timer.timeout.connect(self.hide_image)

        #LSL Label Polling Timer - good for debugging 
        #self.label_poll_timer = QTimer(self)
        #self.label_poll_timer.timeout.connect(self.poll_label)
        #self.label_poll_timer.start(1000)  # Poll every 100 ms (change as needed)

        self.Paused = False

        # User data
        self.user_data = {
            'user_inputs': [],
            'elapsed_time': []
        }  # List to store user inputs and elapsed time

        self.setFocusPolicy(Qt.StrongFocus)
        self.countdown_seconds = 3

        self.current_pixmap = None

        # Initialize image index after pause
        self.paused_image_index = 0
        # Initialize paused time
        self.paused_time = 0 

    #This method is called when the user presses the space bar to start the experiment, it handles the countdown and the selection of the test to start the experiment
    def run_trial(self, event=None):
        current_test = self.current_test
        print(f"Current test: {current_test}")
        #print(f"Available tests: {list(Display.test_assets.keys())}")
        if current_test:
            try:
                if self.paused_time > 0:
                    self.elapsed_time = self.paused_time
                    self.current_image_index = self.paused_image_index - 1
                    self.timer.start(1)  # Start the timer with 100 ms interval
                else:
                    self.images = Display.test_assets[current_test]
                    self.current_image_index = 0  # Reset the image index for the new trial
                    self.elapsed_time = 0  # Reset the elapsed time
                    self.timer.start(1)  # Start the timer with 100 ms interval
                if current_test in ['Multisensory Alcohol (Visual & Tactile)', 'Multisensory Neutral (Visual & Tactile)', 'Multisensory Alcohol (Visual & Olfactory)', 'Multisensory Neutral (Visual & Olfactory)']:
                    self.display_images_stroop()
                else:
                    self.display_images_passive()
            except KeyError as e:
                print(f"KeyError: {e}")

    #This method is called when the user presses the pause button to pause the trial, it stops the timer and the image transition timer, it also stores the current image index and the elapsed time, it also tells the mirror widget to pause
    def pause_trial(self, event=None):
        self.timer.stop()
        self.image_transition_timer.stop()  # Stop the image transition timer
        if hasattr(self, 'stroop_transition_timer'):
            self.stroop_transition_timer.stop()  # Stop the Stroop timer
        self.paused_time = self.elapsed_time
        print(self.paused_time)
        self.paused_image_index = self.current_image_index 
        print(self.paused_image_index)
         # Store the current image index
        self.Paused = True
        if hasattr(self, 'mirror_widget') and self.mirror_widget is not None:
            self.mirror_widget.pause_trial()

    #This method is called when the user presses the resume button to resume the trial, it starts the timer and the image transition timer, it also sets the paused time to 0 and also tells the mirror widget to resume
    #It also calls the run_trial method to start the trial again
    def resume_trial(self, event=None):
        self.Paused = False
        self.run_trial()  # Resume the trial
        if hasattr(self, 'mirror_widget') and self.mirror_widget is not None:
            self.mirror_widget.resume_trial()

    #This is the main logic for displaying the images in the passive test, it handles the image transition and the timer for the images         
    def display_images_passive(self):
        if self.current_image_index < len(self.images):
            img = self.images[self.current_image_index]
            pixmap = QPixmap(img.filename)
            self.current_pixmap = pixmap
            self.update_image_label()
            # Push the filename (without extension) as label
            if hasattr(img, 'filename'):
                label = f"{os.path.splitext(os.path.basename(img.filename))[0]} Image"
                self.label_stream.push_label(label)
                if self.eyetracker is not None:
                    self.eyetracker.send_marker(label)  # Send label to Pupil Labs
                print(f"Current label: {label}")
                self.current_label = label
            self.current_image_index += 1
            self.image_transition_timer.start(5000)  # Display each image for 5 seconds
        else:
            self.end_screen()  # Show end screen after all images are displayed
            self.label_stream.push_label("Test Ended")  # Push end label to LSL stream
            self.paused_image_index = 0  # Reset the paused image index
            self.paused_time = 0  # Reset the paused time
            self.timer.stop()
            self.eyetracker.stop_recording()  # Stop the eyetracker recording if it exists
            #self.label_poll_timer.stop()  # Stop the label polling timer (Good for debugging)

    #This is the main logic for displaying the images in the stroop test, it handles the image transition and the timer for the images
    #It also handles the user input and the elapsed time when the test is done
    def display_images_stroop(self):
        if self.current_image_index < len(self.images):
            img = self.images[self.current_image_index]
            pixmap = QPixmap(img.filename)
            self.current_pixmap = pixmap
            self.update_image_label()
            if hasattr(img, 'filename'):
                label = f"{os.path.splitext(os.path.basename(img.filename))[0]} Image"
                self.label_stream.push_label(label)
                print(f"Current label: {label}")
                self.current_label = label
            self.current_image_index += 1
            self.stroop_transition_timer.start(2000)  # Hide image after 2 seconds
        else:
            self.end_screen()
            self.label_stream.push_label("Test Ended")
            self.current_image_index = 0 # Reset for the next trial  # Push end label to LSL stream
            self.timer.stop()
            #self.label_poll_timer.stop()  # Stop the label polling timer(Good for debugging)
            save_data = Save_Data(self.base_dir, self.test_number)
            save_data.save_data_stroop(self.current_test, self.user_data['user_inputs'], self.user_data['elapsed_time'])
            self.eyetracker.stop_recording()  # Stop the eyetracker recording if it exists



    def poll_label(self):
        # This will print the current label and the current time in ms
        print(f"Polled at {self.elapsed_time} ms: Current label = {self.current_label}")

    #This method is needed to make the image transition timer work, it is called when the image transition timer times out. It is the main way the pause and resume functionality works
    #It is called from the image_transition_timer
    def _on_image_transition(self):
        if not self.Paused:
            self.display_images_passive()

    #This method is called to update the image label with the current image, it scales the image to fit the label and also updates the mirror widget if it exists
    def update_image_label(self):
        if self.current_pixmap:
            scaled_pixmap = self.current_pixmap.scaled(
                self.image_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
            # Update the mirror
            if hasattr(self, 'mirror_widget') and self.mirror_widget is not None:
                self.mirror_widget.set_pixmap(self.current_pixmap)
        else:
            self.image_label.clear()
            if hasattr(self, 'mirror_widget') and self.mirror_widget is not None:
                self.mirror_widget.set_pixmap(None)

    #This method is called when the window is resized, it updates the image label and the instruction text
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Example: scale font size for instructions_label
        label_height = self.instructions_label.height()
        font_size = max(8, int(label_height * 0.08))  # Adjust multiplier as needed
        font = QFont("Arial", font_size, QFont.Bold)
        self.instructions_label.setFont(font)
        # You can do similar scaling for other labels if needed

    #This method is called to set the instruction text for the experiment, it sets the font size and the alignment of the text
    def set_instruction_text(self):
        img = self.images[self.current_image_index - 1]
        text = "Press the 'Y' key if congruent.\nPress the 'N' key if incongruent."
        self.image_label.setText(text)
        self.image_label.setAlignment(Qt.AlignCenter)
        label_height = self.image_label.height()
        font_size = max(8, int(label_height * 0.04))
        font = QFont("Arial", font_size, QFont.Bold)
        self.image_label.setFont(font)
        # Update the mirror
        if hasattr(self, 'mirror_widget') and self.mirror_widget is not None:
            self.mirror_widget.set_instruction_text(text, font)
        if hasattr(img, 'filename'):
              label = f"Instruction Text: {os.path.splitext(os.path.basename(img.filename))[0]} Image"
              self.label_stream.push_label(label)
              print(f"Current label: {label}")
              self.current_label = label
    #This method is called to hide the image and show the instruction text, it clears the image label and sets the instruction text
    def hide_image(self):
        self.image_label.clear()  # Clear the image
        self.set_instruction_text()
        self.wait_for_input()  # Wait for input before displaying the next image

    #This method is called to wait for the user input, it installs an event filter to capture the key press events
    def wait_for_input(self):
        self.installEventFilter(self)

    #This method is called to handle the key press events, it checks if the key pressed is 'Y' or 'N' and stores the user input and the elapsed time
    def eventFilter(self, source, event):
            img = self.images[self.current_image_index - 1]
            if self.Paused == False:
                if event.type() == QEvent.KeyPress:
                    if event.key() == Qt.Key_Y or event.key() == Qt.Key_N:
                        if event.key() == Qt.Key_Y:
                            self.user_data['user_inputs'].append('Yes') # Store the user input
                            if hasattr(img, 'filename'):
                                label = f"{os.path.splitext(os.path.basename(img.filename))[0]} Image: Yes"
                                self.label_stream.push_label(label)
                                print(f"Current label: {label}")
                                self.current_label = label  # Push label to LSL stream
                        else:
                            self.user_data['user_inputs'].append('No')  # Store the user input
                            if hasattr(img, 'filename'):
                                label = f"{os.path.splitext(os.path.basename(img.filename))[0]} Image: No"
                                self.label_stream.push_label(label)
                                print(f"Current label: {label}")
                                self.current_label = label  # Push label to LSL stream
                        self.user_data['elapsed_time'].append(self.elapsed_time)  # Store the elapsed time
                        self.removeEventFilter(self)
                        self.display_next_image()
                        return True
            return super().eventFilter(source, event)

    #This method is called to display the next image, it calls the display_images_stroop method to display the next image
    def display_next_image(self):
        self.display_images_stroop()  # Display the next image

    #This method is called to update the timer label, it updates the elapsed time and formats the timer text
    def update_timer(self):
        self.elapsed_time += 1  # Increment by 1 millisecond
        minutes, remainder = divmod(self.elapsed_time, 60000)
        seconds, milliseconds = divmod(remainder, 1000)
        timer_text = f"{minutes:02}:{seconds:02}:{milliseconds:03}"
        self.timer_label.setText(timer_text)
        if hasattr(self, 'mirror_widget') and self.mirror_widget is not None:
            self.mirror_widget.set_timer(self.timer_label.text())

    #This method is called to handle the key press events, it checks if the overlay widget is visible and if the space bar is pressed, it starts the countdown    
    def keyPressEvent(self, event):
        if self.overlay_widget.isVisible() and event.key() == Qt.Key_Space:
            self.start_countdown()
        else:
            super().keyPressEvent(event)

    #This method is called to start the countdown, it hides the instruction label and shows the countdown label, it also starts the countdown timer
    def start_countdown(self):
        self.instructions_label.setVisible(False)
        self.countdown_label.setVisible(True)
        self.countdown_seconds = 3
        self.countdown_label.setText(str(self.countdown_seconds))
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.countdown_timer.start(1000)
        # Start the mirror's countdown as well
        if hasattr(self, 'mirror_widget'):
            self.mirror_widget.start_countdown()

    #This method is called to update the countdown label, it decrements the countdown seconds and updates the countdown label, if the countdown reaches 0, it stops the timer and calls the begin_experiment method
    def update_countdown(self):
        self.countdown_seconds -= 1
        if self.countdown_seconds > 0:
            self.countdown_label.setText(str(self.countdown_seconds))
        else:
            self.countdown_timer.stop()
            self.countdown_label.setText("Go!")
            QTimer.singleShot(1000, self.begin_experiment)

    #This method is called to begin the experiment, it sets the stacked layout to the experiment widget and starts the experiment
    def begin_experiment(self):
        self.stacked_layout.setCurrentIndex(1)
        if hasattr(self, 'mirror_widget'):
            self.mirror_widget.begin_experiment()
        self.experiment_started.emit()  # Emit the signal to start the experiment
        self.run_trial()

    #This method is called to set the mirror widget, it sets the mirror widget to the passed widget
    def set_mirror(self, mirror_widget):
        self.mirror_widget = mirror_widget

    #This method is called to close the event, it stops the timer and closes the mirror widget if it exists
    def closeEvent(self, event):
        # Stop the timer to prevent update_timer from running after close
        if hasattr(self, 'timer') and self.timer.isActive():
            self.timer.stop()
        # Close or remove the mirror widget if it exists
        if hasattr(self, 'mirror_widget') and self.mirror_widget is not None:
            self.mirror_widget.setParent(None)  # Remove from layout
            self.mirror_widget.deleteLater()    # Schedule for deletion
            self.mirror_widget = None
        super().closeEvent(event)

    def end_screen(self):
        # Create a new widget for the end screen
        end_widget = QWidget()
        end_layout = QVBoxLayout(end_widget)

        # Add a label with the end message
        end_label = QLabel("Test has ended. Please wait for the experimenter to close the test.", end_widget)
        end_label.setFont(QFont("Arial", 18))
        end_label.setAlignment(Qt.AlignCenter)
        end_layout.addWidget(end_label)

        # Set the end_widget as the only widget in the stacked layout
        self.stacked_layout.addWidget(end_widget)
        self.stacked_layout.setCurrentWidget(end_widget)

        # Show end screen in the mirror as well
        if hasattr(self, 'mirror_widget') and self.mirror_widget is not None:
            self.mirror_widget.end_screen()

    def set_eyetracker(self, eyetracker):
        if self.shared_status.get('eyetracker_connected', False):
            # Eye tracker is connected, uses same instance of eye tracker or creates a new one if needed
            if eyetracker is None or eyetracker.device is None:
                eyetracker = PupilLabs()
            if eyetracker and eyetracker.device is not None:
                eyetracker.start_recording()
            else:
                print("Eyetracker not connected")
        else:
            print("Eyetracker not connected")