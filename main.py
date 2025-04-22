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

class AstroSmash:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("AstroSmash MVP")
        
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        
        # inicializa
        self.audio_manager = AudioManager()
        self.load_audio()
        self.score_manager = ScoreManager()
        
        # sprites
        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        
        # cria o player
        self.player = Player(self.audio_manager)
        self.all_sprites.add(self.player)
        
        # variaveis
        self.game_state = SPLASH
        self.splash_time = pygame.time.get_ticks()
        self.last_enemy_spawn = 0
        self.enemy_spawn_interval = 1000
        self.boss_active = False
        
    def load_audio(self):
        """Carrega todos os efeitos sonoros"""
        self.audio_manager.has_sound = True
        try:
            base_path = os.path.join('assets', 'sounds')
            
            # Verifica se a pasta existe
            if not os.path.exists(base_path):
                os.makedirs(base_path)
                print(f"Aviso: Pasta de sons criada em {base_path}")
                self.audio_manager.has_sound = False
                return

            sounds_to_load = [
                ('tiro', 'tiro.mp3'),
                ('fundo', 'fundo.mp3'),
                ('chefe', 'chefe.mp3'),
                ('movimento', 'movimento.mp3'),
                ('hit', 'hit.mp3'),
                ('damage', 'damage.wav'),
                ('gameover', 'gameover.mp3')
            ]

            for name, file in sounds_to_load:
                path = os.path.join(base_path, file)
                try:
                    if os.path.exists(path):
                        self.audio_manager.load_sound(name, path)
                        print(f"Som {name} carregado com sucesso")
                    else:
                        print(f"Aviso: Arquivo não encontrado - {file}")
                        self.audio_manager.has_sound = False
                except Exception as e:
                    print(f"Erro ao carregar {name}: {str(e)}")
                    self.audio_manager.has_sound = False

            # Fallback caso nenhum som seja carregado
            if not self.audio_manager.sounds:
                self.audio_manager.has_sound = False
                print("AVISO: Nenhum som foi carregado - Continuando sem áudio")
                
        except Exception as e:
            print(f"Erro crítico no sistema de áudio: {str(e)}")
            self.audio_manager.has_sound = False
    
    def spawn_enemy(self):
        now = pygame.time.get_ticks()
        
        # Spawn de boss a cada 5 waves
        if self.score_manager.wave % 5 == 0 and not self.boss_active:
            enemy = Enemy(EnemyType.BOSS)
            self.boss_active = True
            self.audio_manager.play_sound('chefe')
        else:
            # Spawn de inimigos normais ou asteroides
            if random.random() < 0.3:  # 30% de chance de ser asteroide
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
    
    def update(self):
        if self.game_state == SPLASH:
            if pygame.time.get_ticks() - self.splash_time > 2000:
                self.game_state = MENU
        
        elif self.game_state == PLAYING:
            self.all_sprites.update()
            
            # Verifica se o boss foi derrotado
            self.boss_active = any(e.enemy_type == EnemyType.BOSS for e in self.enemies)
            
            # Spawn de inimigos
            now = pygame.time.get_ticks()
            if now - self.last_enemy_spawn > self.enemy_spawn_interval:
                self.last_enemy_spawn = now
                self.spawn_enemy()
                
                # Aumenta dificuldade gradualmente
                if random.random() < 0.1:
                    self.enemy_spawn_interval = max(200, self.enemy_spawn_interval - 50)
                    if self.enemy_spawn_interval % 500 == 0:
                        self.score_manager.increase_wave()
            
            # Colisões
            self.check_collisions()
    
    def check_collisions(self):
        # Colisões entre projéteis e inimigos
        hits = pygame.sprite.groupcollide(self.bullets, self.enemies, True, False)
        for bullet, enemy_list in hits.items():
            for enemy in enemy_list:
                damage = 2 if enemy.enemy_type == EnemyType.BOSS else 1
                if enemy.take_damage(damage):
                    self.audio_manager.play_sound('hit')
                    # Pontuação baseada no tipo de inimigo
                    if enemy.enemy_type == EnemyType.BOSS:
                        self.score_manager.add_score(100)
                        self.boss_active = False
                    elif enemy.enemy_type == EnemyType.ASTEROID:
                        self.score_manager.add_score(20)
                    else:
                        self.score_manager.add_score(10)

        # Colisões entre jogador e inimigos
        hits = pygame.sprite.spritecollide(self.player, self.enemies, False)
        for hit in hits:
            damage = 10 if hit.enemy_type == EnemyType.BOSS else 5  # Reduzi o dano do boss de 20 para 10
            self.audio_manager.play_sound('damage')
            if self.player.take_damage(damage):
                self.game_over()

        # Colisões entre jogador e projéteis inimigos
        hits = pygame.sprite.spritecollide(self.player, self.enemy_bullets, True)
        for hit in hits:
            self.audio_manager.play_sound('damage')
            if self.player.take_damage(2):  # Reduzi o dano dos projéteis de 5 para 2
                self.game_over()
    
    def game_over(self):
        self.game_state = GAME_OVER
        self.score_manager.save_high_score()
        self.audio_manager.stop_music()
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
        
        # Reset do score manager
        self.score_manager.score = 0
        self.score_manager.wave = 1
        self.score_manager.load_high_score()  # Recarrega o high score
        
        self.enemy_spawn_interval = 1000
        
        self.audio_manager.play_music('fundo')
    
    def draw(self):
        self.screen.fill(BLACK)
        self.draw_stars()
        self.all_sprites.draw(self.screen)
        self.draw_hud()
        self.draw_state_screens()
    
    def draw_stars(self):
        for i in range(50):
            x = (pygame.time.get_ticks() // 100 + i * 100) % WIDTH
            y = (i * 20 + pygame.time.get_ticks() // 50) % HEIGHT
            brightness = min(255, 50 + abs((pygame.time.get_ticks() // 10 + i * 50) % 510 - 255))
            pygame.draw.circle(self.screen, (brightness, brightness, brightness), (x, y), 1)
    
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
            self.draw_text("BOSS ALERT!", 40, WIDTH//2, 80, ORANGE)
    
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
        self.draw_text("ASTROSMASH", 72, WIDTH//2, HEIGHT//3)
        self.draw_text("MVP Edition", 36, WIDTH//2, HEIGHT//2)
    
    def draw_menu(self):
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))
        self.screen.blit(s, (0, 0))
        self.draw_text("ASTROSMASH", 64, WIDTH//2, HEIGHT//4)
        self.draw_text(f"Recorde: {self.score_manager.high_score}", 36, WIDTH//2, HEIGHT//3)
        self.draw_text("Pressione ENTER para Jogar", 36, WIDTH//2, HEIGHT//2)
        self.draw_text("Setas para mover | Espaço para atirar", 24, WIDTH//2, HEIGHT*3//4)
    
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