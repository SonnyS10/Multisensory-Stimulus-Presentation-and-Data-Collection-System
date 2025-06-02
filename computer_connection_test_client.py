# socket_client.py
import socket

SERVER_IP = '129.21.85.205'  # Replace with the IP of the server (Computer B)
PORT = 9999

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((SERVER_IP, PORT))
    message = "Hello from Computer A!"
    s.sendall(message.encode())
    print("Message sent.")