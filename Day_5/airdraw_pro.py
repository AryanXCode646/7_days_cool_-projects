"""
AirDraw Pro — Touchless Air Whiteboard & Presentation Annotator
--------------------------------------------------------------
A real-time hand-tracking touchless presentation whiteboard with:
1. Freeform Air Drawing & Eraser with finger gesture tracking
2. Geometric Shape Auto-Beautification (Snaps rough circles, boxes, straight lines)
3. Whiteboard, Darkboard & Camera Pass-Through Presentation Modes
4. Multi-Level Undo / Redo & Stroke Adjustment
5. Clipboard & High-Res PNG Export for notes, signatures & diagrams

Controls / Gestures:
    Index Finger Up           -> Draw / Select Palette
    Index + Middle Fingers    -> Move / Pinch Selected Stroke
    Index + Middle + Ring     -> Eraser Mode
    Open Hand (4-5 Fingers)   -> Clear Board
    A                         -> Toggle Shape Auto-Beautification
    W                         -> Toggle Whiteboard Mode
    B                         -> Toggle Darkboard Mode
    Z / Y                     -> Undo / Redo
    S                         -> Save Drawing (High-Res PNG)
    +/-                       -> Increase / Decrease Brush Size
    ESC                       -> Quit
"""

import math
import time
import cv2
import numpy as np
import mediapipe as mp

WIDTH = 1280
HEIGHT = 720

PINCH_THRESHOLD = 35

COLORS = [
    (0, 0, 255),      # Red
    (0, 200, 0),      # Green
    (255, 0, 0),      # Blue
    (0, 220, 255),    # Yellow
    (255, 0, 255),    # Magenta
    (255, 255, 0),    # Cyan
    (255, 255, 255),  # White
    (30, 30, 30),     # Charcoal
    (0, 140, 255),    # Orange
    (180, 50, 220),   # Purple
]


# -------------------------------------------------
# Hand Tracker
# -------------------------------------------------

class HandTracker:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            model_complexity=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.drawer = mp.solutions.drawing_utils

    def detect(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.hands.process(rgb)

        if result.multi_hand_landmarks:
            hand = result.multi_hand_landmarks[0]
            self.drawer.draw_landmarks(frame, hand, self.mp_hands.HAND_CONNECTIONS)
            return hand
        return None


# -------------------------------------------------
# Stroke & Geometric Beautifier
# -------------------------------------------------

class Stroke:
    def __init__(self, color, thickness, stroke_type="freehand"):
        self.points = []
        self.color = color
        self.thickness = thickness
        self.stroke_type = stroke_type  # 'freehand', 'circle', 'rectangle', 'line'
        self.shape_data = None

    def add(self, point):
        self.points.append(point)

    def beautify(self):
        """Analyzes stroke geometry and snaps to geometric primitive if matched."""
        if len(self.points) < 8:
            return

        pts = np.array(self.points, dtype=np.int32)
        start_p = self.points[0]
        end_p = self.points[-1]
        chord_len = math.hypot(end_p[0] - start_p[0], end_p[1] - start_p[1])
        arc_len = cv2.arcLength(pts, False)

        if arc_len == 0:
            return

        # 1. Check Straight Line (Straightness ratio > 0.88)
        if chord_len / arc_len > 0.88 and chord_len > 40:
            self.stroke_type = "line"
            self.shape_data = (start_p, end_p)
            return

        # 2. Check Closed Loop (Distance between start and end < 35% of max dimension)
        x, y, w, h = cv2.boundingRect(pts)
        if chord_len < max(w, h) * 0.35 and len(self.points) > 15:
            area = cv2.contourArea(pts)
            perimeter = cv2.arcLength(pts, True)
            if perimeter > 0:
                circularity = 4 * math.pi * (area / (perimeter * perimeter))
                if circularity > 0.65:
                    (cx, cy), radius = cv2.minEnclosingCircle(pts)
                    self.stroke_type = "circle"
                    self.shape_data = ((int(cx), int(cy)), int(radius))
                    return

                # Otherwise Snap to Box / Rectangle
                self.stroke_type = "rectangle"
                self.shape_data = ((x, y), (x + w, y + h))
                return

    def draw(self, canvas):
        if self.stroke_type == "circle" and self.shape_data:
            center, radius = self.shape_data
            cv2.circle(canvas, center, radius, self.color, self.thickness, cv2.LINE_AA)
        elif self.stroke_type == "rectangle" and self.shape_data:
            p1, p2 = self.shape_data
            cv2.rectangle(canvas, p1, p2, self.color, self.thickness, cv2.LINE_AA)
        elif self.stroke_type == "line" and self.shape_data:
            p1, p2 = self.shape_data
            cv2.line(canvas, p1, p2, self.color, self.thickness, cv2.LINE_AA)
        else:
            if len(self.points) < 2:
                return
            for i in range(1, len(self.points)):
                cv2.line(canvas, self.points[i - 1], self.points[i], self.color, self.thickness, cv2.LINE_AA)

    def move(self, dx, dy):
        self.points = [(p[0] + dx, p[1] + dy) for p in self.points]
        if self.stroke_type == "circle" and self.shape_data:
            (cx, cy), r = self.shape_data
            self.shape_data = ((cx + dx, cy + dy), r)
        elif self.stroke_type in ("rectangle", "line") and self.shape_data:
            (x1, y1), (x2, y2) = self.shape_data
            self.shape_data = ((x1 + dx, y1 + dy), (x2 + dx, y2 + dy))


# -------------------------------------------------
# Main AirDraw Application
# -------------------------------------------------

class AirDraw:
    def __init__(self):
        self.tracker = HandTracker()
        self.canvas = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)

        self.strokes = []
        self.redo_stack = []
        self.current_stroke = None

        self.current_color = COLORS[0]
        self.brush_size = 6
        self.eraser_size = 35
        self.eraser = False

        self.prev_point = None
        self.selected_stroke = None
        self.smooth_buffer = []

        self.is_pinching = False
        self.just_released_pinch = False
        self.auto_beautify = True
        self.board_mode = "camera"  # 'camera', 'whiteboard', 'darkboard'

        self.toast_msg = "AirDraw Pro: Press [A] for Shape Snapping | [W] Whiteboard"
        self.toast_time = time.time() + 4.0

    def smooth_point(self, point):
        self.smooth_buffer.append(point)
        if len(self.smooth_buffer) > 4:
            self.smooth_buffer.pop(0)
        x = int(np.mean([p[0] for p in self.smooth_buffer]))
        y = int(np.mean([p[1] for p in self.smooth_buffer]))
        return (x, y)

    def fingers_up(self, lm):
        fingers = []
        tips = [8, 12, 16, 20]
        for tip in tips:
            fingers.append(1 if lm[tip].y < lm[tip - 2].y else 0)
        return fingers

    def pinch_distance(self, lm):
        x1 = int(lm[4].x * WIDTH)
        y1 = int(lm[4].y * HEIGHT)
        x2 = int(lm[8].x * WIDTH)
        y2 = int(lm[8].y * HEIGHT)
        return math.hypot(x2 - x1, y2 - y1)

    def draw_palette(self, frame):
        # Top Palette Bar
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (WIDTH, 60), (20, 24, 32), -1)
        cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)

        for i, color in enumerate(COLORS):
            x = 20 + i * 48
            cv2.rectangle(frame, (x, 10), (x + 36, 48), color, -1)
            if color == self.current_color:
                cv2.rectangle(frame, (x - 2, 8), (x + 38, 50), (255, 255, 255), 2)

        # Status indicators on top-right
        status = f"Mode: {self.board_mode.upper()} | Shapes: {'AUTO-SNAP' if self.auto_beautify else 'OFF'} | Size: {self.brush_size}px"
        cv2.putText(frame, status, (600, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 240, 220), 1, cv2.LINE_AA)

    def check_palette(self, point):
        x, y = point
        if y < 60:
            index = (x - 20) // 48
            if 0 <= index < len(COLORS):
                self.current_color = COLORS[index]

    def detect_near_stroke(self, point):
        for stroke in reversed(self.strokes):
            for p in stroke.points:
                if math.hypot(point[0] - p[0], point[1] - p[1]) < 35:
                    return stroke
        return None

    def undo(self):
        if self.strokes:
            self.redo_stack.append(self.strokes.pop())
            self.toast_msg = "Undo"
            self.toast_time = time.time() + 1.5

    def redo(self):
        if self.redo_stack:
            self.strokes.append(self.redo_stack.pop())
            self.toast_msg = "Redo"
            self.toast_time = time.time() + 1.5

    def run(self):
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

        prev = time.time()

        while True:
            success, frame = cap.read()
            if not success:
                continue

            frame = cv2.flip(frame, 1)

            # Board background handling
            if self.board_mode == "whiteboard":
                display_bg = np.full((HEIGHT, WIDTH, 3), 245, dtype=np.uint8)
            elif self.board_mode == "darkboard":
                display_bg = np.full((HEIGHT, WIDTH, 3), 25, dtype=np.uint8)
            else:
                display_bg = frame.copy()

            hand = self.tracker.detect(frame)

            if hand:
                lm = hand.landmark
                fingers = self.fingers_up(lm)
                x = int(lm[8].x * WIDTH)
                y = int(lm[8].y * HEIGHT)
                point = self.smooth_point((x, y))
                pinch = self.pinch_distance(lm)

                # Clear All (Open Hand)
                if fingers == [1, 1, 1, 1]:
                    if self.strokes:
                        self.strokes.clear()
                        self.redo_stack.clear()
                        self.toast_msg = "Board Cleared"
                        self.toast_time = time.time() + 2.0

                # Eraser (3 fingers)
                elif fingers == [1, 1, 1, 0]:
                    self.eraser = True
                else:
                    self.eraser = False

                # Pinch to Move Stroke
                if pinch < PINCH_THRESHOLD:
                    self.is_pinching = True
                    if self.current_stroke and self.auto_beautify:
                        self.current_stroke.beautify()
                    self.current_stroke = None

                    if self.selected_stroke is None:
                        self.selected_stroke = self.detect_near_stroke(point)
                        self.prev_point = point
                    else:
                        dx = point[0] - self.prev_point[0]
                        dy = point[1] - self.prev_point[1]
                        self.selected_stroke.move(dx, dy)
                        self.prev_point = point
                else:
                    if self.is_pinching:
                        self.just_released_pinch = True
                    self.is_pinching = False
                    self.selected_stroke = None

                # Drawing (Only when index finger is up)
                if not self.is_pinching and not self.just_released_pinch:
                    if fingers[0] == 1 and fingers[1] == 0:
                        self.check_palette(point)
                        if self.current_stroke is None:
                            thickness = self.eraser_size if self.eraser else self.brush_size
                            color = (0, 0, 0) if (self.eraser and self.board_mode == "camera") else ((245, 245, 245) if (self.eraser and self.board_mode == "whiteboard") else self.current_color)
                            self.current_stroke = Stroke(color, thickness)
                            self.strokes.append(self.current_stroke)
                            self.redo_stack.clear()

                        self.current_stroke.add(point)
                    else:
                        if self.current_stroke:
                            if self.auto_beautify:
                                self.current_stroke.beautify()
                            self.current_stroke = None
                else:
                    if self.current_stroke:
                        if self.auto_beautify:
                            self.current_stroke.beautify()
                        self.current_stroke = None
                    self.just_released_pinch = False

            # Redraw canvas
            self.canvas[:] = 0
            for stroke in self.strokes:
                stroke.draw(self.canvas)

            # Blend canvas with background
            if self.board_mode == "camera":
                output = cv2.add(display_bg, self.canvas)
            else:
                # Masked blend for clean solid white/darkboards
                gray_mask = cv2.cvtColor(self.canvas, cv2.COLOR_BGR2GRAY)
                _, mask = cv2.threshold(gray_mask, 1, 255, cv2.THRESH_BINARY)
                mask_inv = cv2.bitwise_not(mask)
                bg_cut = cv2.bitwise_and(display_bg, display_bg, mask=mask_inv)
                fg_cut = cv2.bitwise_and(self.canvas, self.canvas, mask=mask)
                output = cv2.add(bg_cut, fg_cut)

            self.draw_palette(output)

            # Bottom Help bar
            help_str = "[A] Auto-Shapes | [W/B] White/Dark Board | [Z/Y] Undo/Redo | [S] Save | [+/-] Size"
            cv2.putText(output, help_str, (20, HEIGHT - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 210), 1, cv2.LINE_AA)

            # Toast Notification
            if self.toast_msg and time.time() < self.toast_time:
                cv2.putText(output, self.toast_msg, (WIDTH // 2 - 220, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 180), 2, cv2.LINE_AA)

            cv2.imshow("AirDraw Pro — Touchless Presentation Whiteboard", output)

            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                break
            elif key == ord('a'):
                self.auto_beautify = not self.auto_beautify
                self.toast_msg = f"Shape Beautification: {'ENABLED' if self.auto_beautify else 'DISABLED'}"
                self.toast_time = time.time() + 2.0
            elif key == ord('w'):
                self.board_mode = "whiteboard" if self.board_mode != "whiteboard" else "camera"
            elif key == ord('b'):
                self.board_mode = "darkboard" if self.board_mode != "darkboard" else "camera"
            elif key in (ord('z'), 26):
                self.undo()
            elif key in (ord('y'), 25):
                self.redo()
            elif key in (ord('+'), ord('=')):
                self.brush_size = min(30, self.brush_size + 2)
                self.toast_msg = f"Brush Size: {self.brush_size}px"
                self.toast_time = time.time() + 1.5
            elif key in (ord('-'), ord('_')):
                self.brush_size = max(2, self.brush_size - 2)
                self.toast_msg = f"Brush Size: {self.brush_size}px"
                self.toast_time = time.time() + 1.5
            elif key == ord('s'):
                filename = f"airdraw_export_{int(time.time())}.png"
                cv2.imwrite(filename, self.canvas)
                self.toast_msg = f"Saved Drawing -> {filename}"
                self.toast_time = time.time() + 3.0

        cap.release()
        cv2.destroyAllWindows()


# -------------------------------------------------
if __name__ == "__main__":
    app = AirDraw()
    app.run()
