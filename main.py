import pygame
import sys
import os
import random
from config import *
from game.managers.audio import AudioManager
from game.managers.score import ScoreManager
from game.entities.player import Player
from game.entities.enemies import Enemy, EnemyType
from game.entities.bullets import Bullet, EnemyBullet
WAVE_TRANSITION_DURATION = 2000

class AstroSmash:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("AstroSmash MVP")
        
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        
        self.audio_manager = AudioManager()
        self.load_audio()
        self.score_manager = ScoreManager()
        
        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        
        self.player = Player(self.audio_manager)
        self.all_sprites.add(self.player)
        
        self.game_state = SPLASH
        self.splash_time = pygame.time.get_ticks()
        self.last_enemy_spawn = 0
        self.enemy_spawn_interval = 1000
        self.boss_active = False
        self.stars = self.generate_stars(100)
        
        self.enemies_defeated = 0
        self.enemies_per_wave = 15 
        self.wave_transition_start = 0
        self.show_wave_message = False
        
    def spawn_wave_enemies(self):
        base_enemies = 8 + self.score_manager.wave * 2
        min_interval = max(200, 800 - self.score_manager.wave * 30) 
        
        for i in range(base_enemies):
            spawn_time = i * min_interval  
            pygame.time.set_timer(pygame.USEREVENT + i, spawn_time, True)
        
        self.enemy_spawn_interval = min_interval * 2
        self.last_enemy_spawn = pygame.time.get_ticks()
        
        self.show_wave_message = True
        self.wave_transition_start = pygame.time.get_ticks()
        if self.audio_manager.has_sound and 'wave' in self.audio_manager.sounds:
            self.audio_manager.play_sound('wave')
        
        
    def generate_stars(self, count):
        return [(random.randint(0, WIDTH), random.randint(0, HEIGHT), random.randint(1, 3)) 
                for _ in range(count)]
    
    def load_audio(self):
        self.audio_manager.has_sound = True
        sounds_loaded = False
        
        try:
            base_path = os.path.join('assets', 'sounds')
            
            if not os.path.exists(base_path):
                print(f"Aviso: Pasta de sons não encontrada em {base_path}")
                self.audio_manager.has_sound = False
                return False

            sounds_to_load = [
                ('tiro', 'tiro.mp3'),
                ('fundo', 'fundo.mp3'),
                ('chefe', 'chefe.mp3'),
                ('movimento', 'movimento.mp3'),
                ('hit', 'hit.mp3'),
                ('damage', 'damage.wav'),
                ('gameover', 'gameover.mp3'),
                ('wave', 'wave.mp3')
            ]

            for name, file in sounds_to_load:
                path = os.path.join(base_path, file)
                if os.path.exists(path):
                    self.audio_manager.load_sound(name, path)
                    sounds_loaded = True

            if 'fundo' in self.audio_manager.sounds:
                self.audio_manager.play_music('fundo')
                
        except Exception as e:
            print(f"Erro crítico no sistema de áudio: {str(e)}")
            self.audio_manager.has_sound = False
            
        return sounds_loaded
    
    def spawn_enemy(self):
        now = pygame.time.get_ticks()
        
        if self.score_manager.wave % 5 == 0 and not self.boss_active and len([e for e in self.enemies if e.enemy_type == EnemyType.BOSS]) == 0:
            enemy = Enemy(EnemyType.BOSS)
            self.boss_active = True
            if self.audio_manager.has_sound:
                self.audio_manager.play_sound('chefe')
        else:
            if random.random() < 0.3: 
                enemy = Enemy(EnemyType.ASTEROID)
            else:
                enemy = Enemy(EnemyType.COMMON)
        
        self.all_sprites.add(enemy)
        self.enemies.add(enemy)
    
    def run(self):
        while self.running:
            self.clock.tick(FPS)
            self.handle_events()
            self.update()
            self.draw()
            pygame.display.flip()
        
        pygame.quit()
        sys.exit()
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.game_state == PLAYING:
                        self.game_state = PAUSE
                    elif self.game_state == PAUSE:
                        self.game_state = PLAYING
                if event.key == pygame.K_SPACE and self.game_state == PLAYING:
                    self.player.shoot(self.all_sprites, self.bullets)
                if event.key == pygame.K_RETURN and self.game_state in [MENU, GAME_OVER, SPLASH]:
                    if self.game_state == SPLASH and (pygame.time.get_ticks() - self.splash_time) < 2000:
                        continue
                    self.reset_game()
            if self.game_state == PLAYING and pygame.USEREVENT <= event.type <= pygame.USEREVENT + 50:
                self.spawn_enemy()
    
    def update(self):
        if self.game_state == SPLASH:
            if pygame.time.get_ticks() - self.splash_time > 2000:
                self.game_state = MENU
        
        elif self.game_state == PLAYING:
            self.all_sprites.update()
            
            self.boss_active = any(e.enemy_type == EnemyType.BOSS for e in self.enemies)
            
            now = pygame.time.get_ticks()
            enemies_on_screen = len(self.enemies)
            max_enemies = 5 + self.score_manager.wave
            
            if (now - self.last_enemy_spawn > self.enemy_spawn_interval and 
                enemies_on_screen < max_enemies):
                
                self.last_enemy_spawn = now
                self.spawn_enemy()
                
                if random.random() < 0.2:
                    
                    self.enemy_spawn_interval = max(200, self.enemy_spawn_interval - 30)
                    
                    
                    if self.enemy_spawn_interval <= 300:  
                        self.score_manager.increase_wave()
                        self.enemy_spawn_interval = 800 
                        self.show_wave_message = True
                        self.wave_transition_start = now
            

            if (not self.boss_active and 
                enemies_on_screen == 0 and 
                now - self.last_enemy_spawn > 3000):  
                self.score_manager.increase_wave()
                self.enemy_spawn_interval = 800
                self.last_enemy_spawn = now
            
            self.check_collisions()
            
            if self.show_wave_message:
                if now - self.wave_transition_start > 2000:
                    self.show_wave_message = False
        
    def next_wave(self):
        self.score_manager.increase_wave()
        
        for i in range(50):
            pygame.time.set_timer(pygame.USEREVENT + i, 0)
        
        self.spawn_wave_enemies()
        
        if self.score_manager.wave % 5 == 0:
            self.spawn_boss()
            
    def check_collisions(self):
        DAMAGE_SETTINGS = {
            'player_bullet': {
                EnemyType.BOSS: 3,
                EnemyType.ASTEROID: 2,
                EnemyType.COMMON: 1
            },
            'enemy_collision': {
                EnemyType.BOSS: 6,
                EnemyType.ASTEROID: 4,
                EnemyType.COMMON: 2
            },
            'enemy_bullet': 3
        }
        
        SCORE_VALUES = {
            EnemyType.BOSS: 100,
            EnemyType.ASTEROID: 25,
            EnemyType.COMMON: 10
        }
        
        bullet_hits = pygame.sprite.groupcollide(self.bullets, self.enemies, True, False)
        enemies_defeated_in_this_check = 0  
        
        for bullet, enemies in bullet_hits.items():
            for enemy in enemies:
                damage = DAMAGE_SETTINGS['player_bullet'][enemy.enemy_type]
                if enemy.take_damage(damage):
                    if self.audio_manager.has_sound:
                        self.audio_manager.play_sound('hit')
                    
                    self.score_manager.add_score(SCORE_VALUES[enemy.enemy_type])
                    enemies_defeated_in_this_check += 1 
                    
                    if enemy.enemy_type == EnemyType.BOSS:
                        self.boss_active = False

        if not self.player.invincible:
            hits = pygame.sprite.spritecollide(self.player, self.enemies, True)
            for enemy in hits:
                damage = DAMAGE_SETTINGS['enemy_collision'][enemy.enemy_type]
                
                if self.audio_manager.has_sound:
                    self.audio_manager.play_sound('damage')
                    
                if self.player.take_damage(damage, enemy):
                    self.game_over()


        hits = pygame.sprite.spritecollide(self.player, self.enemy_bullets, True)
        for bullet in hits:
            if self.audio_manager.has_sound:
                self.audio_manager.play_sound('damage')
            
            if self.player.take_damage(DAMAGE_SETTINGS['enemy_bullet']):
                self.game_over()
        
        if enemies_defeated_in_this_check > 0:
            self.enemies_defeated += enemies_defeated_in_this_check
            
            if self.enemies_defeated >= self.enemies_per_wave and not self.boss_active:
                self.score_manager.increase_wave()
                self.enemies_defeated = 0
                self.enemies_per_wave = 15 + self.score_manager.wave * 2
                self.spawn_wave_enemies()
    
    def game_over(self):
        self.game_state = GAME_OVER
        self.score_manager.save_high_score()
        self.audio_manager.stop_music()
        if self.audio_manager.has_sound:
            self.audio_manager.play_sound('gameover')
    
    def reset_game(self):
        self.game_state = PLAYING
        self.all_sprites.empty()
        self.enemies.empty()
        self.bullets.empty()
        self.enemy_bullets.empty()
        self.boss_active = False
        
        self.audio_manager.stop_music()
        self.player = Player(self.audio_manager)
        self.all_sprites.add(self.player)
        
        self.score_manager.score = 0
        self.score_manager.wave = 1
        self.enemy_spawn_interval = 1000
        
        if self.audio_manager.has_sound:
            self.audio_manager.play_music('fundo')
    
    def draw(self):
        self.screen.fill(BLACK)
        self.draw_stars()
        self.all_sprites.draw(self.screen)
        self.draw_hud()
        self.draw_state_screens()
        if self.show_wave_message:
            self.draw_wave_transition()

    def draw_wave_transition(self):
        now = pygame.time.get_ticks()
        if now - self.wave_transition_start < WAVE_TRANSITION_DURATION:
            progress = (now - self.wave_transition_start) / WAVE_TRANSITION_DURATION
            alpha = 255 * (1 - abs(progress - 0.5)) * 2
            
            s = pygame.Surface((WIDTH, 100), pygame.SRCALPHA)
            s.fill((0, 0, 0, 150))
            self.screen.blit(s, (0, HEIGHT//2 - 50))
            
            size = 48 + int(10 * abs(progress - 0.5))
            color = (
                min(255, 150 + int(105 * abs(progress - 0.5) * 2)),
                min(255, 150 + int(105 * abs(progress - 0.5) * 2)),
                0
            )
            
            self.draw_text(f"WAVE {self.score_manager.wave}", size, WIDTH//2, HEIGHT//2, color)
        else:
            self.show_wave_message = False
    
    def draw_stars(self):
        now = pygame.time.get_ticks()
        for x, y, size in self.stars:
            brightness = min(255, 50 + abs((now // 10 + x + y) % 510 - 255))
            pygame.draw.circle(self.screen, (brightness, brightness, brightness), 
                              (x, (y + now // 50) % HEIGHT), size)
    
    def draw_hud(self):
        self.draw_text(f"Pontuação: {self.score_manager.score}", 30, 70, 20)
        self.draw_text(f"Recorde: {self.score_manager.high_score}", 30, 70, 50)
        self.draw_text(f"Nível: {self.score_manager.wave}", 30, WIDTH - 70, 20)
        
        # Barras de status
        pygame.draw.rect(self.screen, (50, 50, 50), (WIDTH - 120, 50, 104, 20))
        pygame.draw.rect(self.screen, RED, (WIDTH - 118, 52, self.player.health, 16))
        pygame.draw.rect(self.screen, (50, 50, 50), (WIDTH - 120, 80, 104, 10))
        pygame.draw.rect(self.screen, BLUE, (WIDTH - 118, 82, self.player.shield, 6))
        pygame.draw.rect(self.screen, (50, 50, 50), (WIDTH//2 - 50, 10, 100, 10))
        pygame.draw.rect(self.screen, (min(255, self.player.heat * 2.55), max(0, 255 - self.player.heat * 2.55), 0), 
                        (WIDTH//2 - 50, 10, self.player.heat, 10))
        
        if self.boss_active:
            self.draw_text("ANTEÇÃO! CHEFÃO A CAMINHO", 40, WIDTH//2, 80, ORANGE)
    
    def draw_state_screens(self):
        if self.game_state == SPLASH:
            self.draw_splash_screen()
        elif self.game_state == MENU:
            self.draw_menu()
        elif self.game_state == PAUSE:
            self.draw_pause()
        elif self.game_state == GAME_OVER:
            self.draw_game_over()
    
    def draw_splash_screen(self):
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))
        self.screen.blit(s, (0, 0))
        self.draw_text("SUPER FAG ASTROSMASH", 72, WIDTH//2, HEIGHT//3)
        self.draw_text("Dedicatória: Professor Jeferson", 36, WIDTH//2, HEIGHT//2)
    
    def draw_menu(self):
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))
        self.screen.blit(s, (0, 0))
        self.draw_text("SUPER FAG ASTROSMASH", 64, WIDTH//2, HEIGHT//4)
        self.draw_text(f"Recorde: {self.score_manager.high_score}", 36, WIDTH//2, HEIGHT//3)
        self.draw_text("Pressione ENTER para Jogar", 36, WIDTH//2, HEIGHT//2)
        self.draw_text("W,A,S,D para mover | Espaço para atirar", 24, WIDTH//2, HEIGHT*3//4)
    
    def draw_pause(self):
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))
        self.screen.blit(s, (0, 0))
        self.draw_text("PAUSADO", 64, WIDTH//2, HEIGHT//2)
        self.draw_text("Pressione ESC para continuar", 24, WIDTH//2, HEIGHT//2 + 50)
    
    def draw_game_over(self):
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))
        self.screen.blit(s, (0, 0))
        self.draw_text("FIM DE JOGO", 64, WIDTH//2, HEIGHT//2 - 50)
        self.draw_text(f"Pontuação: {self.score_manager.score}", 36, WIDTH//2, HEIGHT//2)
        self.draw_text("Pressione ENTER para recomeçar", 24, WIDTH//2, HEIGHT//2 + 80)
    
    def draw_text(self, text, size, x, y, color=WHITE):
        font = pygame.font.Font(None, size)
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(center=(x, y))
        self.screen.blit(text_surface, text_rect)

if __name__ == "__main__":
    game = AstroSmash()
    game.run()