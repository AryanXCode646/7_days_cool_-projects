import pygame
import numpy as np
import random


class Particle:

    def __init__(self, width, height):

        self.pos = np.array([
            random.uniform(0, width),
            random.uniform(0, height)
        ], dtype=float)

        self.vel = np.random.randn(2) * 2
        self.acc = np.zeros(2)

        self.target = self.pos.copy()

        self.size = random.uniform(2.5,4)
        self.color = (255, 255, 255)

        self.max_speed = 6
        self.max_force = 0.25


    def apply_force(self, force):
        self.acc += force


    def seek(self):

        desired = self.target - self.pos
        dist = np.linalg.norm(desired)

        if dist == 0:
            return

        # ARRIVAL BEHAVIOR (slow down near target)
        speed = self.max_speed

        if dist < 100:
            speed = self.max_speed * (dist / 100)

        desired = desired / dist * speed

        steer = desired - self.vel

        mag = np.linalg.norm(steer)

        if mag > self.max_force:
            steer = steer / mag * self.max_force

        self.apply_force(steer)


    def update(self):

        self.vel += self.acc

        # LIMIT SPEED
        speed = np.linalg.norm(self.vel)
        if speed > self.max_speed:
            self.vel = self.vel / speed * self.max_speed

        self.pos += self.vel

        self.acc *= 0


    def draw(self, surface):

        x = int(self.pos[0])
        y = int(self.pos[1])

        # glow
        pygame.draw.circle(surface, self.color, (x, y), int(self.size * 2), 1)

        # core
        pygame.draw.circle(surface, self.color, (x, y), int(self.size))