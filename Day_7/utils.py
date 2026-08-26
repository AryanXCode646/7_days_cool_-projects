import time
import numpy as np

class FPSCounter:
    def __init__(self):
        self.prev = time.time()

    def update(self):
        now = time.time()
        fps = 1 / (now - self.prev + 1e-6)
        self.prev = now
        return fps


def sanitize_points(points, width, height):
    if points is None:
        return None

    points = points.astype(int)
    points[:, 0] = np.clip(points[:, 0], 0, width - 1)
    points[:, 1] = np.clip(points[:, 1], 0, height - 1)

    return points