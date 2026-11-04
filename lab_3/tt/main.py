import time
from multiprocessing import Pool, cpu_count
import numpy as np
from PIL import Image


def apply_sobel(fragment_array):
    gray = fragment_array
    kernel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
    kernel_y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]])
    h, w = gray.shape
    edges = np.zeros((h, w))

    for i in range(1, h - 1):
        for j in range(1, w - 1):
            region = gray[i - 1 : i + 2, j - 1 : j + 2]

            gx = np.sum(region * kernel_x)
            gy = np.sum(region * kernel_y)

            edges[i, j] = np.sqrt(gx**2 + gy**2)

    if edges.max() > 0:
        edges = (edges / edges.max()) * 255

    return edges.astype(np.uint8)


if __name__ == "__main__":
    total_start = time.perf_counter()

    t0 = time.perf_counter()
    image = Image.open("input.jpg").convert("L")
    image_array = np.array(image)
    print(f"Wczytywanie obrazu: {time.perf_counter() - t0:.4f} s")

    n_processes = cpu_count()
    fragments = np.array_split(image_array, n_processes, axis=0)

    t0 = time.perf_counter()
    with Pool(n_processes) as p:
        processed_fragments = p.map(apply_sobel, fragments)
    processing_time = time.perf_counter() - t0
    print(f"Przetwarzanie (Sobel na {n_processes} rdzeniach): {processing_time:.4f} s")

    t0 = time.perf_counter()
    result_array = np.vstack(processed_fragments)
    result_image = Image.fromarray(result_array)
    result_image.save("processed_image.png")
    print(f"Zapisywanie wyniku: {time.perf_counter() - t0:.4f} s")

    total_time = time.perf_counter() - total_start
    print(f"\nCałkowity czas wykonania: {total_time:.4f} s")