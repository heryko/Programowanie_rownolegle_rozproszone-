import socket
import numpy as np
from PIL import Image
from receive import receive_all
from send import send_all


def split_image(image, n_clients):
  image_array = np.array(image)
  return np.array_split(image_array, n_clients, axis=0)


def merge_image(fragments):
  result_array = np.vstack(fragments)
  return Image.fromarray(result_array)


def server_main(image_path, n_clients, host='0.0.0.0', port=2040):
  image = Image.open(image_path)
  fragments = split_image(image, n_clients)

  server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  server_socket.bind((host, port))
  server_socket.listen(n_clients)
  print(f'Serwer nasłuchuje na porcie {port}...')

  processed_fragments = []
  for i in range(n_clients):
    client_socket, client_adress = server_socket.accept()
    print(f'Połączono z klientem {i+1}: {client_adress}')

    send_all(client_socket, fragments[i])
    processed_fragment = receive_all(client_socket)
    processed_fragments.append(processed_fragment)
    client_socket.close()

  result_image = merge_image(processed_fragments)
  result_image.save('processed_image.png')
  print('Obraz przetworzony zapisany jako processed_image.png')


if __name__ == '__main__':
  server_main('input.jpg', n_clients=1)