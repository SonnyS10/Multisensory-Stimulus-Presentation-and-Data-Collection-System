from pupil_labs.realtime_api.simple import Device, discover_one_device
import threading
import logging

# Uncomment the following lines to test connection independently

#ip = "10.117.15.169"
#device = Device(address=ip, port="8080")
#print(f"Phone IP address: {device.phone_ip}")

class PupilLabs():
    def __init__(self, ip_address="10.117.15.169"):
        super().__init__()
        logging.info("Attempting to connect to Pupil Labs device...")
        self.device = Device(address=ip_address, port="8080")
        print(f"Phone IP address: {self.device.phone_ip}")
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
        if self.device:
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
