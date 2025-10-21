import serial
import time

class OlfactoryController:
    def __init__(self):
        # Arduino settings
        self.arduino1_port = 'COM8'  # Scents 1-4
        self.arduino2_port = 'COM9'  # Scents 5-8
        self.baud_rate = 115200
        self.ser1 = None
        self.ser2 = None

    def connect(self):
        """Initialize connections to both Arduinos"""
        try:
            self.ser1 = serial.Serial(self.arduino1_port, self.baud_rate, timeout=1)
            self.ser2 = serial.Serial(self.arduino2_port, self.baud_rate, timeout=1)
            time.sleep(2)  # Wait for Arduinos to initialize
            return True
        except Exception as e:
            print(f"Error connecting to Arduinos: {e}")
            return False

    def safe_readline(self, ser, encoding='utf-8'):
        """Safely read a line from serial port"""
        b = ser.readline()
        if not b:
            return b'', ''
        try:
            s = b.decode(encoding).strip()
        except UnicodeDecodeError:
            s = b.decode('latin-1').strip()
        return b, s

    def trigger_scent(self, scent_number):
        """
        Trigger a specific scent (1-8)
        Returns True if successful, False otherwise
        """
        if not (1 <= scent_number <= 8):
            print(f"Invalid scent number: {scent_number}. Must be between 1 and 8.")
            return False

        try:
            if 1 <= scent_number <= 4:
                # Use ser1 for scents 1-4
                command = f"o{scent_number}\n"
                self.ser1.write(command.encode())
                _, response = self.safe_readline(self.ser1)
            else:
                # Use ser2 for scents 5-8, but adjust command to o1-o4
                command = f"o{scent_number-4}\n"
                self.ser2.write(command.encode())
                _, response = self.safe_readline(self.ser2)

            print(f"Triggered scent {scent_number}, response: {response}")
            return True

        except Exception as e:
            print(f"Error triggering scent {scent_number}: {e}")
            return False

    def stop_scent(self, scent_number):
        """Stop a specific scent (1-8)"""
        try:
            if 1 <= scent_number <= 4:
                self.ser1.write("q\n".encode())
                _, response = self.safe_readline(self.ser1)
            else:
                self.ser2.write("q\n".encode())
                _, response = self.safe_readline(self.ser2)
            return True
        except Exception as e:
            print(f"Error stopping scent {scent_number}: {e}")
            return False

    def close(self):
        """Close both serial connections"""
        if self.ser1:
            self.ser1.close()
        if self.ser2:
            self.ser2.close()
