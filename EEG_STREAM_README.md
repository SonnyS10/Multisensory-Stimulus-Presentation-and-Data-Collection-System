# EEG Stream Window

The EEG Stream Window provides real-time visualization of EEG data streams from LSL (Lab Streaming Layer) sources such as ActiChamp or BrainVision.

## Features

- **Real-time EEG data visualization** with multi-channel display
- **Channel pagination** to navigate through all available EEG channels
- **Configurable time window** (1-30 seconds) for data display
- **Adjustable amplitude scaling** for optimal signal visualization
- **Automatic stream discovery** for EEG devices
- **Separate process execution** for non-blocking operation
- **Professional interface** similar to BrainVision Recorder and EEGLab

## Usage

### From the Control Window

1. Start your EEG acquisition system (ActiChamp, BrainVision, etc.)
2. Run the main application
3. Click the **"EEG Stream"** button in the control window
4. The EEG Stream Window will open automatically and display live data

### Controls

- **Previous/Next Page**: Navigate through different sets of channels
- **Time Window**: Adjust the time span of displayed data (1-30 seconds)
- **Amplitude Scale**: Control the vertical scaling of the signal display
- **Reconnect Stream**: Manually reconnect to the EEG stream if needed

## Technical Details

### LSL Integration

The EEG Stream Window automatically discovers and connects to LSL streams using the following priority:

1. Streams with type `EEG`
2. Streams with name `ActiChamp`
3. Streams with name `BrainVision`

### Supported Systems

- **ActiChamp** EEG amplifier
- **BrainVision** Recorder
- **LabRecorder** with EEG streams
- Any LSL-compatible EEG system

### Display Configuration

- **Channels per page**: 8 channels (configurable)
- **Sample rate**: Auto-detected from stream (typically 250-1000 Hz)
- **Update rate**: 20 Hz (50ms refresh interval)
- **Default time window**: 5 seconds
- **Default amplitude range**: ±50 µV

## Implementation

### Files

- `eeg_stimulus_project/gui/eeg_stream_window.py` - Main EEG Stream Window implementation
- `eeg_stimulus_project/gui/control_window.py` - Integration with control window

### Dependencies

- **PyQt5** - GUI framework
- **pylsl** - Lab Streaming Layer interface
- **matplotlib** - Real-time plotting
- **numpy** - Data processing
- **liblsl** - LSL native library

### Architecture

The EEG Stream Window runs as a separate process to ensure:
- Non-blocking operation of the main application
- Dedicated resources for real-time visualization
- Isolation from other system components
- Smooth data streaming without interruption

## Troubleshooting

### No EEG Streams Found

1. Ensure your EEG system is running and streaming data
2. Check that the LSL stream is properly configured
3. Verify network connectivity if using remote streams
4. Try clicking "Reconnect Stream" button

### Poor Signal Quality

1. Check electrode connections
2. Verify amplifier settings
3. Adjust amplitude scale in the EEG Stream Window
4. Check for electrical interference

### Performance Issues

1. Reduce the time window size
2. Close other resource-intensive applications
3. Ensure adequate system resources
4. Check LSL stream configuration

## Integration with Main System

The EEG Stream Window integrates seamlessly with the main multisensory stimulus presentation system:

- **Shared LSL infrastructure** with other data collection components
- **Coordinated with LabRecorder** for data recording
- **Synchronized with experiment timing** through LSL labels
- **Compatible with existing device management** in the control window

The EEG Stream Window is designed to work alongside other system components without interference, providing researchers with essential real-time feedback during data collection.