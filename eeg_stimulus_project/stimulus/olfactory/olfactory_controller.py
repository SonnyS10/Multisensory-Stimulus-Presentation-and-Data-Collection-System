import serial
import time
from eeg_stimulus_project.config import config

class OlfactoryController:
    def __init__(self):
        olfactory_config = config.get('hardware.olfactory', {})
        self.arduino1_port = olfactory_config.get('arduino1_port', 'COM9')  # Scents 1-4
        self.arduino2_port = olfactory_config.get('arduino2_port', 'COM8')  # Scents 5-8
        self.baud_rate = olfactory_config.get('baud_rate', 115200)
        self.startup_delay = olfactory_config.get('startup_delay', 2)
        self.ser1 = None
        self.ser2 = None

    def connect(self):
        """Initialize connections to both Arduinos"""
        try:
            self.ser1 = serial.Serial(self.arduino1_port, self.baud_rate, timeout=1)
            self.ser2 = serial.Serial(self.arduino2_port, self.baud_rate, timeout=1)
            time.sleep(self.startup_delay)  # Wait for Arduinos to initialize
            return True
        except Exception as e:
            print(f"Error connecting to Arduinos: {e}")
            self.close()
            return False
    def swap_ports(self):
        """Swap the Arduino port assignments."""
        self.arduino1_port, self.arduino2_port = self.arduino2_port, self.arduino1_port
        print(f"Ports swapped. Arduino1 (scents 1-4) now at: {self.arduino1_port}")
        print(f"Ports swapped. Arduino2 (scents 5-8) now at: {self.arduino2_port}")

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
                # Use ser2 for scents 5-8
                command = f"o{scent_number-4}\n"
                self.ser2.write(command.encode())
                _, response = self.safe_readline(self.ser2)

            #print(f"Triggered scent {scent_number}, response: {response}")
            print(f"Triggered scent {scent_number}")
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

    def trigger_humidifier(self, scent_number, duration_ms=None):
        """Trigger humidifier for a specific scent (1-8)"""
        if not (1 <= scent_number <= 8):
            print(f"Invalid scent number: {scent_number}. Must be between 1 and 8.")
            return False

        try:
            if 1 <= scent_number <= 4:
                command = f"h{scent_number}\n"
                self.ser1.write(command.encode())
                _, response = self.safe_readline(self.ser1)
            else:
                command = f"h{scent_number-4}\n"
                self.ser2.write(command.encode())
                _, response = self.safe_readline(self.ser2)
            print(f"Humidifier triggered for scent {scent_number}")
            return True
        except Exception as e:
            print(f"Error triggering humidifier for scent {scent_number}: {e}")
            return False

    def trigger_pump(self, scent_number, duration_ms=None):
        """Trigger pump for a specific scent (1-8)"""
        if not (1 <= scent_number <= 8):
            print(f"Invalid scent number: {scent_number}. Must be between 1 and 8.")
            return False

        try:
            if 1 <= scent_number <= 4:
                command = f"p{scent_number}\n"
                self.ser1.write(command.encode())
                _, response = self.safe_readline(self.ser1)
            else:
                command = f"p{scent_number-4}\n"
                self.ser2.write(command.encode())
                _, response = self.safe_readline(self.ser2)
            print(f"Pump triggered for scent {scent_number}")
            return True
        except Exception as e:
            print(f"Error triggering pump for scent {scent_number}: {e}")
            return False

    def trigger_solenoid(self, scent_number, duration_ms=None):
        """Trigger solenoid for a specific scent (1-8)"""
        if not (1 <= scent_number <= 8):
            print(f"Invalid scent number: {scent_number}. Must be between 1 and 8.")
            return False

        try:
            if 1 <= scent_number <= 4:
                command = f"s{scent_number}\n"
                self.ser1.write(command.encode())
                _, response = self.safe_readline(self.ser1)
            else:
                command = f"s{scent_number-4}\n"
                self.ser2.write(command.encode())
                _, response = self.safe_readline(self.ser2)
            print(f"Solenoid triggered for scent {scent_number}")
            return True
        except Exception as e:
            print(f"Error triggering solenoid for scent {scent_number}: {e}")
            return False

    def close(self):
        """Close both serial connections"""
        if self.ser1 and self.ser1.is_open:
            try:
                self.ser1.write("q\n".encode())
                _, response = self.safe_readline(self.ser1)
            except Exception as e:
                print(f"Error sending stop command to ser1: {e}")
            finally:
                self.ser1.close()
        
        if self.ser2 and self.ser2.is_open:
            try:
                self.ser2.write("q\n".encode())
                _, response = self.safe_readline(self.ser2)
            except Exception as e:
                print(f"Error sending stop command to ser2: {e}")
            finally:
                self.ser2.close()
