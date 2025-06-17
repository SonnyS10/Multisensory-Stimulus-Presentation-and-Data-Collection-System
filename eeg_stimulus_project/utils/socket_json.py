import struct
import json

def send_json(sock, obj):
    data = json.dumps(obj).encode('utf-8')
    length = struct.pack('>I', len(data))  # 4 bytes, big-endian
    sock.sendall(length + data)

def recv_json(sock):
    # Read 4 bytes for the length
    length_bytes = b''
    while len(length_bytes) < 4:
        chunk = sock.recv(4 - len(length_bytes))
        if not chunk:
            return None  # Connection closed
        length_bytes += chunk
    length = struct.unpack('>I', length_bytes)[0]
    # Read the JSON data
    data = b''
    while len(data) < length:
        chunk = sock.recv(length - len(data))
        if not chunk:
            return None
        data += chunk
    return json.loads(data.decode('utf-8'))