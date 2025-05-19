import os
import csv
import sys
sys.path.append('C:\\Users\\srs1520\\Documents\\Paid Research\\Software-for-Paid-Research-')
from eeg_stimulus_project.lsl.stream_manager import LSL

class Save_Data():
    def __init__(self, base_dir, test_number):
        self.base_dir = base_dir
        self.test_number = test_number

    def save_data_stroop(self, current_test, user_inputs, elapsed_time):
        # Check the test number and create the appropriate folder
        test_dir = os.path.join(self.base_dir, current_test)
        os.makedirs(test_dir, exist_ok=True)

        # Save data to a file in the test directory
        file_path = os.path.join(test_dir, 'data.csv')
        file_path_eeg = os.path.join(test_dir, 'eeg_data.csv')
        file_exists = os.path.isfile(file_path)

        with open(file_path, 'a', newline='') as file:  # Append to the file
            writer = csv.writer(file)
            if not file_exists:
                # Write headers if the file does not exist
                writer.writerow(['User Inputs', 'Elapsed Time'])
            # Write the data
            for input, time in zip(user_inputs, elapsed_time):
                writer.writerow([input, time])
        print("Data saved successfully!")
        LSL.stop_collection(file_path_eeg)
        print("super cool")

    def save_data_normal(self, current_test):
        # Check the test number and create the appropriate folder
        test_dir = os.path.join(self.base_dir, current_test)
        os.makedirs(test_dir, exist_ok=True)

        # Save data to a file in the test directory
        file_path_eeg = os.path.join(test_dir, 'eeg_data.csv')

        print("Data saved successfully!")
        LSL.stop_collection(file_path_eeg)
        print("super cool")