import pygame
import os
from config import *
from game.managers.audio import AudioManager
from game.entities.bullets import Bullet

class Player(pygame.sprite.Sprite):
    def __init__(self, audio_manager: AudioManager):
        super().__init__()
        
        self.speed = 5
        self.max_health = 100
        self.health = self.max_health
        self.max_shield = 50
        self.shield = self.max_shield
        self.heat = 0
        self.max_heat = 100
        self.cooling_rate = 1.2
        self.shoot_delay = 200
        self.last_shot = 0
        self.last_movement_sound = 0
        self.movement_sound_delay = 300
        self.audio_manager = audio_manager
        self.invincible = False
        self.invincible_timer = 0
        self.invincible_duration = 1000 
        
        self.frames = self.load_animation_frames()
        self.current_frame = 0
        self.animation_speed = 100
        self.last_update = pygame.time.get_ticks()
        
        self.image = self.frames[self.current_frame] if self.frames else self.create_fallback_image()
        self.rect = self.image.get_rect(center=(WIDTH//2, HEIGHT-50))
        self.original_image = self.image.copy()
    
    def create_fallback_image(self):
        surface = pygame.Surface((30, 40), pygame.SRCALPHA)
        pygame.draw.polygon(surface, GREEN, [(15, 0), (0, 40), (30, 40)])
        return surface
    
    def load_animation_frames(self):
        frames = []
        try:
            frame_files = [f for f in os.listdir('assets/sprites/player/') 
                         if f.endswith(('.png', '.jpg', '.jpeg')) and f.startswith('player_')]
            
            frame_files.sort(key=lambda x: int(x.split('_')[1].split('.')[0]))
            
            for frame_file in frame_files:
                frame = pygame.image.load(f'assets/sprites/player/{frame_file}').convert_alpha()
                frame = pygame.transform.scale(frame, (60, 60))
                frames.append(frame)
                
            if not frames:
                frames.append(self.create_fallback_image())
                
        except Exception as e:
            print(f"ERRO ao carregar frames: {e}")
            frames.append(self.create_fallback_image())
            
        return frames
    
    def update(self):
        now = pygame.time.get_ticks()
        
        # Atualização de animação
        if now - self.last_update > self.animation_speed:
            self.last_update = now
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.image = self.frames[self.current_frame]
            self.original_image = self.image.copy()
            
            if self.invincible:
                if (now // 100) % 2 == 0:
                    self.image.set_alpha(100)
                else:
                    self.image.set_alpha(255)
        
        # Fim da invencibilidade
        if self.invincible and now - self.invincible_timer > self.invincible_duration:
            self.invincible = False
            self.image.set_alpha(255)
        
        # Movimento
        keys = pygame.key.get_pressed()
        is_moving = False
        
        if keys[pygame.K_a] and self.rect.left > 0:
            self.rect.x -= self.speed
            is_moving = True
        if keys[pygame.K_d] and self.rect.right < WIDTH:
            self.rect.x += self.speed
            is_moving = True
        if keys[pygame.K_w] and self.rect.top > 0:
            self.rect.y -= self.speed
            is_moving = True
        if keys[pygame.K_s] and self.rect.bottom < HEIGHT:
            self.rect.y += self.speed
            is_moving = True
            
        if self.audio_manager.has_sound and is_moving and 'movimento' in self.audio_manager.sounds:
            if now - self.last_movement_sound > self.movement_sound_delay:
                self.audio_manager.play_sound('movimento')
                self.last_movement_sound = now
        
        self.heat = max(0, self.heat - self.cooling_rate)
        
    def shoot(self, all_sprites, bullets):
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay and self.heat < self.max_heat:
            self.last_shot = now
            self.heat += 10
            bullet = Bullet(self.rect.centerx, self.rect.top)
            all_sprites.add(bullet)
            bullets.add(bullet)
            
            if self.audio_manager.has_sound:
                self.audio_manager.play_sound('tiro')
            return True
        return False
        
    def take_damage(self, amount, enemy=None):
        if self.invincible:
            return False
            
        # Dano no escudo primeiro
        if self.shield > 0:
            shield_damage = min(amount, self.shield)
            self.shield -= shield_damage
            amount -= shield_damage
            
        # Dano restante vai para a vida
        if amount > 0:
            self.health = max(0, self.health - amount)
            self.invincible = True
            self.invincible_timer = pygame.time.get_ticks()
            
            # Efeito de repulsão
            if enemy:
                knockback = 10
                if enemy.rect.centerx < self.rect.centerx:
                    self.rect.x += knockback
                else:
                    self.rect.x -= knockback
        
        return self.health <= 0