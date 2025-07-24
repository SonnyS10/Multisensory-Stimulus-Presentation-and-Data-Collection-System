# Uses ticcmd to send and receive data from the Tic over USB.
#
# NOTE: The Tic's control mode must be "Serial / I2C / USB"
# in order to set the target position over USB.

import subprocess
import yaml
import time

class DoorController:
    def __init__(self, device_id='00475502', move_steps=-400):
        self.device_id = device_id
        self.move_steps = move_steps
        self.set_motor_parameters()
        self.home()

    def ticcmd(self, *args):
        return subprocess.check_output(['ticcmd', '-d', self.device_id] + list(args))

    def get_position(self):
        status = yaml.safe_load(self.ticcmd('-s', '--full'))
        return status['Current position']

    def set_motor_parameters(self):
        print("Setting motor parameters...")
        self.ticcmd('--current', '1920')
        self.ticcmd('--step-mode', '8')
        self.ticcmd('--max-speed', '500000000')
        self.ticcmd('--max-accel', '100000') # Max of 100000, DON'T GO HIGHER THAN THIS

    def home(self):
        print("Homing to position 0...")
        self.ticcmd('--halt-and-set-position', '0')
        current_pos = self.get_position()
        print(f"Current motor position after homing: {current_pos}")

    def open(self):
        self.ticcmd('--energize')
        print(f"Opening by {self.move_steps} steps...")
        self.ticcmd('--exit-safe-start', '--position', str(self.move_steps))
        time.sleep(2)
        self.ticcmd('--deenergize')
        print("Motor de-energized.")

    def close(self):
        self.ticcmd('--energize')
        print("Closing (moving to 0)...")
        self.ticcmd('--exit-safe-start', '--position', '0')
        time.sleep(2)
        self.ticcmd('--deenergize')
        print("Motor de-energized.")