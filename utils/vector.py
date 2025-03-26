import numpy as np
def cosine_distance(v1, v2):
    v1_array = np.array(v1)
    v2_array = np.array(v2)
    dot_product = np.dot(v1_array, v2_array)
    norm_v1 = np.linalg.norm(v1_array)
    norm_v2 = np.linalg.norm(v2_array)
    if norm_v1 > 0 and norm_v2 > 0:
        return 1 - (dot_product / (norm_v1 * norm_v2))
    return 1.0  # Maximum distance if either vector is zero