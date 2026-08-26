import numpy as np
from collections import deque

class MemorySystem:
    def __init__(self, size=150):
        self.history = deque(maxlen=size)

    def update(self, landmarks, velocity, transcript=None):
        if landmarks is None:
            # still record transcript if available
            if transcript:
                self.history.append({
                    "velocity": 0,
                    "blink": 0,
                    "smile": 0,
                    "landmarks": None,
                    "transcript": transcript
                })
            return

        blink = self._eye_ratio(landmarks)
        smile = self._smile_ratio(landmarks)

        entry = {
            "velocity": velocity,
            "blink": blink,
            "smile": smile,
            "landmarks": landmarks.copy()
        }

        if transcript:
            entry["transcript"] = transcript

        self.history.append(entry)

    def _eye_ratio(self, lm):
        try:
            left = np.linalg.norm(lm[159] - lm[145])
            right = np.linalg.norm(lm[386] - lm[374])
            return (left + right) / 2
        except Exception:
            return 0

    def _smile_ratio(self, lm):
        try:
            return np.linalg.norm(lm[61] - lm[291])
        except Exception:
            return 0

    def get_profile(self):
        if not self.history:
            return None

        v = np.mean([x["velocity"] for x in self.history])
        b = np.mean([x["blink"] for x in self.history])
        s = np.mean([x["smile"] for x in self.history])
        trail = [x["landmarks"] for x in list(self.history)[-15:] if x.get("landmarks") is not None]

        return {
            "avg_velocity": v,
            "blink_rate": b,
            "smile_intensity": s,
            "trail": trail
        }

    def is_staring(self):
        if len(self.history) < 20:
            return False

        recent = list(self.history)[-20:]
        blink_vals = [x["blink"] for x in recent]

        return np.mean(blink_vals) > 8