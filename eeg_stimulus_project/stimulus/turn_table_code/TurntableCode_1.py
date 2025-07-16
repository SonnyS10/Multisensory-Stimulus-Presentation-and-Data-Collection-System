# Uses ticcmd to send and receive data from the Tic over USB.
#
# NOTE: The Tic's control mode must be "Serial / I2C / USB"
# in order to set the target position over USB.
 
import subprocess
import yaml
import keyboard
import time
import csv
import random
 
def ticcmd(*args):
    return subprocess.check_output([r'C:\Program Files (x86)\Pololu\Tic\Bin\ticcmd.exe'] + list(args))
 
def get_position():
    status = yaml.safe_load(ticcmd('-s', '--full'))
    return status['Current position']
 
steps_per_rev = 200  # 200 steps/rev * 16 microsteps = 3200
num_positions = 16
positions = [round(i * steps_per_rev / num_positions) for i in range(num_positions)]
print("Positions:", positions)
current_index = 0
 
# Move to position 0 at startup
print("Homing to position 0...")
ticcmd('--exit-safe-start', '--position', str(positions[0]))
time.sleep(1)
ticcmd('--halt-and-set-position', '0')
current_pos = get_position()
print(f"Current motor position after homing: {current_pos}")
 
print("Press a number (1-16) to move to that position. Press ESC to exit.")
 
def move_to_position(target_index):
    current_step = get_position()
    target_step = positions[target_index]
    step_diffs = [
        (target_step - current_step),
        (target_step - current_step + steps_per_rev),
        (target_step - current_step - steps_per_rev)
    ]
    move = min(step_diffs, key=abs)
    final_target = current_step + move
    print(f"Moving to position {target_index+1} at step {final_target} (shortest path)")
    ticcmd('--exit-safe-start', '--position', str(final_target))
    time.sleep(1)
    current_pos = get_position()
    print(f"Current motor position: {current_pos}")

# Generate a random CSV file for testing
csv_filename = "positions.csv"
num_moves = 10  # Number of random moves to generate

with open(csv_filename, "w", newline='') as csvfile:
    writer = csv.writer(csvfile)
    random_moves = [random.randint(1, 16) for _ in range(num_moves)]
    writer.writerow(random_moves)

print(f"Generated random CSV file '{csv_filename}': {random_moves}")

# Now read positions from CSV file and move accordingly
try:
    with open(csv_filename, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            for value in row:
                value = value.strip()
                if value.isdigit() and 1 <= int(value) <= 16:
                    target_index = int(value) - 1
                    move_to_position(target_index)
                else:
                    print(f"Invalid value in CSV: {value}")
    print("Finished processing CSV file.")

except FileNotFoundError:
    print(f"CSV file '{csv_filename}' not found.")
except KeyboardInterrupt:
    print("Stopped by user.")
