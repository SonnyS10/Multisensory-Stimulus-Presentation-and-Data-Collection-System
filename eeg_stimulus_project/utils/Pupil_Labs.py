from pupil_labs.realtime_api.simple import discover_one_device

#print("Looking for the next best device...")
#device = discover_one_device(max_search_duration_seconds=10)
#if device is None:
#    print("No device found.")
#    raise SystemExit(-1)

from pupil_labs.realtime_api.simple import Device
import threading

class PupilLabs(threading.Thread):
    def __init__(self):
        super().__init__()
        print("Attempting to connect to Pupil Labs device...")
        #self.device = discover_one_device(max_search_duration_seconds=5)

        ip = "172.20.10.2"
        self.device = Device(address=ip, port="8080")
        
        #print(f"Phone IP address: {self.device.phone_ip}")
        #print(f"Phone name: {self.device.phone_name}")
        #print(f"Phone unique ID: {self.device.phone_id}")

    def start_recording(self):
        if not self.device:
            print("Device is not connected.")
            return

        recording_id = self.device.recording_start()
        print(f"Started eyetracker recording with id {recording_id}")

    def stop_recording(self):
        if self.device:
            self.device.recording_stop_and_save()
            print("Stopped and saved the eyetracker recording.")

    def estimate_time_offset(self):
        estimate = self.device.estimate_time_offset()
        if estimate is None:
            self.device.close()
            raise SystemExit("Pupil Companion app is too old")

        print(f"Mean time offset: {estimate.time_offset_ms.mean} ms")
        print(f"Mean roundtrip duration: {estimate.roundtrip_duration_ms.mean} ms")

    def send_marker(self, event):
        self.device.send_event(event)

    def close(self):
        if self.device:
            self.device.close()
            print("Pupil Labs device connection closed.")
        else:
            print("No Pupil Labs device to close.")
