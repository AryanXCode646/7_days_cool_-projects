import pygame
import random
import time
from config import *
from gesture_controller import GestureController

GRID_SIZE = 20


class SnakeGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Neon Gesture Snake & Touchless PC Remote 🐍")

        self.clock = pygame.time.Clock()
        self.controller = GestureController()

        self.font_big = pygame.font.SysFont("Segoe UI", 52, bold=True)
        self.font = pygame.font.SysFont("Segoe UI", 24)
        self.font_sm = pygame.font.SysFont("Segoe UI", 16)

        self.app_mode = "game"  # 'game' or 'remote'
        self.state = "menu"
        self.shake = 0

        # SPEED
        self.move_delay = 260
        self.last_move_time = 0

        # TURN CONTROL
        self.turn_cooldown = 120
        self.last_turn_time = 0
        self.can_change_direction = True

        self.reset()

    def reset(self):
        head_x = WIDTH // 2
        head_y = HEIGHT // 2

        self.snake = [
            (head_x, head_y),
            (head_x - GRID_SIZE, head_y),
            (head_x - 2 * GRID_SIZE, head_y)
        ]

        self.direction = (GRID_SIZE, 0)
        self.food = self.spawn_food()
        self.score = 0
        self.paused = False

    def spawn_food(self):
        return (
            random.randint(0, WIDTH // GRID_SIZE - 1) * GRID_SIZE,
            random.randint(0, HEIGHT // GRID_SIZE - 1) * GRID_SIZE
        )

    def handle_gesture(self):
        gesture = self.controller.get_gesture()

        if self.app_mode == "remote":
            return

        if self.state == "menu" and gesture:
            self.state = "playing"

        elif self.state == "gameover" and gesture:
            self.reset()
            self.state = "playing"

        elif self.state == "playing":
            now = pygame.time.get_ticks()

            if not gesture or not self.can_change_direction:
                return

            if now - self.last_turn_time < self.turn_cooldown:
                return

            if gesture == "left" and self.direction != (GRID_SIZE, 0):
                self.direction = (-GRID_SIZE, 0)

            elif gesture == "right" and self.direction != (-GRID_SIZE, 0):
                self.direction = (GRID_SIZE, 0)

            elif gesture == "forward" and self.direction != (0, GRID_SIZE):
                self.direction = (0, -GRID_SIZE)

            elif gesture == "shoot" and self.direction != (0, -GRID_SIZE):
                self.direction = (0, GRID_SIZE)

            else:
                return

            self.can_change_direction = False
            self.last_turn_time = now

    def update(self):
        if self.paused or self.app_mode == "remote":
            return

        now = pygame.time.get_ticks()

        if now - self.last_move_time < self.move_delay:
            return

        self.last_move_time = now
        self.can_change_direction = True

        head_x, head_y = self.snake[0]
        dx, dy = self.direction

        new_head = (head_x + dx, head_y + dy)

        # Collision
        if (
            new_head[0] < 0 or new_head[0] >= WIDTH or
            new_head[1] < 0 or new_head[1] >= HEIGHT or
            new_head in self.snake
        ):
            self.state = "gameover"
            return

        self.snake.insert(0, new_head)

        if new_head == self.food:
            self.food = self.spawn_food()
            self.score += 10
            self.shake = 10

            for _ in range(2):
                self.snake.append(self.snake[-1])

            if self.move_delay > 180:
                self.move_delay -= 0.3
        else:
            self.snake.pop()

    def draw_background(self):
        for y in range(HEIGHT):
            color = (10 + y // 20, 10, 20 + y // 15)
            pygame.draw.line(self.screen, color, (0, y), (WIDTH, y))

    def draw_grid(self):
        for x in range(0, WIDTH, GRID_SIZE):
            pygame.draw.line(self.screen, (25, 25, 25), (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, GRID_SIZE):
            pygame.draw.line(self.screen, (25, 25, 25), (0, y), (WIDTH, y))

    def draw_snake(self):
        for i, segment in enumerate(self.snake):
            glow = 6 if i == 0 else 3
            pygame.draw.rect(
                self.screen,
                (0, 255, 150),
                (segment[0] - glow, segment[1] - glow, GRID_SIZE + glow * 2, GRID_SIZE + glow * 2),
                border_radius=6
            )
            pygame.draw.rect(
                self.screen,
                (0, 180, 120),
                (segment[0], segment[1], GRID_SIZE, GRID_SIZE),
                border_radius=4
            )

    def draw_food(self):
        pulse = (pygame.time.get_ticks() // 150) % 10
        pygame.draw.rect(
            self.screen,
            (255, 50 + pulse * 10, 50),
            (*self.food, GRID_SIZE, GRID_SIZE),
            border_radius=6
        )

    def draw_hud(self):
        panel = pygame.Rect(10, 10, 280, 90)
        pygame.draw.rect(self.screen, (20, 20, 20), panel, border_radius=10)
        pygame.draw.rect(self.screen, (0, 255, 150), panel, 2, border_radius=10)

        score_text = self.font.render(f"Score: {self.score}", True, (0, 255, 180))
        self.screen.blit(score_text, (20, 20))

        speed_text = self.font.render(f"Speed: {round(1000/self.move_delay)} | [M] Mode", True, (200, 200, 200))
        self.screen.blit(speed_text, (20, 55))

    def draw_remote_dashboard(self):
        """Renders futuristic Touchless Remote Controller HUD."""
        w, h = WIDTH, HEIGHT

        title = self.font_big.render("Touchless PC Remote Controller", True, (0, 240, 220))
        self.screen.blit(title, (w // 2 - title.get_width() // 2, 40))

        sub = self.font.render("Control your PC, Media & Slides without touching the keyboard!", True, (200, 210, 230))
        self.screen.blit(sub, (w // 2 - sub.get_width() // 2, 105))

        # Action Display Card
        action_card = pygame.Rect(w // 2 - 280, 160, 560, 120)
        pygame.draw.rect(self.screen, (20, 25, 38), action_card, border_radius=16)
        pygame.draw.rect(self.screen, (0, 240, 220), action_card, 2, border_radius=16)

        act_lbl = self.font_sm.render("CURRENT DISPATCHED ACTION", True, (140, 160, 180))
        action_card_txt = self.font_big.render(self.controller.last_remote_action, True, (255, 215, 60))

        self.screen.blit(act_lbl, (w // 2 - act_lbl.get_width() // 2, 175))
        self.screen.blit(action_card_txt, (w // 2 - action_card_txt.get_width() // 2, 210))

        # Gestures Map Grid
        grid_items = [
            ("☝️ 1 Finger (Index)", "Volume Up (System Volume +)"),
            ("✌️ 2 Fingers (Peace)", "Volume Down (System Volume -)"),
            ("🤟 3 Fingers", "Play / Pause Media (Spotify, YouTube, Video)"),
            ("✋ Open Palm", "Next Slide / Page Forward ➡️"),
            ("✊ Closed Fist", "Mute Audio / Microphone 🔇"),
            ("⌨️ 'M' Key", "Switch back to Arcade Snake Game"),
        ]

        start_y = 310
        for i, (gesture_name, action_desc) in enumerate(grid_items):
            box = pygame.Rect(w // 2 - 320, start_y + i * 55, 640, 46)
            pygame.draw.rect(self.screen, (25, 30, 44), box, border_radius=10)
            pygame.draw.rect(self.screen, (60, 70, 95), box, 1, border_radius=10)

            g_txt = self.font.render(gesture_name, True, (0, 230, 200))
            a_txt = self.font_sm.render(action_desc, True, (220, 220, 230))

            self.screen.blit(g_txt, (box.x + 20, box.y + 8))
            self.screen.blit(a_txt, (box.x + 260, box.y + 14))

    def draw_center_text(self, text, sub=None):
        t = self.font_big.render(text, True, (255, 255, 255))
        self.screen.blit(t, (WIDTH // 2 - t.get_width() // 2, HEIGHT // 2 - 50))

        if sub:
            s = self.font.render(sub, True, (200, 200, 200))
            self.screen.blit(s, (WIDTH // 2 - s.get_width() // 2, HEIGHT // 2 + 20))

    def draw(self):
        offset_x = random.randint(-self.shake, self.shake)
        offset_y = random.randint(-self.shake, self.shake)
        self.shake = max(0, self.shake - 1)

        self.draw_background()
        self.draw_grid()

        if self.app_mode == "remote":
            self.draw_remote_dashboard()
        elif self.state == "playing":
            self.draw_snake()
            self.draw_food()
            self.draw_hud()
        elif self.state == "menu":
            self.draw_center_text("NEON GESTURE SNAKE", "Show any gesture to start | Press [M] for PC Remote")
        elif self.state == "gameover":
            self.draw_center_text("GAME OVER", f"Score: {self.score} | Gesture to restart | [M] for PC Remote")

        self.screen.blit(self.screen, (offset_x, offset_y))

    def run(self):
        while self.state != "exit":
            self.clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.state = "exit"

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_m:
                        # Toggle mode
                        self.app_mode = "remote" if self.app_mode != "remote" else "game"
                        self.controller.set_mode(self.app_mode)

                    elif self.state == "playing" and self.app_mode == "game":
                        now = pygame.time.get_ticks()
                        if now - self.last_turn_time < self.turn_cooldown:
                            continue

                        if event.key in [pygame.K_LEFT, pygame.K_a] and self.direction != (GRID_SIZE, 0):
                            self.direction = (-GRID_SIZE, 0)
                        elif event.key in [pygame.K_RIGHT, pygame.K_d] and self.direction != (-GRID_SIZE, 0):
                            self.direction = (GRID_SIZE, 0)
                        elif event.key in [pygame.K_UP, pygame.K_w] and self.direction != (0, GRID_SIZE):
                            self.direction = (0, -GRID_SIZE)
                        elif event.key in [pygame.K_DOWN, pygame.K_s] and self.direction != (0, -GRID_SIZE):
                            self.direction = (0, GRID_SIZE)
                        else:
                            continue

                        self.can_change_direction = False
                        self.last_turn_time = now

            self.handle_gesture()

            if self.state == "playing":
                self.update()

            self.draw()
            pygame.display.flip()

        self.controller.stop()
        pygame.quit()