from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from matplotlib.animation import FuncAnimation
from PyQt5.QtWidgets import QWidget, QVBoxLayout

class EEGGraphWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Constants
        self.NUM_CHANNELS = 32  # Total number of EEG channels
        self.CHANNELS_PER_PAGE = 8  # Number of channels per page
        self.SAMPLE_RATE = 250  # Samples per second
        self.WINDOW_SIZE = 5  # Window size in seconds (time span of the graph)

        # Default channel names
        self.channel_names = [f"Ch {i + 1}" for i in range(self.NUM_CHANNELS)]

        # Initialize data buffer
        self.data_buffer = np.zeros((self.NUM_CHANNELS, self.SAMPLE_RATE * self.WINDOW_SIZE))
        self.current_page = 0

        # Create the matplotlib figure and axes
        self.figure = Figure(figsize=(10, 15))
        self.canvas = FigureCanvas(self.figure)
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.canvas)

        self.axes = []
        for _ in range(self.CHANNELS_PER_PAGE):
            ax = self.figure.add_subplot(self.CHANNELS_PER_PAGE, 1, len(self.axes) + 1)
            ax.set_xlim(0, self.WINDOW_SIZE)
            ax.set_ylim(-50, 50)  # Adjust the y-axis limits as needed
            self.axes.append(ax)

        self.lines = [ax.plot([], [], lw=1)[0] for ax in self.axes]
        self.update_axes_labels()

        # Set up the animation
        self.animation = FuncAnimation(self.figure, self.update, interval=1000 / self.SAMPLE_RATE * self.SAMPLE_RATE, blit=True, cache_frame_data=False)

    def set_channel_names(self, names):
        """
        Sets custom names for the EEG channels.
        
        :param names: List of strings representing the channel names.
        """
        if len(names) != self.NUM_CHANNELS:
            raise ValueError(f"Expected {self.NUM_CHANNELS} channel names, but got {len(names)}.")
        self.channel_names = names
        self.update_axes_labels()

    def generate_fake_eeg_data(self):
        """
        Simulates EEG data for NUM_CHANNELS.
        Returns a numpy array of shape (NUM_CHANNELS, SAMPLE_RATE).
        """
        data = np.random.randn(self.NUM_CHANNELS, self.SAMPLE_RATE) * 10  # Random noise scaled to simulate EEG signals
        # Set channels 2, 10, 20, and 31 to all zeros
        zero_channels = [1, 9, 19, 30]  # Zero-based indices for channels 2, 10, 20, and 31
        data[zero_channels, :] = 0
        return data

    def update_axes_labels(self):
        """
        Updates the labels on the left side of the plot to reflect the current page's channels.
        """
        for i, ax in enumerate(self.axes):
            channel_index = self.current_page * self.CHANNELS_PER_PAGE + i
            if channel_index < self.NUM_CHANNELS:
                ax.set_ylabel(self.channel_names[channel_index])  # Use custom channel names
                ax.set_visible(True)
            else:
                ax.set_visible(False)
        self.axes[-1].set_xlabel("Time (s)")

    def update(self, frame):
        """
        Update function for the animation.
        """
        # Generate new fake EEG data
        new_data = self.generate_fake_eeg_data()

        # Shift the data buffer and append the new data
        self.data_buffer = np.roll(self.data_buffer, -self.SAMPLE_RATE, axis=1)
        self.data_buffer[:, -self.SAMPLE_RATE:] = new_data

        # Update the lines for the current page
        time = np.linspace(0, self.WINDOW_SIZE, self.data_buffer.shape[1])
        for i, line in enumerate(self.lines):
            channel_index = self.current_page * self.CHANNELS_PER_PAGE + i
            if channel_index < self.NUM_CHANNELS:
                line.set_data(time, self.data_buffer[channel_index])
            else:
                line.set_data([], [])

        return self.lines

    def next_page(self):
        """
        Moves to the next page of channels if available.
        """
        if (self.current_page + 1) * self.CHANNELS_PER_PAGE < self.NUM_CHANNELS:
            self.current_page += 1
            self.update_axes_labels()

    def previous_page(self):
        """
        Moves to the previous page of channels if available.
        """
        if self.current_page > 0:
            self.current_page -= 1
            self.update_axes_labels()

