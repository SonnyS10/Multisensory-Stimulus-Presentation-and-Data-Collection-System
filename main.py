from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit
import os 
import subprocess
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Subject Information")
        self.setGeometry(100, 100, 400, 200)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

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
        subject_id = self.subject_id_input.text()
        test_number = self.test_number_input.text()

        if subject_id and test_number in ['1', '2']:
            # Pass the subject ID and test number as environment variables
            env = os.environ.copy()
            env['SUBJECT_ID'] = subject_id
            env['TEST_NUMBER'] = test_number

            # Run the GUI_pyQt.py file
            subprocess.Popen([sys.executable, 'GUI_pyQt.py'], env=env)
        else:
            print("Please enter a valid Subject ID and Test Number (1 or 2).")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
