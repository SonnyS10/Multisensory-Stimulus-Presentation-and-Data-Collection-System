import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Constants
NUM_CHANNELS = 32  # Standard number of EEG channels
SAMPLE_RATE = 250  # Samples per second
WINDOW_SIZE = 5  # Window size in seconds (time span of the graph)

# Generate fake EEG data
def generate_fake_eeg_data():
    """
    Simulates EEG data for 32 channels.
    Returns a numpy array of shape (NUM_CHANNELS, SAMPLE_RATE).
    """
    return np.random.randn(NUM_CHANNELS, SAMPLE_RATE) * 10  # Random noise scaled to simulate EEG signals

# Initialize data buffer
data_buffer = np.zeros((NUM_CHANNELS, SAMPLE_RATE * WINDOW_SIZE))

# Create the figure and axes for the plot
fig, axes = plt.subplots(NUM_CHANNELS, 1, figsize=(10, 15), sharex=True)
fig.suptitle("Real-Time EEG Data", fontsize=16)

# Initialize the lines for each channel
lines = []
for i, ax in enumerate(axes):
    line, = ax.plot([], [], lw=1)
    ax.set_xlim(0, WINDOW_SIZE)
    ax.set_ylim(-50, 50)  # Adjust the y-axis limits as needed
    ax.set_ylabel(f"Ch {i+1}")
    if i == NUM_CHANNELS - 1:
        ax.set_xlabel("Time (s)")
    lines.append(line)

# Update function for the animation
def update(frame):
    global data_buffer

    # Generate new fake EEG data
    new_data = generate_fake_eeg_data()

    # Shift the data buffer and append the new data
    data_buffer = np.roll(data_buffer, -SAMPLE_RATE, axis=1)
    data_buffer[:, -SAMPLE_RATE:] = new_data

    # Update the lines for each channel
    time = np.linspace(0, WINDOW_SIZE, data_buffer.shape[1])
    for i, line in enumerate(lines):
        line.set_data(time, data_buffer[i])

    return lines

# Set up the animation
ani = FuncAnimation(fig, update, interval=1000 / SAMPLE_RATE * SAMPLE_RATE, blit=True)

# Show the plot
plt.tight_layout()
plt.subplots_adjust(top=0.95)
plt.show()