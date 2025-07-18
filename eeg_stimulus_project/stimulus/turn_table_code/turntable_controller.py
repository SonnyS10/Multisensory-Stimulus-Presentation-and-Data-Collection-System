import subprocess
import yaml
import time

class TurntableController:
    def __init__(self):
        self.steps_per_rev = 800
        self.num_positions = 16
        self.positions = [round(i * self.steps_per_rev / self.num_positions) for i in range(self.num_positions)]
        self.ticcmd_path = r'C:\Program Files (x86)\Pololu\Tic\Bin\ticcmd.exe'
        self.home()

    def ticcmd(self, *args):
        return subprocess.check_output([self.ticcmd_path] + list(args))

    def get_position(self):
        status = yaml.safe_load(self.ticcmd('-s', '--full'))
        return status['Current position']

    def home(self):
        self.ticcmd('--exit-safe-start', '--position', str(self.positions[0]))
        time.sleep(1)
        self.ticcmd('--halt-and-set-position', '0')

    def move_to_position(self, target_index):
        current_step = self.get_position()
        target_step = self.positions[target_index]
        step_diffs = [
            (target_step - current_step),
            (target_step - current_step + self.steps_per_rev),
            (target_step - current_step - self.steps_per_rev)
        ]
        move = min(step_diffs, key=abs)
        final_target = current_step + move
        print(f"Moving to position {target_index+1} at step {final_target} (shortest path)")
        self.ticcmd('--exit-safe-start', '--position', str(final_target))
        time.sleep(3)
        current_pos = self.get_position()
        print(f"Current motor position: {current_pos}")
        return self.get_position()