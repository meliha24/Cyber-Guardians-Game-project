import pygame
from entities import load_strip, AnimatedSprite
import sys, os

def resource_path(relative_path):
    # Get the folder of this script
    try:
        base_path = sys._MEIPASS  
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

class Player(AnimatedSprite):
    def __init__(self, settings):
        self.settings = settings
        frames = load_strip(
            resource_path(os.path.join("assets", "player_spaceship_1.png")),
            frame_w=32,
            frame_h=40,
            scale_to=(70, 90)
        )

        super().__init__(frames, fps=12)
        self.rect = self.image.get_rect(center=(100, 300))

    def update(self, keys):
        self.animate()

        speed = self.settings.player_speed

        if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and self.rect.left > 0:
            self.rect.x -= speed
        if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and self.rect.right < 900:
            self.rect.x += speed
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and self.rect.top > 0:
            self.rect.y -= speed
        if (keys[pygame.K_DOWN] or keys[pygame.K_s]) and self.rect.bottom < 600:
            self.rect.y += speed
