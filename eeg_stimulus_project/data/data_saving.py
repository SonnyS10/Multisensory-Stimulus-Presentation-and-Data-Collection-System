import os
import csv
import sys
sys.path.append('C:\\Users\\cpl4168\\Documents\\Paid Research\\Software-for-Paid-Research-')
from eeg_stimulus_project.lsl.stream_manager import LSL
#from eeg_stimulus_project.utils.labrecorder import LabRecorder

class Save_Data():
    def __init__(self, base_dir, test_number):
        self.base_dir = base_dir
        self.test_number = test_number

    def save_data_stroop(self, current_test, user_inputs, elapsed_time, labrecorder=None):
        # Check the test number and create the appropriate folder
        test_dir = os.path.join(self.base_dir, current_test)
        os.makedirs(test_dir, exist_ok=True)

        # Save data to a file in the test directory
        file_path = os.path.join(test_dir, 'data.csv')
        file_exists = os.path.isfile(file_path)

        # If the file exists, delete it
        if file_exists:
            print("File already exists. Deleting the old file.")
            os.remove(file_path)
        
        with open(file_path, 'a', newline='') as file:  # Append to the file
            writer = csv.writer(file)
            # Write headers
            writer.writerow(['User Inputs', 'Elapsed Time'])
            # Write the data
            for input, time in zip(user_inputs, elapsed_time):
                writer.writerow([input, time])
        print("Data saved successfully!")

    def save_data_passive(self, current_test, labrecorder=None):
        # Check the test number and create the appropriate folder
        test_dir = os.path.join(self.base_dir, current_test)
        os.makedirs(test_dir, exist_ok=True)

        print("Data saved successfully!")