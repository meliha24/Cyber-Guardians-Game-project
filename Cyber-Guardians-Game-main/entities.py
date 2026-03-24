import pygame
import random
import math
import sys, os

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS 
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def load_strip(path, frame_w, frame_h, scale_to=None):
    try:
        sheet = pygame.image.load(path).convert_alpha()
        sheet_w, sheet_h = sheet.get_size()
        frames = []
        for x in range(0, sheet_w, frame_w):
            frame = sheet.subsurface(pygame.Rect(x, 0, frame_w, frame_h)).copy()
            if scale_to:
                frame = pygame.transform.smoothscale(frame, scale_to)
            frames.append(frame)
        return frames
    except Exception as e:
        print(f"Грешка при вчитување на {path}: {e}")
        surf = pygame.Surface(scale_to if scale_to else (32, 32))
        surf.fill((255, 0, 255))
        return [surf]


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, settings):
        super().__init__()
        self.image = pygame.Surface((5, 15))
        self.image.fill((0, 255, 255))
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = settings.bullet_speed

    def update(self):
        self.rect.y += self.speed
        if self.rect.bottom < 0:
            self.kill()


class AnimatedSprite(pygame.sprite.Sprite):
    def __init__(self, frames, fps=12):
        super().__init__()
        self.frames = frames
        self.fps = fps
        self.frame_i = 0
        self.image = self.frames[0]
        self.rect = self.image.get_rect()
        self._frame_ms = int(1000 / fps)
        self._last = pygame.time.get_ticks()

    def animate(self):
        now = pygame.time.get_ticks()
        if now - self._last >= self._frame_ms:
            self._last = now
            self.frame_i = (self.frame_i + 1) % len(self.frames)
            old_center = self.rect.center
            self.image = self.frames[self.frame_i]
            self.rect = self.image.get_rect(center=old_center)


class Enemy(AnimatedSprite): 
    def __init__(self, settings, is_special=False):
        self.is_special = is_special
        self.hp = 3 if is_special else 1
        if not is_special:
            frames = load_strip(
                resource_path(os.path.join("assets", "enemy_spaceship_2.png")),
                frame_w=32, frame_h=32, scale_to=(48, 48)
            )
        else:
            frames = load_strip(
                resource_path(os.path.join("assets", "enemy_spaceship_5.png")),
                frame_w=32, frame_h=40, scale_to=(48, 60)
            )

        super().__init__(frames, fps=10)

        self.rect.x = random.randint(0, 900 - self.rect.width)
        self.rect.y = -self.rect.height
        base_speed = random.uniform(2.0, 4.0)
        self.speed = base_speed + (settings.current_level * 0.2)

    def update(self):
        self.animate()
        self.rect.y += self.speed
        if self.rect.top > 700:
            self.kill()


class KnowledgeDrop(pygame.sprite.Sprite):
    _image = None

    def __init__(self, x, y, available_info):
        super().__init__()

        if available_info and len(available_info) > 0:
            self.text = available_info.pop(0)
        else:
            self.text = "Знењето е моќ! Подготви се за квизот!"

        if KnowledgeDrop._image is None:
            try:
                img = pygame.image.load(resource_path(os.path.join("assets", "gem.png"))).convert_alpha()
                KnowledgeDrop._image = pygame.transform.smoothscale(img, (28, 28))
            except:
                KnowledgeDrop._image = pygame.Surface((28, 28))
                KnowledgeDrop._image.fill((0, 255, 0))

        self.image = KnowledgeDrop._image
        self.rect = self.image.get_rect(center=(x, y))
        self.t = 0  

    def update(self):
        self.t += 0.1
        self.rect.y += 2
        self.rect.x += math.sin(self.t) * 1.5
        if self.rect.top > 700:
            self.kill()


class BossBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, target_x, target_y, attack_type="aimed"):
        super().__init__()

        self.attack_type = attack_type
        # visuals
        self.image = pygame.Surface((6, 12), pygame.SRCALPHA)
        self.image.fill((255, 50, 50))
        self.rect = self.image.get_rect(center=(x, y))

        # direction toward target
        dx = target_x - x
        dy = target_y - y
        length = max(1, (dx ** 2 + dy ** 2) ** 0.5)

        # defaults
        self.speed = 9
        self.vel_x = dx / length * self.speed
        self.vel_y = dy / length * self.speed

        if self.attack_type == "fast":
            self.speed = 13
            self.vel_x = dx / length * self.speed
            self.vel_y = dy / length * self.speed

        elif self.attack_type == "zigzag":
            self.zigzag_timer = 0
            self.zigzag_strength = 4

    def update(self):
        # zigzag motion
        if self.attack_type == "zigzag":
            self.zigzag_timer += 1
            zigzag_offset = self.zigzag_strength * (
                1 if (self.zigzag_timer // 10) % 2 == 0 else -1
            )
            self.rect.x += self.vel_x + zigzag_offset
        else:
            self.rect.x += self.vel_x

        self.rect.y += self.vel_y

        # kill bullet if off-screen
        if (
            self.rect.top > 800
            or self.rect.bottom < -50
            or self.rect.right < -50
            or self.rect.left > 950
        ):
            self.kill()
