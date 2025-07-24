# Uses ticcmd to send and receive data from the Tic over USB.
#
# NOTE: The Tic's control mode must be "Serial / I2C / USB"
# in order to set the target position over USB.

import subprocess
import yaml   
import keyboard
import time

def ticcmd(*args):
    return subprocess.check_output(['ticcmd', '-d', '00475502'] + list(args))

def get_position():
    status = yaml.safe_load(ticcmd('-s', '--full'))
    return status['Current position']

move_steps = 200  # <-- Set your desired number of steps here
     
print("Setting motor parameters...")
ticcmd('--current', '1860')                # Set motor current to 1760 mA
ticcmd('--step-mode', '4')                 # 1/16 step mode (4 = 1/16 for Tic controllers)
ticcmd('--max-speed', '60000000')             # M   ax speed: 20000 pulses/sec
ticcmd('--max-accel', '50000000')               # Max acceleration: 500 pulses/sec^2

print("Homing to position 0...")
ticcmd('--exit-safe-start', '--position', '0')  
time.sleep(3)
ticcmd('--halt-and-set-position', '0')
current_pos = get_position()
print(f"Current motor position after homing: {current_pos}")

at_home = True
current_pos = get_position()  # Always track the current position

print("Press SPACE to move out, SPACE again to return. Press ESC to exit.")

while True:
    if keyboard.is_pressed('esc'):
        print("Exiting.") 
        break
    if keyboard.is_pressed('0'):
        ticcmd('--energize')
        print("Closing (moving to 0)...")
        ticcmd('--exit-safe-start', '--position', '0')
        time.sleep(2)
        ticcmd('--deenergize')
        print("Motor de-energized.")
        while keyboard.is_pressed('0'):
            time.sleep(0.1)
    if keyboard.is_pressed('1'):
        ticcmd('--energize')
        print(f"Opening by {move_steps} steps...")
        ticcmd('--exit-safe-start', '--position', str(move_steps))
        time.sleep(2)
        ticcmd('--deenergize')
        print("Motor de-energized.")
        while keyboard.is_pressed('1'):
            time.sleep(0.1)
    if keyboard.is_pressed('2'):
        ticcmd('--energize')
        print(f"Opening by {2 * move_steps} steps...")
        ticcmd('--exit-safe-start', '--position', str(2 * move_steps))
        time.sleep(2)
        ticcmd('--deenergize')
        print("Motor de-energized.")
        while keyboard.is_pressed('2'):
            time.sleep(0.1)
    time.sleep(0.05)