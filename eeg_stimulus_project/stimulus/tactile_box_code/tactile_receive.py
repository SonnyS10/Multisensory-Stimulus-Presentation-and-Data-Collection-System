import socket
import threading
import time

HOST = "0.0.0.0"
PORT = 9999

def listen_for_button_presses():
    """Continuously listen for button press messages from the Raspberry Pi."""
    print(f"Starting listener on {HOST}:{PORT}...")
    
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
                server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server.bind((HOST, PORT))
                server.listen(5)  # Increased backlog
                print(f"✓ Listening on {HOST}:{PORT} - waiting for button press...")
                
                try:
                    # No timeout on accept() - wait indefinitely for connection
                    conn, addr = server.accept()
                    print(f"✓ Connected from: {addr[0]}:{addr[1]}")
                    
                    with conn:
                        conn.settimeout(5)  # Timeout for receiving data
                        try:
                            data = conn.recv(1024)
                            if data:
                                message = data.decode("utf-8").strip()
                                print(f"✓ Button pressed! Pi IP: {message}")
                                handle_button_press(message)
                            else:
                                print("✗ Connection closed (no data)")
                        except socket.timeout:
                            print("✗ Timeout waiting for data")
                        except UnicodeDecodeError:
                            print("✗ Could not decode message")
                            
                except Exception as e:
                    print(f"✗ Accept error: {e}")
                    time.sleep(2)
                    
        except OSError as e:
            print(f"✗ Socket error: {e}")
            time.sleep(2)
        except KeyboardInterrupt:
            print("\nShutting down...")
            break

def handle_button_press(pi_ip):
    """Called when the button is pressed."""
    print(f"  -> Handling button press from {pi_ip}")
    # Add your logic here

if __name__ == "__main__":
    listen_for_button_presses()