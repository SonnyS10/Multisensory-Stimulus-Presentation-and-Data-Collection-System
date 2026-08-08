from pupil_labs.realtime_api.simple import Device, discover_one_device
import threading
import queue
import logging

# Uncomment the following lines to test connection independently

#ip = "10.117.15.169"
#device = Device(address=ip, port="8080")
#print(f"Phone IP address: {device.phone_ip}")

class PupilLabs():
    def __init__(self, ip_address="10.117.36.226"):
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


class EyetrackerMarkerWorker:
    """Runs eyetracker operations on a dedicated background thread.

    Pupil Labs calls (send_event / recording_start / recording_stop_and_save)
    are synchronous network requests that can take hundreds of ms or hang on a
    flaky link. Calling them inline on the host command-listener thread or the
    display Qt thread stalls those threads -- which is what starves tactile
    'touch_detection_armed' arming when the eyetracker is connected.

    Submitting work here keeps callers non-blocking. A single FIFO thread also
    preserves ordering (e.g. recording_start before its markers). Delivery is
    fire-and-forget: failures are logged, never raised back to the caller.
    """

    def __init__(self):
        self._queue = queue.Queue()
        self._thread = threading.Thread(
            target=self._run, name="EyetrackerMarkerWorker", daemon=True
        )
        self._thread.start()

    def submit(self, func, *args, description=""):
        """Enqueue an eyetracker operation to run on the worker thread."""
        if func is None:
            return
        self._queue.put((func, args, description))

    def _run(self):
        while True:
            func, args, description = self._queue.get()
            if func is None:  # Sentinel to stop the worker.
                break
            label = description or getattr(func, "__name__", "operation")
            try:
                func(*args)
            except Exception as exc:
                logging.error("[EYETRACKER] Async %s failed: %s", label, exc)

    def stop(self):
        self._queue.put((None, (), ""))
