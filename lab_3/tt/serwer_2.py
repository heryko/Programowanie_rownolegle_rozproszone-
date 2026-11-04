import socket
import numpy as np
from PIL import Image
from send_receive import receive_all, send_all

def split_image(image: Image.Image, n_clients: int) -> list:
    """Dzieli obraz na N równych fragmentów wzdłuż osi Y."""
    image_array = np.array(image)
    return np.array_split(image_array, n_clients, axis=0)

def merge_image(fragments: list) -> Image.Image:
    """Scalanie przetworzonych fragmentów w jeden obraz."""
    result_array = np.vstack(fragments)
    return Image.fromarray(result_array)

def server_main(image_path: str, n_clients: int, host: str = '0.0.0.0', port: int = 2040):
    image = Image.open(image_path)
    fragments = split_image(image, n_clients)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    server_socket.bind((host, port))
    server_socket.listen(n_clients)
    print(f'Serwer nasłuchuje na {host}:{port} (Oczekuje na {n_clients} klientów)...')

    processed_fragments = []
    
    for i in range(n_clients):
        client_socket, client_address = server_socket.accept()
        print(f'[{i+1}/{n_clients}] Połączono z klientem: {client_address}')

        send_all(client_socket, fragments[i])
        processed_fragment = receive_all(client_socket)
        processed_fragments.append(processed_fragment)
        
        client_socket.close()

    server_socket.close()

    result_image = merge_image(processed_fragments)
    result_image.save('processed_image.png')
    print('Obraz przetworzony i zapisany jako processed_image.png')

if __name__ == '__main__':
    server_main('input.jpg', n_clients=2)