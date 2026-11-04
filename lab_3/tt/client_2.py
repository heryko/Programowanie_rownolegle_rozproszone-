import socket
from send_receive import receive_all, send_all
from edge_filter import edge_filter

SERVER_IP = '10.148.208.146'
SERVER_PORT = 2040

def client_main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((SERVER_IP, SERVER_PORT))
        print(f"Połączono z serwerem {SERVER_IP}:{SERVER_PORT}")
        
        fragment = receive_all(client_socket)
        print("Pobrano fragment obrazu. Przetwarzanie...")
        
        processed_fragment = edge_filter(fragment)
        
        send_all(client_socket, processed_fragment)
        print("Fragment przetworzony i wysłany z powrotem do serwera.")
        
    except ConnectionRefusedError:
        print("Nie udało się połączyć z serwerem. Upewnij się, że serwer jest uruchomiony.")
    finally:
        client_socket.close()

if __name__ == '__main__':
    client_main()