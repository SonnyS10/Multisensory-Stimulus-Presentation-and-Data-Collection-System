"""
EEG Stream Window for real-time EEG data visualization.
This module provides a PyQt5-based window for displaying live EEG data streams
from LSL (Lab Streaming Layer) sources like ActiChamp or LabRecorder.
"""

import sys
import numpy as np
import pylsl
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, 
    QPushButton, QLabel, QSlider, QSpinBox, QMessageBox, QFrame
)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QFont
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import threading
import time
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from eeg_stimulus_project.lsl.stream_manager import LSL


class EEGStreamWindow(QMainWindow):
    """
    Main window for EEG stream visualization.
    Displays real-time EEG data from LSL streams in a multi-channel plot.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("EEG Stream Viewer")
        self.setGeometry(100, 100, 1200, 800)

        # EEG data parameters
        self.sample_rate = 500  # Default sample rate
        self.window_size = 5  # Window size in seconds
        self.channels_per_page = 4  # Number of channels per page
        self.current_page = 0
        self.num_channels = 0

        # Data storage
        self.data_buffer = None
        self.channel_names = []
        self.time_data = None

        # LSL stream
        self.inlet = None
        self.stream_connected = False

        # Setup UI
        self.setup_ui()

        # Timer for data updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_plot)

        # Try to connect to EEG stream
        self.connect_to_stream()

    def setup_ui(self):
        """Setup the user interface components."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Control panel
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel)

        # Matplotlib canvas for plotting
        self.figure = Figure(figsize=(12, 8))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        # Status bar
        self.status_label = QLabel("Status: Connecting to EEG stream...")
        self.status_label.setFont(QFont("Arial", 10))
        layout.addWidget(self.status_label)

    def create_control_panel(self):
        """Create the control panel with navigation and settings."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Box)
        panel.setLineWidth(2)
        panel.setMaximumHeight(80)

        layout = QHBoxLayout(panel)

        # Navigation buttons
        self.prev_button = QPushButton("Previous Page")
        self.prev_button.clicked.connect(self.previous_page)
        self.prev_button.setEnabled(False)
        layout.addWidget(self.prev_button)

        self.next_button = QPushButton("Next Page")
        self.next_button.clicked.connect(self.next_page)
        self.next_button.setEnabled(False)
        layout.addWidget(self.next_button)

        # Page info
        self.page_label = QLabel("Page: 1/1")
        self.page_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(self.page_label)

        # Time window control
        layout.addWidget(QLabel("Time Window (s):"))
        self.time_window_spinbox = QSpinBox()
        self.time_window_spinbox.setRange(1, 30)
        self.time_window_spinbox.setValue(self.window_size)
        self.time_window_spinbox.valueChanged.connect(self.update_time_window)
        layout.addWidget(self.time_window_spinbox)

        # Amplitude scale control
        layout.addWidget(QLabel("Amplitude Scale:"))
        self.amplitude_slider = QSlider(Qt.Horizontal)
        self.amplitude_slider.setRange(.1, 100)
        self.amplitude_slider.setValue(20)  # Lower value = more sensitive
        self.amplitude_slider.valueChanged.connect(self.update_amplitude_scale)
        layout.addWidget(self.amplitude_slider)

        # Connection control
        self.connect_button = QPushButton("Reconnect Stream")
        self.connect_button.clicked.connect(self.connect_to_stream)
        layout.addWidget(self.connect_button)

        return panel

    def connect_to_stream(self):
        """Connect to the EEG LSL stream."""
        try:
            self.status_label.setText("Status: Searching for EEG stream...")

            # Look for EEG streams
            streams = pylsl.resolve_byprop('type', 'EEG', minimum=0, timeout=5.0)
            if not streams:
                # Also try to find streams by name containing common EEG device names
                streams = pylsl.resolve_byprop('name', 'ActiChamp', minimum=0, timeout=5.0)
                if not streams:
                    streams = pylsl.resolve_byprop('name', 'BrainVision', minimum=0, timeout=5.0)

            if streams:
                # Connect to the first EEG stream found
                self.inlet = pylsl.StreamInlet(streams[0])

                # Get stream info
                info = self.inlet.info()
                self.num_channels = info.channel_count()
                self.sample_rate = int(info.nominal_srate())
                stream_name = info.name()

                # Get channel names if available
                self.channel_names = []
                ch = info.desc().child("channels").child("channel")
                for i in range(self.num_channels):
                    if ch.child_value("label"):
                        self.channel_names.append(ch.child_value("label"))
                    else:
                        self.channel_names.append(f"Ch {i+1}")
                    ch = ch.next_sibling()

                if not self.channel_names:
                    self.channel_names = [f"Ch {i+1}" for i in range(self.num_channels)]

                # Initialize data buffer
                buffer_size = self.sample_rate * self.window_size
                self.data_buffer = np.zeros((self.num_channels, buffer_size))
                self.time_data = np.linspace(-self.window_size, 0, buffer_size)

                # Setup plot
                self.setup_plot()

                # Start data collection
                self.stream_connected = True
                self.update_timer.start(50)  # Update every 50ms

                self.status_label.setText(f"Status: Connected to {stream_name} ({self.num_channels} channels, {self.sample_rate} Hz)")
                self.update_navigation_buttons()

                logging.info(f"Connected to EEG stream: {stream_name}")

            else:
                raise Exception("No EEG streams found")

        except Exception as e:
            self.status_label.setText(f"Status: Connection failed - {str(e)}")
            self.stream_connected = False
            QMessageBox.warning(self, "Connection Error", f"Could not connect to EEG stream:\n{str(e)}")
            logging.error(f"EEG stream connection failed: {e}")

    def setup_plot(self):
        """Setup the matplotlib plot for EEG data."""
        self.figure.clear()

        # Create subplots for each channel on current page
        channels_to_show = min(self.channels_per_page, self.num_channels - self.current_page * self.channels_per_page)

        self.axes = []
        for i in range(channels_to_show):
            ax = self.figure.add_subplot(channels_to_show, 1, i + 1)
            ax.set_xlim(-self.window_size, 0)
            ax.set_ylim(-100, 100)  # Default amplitude range

            channel_idx = self.current_page * self.channels_per_page + i
            ax.set_ylabel(self.channel_names[channel_idx])
            ax.grid(True, alpha=0.3)

            # Only show x-axis label on bottom subplot
            if i == channels_to_show - 1:
                ax.set_xlabel("Time (s)")
            else:
                ax.set_xticklabels([])

            self.axes.append(ax)

        self.figure.tight_layout()
        self.canvas.draw()

    def update_plot(self):
        """Update the plot with new EEG data."""
        if not self.stream_connected or self.inlet is None:
            return

        try:
            # Pull available samples
            samples, timestamps = self.inlet.pull_chunk(timeout=0.0)

            if samples:
                samples = np.array(samples).T  # Transpose to get channels x samples

                # Update data buffer
                num_new_samples = samples.shape[1]
                self.data_buffer = np.roll(self.data_buffer, -num_new_samples, axis=1)
                self.data_buffer[:, -num_new_samples:] = samples

                # Update plots
                channels_to_show = min(self.channels_per_page, self.num_channels - self.current_page * self.channels_per_page)

                for i in range(channels_to_show):
                    channel_idx = self.current_page * self.channels_per_page + i

                    # Clear previous plot
                    self.axes[i].clear()

                    # Plot new data
                    self.axes[i].plot(self.time_data, self.data_buffer[channel_idx], 'b-', linewidth=0.8)

                    # Set labels and limits
                    self.axes[i].set_ylabel(self.channel_names[channel_idx])
                    self.axes[i].set_xlim(-self.window_size, 0)

                    # Dynamic amplitude scaling
                    amplitude_scale = self.amplitude_slider.value()
                    self.axes[i].set_ylim(-amplitude_scale, amplitude_scale)

                    self.axes[i].grid(True, alpha=0.3)

                    # Only show x-axis label on bottom subplot
                    if i == channels_to_show - 1:
                        self.axes[i].set_xlabel("Time (s)")
                    else:
                        self.axes[i].set_xticklabels([])

                self.canvas.draw()

        except Exception as e:
            logging.error(f"Error updating EEG plot: {e}")

    def next_page(self):
        """Navigate to next page of channels."""
        max_pages = (self.num_channels - 1) // self.channels_per_page + 1
        if self.current_page < max_pages - 1:
            self.current_page += 1
            self.setup_plot()
            self.update_navigation_buttons()

    def previous_page(self):
        """Navigate to previous page of channels."""
        if self.current_page > 0:
            self.current_page -= 1
            self.setup_plot()
            self.update_navigation_buttons()

    def update_navigation_buttons(self):
        """Update the state of navigation buttons."""
        if self.num_channels == 0:
            return

        max_pages = (self.num_channels - 1) // self.channels_per_page + 1

        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < max_pages - 1)

        self.page_label.setText(f"Page: {self.current_page + 1}/{max_pages}")

    def update_time_window(self, value):
        """Update the time window size."""
        self.window_size = value
        if self.stream_connected:
            buffer_size = self.sample_rate * self.window_size
            self.data_buffer = np.zeros((self.num_channels, buffer_size))
            self.time_data = np.linspace(-self.window_size, 0, buffer_size)
            self.setup_plot()

    def update_amplitude_scale(self, value):
        """Update the amplitude scale."""
        # The amplitude scale is updated in real-time during plot updates
        pass

    def closeEvent(self, event):
        """Handle window close event."""
        self.update_timer.stop()
        if self.inlet:
            self.inlet.close_stream()
        event.accept()


def run_eeg_stream_window():
    """
    Standalone function to run the EEG stream window.
    This is called from the control window as a separate process.
    """
    app = QApplication(sys.argv)
    window = EEGStreamWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    run_eeg_stream_window()