from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit
import os
import subprocess
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Subject Information")
        self.setGeometry(100, 100, 400, 200)

        # Create the central widget and set it as the central widget of the main window
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create a vertical layout for the central widget
        layout = QVBoxLayout(central_widget)

        # Subject ID input
        self.subject_id_label = QLabel("Subject ID:", self)
        layout.addWidget(self.subject_id_label)
        self.subject_id_input = QLineEdit(self)
        layout.addWidget(self.subject_id_input)

        # Test number input
        self.test_number_label = QLabel("Test Number (1 or 2):", self)
        layout.addWidget(self.test_number_label)
        self.test_number_input = QLineEdit(self)
        layout.addWidget(self.test_number_input)

        # Start button
        self.start_button = QPushButton("Start", self)
        self.start_button.clicked.connect(self.start_experiment)
        layout.addWidget(self.start_button)

    def start_experiment(self):
        # Get the subject ID and test number from the input fields
        subject_id = self.subject_id_input.text()
        test_number = self.test_number_input.text()

        # Check if the subject ID and test number are valid
        if subject_id and test_number in ['1', '2']:
            # Create base directory structure
            base_dir = os.path.join('subject_data', f'subject_{subject_id}', f'test_{test_number}')
            os.makedirs(base_dir, exist_ok=True)

            # List of tests
            tests = [
                'Unisensory Neutral Visual',
                'Unisensory Alcohol Visual',
                'Multisensory Neutral Visual & Olfactory',
                'Multisensory Alcohol Visual & Olfactory',
                'Multisensory Neutral Visual, Tactile & Olfactory',
                'Multisensory Alcohol Visual, Tactile & Olfactory',
                'Multisensory Alcohol (Visual & Tactile)',
                'Multisensory Neutral (Visual & Tactile)',
                'Multisensory Alcohol (Visual & Olfactory)',
                'Multisensory Neutral (Visual & Olfactory)'
            ]

            # Create subdirectories for each test and clear the data.csv file if it exists
            for test in tests:
                test_dir = os.path.join(base_dir, test)
                os.makedirs(test_dir, exist_ok=True)
                file_path = os.path.join(test_dir, 'data.csv')
                if os.path.exists(file_path):
                    with open(file_path, 'w') as file:
                        file.truncate(0)

            # Pass the subject ID, test number, and base directory as environment variables
            env = os.environ.copy()
            env['SUBJECT_ID'] = subject_id
            env['TEST_NUMBER'] = test_number
            env['BASE_DIR'] = base_dir

            # Run the GUI_pyQt.py file
            subprocess.Popen([sys.executable, 'GUI_pyQt.py'], env=env)
        else:
            print("Please enter a valid Subject ID and Test Number (1 or 2).")

if __name__ == "__main__":
    # Create the application and main window, then run the application
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
