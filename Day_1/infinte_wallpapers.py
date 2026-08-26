"""
Infinite Wallpaper Generator & Live Desktop Studio
---------------------------------------------------------
A real-time procedural abstract wallpaper generator with direct
Windows desktop application, multi-resolution support, curated
focus themes, and daily productivity clock/affirmation overlays.

Controls:
    SPACE  -> Generate new wallpaper
    W      -> Set directly as Windows Desktop Wallpaper
    S      -> Save wallpaper to folder
    T      -> Cycle Focus / Color Themes
    C      -> Toggle Clock & Focus Affirmation Overlay
    R      -> Switch Resolution (Desktop 16:9 / Ultrawide / Mobile 9:16)
    P      -> Pause / Resume Auto-Rotation
    +/-    -> Adjust Auto-Cycle Interval
    ESC    -> Exit
"""

import os
import sys
import time
import ctypes
import datetime
from pathlib import Path

import cv2
import numpy as np
import pygame

# ---------------------------------------------------------
# Settings & State
# ---------------------------------------------------------

TITLE = "Infinite Wallpaper Studio & Focus Manager"
SAVE_DIR = Path("saved_wallpapers")
SAVE_DIR.mkdir(exist_ok=True)

RESOLUTIONS = [
    ("Desktop 1080p", (1920, 1080)),
    ("Desktop 2K/1440p", (2560, 1440)),
    ("Ultrawide 21:9", (2560, 1080)),
    ("Mobile 9:16", (1080, 1920)),
    ("Compact Window", (1280, 720)),
]
curr_res_idx = 4  # Start with compact preview window

WINDOW_SIZE = (1280, 720)
FPS = 60

THEMES = [
    ("Cyberpunk Neon", [(10, 15, 30), (255, 0, 128), (0, 240, 255), (120, 0, 255)]),
    ("Focus Dark Slate", [(15, 18, 24), (45, 55, 72), (99, 179, 237), (226, 232, 240)]),
    ("Nordic Calm", [(240, 244, 248), (142, 168, 157), (74, 96, 88), (212, 163, 115)]),
    ("Golden Sunset", [(30, 10, 25), (255, 110, 80), (255, 200, 60), (140, 45, 110)]),
    ("Emerald Forest", [(10, 25, 18), (30, 80, 50), (80, 200, 120), (180, 240, 190)]),
]
curr_theme_idx = 0

AFFIRMATIONS = [
    "Focus on what truly matters today.",
    "Small consistent steps lead to massive achievements.",
    "Clarity precedes mastery.",
    "Deep work creates extraordinary value.",
    "Stay curious, build fearlessly.",
    "Calm mind, relentless execution.",
]

# ---------------------------------------------------------
# Pattern Generators
# ---------------------------------------------------------

def gradient_pattern(w, h, theme_idx):
    theme = THEMES[theme_idx][1]
    c1, c2 = theme[0], theme[2]
    
    xv, yv = np.meshgrid(np.linspace(0, 1, w), np.linspace(0, 1, h))
    
    r = (c1[0] * (1 - yv) + c2[0] * yv + np.sin(xv * np.pi) * 30).clip(0, 255).astype(np.uint8)
    g = (c1[1] * (1 - xv) + c2[1] * xv + np.cos(yv * np.pi) * 30).clip(0, 255).astype(np.uint8)
    b = (c1[2] * (1 - yv) + c2[2] * yv).clip(0, 255).astype(np.uint8)
    
    return np.dstack([b, g, r])


def wave_pattern(w, h, theme_idx):
    theme = THEMES[theme_idx][1]
    xv, yv = np.meshgrid(np.linspace(0, 4 * np.pi, w), np.linspace(0, 4 * np.pi, h))
    waves = (np.sin(xv) + np.cos(yv * 1.5)) * 127 + 128
    waves = waves.astype(np.uint8)

    canvas = np.zeros((h, w, 3), dtype=np.uint8)
    c = theme[np.random.randint(1, len(theme))]
    canvas[..., 0] = (waves * (c[2] / 255.0)).astype(np.uint8)
    canvas[..., 1] = (np.roll(waves, 80, axis=1) * (c[1] / 255.0)).astype(np.uint8)
    canvas[..., 2] = (np.roll(waves, 160, axis=0) * (c[0] / 255.0)).astype(np.uint8)
    return canvas


def noise_pattern(w, h, theme_idx):
    theme = THEMES[theme_idx][1]
    base = np.zeros((h, w, 3), dtype=np.uint8)
    base[:] = theme[0]
    
    noise = (np.random.rand(h, w, 3) * 60).astype(np.uint8)
    canvas = cv2.add(base, noise)
    
    # Add subtle soft orbs
    for _ in range(5):
        cx, cy = np.random.randint(0, w), np.random.randint(0, h)
        radius = np.random.randint(min(w, h) // 6, min(w, h) // 3)
        color = theme[np.random.randint(1, len(theme))]
        overlay = canvas.copy()
        cv2.circle(overlay, (cx, cy), radius, color, -1)
        cv2.addWeighted(overlay, 0.25, canvas, 0.75, 0, canvas)
        
    return cv2.GaussianBlur(canvas, (31, 31), 0)


def geometric_pattern(w, h, theme_idx):
    theme = THEMES[theme_idx][1]
    canvas = np.zeros((h, w, 3), dtype=np.uint8)
    canvas[:] = theme[0]

    for _ in range(35):
        p1 = (np.random.randint(0, w), np.random.randint(0, h))
        p2 = (np.random.randint(0, w), np.random.randint(0, h))
        color = theme[np.random.randint(1, len(theme))]
        cv2.line(canvas, p1, p2, color, thickness=np.random.randint(1, 4), lineType=cv2.LINE_AA)

    for _ in range(12):
        p = (np.random.randint(0, w), np.random.randint(0, h))
        r = np.random.randint(15, 80)
        color = theme[np.random.randint(1, len(theme))]
        cv2.circle(canvas, p, r, color, thickness=np.random.randint(1, 3), lineType=cv2.LINE_AA)

    return canvas


def particle_pattern(w, h, theme_idx):
    theme = THEMES[theme_idx][1]
    canvas = np.zeros((h, w, 3), dtype=np.uint8)
    canvas[:] = theme[0]

    for _ in range(400):
        pos = (np.random.randint(0, w), np.random.randint(0, h))
        color = theme[np.random.randint(1, len(theme))]
        r = np.random.randint(1, 4)
        cv2.circle(canvas, pos, r, color, -1, lineType=cv2.LINE_AA)

    return cv2.GaussianBlur(canvas, (3, 3), 0)


PATTERNS = [gradient_pattern, wave_pattern, noise_pattern, geometric_pattern, particle_pattern]

def generate_wallpaper(width, height, theme_idx):
    pattern = np.random.choice(PATTERNS)
    img = pattern(width, height, theme_idx)
    
    # Visual effects
    blurred = cv2.GaussianBlur(img, (0, 0), sigmaX=5)
    result = cv2.addWeighted(img, 0.8, blurred, 0.2, 0)
    return result

# ---------------------------------------------------------
# Windows Wallpaper Integration
# ---------------------------------------------------------

def set_as_windows_wallpaper(img_bgr, target_res=None):
    """Sets the image as the active Windows desktop wallpaper."""
    if target_res:
        img_bgr = cv2.resize(img_bgr, target_res, interpolation=cv2.INTER_LANCZOS4)
        
    out_path = SAVE_DIR / f"desktop_wallpaper_{int(time.time())}.png"
    cv2.imwrite(str(out_path), img_bgr)
    
    try:
        if sys.platform == "win32":
            abs_path = str(out_path.resolve())
            # SPI_SETDESKWALLPAPER = 20, SPIF_UPDATEINIFILE = 1, SPIF_SENDCHANGE = 2
            ctypes.windll.user32.SystemParametersInfoW(20, 0, abs_path, 3)
            return True, f"Set as Windows Wallpaper! ({out_path.name})"
        else:
            return True, f"Saved -> {out_path.name}"
    except Exception as e:
        return False, f"Failed to set wallpaper: {e}"

# ---------------------------------------------------------
# UI & Overlays
# ---------------------------------------------------------

def cv_to_surface(img):
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    h, w, _ = img.shape
    return pygame.image.frombuffer(img_rgb.tobytes(), (w, h), "RGB")


def draw_hud(screen, fonts, theme_name, res_name, auto_interval, paused, toast_msg, toast_timer, show_clock):
    w, h = screen.get_size()
    
    # Top overlay bar
    bar = pygame.Surface((w, 75), pygame.SRCALPHA)
    bar.fill((10, 12, 18, 210))
    screen.blit(bar, (0, 0))

    title_txt = fonts["title"].render(TITLE, True, (255, 255, 255))
    screen.blit(title_txt, (18, 8))

    status_str = f"Theme: {theme_name} | Target: {res_name} | Auto: {'PAUSED' if paused else f'{auto_interval:.1f}s'}"
    status_txt = fonts["ui"].render(status_str, True, (0, 230, 200))
    screen.blit(status_txt, (18, 44))

    # Controls HUD bottom
    bottom_bar = pygame.Surface((w, 40), pygame.SRCALPHA)
    bottom_bar.fill((10, 12, 18, 200))
    screen.blit(bottom_bar, (0, h - 40))

    help_str = "[SPACE] New  |  [W] Set as Windows Wallpaper  |  [S] Save  |  [T] Theme  |  [C] Clock  |  [R] Res  |  [P] Pause"
    help_txt = fonts["ui_sm"].render(help_str, True, (220, 220, 230))
    screen.blit(help_txt, (18, h - 30))

    # Clock & Affirmation Overlay
    if show_clock:
        now = datetime.datetime.now()
        time_str = now.strftime("%I:%M:%S %p")
        date_str = now.strftime("%A, %B %d, %Y")
        quote = AFFIRMATIONS[(now.minute // 10) % len(AFFIRMATIONS)]

        card_w, card_h = 520, 160
        card = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        card.fill((15, 20, 30, 190))
        pygame.draw.rect(card, (0, 220, 200, 120), (0, 0, card_w, card_h), 2, border_radius=16)

        t_surf = fonts["clock"].render(time_str, True, (255, 255, 255))
        d_surf = fonts["ui"].render(date_str, True, (0, 220, 200))
        q_surf = fonts["quote"].render(f'"{quote}"', True, (230, 230, 230))

        card.blit(t_surf, (card_w // 2 - t_surf.get_width() // 2, 18))
        card.blit(d_surf, (card_w // 2 - d_surf.get_width() // 2, 78))
        card.blit(q_surf, (card_w // 2 - q_surf.get_width() // 2, 115))

        screen.blit(card, (w // 2 - card_w // 2, h // 2 - card_h // 2))

    # Toast badge
    if toast_msg and time.time() < toast_timer:
        toast = fonts["ui"].render(toast_msg, True, (255, 255, 255))
        tw = toast.get_width() + 40
        t_box = pygame.Surface((tw, 44), pygame.SRCALPHA)
        t_box.fill((0, 150, 90, 230))
        pygame.draw.rect(t_box, (255, 255, 255), (0, 0, tw, 44), 2, border_radius=10)
        t_box.blit(toast, (20, 10))
        screen.blit(t_box, (w // 2 - tw // 2, 85))

# ---------------------------------------------------------
# Main Application
# ---------------------------------------------------------

def run():
    global curr_theme_idx, curr_res_idx
    os.environ["SDL_VIDEO_CENTERED"] = "1"
    pygame.init()
    pygame.display.set_caption(TITLE)

    screen = pygame.display.set_mode(WINDOW_SIZE)
    clock = pygame.time.Clock()

    # Force window to foreground on Windows
    try:
        if sys.platform == "win32":
            wm_info = pygame.display.get_wm_info()
            hwnd = wm_info.get("window")
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 5)  # SW_SHOW
                ctypes.windll.user32.SetForegroundWindow(hwnd)
    except Exception:
        pass

    fonts = {
        "title": pygame.font.SysFont("Segoe UI", 26, bold=True),
        "ui": pygame.font.SysFont("Segoe UI", 16),
        "ui_sm": pygame.font.SysFont("Segoe UI", 14),
        "clock": pygame.font.SysFont("Segoe UI", 48, bold=True),
        "quote": pygame.font.SysFont("Segoe UI", 16, italic=True),
    }

    auto_interval = 4.0
    paused = False
    show_clock = False
    toast_msg = "Press [W] anytime to set as Desktop Wallpaper!"
    toast_timer = time.time() + 4.0

    raw_img = generate_wallpaper(WINDOW_SIZE[0], WINDOW_SIZE[1], curr_theme_idx)
    surface = cv_to_surface(raw_img)
    last_gen = time.time()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                elif event.key == pygame.K_SPACE:
                    raw_img = generate_wallpaper(WINDOW_SIZE[0], WINDOW_SIZE[1], curr_theme_idx)
                    surface = cv_to_surface(raw_img)
                    last_gen = time.time()

                elif event.key == pygame.K_w:
                    target_dim = RESOLUTIONS[curr_res_idx][1]
                    # Generate full target-res image for ultra-sharp wallpaper
                    hi_res = generate_wallpaper(target_dim[0], target_dim[1], curr_theme_idx)
                    ok, msg = set_as_windows_wallpaper(hi_res)
                    toast_msg = msg
                    toast_timer = time.time() + 3.5

                elif event.key == pygame.K_s:
                    target_dim = RESOLUTIONS[curr_res_idx][1]
                    hi_res = generate_wallpaper(target_dim[0], target_dim[1], curr_theme_idx)
                    path = SAVE_DIR / f"wallpaper_{int(time.time())}.png"
                    cv2.imwrite(str(path), hi_res)
                    toast_msg = f"Saved -> {path.name}"
                    toast_timer = time.time() + 3.0

                elif event.key == pygame.K_t:
                    curr_theme_idx = (curr_theme_idx + 1) % len(THEMES)
                    raw_img = generate_wallpaper(WINDOW_SIZE[0], WINDOW_SIZE[1], curr_theme_idx)
                    surface = cv_to_surface(raw_img)
                    toast_msg = f"Theme: {THEMES[curr_theme_idx][0]}"
                    toast_timer = time.time() + 2.0

                elif event.key == pygame.K_c:
                    show_clock = not show_clock

                elif event.key == pygame.K_r:
                    curr_res_idx = (curr_res_idx + 1) % len(RESOLUTIONS)
                    toast_msg = f"Target Export: {RESOLUTIONS[curr_res_idx][0]} ({RESOLUTIONS[curr_res_idx][1][0]}x{RESOLUTIONS[curr_res_idx][1][1]})"
                    toast_timer = time.time() + 2.5

                elif event.key == pygame.K_p:
                    paused = not paused
                    toast_msg = "Auto-Rotation Paused" if paused else "Auto-Rotation Resumed"
                    toast_timer = time.time() + 2.0

                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                    auto_interval = max(1.0, auto_interval - 0.5)
                    toast_msg = f"Interval: {auto_interval:.1f}s"
                    toast_timer = time.time() + 1.5

                elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    auto_interval = min(30.0, auto_interval + 0.5)
                    toast_msg = f"Interval: {auto_interval:.1f}s"
                    toast_timer = time.time() + 1.5

        # Auto-generation
        if not paused and time.time() - last_gen > auto_interval:
            raw_img = generate_wallpaper(WINDOW_SIZE[0], WINDOW_SIZE[1], curr_theme_idx)
            surface = cv_to_surface(raw_img)
            last_gen = time.time()

        screen.blit(surface, (0, 0))
        draw_hud(
            screen,
            fonts,
            THEMES[curr_theme_idx][0],
            RESOLUTIONS[curr_res_idx][0],
            auto_interval,
            paused,
            toast_msg,
            toast_timer,
            show_clock,
        )

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    run()