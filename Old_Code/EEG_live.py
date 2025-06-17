import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Button

# Constants
NUM_CHANNELS = 32  # Total number of EEG channels
CHANNELS_PER_PAGE = 8  # Number of channels per page
SAMPLE_RATE = 250  # Samples per second
WINDOW_SIZE = 5  # Window size in seconds (time span of the graph)

# Generate fake EEG data
def generate_fake_eeg_data():
    """
    Simulates EEG data for NUM_CHANNELS.
    Returns a numpy array of shape (NUM_CHANNELS, SAMPLE_RATE).
    """
    data = np.random.randn(NUM_CHANNELS, SAMPLE_RATE) * 10  # Random noise scaled to simulate EEG signals
    # Set channels 2, 10, 20, and 31 to all zeros
    zero_channels = [1, 12, 19, 30]  # Zero-based indices for channels 2, 10, 20, and 31
    data[zero_channels, :] = 0
    return data

# Initialize data buffer
data_buffer = np.zeros((NUM_CHANNELS, SAMPLE_RATE * WINDOW_SIZE))

# Current page index
current_page = 0

# Create the figure and axes for the plot
fig, axes = plt.subplots(CHANNELS_PER_PAGE, 1, figsize=(10, 15), sharex=True)
fig.suptitle("Real-Time EEG Data", fontsize=16)

# Initialize the lines for each channel
lines = []
for ax in axes:
    line, = ax.plot([], [], lw=1)
    ax.set_xlim(0, WINDOW_SIZE)
    ax.set_ylim(-50, 50)  # Adjust the y-axis limits as needed
    lines.append(line)

# Update the axes labels
def update_axes_labels():
    """
    Updates the labels on the left side of the plot to reflect the current page's channels.
    """
    for i, ax in enumerate(axes):
        channel_index = current_page * CHANNELS_PER_PAGE + i
        if channel_index < NUM_CHANNELS:
            ax.set_ylabel(f"Ch {channel_index + 1}")  # Update channel label
            ax.set_visible(True)
        else:
            ax.set_visible(False)
    axes[-1].set_xlabel("Time (s)")

# Call the function initially to set up the labels
update_axes_labels()

# Update function for the animation
def update(frame):
    global data_buffer

    # Generate new fake EEG data
    new_data = generate_fake_eeg_data()

    # Shift the data buffer and append the new data
    data_buffer = np.roll(data_buffer, -SAMPLE_RATE, axis=1)
    data_buffer[:, -SAMPLE_RATE:] = new_data

    # Update the lines for the current page
    time = np.linspace(0, WINDOW_SIZE, data_buffer.shape[1])
    for i, line in enumerate(lines):
        channel_index = current_page * CHANNELS_PER_PAGE + i
        if channel_index < NUM_CHANNELS:
            line.set_data(time, data_buffer[channel_index])
        else:
            line.set_data([], [])
    return lines

# Navigation button callbacks
def next_page(event):
    """
    Moves to the next page of channels if available.
    """
    global current_page
    if (current_page + 1) * CHANNELS_PER_PAGE < NUM_CHANNELS:
        current_page += 1
        print(f"Current page: {current_page}")
        update_axes_labels()

def previous_page(event):
    """
    Moves to the previous page of channels if available.
    """
    global current_page
    if current_page > 0:
        current_page -= 1
        print(f"Current page: {current_page}")
        update_axes_labels()

# Add navigation buttons
ax_next = plt.axes([0.9, 0.01, 0.08, 0.05])  # Bottom-right corner
btn_next = Button(ax_next, "Next")
btn_next.on_clicked(next_page)

ax_prev = plt.axes([0.8, 0.01, 0.08, 0.05])  # Bottom-left corner
btn_prev = Button(ax_prev, "Previous")
btn_prev.on_clicked(previous_page)

# Set up the animation
ani = FuncAnimation(fig, update,  interval=1000 / SAMPLE_RATE * SAMPLE_RATE, blit=True)

# Show the plot
plt.tight_layout()
plt.subplots_adjust(top=0.95, bottom=0.1)
plt.show()