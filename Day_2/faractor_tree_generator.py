"""
Fractal Tree Visualizer, Disk Explorer & Breathing Guide
-------------------------------------------------------
A multi-mode organic visualizer featuring:
1. Procedural Botanical & Seasonal Fractal Trees
2. Live Project / Disk Directory Tree Visualizer
3. Mindful 4-7-8 Stress-Relief Breathing Guide
4. High-Res PNG & Vector-ready Export

Controls:
    SPACE      -> Regenerate / Refresh Tree
    F          -> Toggle Project/Disk Directory Visualizer Mode
    B          -> Toggle 4-7-8 Mindful Breathing Pacer Mode
    T          -> Cycle Seasonal Palettes (Spring / Summer / Autumn / Winter / Cyber)
    UP/DOWN    -> Increase / Decrease Recursion Depth
    LEFT/RIGHT -> Adjust Branch Angle
    S / E      -> Save Screenshot (High-Res)
    ESC        -> Exit
"""

import os
import math
import random
import datetime
from pathlib import Path
import pygame

# -------------------------------------------------------
# Configuration & Themes
# -------------------------------------------------------

WIDTH = 1100
HEIGHT = 720
FPS = 60

SEASONS = [
    ("Spring Blossom", (18, 22, 20), (180, 140, 100), (255, 180, 200)),
    ("Summer Lush", (14, 20, 18), (140, 110, 75), (60, 210, 100)),
    ("Autumn Sunset", (24, 18, 16), (160, 90, 60), (255, 140, 40)),
    ("Winter Frost", (12, 16, 26), (160, 190, 220), (100, 220, 255)),
    ("Cyber Neon", (10, 10, 20), (80, 240, 220), (255, 0, 130)),
]
curr_season_idx = 0

# -------------------------------------------------------
# Directory Tree Scanner
# -------------------------------------------------------

class DirectoryNode:
    def __init__(self, name, is_dir=True):
        self.name = name
        self.is_dir = is_dir
        self.children = []
        self.size_count = 1

    def scan(self, path, max_depth=5, curr_depth=0):
        if curr_depth >= max_depth or not os.path.isdir(path):
            return
        try:
            entries = os.listdir(path)
            for entry in entries[:8]:  # Limit branching factor for clean aesthetics
                if entry.startswith(('.', '__pycache__', 'node_modules', '.venv')):
                    continue
                full = os.path.join(path, entry)
                if os.path.isdir(full):
                    child = DirectoryNode(entry, is_dir=True)
                    child.scan(full, max_depth, curr_depth + 1)
                    self.children.append(child)
                    self.size_count += child.size_count
                else:
                    self.children.append(DirectoryNode(entry, is_dir=False))
                    self.size_count += 1
        except Exception:
            pass


# -------------------------------------------------------
# Fractal Tree & Directory Graph Engine
# -------------------------------------------------------

class FractalTree:
    def __init__(self):
        self.depth = 9
        self.angle = 26
        self.length = 140
        self.randomness = 0.12
        self.growth_progress = 0
        self.branches = []
        self.mode = "fractal"  # 'fractal', 'directory', 'breathing'
        self.dir_root = None
        self.total_nodes = 0
        self.node_labels = []

    def set_directory_mode(self, root_path="."):
        self.mode = "directory" if self.mode != "directory" else "fractal"
        if self.mode == "directory":
            self.dir_root = DirectoryNode(os.path.basename(os.path.abspath(root_path)) or "Project Root")
            self.dir_root.scan(root_path)
        self.regenerate()

    def set_breathing_mode(self):
        self.mode = "breathing" if self.mode != "breathing" else "fractal"
        self.regenerate()

    def regenerate(self):
        self.branches.clear()
        self.node_labels.clear()
        self.growth_progress = 0
        start_x = WIDTH // 2
        start_y = HEIGHT - 90

        if self.mode == "directory" and self.dir_root:
            self._build_directory_tree(self.dir_root, start_x, start_y, -90, 130, 0)
        else:
            self._build_tree(start_x, start_y, -90, self.length, self.depth)

    def _build_tree(self, x, y, angle, length, depth):
        if depth == 0 or length < 2:
            return

        rad = math.radians(angle)
        x2 = x + math.cos(rad) * length
        y2 = y + math.sin(rad) * length

        self.branches.append((x, y, x2, y2, depth, None))

        new_len = length * random.uniform(0.68, 0.75)
        angle_var = self.angle * random.uniform(1 - self.randomness, 1 + self.randomness)

        self._build_tree(x2, y2, angle - angle_var, new_len, depth - 1)
        self._build_tree(x2, y2, angle + angle_var, new_len, depth - 1)

    def _build_directory_tree(self, node, x, y, angle, length, depth):
        rad = math.radians(angle)
        x2 = x + math.cos(rad) * length
        y2 = y + math.sin(rad) * length

        is_leaf = len(node.children) == 0
        depth_val = max(1, 7 - depth)
        self.branches.append((x, y, x2, y2, depth_val, node.name if is_leaf or depth < 3 else None))

        if not node.children:
            return

        child_count = len(node.children)
        spread = min(110, max(25, child_count * 22))
        start_ang = angle - spread / 2
        step = spread / max(1, child_count - 1) if child_count > 1 else 0

        for i, child in enumerate(node.children):
            c_ang = start_ang + (i * step if child_count > 1 else 0)
            c_len = length * 0.75
            self._build_directory_tree(child, x2, y2, c_ang, c_len, depth + 1)

    def update(self, breath_phase_factor=1.0):
        if self.mode == "breathing":
            # Growth pulses rhythmically with breath factor
            target_prog = int(len(self.branches) * (0.35 + 0.65 * breath_phase_factor))
            if self.growth_progress < target_prog:
                self.growth_progress = min(len(self.branches), self.growth_progress + 8)
            elif self.growth_progress > target_prog:
                self.growth_progress = max(5, self.growth_progress - 6)
        else:
            if self.growth_progress < len(self.branches):
                self.growth_progress += 8

    def draw(self, surface, season_idx, font_sm):
        _, _, b_color, l_color = SEASONS[season_idx]
        visible = self.branches[: self.growth_progress]

        for x1, y1, x2, y2, depth, label in visible:
            thickness = max(1, min(10, depth))
            pygame.draw.line(surface, b_color, (x1, y1), (x2, y2), thickness)

            if depth <= 2:
                pygame.draw.circle(surface, l_color, (int(x2), int(y2)), 4)
                if label and self.mode == "directory":
                    txt = font_sm.render(label[:14], True, (230, 230, 230))
                    surface.blit(txt, (int(x2) + 6, int(y2) - 6))


# -------------------------------------------------------
# Breathing Controller (4-7-8 Technique)
# -------------------------------------------------------

class BreathingPacer:
    """
    4-7-8 Relaxing Breath Technique:
    - 4s Inhale
    - 7s Hold
    - 8s Exhale
    Total cycle: 19 seconds
    """
    def __init__(self):
        self.start_time = pygame.time.get_ticks() / 1000.0

    def get_state(self):
        t = (pygame.time.get_ticks() / 1000.0 - self.start_time) % 19.0
        if t < 4.0:
            phase = "INHALE (4s)"
            pct = t / 4.0
            factor = pct
            color = (80, 220, 180)
        elif t < 11.0:
            phase = "HOLD (7s)"
            pct = (t - 4.0) / 7.0
            factor = 1.0
            color = (255, 215, 80)
        else:
            phase = "EXHALE (8s)"
            pct = (t - 11.0) / 8.0
            factor = 1.0 - pct
            color = (120, 170, 255)

        return phase, factor, color, t


# -------------------------------------------------------
# UI Rendering
# -------------------------------------------------------

class UI:
    def __init__(self):
        pygame.font.init()
        self.font_title = pygame.font.SysFont("Segoe UI", 22, bold=True)
        self.font = pygame.font.SysFont("Segoe UI", 16)
        self.font_sm = pygame.font.SysFont("Segoe UI", 12)
        self.font_breath = pygame.font.SysFont("Segoe UI", 32, bold=True)

    def draw(self, surface, tree, season_idx, breath_pacer):
        theme_name, bg_col, b_col, l_col = SEASONS[season_idx]
        
        # Header bar
        header = pygame.Surface((WIDTH, 60), pygame.SRCALPHA)
        header.fill((10, 14, 20, 200))
        surface.blit(header, (0, 0))

        title = self.font_title.render("Fractal Tree Studio & Mindful Guide", True, (255, 255, 255))
        surface.blit(title, (20, 8))

        mode_str = f"Mode: {tree.mode.upper()}  |  Season: {theme_name}  |  Depth: {tree.depth}  |  Angle: {tree.angle}°"
        info = self.font.render(mode_str, True, (0, 220, 200))
        surface.blit(info, (20, 34))

        # Bottom help HUD
        bottom = pygame.Surface((WIDTH, 40), pygame.SRCALPHA)
        bottom.fill((10, 14, 20, 200))
        surface.blit(bottom, (0, HEIGHT - 40))

        controls = "[SPACE] New  |  [F] Project Tree  |  [B] 4-7-8 Breathing Guide  |  [T] Season  |  [UP/DOWN] Depth  |  [S] Save"
        help_txt = self.font.render(controls, True, (210, 210, 220))
        surface.blit(help_txt, (20, HEIGHT - 30))

        # Breathing Mode HUD Overlay
        if tree.mode == "breathing":
            phase, factor, color, t = breath_pacer.get_state()
            box_w, box_h = 320, 120
            box = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
            box.fill((15, 20, 30, 220))
            pygame.draw.rect(box, color, (0, 0, box_w, box_h), 2, border_radius=14)

            p_txt = self.font_breath.render(phase, True, color)
            box.blit(p_txt, (box_w // 2 - p_txt.get_width() // 2, 18))

            # Progress Bar
            bar_w = 260
            pygame.draw.rect(box, (50, 50, 60), (30, 75, bar_w, 16), border_radius=8)
            pygame.draw.rect(box, color, (30, 75, int(bar_w * factor), 16), border_radius=8)

            tip_txt = self.font_sm.render("Breathe smoothly with the tree expansion", True, (200, 200, 200))
            box.blit(tip_txt, (box_w // 2 - tip_txt.get_width() // 2, 96))

            surface.blit(box, (WIDTH - box_w - 25, 80))


# -------------------------------------------------------
# Main Application
# -------------------------------------------------------

def main():
    global curr_season_idx
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Fractal Tree Studio & Mindful Guide")
    clock = pygame.time.Clock()

    tree = FractalTree()
    tree.regenerate()

    ui = UI()
    breath_pacer = BreathingPacer()

    running = True
    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                elif event.key == pygame.K_SPACE:
                    tree.regenerate()

                elif event.key == pygame.K_f:
                    tree.set_directory_mode(".")

                elif event.key == pygame.K_b:
                    tree.set_breathing_mode()

                elif event.key == pygame.K_t:
                    curr_season_idx = (curr_season_idx + 1) % len(SEASONS)

                elif event.key == pygame.K_UP:
                    tree.depth = min(14, tree.depth + 1)
                    tree.regenerate()

                elif event.key == pygame.K_DOWN:
                    tree.depth = max(1, tree.depth - 1)
                    tree.regenerate()

                elif event.key == pygame.K_LEFT:
                    tree.angle = max(5, tree.angle - 2)
                    tree.regenerate()

                elif event.key == pygame.K_RIGHT:
                    tree.angle = min(60, tree.angle + 2)
                    tree.regenerate()

                elif event.key in (pygame.K_s, pygame.K_e):
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"tree_{tree.mode}_{timestamp}.png"
                    pygame.image.save(screen, filename)
                    print(f"[Saved] -> {filename}")

        breath_factor = 1.0
        if tree.mode == "breathing":
            _, breath_factor, _, _ = breath_pacer.get_state()

        tree.update(breath_factor)

        bg_color = SEASONS[curr_season_idx][1]
        screen.fill(bg_color)

        tree.draw(screen, curr_season_idx, ui.font_sm)
        ui.draw(screen, tree, curr_season_idx, breath_pacer)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()