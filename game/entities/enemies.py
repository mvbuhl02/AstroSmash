import pygame
import os
import random
from config import *
from enum import Enum

class EnemyType(Enum):
    COMMON = 1
    ASTEROID = 2
    BOSS = 3

class Enemy(pygame.sprite.Sprite):
    def __init__(self, enemy_type=EnemyType.COMMON):
        super().__init__()
        self.enemy_type = enemy_type
        self._setup_attributes()
        self.frames = self.load_animation_frames()
        self.current_frame = 0
        self.animation_speed = self.get_animation_speed()
        self.last_update = pygame.time.get_ticks()
        self.image = self.frames[self.current_frame] if self.frames else self.create_fallback_image()
        self.rect = self.image.get_rect(center=self.get_initial_position())
        self.hit = False
        self.hit_timer = 0
    
    def _setup_attributes(self):
        if self.enemy_type == EnemyType.BOSS:
            self.health = 50
            self.damage = 50
            self.speed = random.uniform(0.8, 1.2)
        elif self.enemy_type == EnemyType.ASTEROID:
            self.health = 10
            self.damage = 20
            self.speed = random.uniform(1.5, 2.5)
        else:
            self.health = 1
            self.damage = 10
            self.speed = random.uniform(2.0, 3.0)
        self.shield = 0
    
    def get_initial_position(self):
        if self.enemy_type == EnemyType.BOSS:
            return (WIDTH // 2, -100)
        return (random.randint(30, WIDTH-30), -30)
    
    def get_animation_speed(self):
        return 100 if self.enemy_type == EnemyType.BOSS else 150
    
    def get_sprite_folder(self):
        return {
            EnemyType.BOSS: 'boss',
            EnemyType.ASTEROID: 'asteroid',
            EnemyType.COMMON: 'enemy'
        }[self.enemy_type]
    
    def create_fallback_image(self):
        size = (60, 60) if self.enemy_type == EnemyType.BOSS else (30, 30)
        surface = pygame.Surface(size, pygame.SRCALPHA)
        colors = {
            EnemyType.BOSS: PURPLE,
            EnemyType.ASTEROID: GRAY,
            EnemyType.COMMON: RED
        }
        if self.enemy_type == EnemyType.BOSS:
            pygame.draw.polygon(surface, colors[self.enemy_type], [(30, 0), (0, 60), (60, 60)])
        else:
            pygame.draw.circle(surface, colors[self.enemy_type], (15, 15), 15)
        return surface
    
    def load_animation_frames(self):
        frames = []
        folder = self.get_sprite_folder()
        sprite_path = os.path.join('assets', 'sprites', folder)
        try:
            if not os.path.exists(sprite_path):
                return [self.create_fallback_image()]
            frame_files = sorted([f for f in os.listdir(sprite_path) 
                               if f.endswith(('.png', '.jpg', '.jpeg')) and f.startswith(f'{folder}_')])
            for frame_file in frame_files:
                try:
                    frame = pygame.image.load(os.path.join(sprite_path, frame_file)).convert_alpha()
                    size = (60, 60) if self.enemy_type == EnemyType.BOSS else (30, 30)
                    frames.append(pygame.transform.scale(frame, size))
                except Exception as e:
                    continue
        except Exception as e:
            pass
        return frames or [self.create_fallback_image()]
    
    def update(self):
        now = pygame.time.get_ticks()
        if now - self.last_update > self.animation_speed:
            self.last_update = now
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.image = self.frames[self.current_frame]
        if self.hit:
            self.hit_timer += 1
            if self.hit_timer > 10:
                self.hit = False
                self.hit_timer = 0
            else:
                hit_image = self.image.copy()
                hit_image.fill((255, 100, 100, 150), special_flags=pygame.BLEND_MULT)
                self.image = hit_image
        self.rect.y += self.speed
        if self.enemy_type == EnemyType.BOSS and self.rect.top > 20:
            self.rect.x += random.randint(-2, 2)
        if self.rect.top > HEIGHT:
            self.kill()
    
    def take_damage(self, amount):
        self.health -= amount
        self.hit = True
        self.hit_timer = 0
        if self.health <= 0:
            self.kill()
            return True
        return False
