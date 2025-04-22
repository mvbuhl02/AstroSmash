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
        
        # Carrega os frames específicos para cada tipo
        self.frames = self.load_animation_frames()
        self.current_frame = 0
        self.animation_speed = self.get_animation_speed()
        self.last_update = pygame.time.get_ticks()
        
        # Configurações iniciais
        self.image = self.frames[self.current_frame] if self.frames else self.create_fallback_image()
        self.rect = self.image.get_rect(center=self.get_initial_position())
        self.speed = self.get_speed()
        self.health = self.get_initial_health()
        self.hit = False
        self.hit_timer = 0
    
    def get_initial_position(self):
        if self.enemy_type == EnemyType.BOSS:
            return (WIDTH // 2, -100)
        return (random.randint(30, WIDTH-30), -30)
    
    def get_speed(self):
        if self.enemy_type == EnemyType.BOSS:
            return random.uniform(0.5, 1.5)
        elif self.enemy_type == EnemyType.ASTEROID:
            return random.uniform(1.0, 3.0)
        return random.uniform(2.0, 4.0)
    
    def get_initial_health(self):
        if self.enemy_type == EnemyType.BOSS:
            return 20
        elif self.enemy_type == EnemyType.ASTEROID:
            return 3
        return 1
    
    def get_animation_speed(self):
        if self.enemy_type == EnemyType.BOSS:
            return 100  # ms entre frames (mais lento)
        return 150  # ms entre frames (mais rápido)
    
    def get_sprite_folder(self):
        if self.enemy_type == EnemyType.BOSS:
            return 'boss'
        elif self.enemy_type == EnemyType.ASTEROID:
            return 'asteroid'
        return 'enemy'
    
    def create_fallback_image(self):
        """Cria uma imagem de fallback baseada no tipo"""
        size = (60, 60) if self.enemy_type == EnemyType.BOSS else (30, 30)
        surface = pygame.Surface(size, pygame.SRCALPHA)
        
        if self.enemy_type == EnemyType.BOSS:
            pygame.draw.polygon(surface, PURPLE, [(30, 0), (0, 60), (60, 60)])
        elif self.enemy_type == EnemyType.ASTEROID:
            pygame.draw.circle(surface, GRAY, (15, 15), 15)
        else:
            pygame.draw.circle(surface, RED, (15, 15), 15)
            
        return surface
    
    def load_animation_frames(self):
        """Carrega os frames de animação com fallback robusto"""
        frames = []
        folder = self.get_sprite_folder()
        sprite_path = os.path.join('assets', 'sprites', folder)
        
        # Fallback colors para cada tipo
        fallback_colors = {
            EnemyType.COMMON: RED,
            EnemyType.ASTEROID: GRAY,
            EnemyType.BOSS: PURPLE
        }
        
        try:
            # Cria a pasta se não existir
            os.makedirs(sprite_path, exist_ok=True)
            
            # Tenta carregar frames
            frame_files = sorted([f for f in os.listdir(sprite_path) 
                            if f.endswith(('.png', '.jpg', '.jpeg')) and f.startswith(f'{folder}_')])
            
            for frame_file in frame_files:
                try:
                    frame = pygame.image.load(os.path.join(sprite_path, frame_file)).convert_alpha()
                    size = (60, 60) if self.enemy_type == EnemyType.BOSS else (30, 30)
                    frames.append(pygame.transform.scale(frame, size))
                except:
                    continue
            
            if not frames:
                print(f"AVISO: Usando fallback para {folder}")
                surface = pygame.Surface((60, 60) if self.enemy_type == EnemyType.BOSS else (30, 30), pygame.SRCALPHA)
                
                if self.enemy_type == EnemyType.BOSS:
                    pygame.draw.polygon(surface, fallback_colors[EnemyType.BOSS], 
                                    [(30, 0), (0, 60), (60, 60)])
                elif self.enemy_type == EnemyType.ASTEROID:
                    pygame.draw.circle(surface, fallback_colors[EnemyType.ASTEROID], (15, 15), 15)
                else:
                    pygame.draw.circle(surface, fallback_colors[EnemyType.COMMON], (15, 15), 15)
                
                frames.append(surface)
                
        except Exception as e:
            print(f"ERRO ao carregar frames: {str(e)}")
            # Fallback extremo - quadrado vermelho
            surface = pygame.Surface((30, 30), pygame.SRCALPHA)
            surface.fill(RED)
            frames.append(surface)
        
        return frames
    
    def update(self):
        # Atualiza animação
        now = pygame.time.get_ticks()
        if now - self.last_update > self.animation_speed:
            self.last_update = now
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.image = self.frames[self.current_frame]
        
        # Efeito de hit (piscar quando atingido)
        if self.hit:
            self.hit_timer += 1
            if self.hit_timer > 10:  # Duração do efeito
                self.hit = False
                self.hit_timer = 0
            else:
                # Aplica um efeito visual quando atingido
                hit_image = self.image.copy()
                hit_image.fill((255, 100, 100, 150), special_flags=pygame.BLEND_MULT)
                self.image = hit_image
        
        # Movimento
        if self.enemy_type == EnemyType.BOSS:
            # Movimento mais complexo para o boss
            self.rect.y += self.speed
            if self.rect.top > 20:
                self.rect.x += random.randint(-2, 2)
        else:
            # Movimento reto para baixo para outros inimigos
            self.rect.y += self.speed
        
        # Remove se sair da tela
        if self.rect.top > HEIGHT:
            self.kill()
            
    def take_damage(self, amount):
        """Sistema de dano com proteção contra hitkill"""
        if self.shield > 0:
            damage_to_shield = min(amount, self.shield)
            self.shield -= damage_to_shield
            amount -= damage_to_shield
        
        if amount > 0:
            self.health = max(0, self.health - amount)
        
        # Efeito visual
        self.hit_animation = 5  # Número de frames para piscar
        
        if self.health <= 0:
            return True
        return False