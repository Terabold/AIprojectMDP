import random
import numpy as np  # Import numpy
from scripts.utils import Animation
from scripts.constants import BASE_IMG_DUR
import pygame

class Star:
    def __init__(self, pos, anim, speed, depth, scale=1.0):
        self.pos = np.array(pos, dtype=float)  # Use numpy array for position
        self.anim = anim
        self.speed = speed
        self.depth = depth
        self.scale = scale
        self._cached_img = None
        self._last_frame = -1
        
    def update(self, dt=1.0):
        self.anim.update(dt * self.speed)
        
    def render(self, surf, offset=(0, 0)):
        current_frame = int(self.anim.frame)
        if self._last_frame != current_frame:
            img = self.anim.img()
            if self.scale != 1.0:
                size = (int(img.get_width() * self.scale), int(img.get_height() * self.scale))
                self._cached_img = pygame.transform.smoothscale(img, size)
            else:
                self._cached_img = img
            self._last_frame = current_frame

        img = self._cached_img
        offset = np.array(offset, dtype=float)  # Ensure offset is numpy array
        render_pos = self.pos - offset * self.depth
        surf.blit(
            img,
            (
                render_pos[0] % (surf.get_width() + img.get_width()) - img.get_width(),
                render_pos[1] % (surf.get_height() + img.get_height()) - img.get_height(),
            ),
        )

class Stars:
    def __init__(self, base_images, count=20):
        self.stars = []
        for i in range(count):
            depth = random.uniform(0.4, 1.0)
            speed = random.uniform(10, 20)
            scale = random.uniform(0.3, 0.8)
            img_dur = BASE_IMG_DUR + random.randint(0, 5)
            anim = Animation(base_images, img_dur=img_dur, loop=True)
            anim.frame = random.uniform(0, img_dur * len(base_images))
            # Use numpy array for position
            self.stars.append(
                Star(np.array([random.random() * 99999, random.random() * 99999]), anim, speed, depth, scale)
            )
        self.stars.sort(key=lambda x: x.depth)

    def update(self, dt=1.0):
        for star in self.stars:
            star.update(dt)

    def render(self, surf, offset=(0, 0)):
        for star in self.stars:
            star.render(surf, offset)