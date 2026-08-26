from particle import Particle
import numpy as np


class ParticleSystem:

    def __init__(self, width, height, count=6000):

        self.width = width
        self.height = height

        self.particles = [
            Particle(width, height)
            for _ in range(count)
        ]

        self.targets = []
        self.colors = []


    def update_targets(self, points, colors):

        if len(points) == 0:
            return

        # limit number of targets
        if len(points) > len(self.particles):
            indices = np.random.choice(len(points), len(self.particles), replace=False)
            self.targets = [points[i] for i in indices]
            self.colors = [colors[i] for i in indices]
        else:
            self.targets = points
            self.colors = colors

        for i, p in enumerate(self.particles):

            idx = i % len(self.targets)

            p.target = np.array(self.targets[idx])
            p.color = self.colors[idx]


    def update(self):

        for p in self.particles:
            p.seek()
            p.update()


    def draw(self, surface):

        for p in self.particles:
            p.draw(surface)