import os
import csv

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
        print("super cool")