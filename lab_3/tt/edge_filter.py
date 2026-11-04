import numpy as np
from scipy.ndimage import convolve

def edge_filter(image_array: np.ndarray) -> np.ndarray:
    """
    Aplikuje filtr Sobela do wykrywania krawędzi na macierzy obrazu.
    """
    if len(image_array.shape) == 3:
        gray = np.dot(image_array[..., :3], [0.2989, 0.5870, 0.1140])
    else:
        gray = image_array.astype(float)

    kernel_x = np.array([[-1, 0, 1], 
                         [-2, 0, 2], 
                         [-1, 0, 1]])
    
    kernel_y = np.array([[-1, -2, -1], 
                         [ 0,  0,  0], 
                         [ 1,  2,  1]])

    gx = convolve(gray, kernel_x)
    gy = convolve(gray, kernel_y)

    magnitude = np.hypot(gx, gy)
    

    if magnitude.max() > 0:
        magnitude = (magnitude / magnitude.max()) * 255
        
    return magnitude.astype(np.uint8)