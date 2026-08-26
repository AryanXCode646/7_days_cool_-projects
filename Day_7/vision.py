import cv2
import mediapipe as mp
import numpy as np

class VisionSystem:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)

        self.mp_face = mp.solutions.face_mesh
        self.face_mesh = self.mp_face.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True
        )

        # Hands detector (for simple object hints)
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(max_num_hands=2)

        self.prev_landmarks = None

    def get_frame(self):
        try:
            ret, frame = self.cap.read()
            if not ret:
                return None, None, 0, []

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            result = self.face_mesh.process(rgb)
        except Exception:
            return None, None, 0, []

        landmarks = None
        velocity = 0
        detected_objects = []

        if getattr(result, 'multi_face_landmarks', None):
            face = result.multi_face_landmarks[0]
            h, w, _ = frame.shape

            landmarks = np.array([
                (int(p.x * w), int(p.y * h))
                for p in face.landmark
            ])

            if self.prev_landmarks is not None:
                diff = landmarks - self.prev_landmarks
                velocity = np.mean(np.linalg.norm(diff, axis=1))

            self.prev_landmarks = landmarks

        # run hands detection to get simple object hints
        hands_rgb = rgb
        hands_res = self.hands.process(hands_rgb)
        if getattr(hands_res, 'multi_hand_landmarks', None):
            detected_objects.append('hand')

        if landmarks is not None:
            detected_objects.append('face')

        # Heuristic surrounding object detection (phone, bottle/cup, large rectangular objects)
        try:
            small = cv2.resize(frame, (320, int(frame.shape[0] * 320 / frame.shape[1])))
            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(blur, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            h_s, w_s = small.shape[:2]
            seen = set(detected_objects)
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area < 800:  # skip small
                    continue
                x, y, w, h = cv2.boundingRect(cnt)
                ar = float(h) / (w + 1e-6)
                # approximate polygon to check rectangularity
                peri = cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)

                # phone-like: tall rectangle, 4-sided approx, reasonable area
                if len(approx) == 4 and 1.2 < ar < 4.0 and area > 1500:
                    if 'phone' not in seen:
                        detected_objects.append('phone')
                        seen.add('phone')
                        continue

                # bottle/cup-like: circular-ish
                if peri > 0:
                    circularity = 4 * 3.1415 * area / (peri * peri)
                else:
                    circularity = 0
                if circularity > 0.55 and area > 1200:
                    if 'bottle' not in seen:
                        detected_objects.append('bottle')
                        seen.add('bottle')
                        continue

                # large flat objects (book, tablet)
                if len(approx) == 4 and area > (w_s * h_s * 0.05):
                    if 'large_rect' not in seen:
                        detected_objects.append('large_rect')
                        seen.add('large_rect')
                        continue
        except Exception:
            pass

        return frame, landmarks, velocity, detected_objects