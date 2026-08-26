import cv2
import mediapipe as mp
import time
import threading
import math
import sys
import ctypes
from config import GESTURE_COOLDOWN


# ---------------------------------------------------------
# Windows Virtual Key Simulator (Standard Library ctypes)
# ---------------------------------------------------------

def send_win_key(vk_code):
    """Sends a key down and key up event via user32."""
    if sys.platform == "win32":
        try:
            # keybd_event(bVk, bScan, dwFlags, dwExtraInfo)
            ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
            time.sleep(0.05)
            ctypes.windll.user32.keybd_event(vk_code, 0, 2, 0)  # KEYEVENTF_KEYUP = 2
        except Exception:
            pass


class GestureController:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6
        )
        self.mp_draw = mp.solutions.drawing_utils

        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        self.current_gesture = None
        self.last_gesture_time = 0
        self.running = True
        self.mode = "game"  # 'game' or 'remote'
        self.last_remote_action = "None"

        # Buffer for gesture smoothing
        self.gesture_buffer = []
        self.buffer_size = 5

        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def set_mode(self, mode):
        self.mode = mode

    def _count_fingers(self, landmarks):
        fingers = []
        # Thumb (adjusted for flipped camera)
        fingers.append(1 if landmarks[4].x < landmarks[3].x else 0)
        tips = [8, 12, 16, 20]
        for tip in tips:
            fingers.append(1 if landmarks[tip].y < landmarks[tip - 2].y else 0)
        return sum(fingers)

    def _recognize(self, landmarks):
        fingers = self._count_fingers(landmarks)
        if fingers == 0:
            return "fist"  # shoot in game / mute in remote
        elif fingers == 1:
            return "forward"  # 1 finger (index): forward / vol up
        elif fingers == 2:
            return "left"     # 2 fingers: turn / vol down
        elif fingers == 3:
            return "right"    # 3 fingers: turn / play-pause
        elif fingers == 4:
            return "jump"     # 4 fingers
        elif fingers == 5:
            return "palm"     # open palm: pause / next slide
        return None

    def execute_remote_action(self, gesture):
        """Dispatches real system actions based on touchless gesture."""
        if gesture == "forward":  # 1 finger -> Volume Up / Next Slide
            send_win_key(0xAF)  # VK_VOLUME_UP
            self.last_remote_action = "Volume Up 🔊"
        elif gesture == "left":  # 2 fingers -> Volume Down / Prev Slide
            send_win_key(0xAE)  # VK_VOLUME_DOWN
            self.last_remote_action = "Volume Down 🔉"
        elif gesture == "right":  # 3 fingers -> Play / Pause Media
            send_win_key(0xB3)  # VK_MEDIA_PLAY_PAUSE
            self.last_remote_action = "Media Play/Pause ⏯"
        elif gesture == "palm":  # Open Hand -> Next Slide (Right Arrow)
            send_win_key(0x27)  # VK_RIGHT
            self.last_remote_action = "Next Slide ➡️"
        elif gesture == "fist":  # Fist -> Mute Audio
            send_win_key(0xAD)  # VK_VOLUME_MUTE
            self.last_remote_action = "Mute Audio 🔇"

    def _run(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb)

            detected_gesture = None
            if results.multi_hand_landmarks:
                hand = results.multi_hand_landmarks[0]
                self.mp_draw.draw_landmarks(frame, hand, self.mp_hands.HAND_CONNECTIONS)
                detected_gesture = self._recognize(hand.landmark)

            now = time.time()
            if detected_gesture:
                self.gesture_buffer.append(detected_gesture)
                if len(self.gesture_buffer) > self.buffer_size:
                    self.gesture_buffer.pop(0)

                final_gesture = max(set(self.gesture_buffer), key=self.gesture_buffer.count)

                if (
                    self.gesture_buffer.count(final_gesture) >= 3 and
                    now - self.last_gesture_time > GESTURE_COOLDOWN
                ):
                    self.current_gesture = final_gesture
                    self.last_gesture_time = now

                    # If in remote mode, dispatch direct PC command
                    if self.mode == "remote":
                        self.execute_remote_action(final_gesture)

            # Camera HUD
            mode_lbl = f"Mode: {self.mode.upper()} | Last: {self.current_gesture or 'None'}"
            cv2.putText(frame, mode_lbl, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 180), 2)
            if self.mode == "remote":
                cv2.putText(frame, f"Action: {self.last_remote_action}", (15, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 200, 50), 2)

            cv2.imshow("Gesture Controller HUD", frame)
            if cv2.waitKey(1) & 0xFF == 27:
                break

        self.cap.release()
        cv2.destroyAllWindows()

    def get_gesture(self):
        g = self.current_gesture
        self.current_gesture = None
        # Map back to snake directions if in game mode
        if g == "fist":
            return "shoot"
        return g

    def stop(self):
        self.running = False