"""
EEG Stimulus Project - LSL Event Labeling System

This module provides event marker functionality for synchronizing experiment
events with data collection systems via Lab Streaming Layer (LSL). Event
markers are critical for correlating stimulus presentation with physiological
responses in the recorded data.

Key Features:
- Real-time event marker streaming via LSL
- Integration with LabRecorder for EEG synchronization
- Configurable stream parameters for different experimental setups
- String-based label system for flexible event description

Usage:
    The LSL label stream is typically used to mark:
    - Stimulus onset/offset times
    - Experimental condition changes
    - User response events
    - Phase transitions in experiments

Integration:
    Works with LabRecorder to create synchronized XDF files containing
    both physiological data and precisely timed event markers.

Author: Research Team
Last Modified: 2024
"""

from pylsl import StreamInfo, StreamOutlet

class LSLLabelStream:
    """
    LSL-based event labeling system for experiment synchronization.
    
    This class creates and manages an LSL stream specifically for sending
    event markers to data collection systems. Event markers are essential
    for post-experiment analysis to align stimulus events with recorded
    physiological responses.
    
    The stream uses string-based labels allowing flexible description of
    experimental events and conditions. Labels are automatically timestamped
    by the LSL system ensuring precise temporal alignment.
    
    Attributes:
        info (StreamInfo): LSL stream information object
        outlet (StreamOutlet): LSL outlet for sending data
        
    Stream Configuration:
        - Default stream name: "labels"
        - Stream type: "Markers" (standard for event markers)
        - Channel format: string (allows descriptive labels)
        - Sampling rate: 0 (irregular/event-based timing)
    """

    def __init__(self, stream_name="labels", stream_type="Markers", channel_count=1, nominal_srate=0, source_id="label_stream"):
        """
        Initialize the LSL label stream.
        
        Creates an LSL stream outlet configured for sending event markers
        to connected recording systems (primarily LabRecorder).
        
        Args:
            stream_name (str): Name identifier for the LSL stream
            stream_type (str): Type category for the stream (typically "Markers")
            channel_count (int): Number of channels (1 for single label stream)
            nominal_srate (float): Sampling rate (0 for irregular event timing)
            source_id (str): Unique source identifier for the stream
            
        Stream Properties:
            - Uses string format for descriptive event labels
            - Configured for event-based (not continuous) data
            - Compatible with standard LSL recording systems
            - Automatically timestamped by LSL infrastructure
        """
        # Create LSL stream information object with experiment-specific parameters
        self.info = StreamInfo(
            name=stream_name,           # Stream identifier for discovery
            type=stream_type,           # Category type (Markers for events)
            channel_count=channel_count, # Single channel for labels
            nominal_srate=nominal_srate, # Event-based timing (0 = irregular)
            channel_format='string',     # String format for descriptive labels
            source_id=source_id         # Unique source identifier
        )
        
        # Create the LSL outlet for streaming data
        self.outlet = StreamOutlet(self.info)

    def push_label(self, label):
        """
        Send an event label to the LSL stream.
        
        This method sends a timestamped event marker to all connected
        recording systems. The LSL system automatically adds precise
        timestamps enabling accurate synchronization with other data streams.
        
        Args:
            label (str): Descriptive label for the event
            
        Event Label Examples:
            - "stimulus_onset_visual_alcohol"
            - "user_response_correct"
            - "trial_start"
            - "experiment_phase_passive"
            - "tactile_stimulation_start"
            
        Synchronization:
            Labels are automatically timestamped by LSL using the system's
            high-resolution clock, ensuring sub-millisecond precision for
            synchronization with EEG, eye tracking, and other data streams.
            
        Error Handling:
            Gracefully handles cases where outlet is not available,
            preventing experiment interruption due to recording issues.
        """
        if self.outlet:
            # Convert label to string and send as single-item list
            # LSL expects sample data as a list/array even for single values
            self.outlet.push_sample([str(label)])
