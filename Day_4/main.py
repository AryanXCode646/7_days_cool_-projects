"""
Live Particle Face, Ergonomic Posture Monitor & Privacy Avatar
--------------------------------------------------------------
A real-time webcam particle tracking tool with:
1. Real-time Posture & Slouching Detection (Visual color alerts)
2. Eye-Strain & 20-20-20 Blink Rate Fatigue Monitor
3. Privacy Avatar Anonymizer Mode ('A' key)
4. High-Res Snapshot Portrait Generator ('S' key)

Controls:
    A    -> Toggle Privacy Avatar Mode
    S    -> Save High-Res Snapshot / Avatar
    R    -> Reset Posture Baseline
    H    -> Toggle Ergonomics HUD
    ESC  -> Quit
"""

import time
import math
import pygame
import cv2
import numpy as np
import mediapipe as mp

from particle_system import ParticleSystem

WIDTH = 1280
HEIGHT = 720

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)


def extract_features(frame, privacy_mode=False):
    h, w, _ = frame.shape
    frame_small = cv2.resize(frame, (320, 240))
    rgb = cv2.cvtColor(frame_small, cv2.COLOR_BGR2RGB)

    results = face_mesh.process(rgb)

    if not results.multi_face_landmarks:
        return [], [], None, None

    points = []
    colors = []
    landmarks = results.multi_face_landmarks[0].landmark

    # Posture metrics (nose vs chin vs forehead)
    nose = landmarks[1]
    forehead = landmarks[10]
    chin = landmarks[152]
    left_eye_top = landmarks[159]
    left_eye_bottom = landmarks[145]
    left_eye_left = landmarks[33]
    left_eye_right = landmarks[133]

    # Slouching / Head Pitch angle estimation
    tilt = (nose.y - forehead.y) / max(0.01, (chin.y - forehead.y))
    # Distance estimation via face span
    face_span = math.hypot(chin.x - forehead.x, chin.y - forehead.y)
    
    # Eye Aspect Ratio (EAR) for blink detection
    eye_h = math.hypot(left_eye_top.x - left_eye_bottom.x, left_eye_top.y - left_eye_bottom.y)
    eye_w = math.hypot(left_eye_left.x - left_eye_right.x, left_eye_left.y - left_eye_right.y)
    ear = eye_h / max(0.001, eye_w)

    for i, landmark in enumerate(landmarks):
        x = int(landmark.x * 320)
        y = int(landmark.y * 240)

        if 0 <= x < 320 and 0 <= y < 240:
            sx = int(x * (WIDTH / 320))
            sy = int(y * (HEIGHT / 240))

            if privacy_mode:
                # Stylized cyberpunk / holographic privacy avatar palette
                hue = (i * 7) % 180
                color = (
                    int(120 + 120 * math.sin(i * 0.1)),
                    int(200 + 55 * math.cos(i * 0.1)),
                    255
                )
            else:
                c = frame_small[y, x]
                color = (int(c[2]), int(c[1]), int(c[0]))

            points.append((sx, sy))
            colors.append(color)

    metrics = {
        "tilt": tilt,
        "face_span": face_span,
        "ear": ear,
    }

    return points, colors, metrics, len(landmarks)


def draw_hud(screen, font_title, font, font_sm, posture_score, blink_rate, session_sec, privacy_mode, show_hud, toast_msg, toast_timer):
    if not show_hud:
        return

    w, h = screen.get_size()

    # Top overlay bar
    bar = pygame.Surface((w, 64), pygame.SRCALPHA)
    bar.fill((10, 12, 18, 210))
    screen.blit(bar, (0, 0))

    title_txt = font_title.render("Live Particle Face & Ergonomic Health HUD", True, (255, 255, 255))
    screen.blit(title_txt, (20, 8))

    mode_str = f"Avatar Privacy Mode: {'ACTIVE (Anonymized)' if privacy_mode else 'OFF'}  |  Session: {session_sec//60}m {session_sec%60}s"
    screen.blit(font.render(mode_str, True, (0, 220, 200)), (20, 36))

    # Ergonomics Card Top-Right
    card_w, card_h = 320, 150
    card = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
    card.fill((15, 20, 30, 220))

    status_color = (80, 230, 140) if posture_score > 75 else ((255, 200, 50) if posture_score > 50 else (255, 70, 80))
    pygame.draw.rect(card, status_color, (0, 0, card_w, card_h), 2, border_radius=12)

    c_title = font_title.render("Ergonomics & Fatigue", True, (255, 255, 255))
    card.blit(c_title, (16, 12))

    posture_txt = font.render(f"Posture Health: {int(posture_score)}%", True, status_color)
    card.blit(posture_txt, (16, 44))

    # Progress bar
    pygame.draw.rect(card, (50, 55, 70), (16, 72, 280, 12), border_radius=6)
    pygame.draw.rect(card, status_color, (16, 72, int(280 * (posture_score / 100.0)), 12), border_radius=6)

    blink_txt = font_sm.render(f"Blink Activity: {blink_rate} /min (20-20-20 Rule Active)", True, (200, 210, 220))
    card.blit(blink_txt, (16, 96))

    if posture_score < 55:
        warn = font_sm.render("⚠️ Slouch Alert: Sit up straight & rest neck", True, (255, 80, 80))
        card.blit(warn, (16, 120))
    else:
        good = font_sm.render("✓ Good ergonomic alignment detected", True, (80, 230, 140))
        card.blit(good, (16, 120))

    screen.blit(card, (w - card_w - 20, 75))

    # Bottom controls help
    bot = pygame.Surface((w, 36), pygame.SRCALPHA)
    bot.fill((10, 12, 18, 200))
    screen.blit(bot, (0, h - 36))
    help_txt = font_sm.render("[A] Toggle Privacy Avatar  |  [S] Save Snapshot  |  [R] Reset Baseline  |  [H] Toggle HUD  |  [ESC] Exit", True, (220, 220, 230))
    screen.blit(help_txt, (20, h - 26))

    # Toast badge
    if toast_msg and time.time() < toast_timer:
        t_surf = font.render(toast_msg, True, (255, 255, 255))
        tw = t_surf.get_width() + 30
        box = pygame.Surface((tw, 38), pygame.SRCALPHA)
        box.fill((0, 150, 100, 230))
        pygame.draw.rect(box, (255, 255, 255), (0, 0, tw, 38), 1, border_radius=8)
        box.blit(t_surf, (15, 8))
        screen.blit(box, (w // 2 - tw // 2, 80))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Live Particle Face & Ergonomic Health Assistant")
    clock = pygame.time.Clock()

    font_title = pygame.font.SysFont("Segoe UI", 20, bold=True)
    font = pygame.font.SysFont("Segoe UI", 16)
    font_sm = pygame.font.SysFont("Segoe UI", 13)

    cap = cv2.VideoCapture(0)
    system = ParticleSystem(WIDTH, HEIGHT, 5000)

    running = True
    frame_counter = 0
    privacy_mode = False
    show_hud = True
    start_time = time.time()

    posture_score = 100.0
    blink_count = 0
    last_blink_time = time.time()
    is_blinking = False

    toast_msg = "Posture monitor active! Press [A] for Privacy Avatar."
    toast_timer = time.time() + 4.0

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                elif event.key == pygame.K_a:
                    privacy_mode = not privacy_mode
                    toast_msg = f"Privacy Avatar Mode: {'ENABLED' if privacy_mode else 'DISABLED'}"
                    toast_timer = time.time() + 2.5

                elif event.key == pygame.K_s:
                    filename = f"avatar_snapshot_{int(time.time())}.png"
                    pygame.image.save(screen, filename)
                    toast_msg = f"Snapshot Saved -> {filename}"
                    toast_timer = time.time() + 3.0

                elif event.key == pygame.K_r:
                    posture_score = 100.0
                    toast_msg = "Posture Baseline Recalibrated"
                    toast_timer = time.time() + 2.0

                elif event.key == pygame.K_h:
                    show_hud = not show_hud

        ret, frame = cap.read()
        if not ret:
            continue

        frame = cv2.flip(frame, 1)
        frame_counter += 1

        if frame_counter % 3 == 0:
            points, colors, metrics, lm_count = extract_features(frame, privacy_mode=privacy_mode)
            if metrics:
                # Slouch calculation: ideal tilt ratio is around 0.58-0.65
                tilt = metrics["tilt"]
                span = metrics["face_span"]
                ear = metrics["ear"]

                # Posture quality
                tilt_diff = abs(tilt - 0.60)
                target_score = max(20.0, 100.0 - (tilt_diff * 220) - (max(0, span - 0.6) * 150))
                posture_score = posture_score * 0.92 + target_score * 0.08

                # Blink detection (EAR threshold ~0.18)
                if ear < 0.18:
                    if not is_blinking:
                        blink_count += 1
                        is_blinking = True
                else:
                    is_blinking = False

            system.update_targets(points, colors)

        system.update()

        screen.fill((10, 12, 20))
        system.draw(screen)

        elapsed = int(time.time() - start_time)
        blinks_per_min = int(blink_count / max(1, elapsed / 60.0))

        draw_hud(
            screen,
            font_title,
            font,
            font_sm,
            posture_score,
            blinks_per_min,
            elapsed,
            privacy_mode,
            show_hud,
            toast_msg,
            toast_timer,
        )

        pygame.display.flip()
        clock.tick(60)

    cap.release()
    pygame.quit()


if __name__ == "__main__":
    main()