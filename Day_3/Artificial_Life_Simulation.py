"""
Artificial Life Ecosystem & Swarm Problem Solver
------------------------------------------------
An interactive multi-agent artificial life simulator with:
1. Evolutionary Genetic Adaptation (Speed vs Efficiency vs Sensory Range)
2. Interactive Environment Painter (Left-click: Food, Right-click: Obstacle Walls)
3. Epidemiological Disease Spread & Herd Immunity Sandbox (Toggle 'E')
4. Real-time Population & Fitness Telemetry with CSV Exporter ('X')

Controls:
    SPACE        -> Pause / Resume
    Left Click   -> Place Food / Resources
    Right Click  -> Draw Obstacle Walls / Maze Barriers
    Middle Click -> Spawn Agent
    E            -> Toggle Epidemic / Immunity Simulation Mode
    C            -> Clear Obstacles
    R            -> Reset Ecosystem
    S            -> Simulation Speed (1x -> 4x)
    X            -> Export Population Telemetry to CSV
    ESC          -> Quit
"""

import os
import csv
import time
import math
import random
import pygame
import numpy as np

# ------------------------------------------------
# Configuration
# ------------------------------------------------

WIDTH = 1150
HEIGHT = 720
WORLD_WIDTH = 870
SIDEBAR_WIDTH = WIDTH - WORLD_WIDTH

BACKGROUND = (14, 17, 24)
SIDEBAR_COLOR = (22, 26, 36)
TEXT_COLOR = (230, 230, 235)
ACCENT_COLOR = (0, 220, 200)

FOOD_COLOR = (70, 220, 120)
HEALTHY_COLOR = (110, 180, 255)
INFECTED_COLOR = (255, 60, 80)
IMMUNE_COLOR = (255, 215, 0)
WALL_COLOR = (80, 90, 110)

FPS = 60


# ------------------------------------------------
# Obstacle Wall Class
# ------------------------------------------------

class Wall:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)

    def draw(self, surface):
        pygame.draw.rect(surface, WALL_COLOR, self.rect, border_radius=4)
        pygame.draw.rect(surface, (120, 130, 150), self.rect, 1, border_radius=4)


# ------------------------------------------------
# Food Entity
# ------------------------------------------------

class Food:
    def __init__(self, position, energy=35):
        self.position = np.array(position, dtype=float)
        self.energy = energy
        self.radius = 4

    def draw(self, surface):
        pygame.draw.circle(surface, FOOD_COLOR, self.position.astype(int), self.radius)


# ------------------------------------------------
# Organism with Genetic Traits & Health States
# ------------------------------------------------

class Organism:
    def __init__(self, position, genes=None):
        self.position = np.array(position, dtype=float)
        self.velocity = np.random.uniform(-1, 1, 2)
        if np.linalg.norm(self.velocity) > 0:
            self.velocity = self.velocity / np.linalg.norm(self.velocity)

        # Genes: [speed_trait, sense_radius, efficiency, immunity]
        if genes is None:
            self.speed = random.uniform(1.0, 2.2)
            self.sense_radius = random.uniform(70, 180)
            self.efficiency = random.uniform(0.7, 1.3)
            self.immunity = random.uniform(0.1, 0.9)
        else:
            # Inherit with mutation
            self.speed = np.clip(genes[0] + random.uniform(-0.15, 0.15), 0.6, 3.5)
            self.sense_radius = np.clip(genes[1] + random.uniform(-10, 10), 40, 250)
            self.efficiency = np.clip(genes[2] + random.uniform(-0.1, 0.1), 0.4, 2.0)
            self.immunity = np.clip(genes[3] + random.uniform(-0.08, 0.08), 0.05, 0.98)

        self.energy = 90.0
        self.base_radius = 6
        self.radius = self.base_radius
        self.pulse = random.uniform(0, 6.28)

        # Health state: 'healthy', 'infected', 'immune'
        self.health_state = 'healthy'
        self.infection_timer = 0

    def get_genes(self):
        return [self.speed, self.sense_radius, self.efficiency, self.immunity]

    def update(self, world):
        self.pulse += 0.08
        self.radius = self.base_radius + int(np.sin(self.pulse) * 1.5)

        # Metabolism: faster movement & wider vision consumes more energy
        cost = (0.03 * (self.speed ** 1.3) + (self.sense_radius * 0.0002)) / self.efficiency
        self.energy -= cost

        # Epidemic contagion update
        if self.health_state == 'infected':
            self.energy -= 0.04  # Extra energy drain from sickness
            self.infection_timer += 1
            if self.infection_timer > 350:
                if random.random() < self.immunity:
                    self.health_state = 'immune'  # Recovered with antibodies!
                else:
                    self.energy = 0  # Succumbed to infection

        if self.energy <= 0:
            world.remove_organism(self)
            return

        self.seek_food(world)
        self.avoid_walls(world)
        self.move()
        self.eat(world)
        self.spread_infection(world)
        self.reproduce(world)

    def seek_food(self, world):
        if not world.food:
            return

        nearby = []
        for f in world.food:
            dist = np.linalg.norm(f.position - self.position)
            if dist < self.sense_radius:
                nearby.append((dist, f))

        if nearby:
            nearest = min(nearby, key=lambda x: x[0])[1]
            direction = nearest.position - self.position
            dist = np.linalg.norm(direction)
            if dist > 0:
                self.velocity += (direction / dist) * 0.08

    def avoid_walls(self, world):
        for wall in world.walls:
            cx = wall.rect.centerx
            cy = wall.rect.centery
            to_wall = np.array([cx, cy]) - self.position
            dist = np.linalg.norm(to_wall)
            if dist < max(wall.rect.width, wall.rect.height) + 15:
                # Push away from wall
                if dist > 0:
                    self.velocity -= (to_wall / dist) * 0.25

    def move(self):
        noise = np.random.uniform(-0.15, 0.15, 2)
        self.velocity += noise

        speed_mag = np.linalg.norm(self.velocity)
        if speed_mag > 0:
            self.velocity = (self.velocity / speed_mag)

        self.position += self.velocity * self.speed

        # Bounds clipping
        self.position[0] = np.clip(self.position[0], self.radius, WORLD_WIDTH - self.radius)
        self.position[1] = np.clip(self.position[1], self.radius, HEIGHT - self.radius)

    def eat(self, world):
        for food in world.food[:]:
            if np.linalg.norm(food.position - self.position) < self.radius + food.radius:
                self.energy += food.energy
                if food in world.food:
                    world.food.remove(food)

    def spread_infection(self, world):
        if not world.epidemic_mode or self.health_state != 'infected':
            return
        for other in world.organisms:
            if other != self and other.health_state == 'healthy':
                if np.linalg.norm(other.position - self.position) < 22:
                    if random.random() > other.immunity * 0.8:
                        other.health_state = 'infected'
                        other.infection_timer = 0

    def reproduce(self, world):
        if self.energy > 170 and len(world.organisms) < 120:
            self.energy *= 0.55
            child_pos = self.position + np.random.uniform(-12, 12, 2)
            child = Organism(child_pos, genes=self.get_genes())
            world.add_organism(child)

    def draw(self, surface):
        x, y = self.position.astype(int)

        if self.health_state == 'infected':
            color = INFECTED_COLOR
        elif self.health_state == 'immune':
            color = IMMUNE_COLOR
        else:
            color = HEALTHY_COLOR

        # Subtle glow
        glow_radius = self.radius + 6
        glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, (*color[:3], 35), (glow_radius, glow_radius), glow_radius)
        surface.blit(glow_surface, (x - glow_radius, y - glow_radius))

        # Body & sensory perimeter
        pygame.draw.circle(surface, color, (x, y), self.radius)
        pygame.draw.circle(surface, (*color[:3], 80), (x, y), int(self.sense_radius), 1)


# ------------------------------------------------
# Simulation World
# ------------------------------------------------

class World:
    def __init__(self):
        self.organisms = []
        self.food = []
        self.walls = []
        self.generation = 1
        self.epidemic_mode = False
        self.history = []  # [(time, pop, avg_speed, avg_sense, infected_count)]

    def populate(self, count=28):
        for _ in range(count):
            pos = (random.randint(40, WORLD_WIDTH - 40), random.randint(40, HEIGHT - 40))
            self.organisms.append(Organism(pos))

    def spawn_food(self):
        if random.random() < 0.12 and len(self.food) < 70:
            pos = (random.randint(20, WORLD_WIDTH - 20), random.randint(20, HEIGHT - 20))
            self.food.append(Food(pos))

    def update(self):
        self.spawn_food()
        for org in self.organisms[:]:
            org.update(self)

        if len(self.organisms) == 0:
            self.generation += 1
            self.populate(20)

    def draw(self, surface):
        for wall in self.walls:
            wall.draw(surface)
        for f in self.food:
            f.draw(surface)
        for org in self.organisms:
            org.draw(surface)

    def add_organism(self, organism):
        self.organisms.append(organism)

    def remove_organism(self, organism):
        if organism in self.organisms:
            self.organisms.remove(organism)


# ------------------------------------------------
# Main Simulation Application
# ------------------------------------------------

class Simulation:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Swarm Ecosystem & Genetic Problem Solver")
        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont("Consolas", 15)
        self.font_bold = pygame.font.SysFont("Segoe UI", 18, bold=True)
        self.font_title = pygame.font.SysFont("Segoe UI", 22, bold=True)

        self.world = World()
        self.world.populate()

        self.running = True
        self.paused = False
        self.speed = 1
        self.toast_msg = "Left-click: Food | Right-click: Obstacles | 'E': Epidemic"
        self.toast_timer = time.time() + 4.0

    def reset(self):
        self.world = World()
        self.world.populate()
        self.toast_msg = "World Reset"
        self.toast_timer = time.time() + 2.0

    def toggle_epidemic(self):
        self.world.epidemic_mode = not self.world.epidemic_mode
        if self.world.epidemic_mode and self.world.organisms:
            # Infect 1 patient zero
            patient_zero = random.choice(self.world.organisms)
            patient_zero.health_state = 'infected'
            self.toast_msg = "Epidemic Mode: Active! (Patient Zero Spawned)"
        else:
            for org in self.world.organisms:
                org.health_state = 'healthy'
            self.toast_msg = "Epidemic Mode: Disabled"
        self.toast_timer = time.time() + 3.0

    def export_csv(self):
        filename = f"ecosystem_telemetry_{int(time.time())}.csv"
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Time_Sec", "Generation", "Population", "Food_Count", "Avg_Speed", "Avg_Sense_Radius", "Avg_Immunity", "Infected_Count"])
                speeds = [o.speed for o in self.world.organisms] or [0]
                senses = [o.sense_radius for o in self.world.organisms] or [0]
                immunities = [o.immunity for o in self.world.organisms] or [0]
                infected = sum(1 for o in self.world.organisms if o.health_state == 'infected')
                
                writer.writerow([
                    round(pygame.time.get_ticks() / 1000.0, 1),
                    self.world.generation,
                    len(self.world.organisms),
                    len(self.world.food),
                    round(np.mean(speeds), 2),
                    round(np.mean(senses), 1),
                    round(np.mean(immunities), 2),
                    infected
                ])
            self.toast_msg = f"Exported -> {filename}"
        except Exception as e:
            self.toast_msg = f"Export Error: {e}"
        self.toast_timer = time.time() + 3.0

    def handle_mouse_drawing(self):
        buttons = pygame.mouse.get_pressed()
        m_x, m_y = pygame.mouse.get_pos()
        if m_x >= WORLD_WIDTH - 10:
            return

        if buttons[0]:  # Left click: place food cache
            self.world.food.append(Food((m_x, m_y)))
        elif buttons[2]:  # Right click: draw obstacle wall block
            wall_rect = pygame.Rect(m_x - 12, m_y - 12, 24, 24)
            # Avoid duplicate overlapping walls
            if not any(w.rect.colliderect(wall_rect) for w in self.world.walls):
                self.world.walls.append(Wall(wall_rect))
        elif buttons[1]:  # Middle click: spawn custom agent
            self.world.add_organism(Organism((m_x, m_y)))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_r:
                    self.reset()
                elif event.key == pygame.K_e:
                    self.toggle_epidemic()
                elif event.key == pygame.K_x:
                    self.export_csv()
                elif event.key == pygame.K_c:
                    self.world.walls.clear()
                    self.toast_msg = "Obstacles Cleared"
                    self.toast_timer = time.time() + 2.0
                elif event.key == pygame.K_s:
                    self.speed = (self.speed % 4) + 1
                elif event.key == pygame.K_ESCAPE:
                    self.running = False

    def draw_sidebar(self):
        sidebar_rect = pygame.Rect(WORLD_WIDTH, 0, SIDEBAR_WIDTH, HEIGHT)
        pygame.draw.rect(self.screen, SIDEBAR_COLOR, sidebar_rect)
        pygame.draw.line(self.screen, (45, 50, 65), (WORLD_WIDTH, 0), (WORLD_WIDTH, HEIGHT), 2)

        title = self.font_title.render("Ecosystem HUD", True, (255, 255, 255))
        self.screen.blit(title, (WORLD_WIDTH + 18, 16))

        speeds = [o.speed for o in self.world.organisms] or [0]
        senses = [o.sense_radius for o in self.world.organisms] or [0]
        immunities = [o.immunity for o in self.world.organisms] or [0]
        infected = sum(1 for o in self.world.organisms if o.health_state == 'infected')
        immune_count = sum(1 for o in self.world.organisms if o.health_state == 'immune')

        stats = [
            f"Population : {len(self.world.organisms)}",
            f"Food Supply: {len(self.world.food)}",
            f"Walls/Maze : {len(self.world.walls)}",
            f"Generation : {self.world.generation}",
            f"Sim Speed  : {self.speed}x {'(PAUSED)' if self.paused else ''}",
            "",
            "--- Genetics Avg ---",
            f"Speed      : {np.mean(speeds):.2f}",
            f"Sensory R  : {np.mean(senses):.1f}px",
            f"Immunity   : {np.mean(immunities):.2f}",
            "",
            "--- Health & Epidemic ---",
            f"Mode       : {'ACTIVE' if self.world.epidemic_mode else 'OFF'}",
            f"Infected   : {infected}",
            f"Immune/Rec : {immune_count}",
            "",
            "--- Controls ---",
            "Left-Click : Place Food",
            "Right-Click: Draw Obstacle",
            "Middle-Clk : Spawn Agent",
            "SPACE      : Pause/Play",
            "E          : Epidemic Mode",
            "C          : Clear Walls",
            "X          : Export CSV Log",
            "S          : Speed Toggle",
            "R          : Reset World",
        ]

        y = 56
        for line in stats:
            if line.startswith("---"):
                txt = self.font_bold.render(line, True, ACCENT_COLOR)
                y += 4
            else:
                txt = self.font.render(line, True, TEXT_COLOR)
            self.screen.blit(txt, (WORLD_WIDTH + 18, y))
            y += 22

        # Toast badge
        if self.toast_msg and time.time() < self.toast_timer:
            t_surf = self.font.render(self.toast_msg, True, (255, 255, 255))
            tw = t_surf.get_width() + 30
            box = pygame.Surface((tw, 36), pygame.SRCALPHA)
            box.fill((0, 150, 120, 230))
            pygame.draw.rect(box, (255, 255, 255), (0, 0, tw, 36), 1, border_radius=8)
            box.blit(t_surf, (15, 8))
            self.screen.blit(box, (20, 16))

    def run(self):
        while self.running:
            self.handle_events()
            self.handle_mouse_drawing()

            if not self.paused:
                for _ in range(self.speed):
                    self.world.update()

            self.screen.fill(BACKGROUND)
            self.world.draw(self.screen)
            self.draw_sidebar()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()


# ------------------------------------------------
if __name__ == "__main__":
    sim = Simulation()
    sim.run()