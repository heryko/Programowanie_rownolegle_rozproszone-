import pickle
import socket

def send_all(sock: socket.socket, data: object) -> None:
    """Wysyła obiekt zserializowany pickle wraz z rozmiarem (4 bajty)."""
    serialized_data = pickle.dumps(data)
    sock.sendall(len(serialized_data).to_bytes(4, byteorder='big'))
    sock.sendall(serialized_data)

def receive_all(sock: socket.socket) -> object:
    """Odbiera 4 bajty rozmiaru danych, a następnie w pętli pełną zawartość."""
    raw_length = sock.recv(4)
    if not raw_length:
        return None
    length = int.from_bytes(raw_length, byteorder='big')
    
    data = bytearray()
    while len(data) < length:
        packet = sock.recv(4096)
        if not packet:
            break
        data.extend(packet)
        
    return pickle.loads(bytes(data))