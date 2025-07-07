import socket

PI_IP = '10.115.12.225'  # Raspberry Pi's IP
PORT = 5006
OUTPUT_FILENAME = r"C:\Users\cpl4168\Documents\Paid Research\Software-for-Paid-Research-\eeg_stimulus_project\stimulus\tactile_box_code\received_data.txt"

try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((PI_IP, PORT))
        with open(OUTPUT_FILENAME, "wb") as f:
            print(f"Connected to {PI_IP}:{PORT}. Receiving data...")
            while True:
                data = s.recv(1024)
                if not data:
                    break
                f.write(data)
    print(f"All data saved to {OUTPUT_FILENAME}")
except KeyboardInterrupt:
    print("Connection terminated by user.")  