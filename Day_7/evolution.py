import numpy as np
import random

class EvolutionEngine:
    def __init__(self):
        self.level = 0
        self.mode = "SCANNING"
        self.last_points = None
        self.last_action = None

    def update(self, profile, staring=False, transcript=None):
        if profile is None:
            return

        self.level += 0.05

        if staring:
            self.level += 0.2

        self.level = min(self.level, 100)

        if self.level < 30:
            self.mode = "SCANNING"
        elif self.level < 70:
            self.mode = "LEARNING"
        else:
            self.mode = "AUTONOMOUS"

        # Influence from speech: positive or negative keywords
        if transcript:
            t = transcript.lower()
            # english triggers
            if any(k in t for k in ["good", "smile", "yes", "friend"]):
                self.level = min(100, self.level + 0.5)
            if any(k in t for k in ["no", "stop", "leave", "hate"]):
                self.level = max(0, self.level - 0.5)

            # simple hindi keywords
            if any(k in t for k in ["haan", "achha", "pyar", "dost"]):
                self.level = min(100, self.level + 0.6)
            if any(k in t for k in ["nahin", "nahi", "ruk", "chhod"]):
                self.level = max(0, self.level - 0.6)

    def independent_trigger(self):
        return self.level > 70 and random.random() < 0.02

    def autonomous_action(self, points):
        if points is None:
            return None

        self.last_points = points

        action = random.choice(["drift", "freeze", "twitch"])
        self.last_action = action

        if action == "drift":
            return points + np.random.randint(-15, 15, points.shape)

        if action == "freeze":
            return self.last_points if self.last_points is not None else points

        if action == "twitch":
            return points + np.random.randint(-5, 5, points.shape)

        return points