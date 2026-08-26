import numpy as np

class PredictionEngine:
    def __init__(self):
        self.prev = None

    def predict(self, current, strength=0.5):
        if current is None:
            return None

        if self.prev is None:
            self.prev = current
            return current

        velocity = current - self.prev
        predicted = current + velocity * strength

        self.prev = current
        return predicted