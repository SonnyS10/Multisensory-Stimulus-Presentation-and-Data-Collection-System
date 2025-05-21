from pupil_labs.realtime_api.simple import discover_one_device

#print("Looking for the next best device...")
#device = discover_one_device(max_search_duration_seconds=60)
#if device is None:
#    print("No device found.")
#    raise SystemExit(-1)
#
#print(f"Phone IP address: {device.phone_ip}")
#print(f"Phone name: {device.phone_name}")
#print(f"Phone unique ID: {device.phone_id}")

from pupil_labs.realtime_api.simple import Device

# This address is just an example. Find out the actual IP address of your device!
ip = "172.20.10.2"

device = Device(address=ip, port="8080")

print(f"Phone IP address: {device.phone_ip}")
print(f"Phone name: {device.phone_name}")
print(f"Phone unique ID: {device.phone_id}")

#import time
#
#recording_id = device.recording_start()
#print(f"Started recording with id {recording_id}")
#
#time.sleep(5)
#
#device.recording_stop_and_save()

estimate = device.estimate_time_offset()
if estimate is None:
    device.close()
    raise SystemExit("Pupil Companion app is too old")

print(f"Mean time offset: {estimate.time_offset_ms.mean} ms")
print(f"Mean roundtrip duration: {estimate.roundtrip_duration_ms.mean} ms")


device.close()