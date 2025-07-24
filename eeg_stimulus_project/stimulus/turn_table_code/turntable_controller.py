import subprocess
import yaml
import time



class TurntableController:
    def __init__(self, interval_steps=200, num_bays=16):
        self.interval_steps = interval_steps
        self.num_bays = num_bays
        self.current_bay = 0
        self.ticcmd_path = r'C:\Program Files (x86)\Pololu\Tic\Bin\ticcmd.exe'
        #self.home()

        print("Setting motor parameters...")
        #self.ticcmd('--reset-command-timeout')
        self.ticcmd('--current', '1000')                # Set motor current to 1760 mA
        self.ticcmd('--step-mode', '16')                 # 1/16 step mode (4 = 1/16 for Tic controllers)
        self.ticcmd('--max-speed', '6000000')             # Max speed: 20000 pulses/sec
        self.ticcmd('--max-accel', '4000000')               # Max acceleration: 500 pulses/sec^2

    def ticcmd(self, *args):
        return subprocess.check_output([self.ticcmd_path, '-d', '00466055'] + list(args))

    def get_position(self):
        status = yaml.safe_load(self.ticcmd('-s', '--full'))
        return status['Current position']

    def home(self):
        # Home to position 0
        self.ticcmd('--exit-safe-start', '--position', '0')
        time.sleep(2)
        self.ticcmd('--halt-and-set-position', '0')
        self.current_bay = 0

    def move_to_bay(self, bay_index, wait=True, timeout=20):
        """Move to the specified bay (0-based index) using the shortest path.
        If wait=True, block until the move is complete or timeout (in seconds) is reached.
        """
        diff = (bay_index - self.current_bay) % self.num_bays
        if diff > self.num_bays // 2:
            # Move clockwise (reverse previous direction)
            steps = (self.num_bays - diff) * self.interval_steps
        else:
            # Move counterclockwise (reverse previous direction)
            steps = -diff * self.interval_steps

        # Get current position in steps
        current_steps = self.get_position()
        target_steps = current_steps + steps

        print(f"Moving from bay {self.current_bay + 1} to {bay_index + 1}")
        #print(f"Current steps: {current_steps}, Target steps: {target_steps}")

        self.ticcmd('--exit-safe-start', '--position', str(target_steps))
        #time.sleep(3)

        if wait:
            start_time = time.time()
            while True:
                pos = self.get_position()
                #print(f"Current position: {pos}, Target: {target_steps}")
                if abs(pos - target_steps) < 5:  # Increased tolerance
                    break
                if time.time() - start_time > timeout:
                    print("Warning: move_to_bay timed out.")
                    break
                time.sleep(0.2)  # Slower polling

        self.current_bay = bay_index

    def move_by_bays(self, num_bays):
        self.move_to_bay((self.current_bay + num_bays) % self.num_bays)