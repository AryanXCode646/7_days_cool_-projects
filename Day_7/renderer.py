import cv2
import numpy as np

class Renderer:
    def __init__(self):
        self.glow_phase = 0

    def draw(self, frame, points, evo, profile, fps, sync, volume, transcript=None, lang=None, highlight=False, autonomous_flag=False, last_action=None, detection_text=None, detection_conf=0.0):
        if points is None:
            return frame

        h, w, _ = frame.shape
        overlay = np.zeros_like(frame)

        # Trail
        if profile:
            for i, trail_pts in enumerate(profile["trail"]):
                alpha = i / len(profile["trail"])
                for p in trail_pts:
                    x, y = int(p[0].item() if hasattr(p[0], 'item') else p[0]), int(p[1].item() if hasattr(p[1], 'item') else p[1])
                    if 0 <= x < w and 0 <= y < h:
                        cv2.circle(frame, (x, y), 1, (255, int(255*alpha), 255), -1)

        # Main: choose visual style based on evolution level
        style = 'particles' if evo.level < 60 else 'wireframe'

        if style == 'particles':
            for p in points:
                x, y = int(p[0].item() if hasattr(p[0], 'item') else p[0]), int(p[1].item() if hasattr(p[1], 'item') else p[1])
                if 0 <= x < w and 0 <= y < h:
                    cv2.circle(overlay, (x, y), 2, (200, 50, 255), -1)
        else:
            # simple wireframe by connecting landmark neighbors
            pts = []
            for p in points:
                pts.append((int(p[0].item() if hasattr(p[0], 'item') else p[0]), int(p[1].item() if hasattr(p[1], 'item') else p[1])))
            for i in range(1, len(pts)):
                cv2.line(overlay, pts[i-1], pts[i], (180, 255, 100), 1)

        # Glow
        self.glow_phase += 0.05
        pulse = (np.sin(self.glow_phase) + 1) * 0.5
        intensity = 0.3 + pulse * 0.7

        blurred = cv2.GaussianBlur(overlay, (0, 0), sigmaX=6)
        frame = cv2.addWeighted(frame, 1, blurred, intensity, 0)

        # Glitch
        if evo.level > 50:
            frame = self.glitch(frame)

        # Highlight (triggered by keyword or important event)
        if highlight:
            overlay2 = frame.copy()
            alpha = 0.5 + 0.5 * pulse
            cv2.rectangle(overlay2, (0,0), (w-1,h-1), (0,200,255), 12)
            frame = cv2.addWeighted(frame, 1, overlay2, alpha*0.3, 0)

        # HUD (include extra state)
        self.hud(frame, evo, fps, sync, volume, transcript, lang, autonomous_flag, last_action, profile, points, detection_text, detection_conf)

        return frame

    def glitch(self, frame):
        h, w, _ = frame.shape

        if np.random.rand() < 0.05:
            x = np.random.randint(0, w)
            frame[:, x:x+5] = frame[:, x:x+5][::-1]

        if np.random.rand() < 0.03:
            shift = np.random.randint(-20, 20)
            frame = np.roll(frame, shift, axis=1)

        return frame

    def hud(self, frame, evo, fps, sync, volume, transcript=None, lang=None, autonomous_flag=False, last_action=None, profile=None, points=None, detection_text=None, detection_conf=0.0):
        cv2.putText(frame, f"FPS: {int(fps)}", (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)

        cv2.putText(frame, f"EVOLUTION: {int(evo.level)}%", (20, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,0,255), 2)

        cv2.putText(frame, f"MODE: {evo.mode}", (20, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)

        cv2.putText(frame, f"SYNC: {int(sync)}%", (20, 120),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,0), 2)

        cv2.putText(frame, f"VOICE: {int(volume)}", (20, 150),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,100), 2)

        if transcript:
            display = transcript if len(transcript) < 40 else transcript[:37] + '...'
            lang_tag = f"[{lang}]" if lang else ''
            cv2.putText(frame, f"SAY: {lang_tag} {display}", (20, 185),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,200), 2)
        # Extra debug/state
        y = 210
        if profile:
            avg_v = profile.get('avg_velocity', 0)
            blink = profile.get('blink_rate', 0)
            smile = profile.get('smile_intensity', 0)
            trail_len = len(profile.get('trail', []))
            cv2.putText(frame, f"AVG_V: {avg_v:.1f}", (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 1)
            cv2.putText(frame, f"BLINK: {blink:.1f}", (140, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 1)
            cv2.putText(frame, f"SMILE: {smile:.1f}", (260, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 1)
            cv2.putText(frame, f"TRAIL: {trail_len}", (380, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 1)
            y += 22
        # predicted count
        pred_count = 0
        try:
            pred_count = len(points) if points is not None else 0
        except Exception:
            pred_count = 0
        cv2.putText(frame, f"PRED: {pred_count}", (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,100), 1)
        cv2.putText(frame, f"AUTON: {str(bool(autonomous_flag))}", (110, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,100,200), 1)
        act = last_action if last_action else '-'
        cv2.putText(frame, f"ACT: {act}", (240, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100,200,200), 1)
        # detection
        if detection_text:
            det_disp = f"SEE: {detection_text} ({int(detection_conf*100)}%)"
            cv2.putText(frame, det_disp, (20, y+22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,200,255), 1)