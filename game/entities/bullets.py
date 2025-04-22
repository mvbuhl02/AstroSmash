import pygame
from config import *

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((4, 10), pygame.SRCALPHA)
        pygame.draw.rect(self.image, YELLOW, (0, 0, 4, 10))
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 10
        
    def update(self):
        self.rect.y -= self.speed
        if self.rect.bottom < 0:
            self.kill()

class EnemyBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, angle):
        super().__init__()
        self.image = pygame.Surface((8, 8), pygame.SRCALPHA)
        pygame.draw.circle(self.image, ORANGE, (4, 4), 4)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 3
        self.angle = angle
        self.direction = Vector2(1, 0).rotate(-angle)
        
    def update(self):
        self.rect.x += self.direction.x * self.speed
        self.rect.y += self.direction.y * self.speed
        if not (0 <= self.rect.x <= WIDTH and 0 <= self.rect.y <= HEIGHT):
            self.kill()