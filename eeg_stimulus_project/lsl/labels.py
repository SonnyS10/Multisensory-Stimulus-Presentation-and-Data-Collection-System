from pylsl import StreamInfo, StreamOutlet

class LSLLabelStream:
    """
    Handles an LSL stream for sending event labels to LabRecorder.
    """

    def __init__(self, stream_name="labels", stream_type="Markers", channel_count=1, nominal_srate=0, source_id="label_stream"):
        # Create LSL stream info
            self.info = StreamInfo(
                name=stream_name,
                type=stream_type,
                channel_count=channel_count,
                nominal_srate=nominal_srate,
                channel_format='string',
                source_id=source_id
            )
            # Create the LSL outlet
            self.outlet = StreamOutlet(self.info)

    def push_label(self, label):
        """
        Push a label (string) to the LSL stream.
        """
        if self.outlet:
            self.outlet.push_sample([str(label)])

class LSLTactileStream:
    """
    Handles an LSL stream for sending binary touch state (1=touched, 0=not touched).
    """
    def __init__(self, stream_name="tactile_touch", stream_type="Touch", channel_count=1, nominal_srate=0, source_id="tactile_touch_stream"):
        self.info = StreamInfo(
            name=stream_name,
            type=stream_type,
            channel_count=channel_count,
            nominal_srate=nominal_srate,
            channel_format='int8',  # Binary integer
            source_id=source_id
        )
        self.outlet = StreamOutlet(self.info)

    def push_touch(self, touched):
        # touched should be 1 (touch) or 0 (no touch)
        self.outlet.push_sample([int(touched)])
