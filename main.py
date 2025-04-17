import pygame
import random
import os
import sys
from pygame.math import Vector2

# Inicialização do Pygame com configurações de áudio otimizadas
pygame.init()
pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
pygame.mixer.init()
pygame.display.set_caption("AstroSmash MVP - Versão com Áudio")

# Configurações básicas
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
FPS = 60

# Cores
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
BLUE = (0, 0, 255)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)

# Estados do jogo
MENU = 0
PLAYING = 1
GAME_OVER = 2
PAUSE = 3
SPLASH = 4
game_state = SPLASH

# Função para carregar sons com fallback
def load_sound(filename, volume=1.0):
    """Carrega um arquivo de som com tratamento de erros robusto"""
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        
        # Verifica se o arquivo existe
        if not os.path.exists(filename):
            print(f"Arquivo não encontrado: {filename}")
            return None
            
        sound = pygame.mixer.Sound(filename)
        sound.set_volume(volume)
        return sound
    except Exception as e:
        print(f"Erro ao carregar {filename}: {str(e)}")
        return None

# Carregar sons com fallback
try:
    shoot_sound = load_sound('tiro.wav') or load_sound('tiro.mp3', 0.3)
    background_music = load_sound('fundo.wav') or load_sound('fundo.mp3', 0.2)
    boss_spawn_sound = load_sound('chefe.wav') or load_sound('chefe.mp3', 0.5)
    movement_sound = load_sound('movimento.wav') or load_sound('movimento.mp3', 0.1)
    
    # Verificação final se algum som foi carregado
    has_sound = any([shoot_sound, background_music, boss_spawn_sound, movement_sound])
    
    # Tocar música de fundo se disponível
    if background_music:
        background_music.play(-1)  # Loop infinito
except Exception as e:
    print(f"Erro crítico no sistema de áudio: {str(e)}")
    has_sound = False

# Classe do Jogador
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((30, 40), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, GREEN, [(15, 0), (0, 40), (30, 40)])
        self.rect = self.image.get_rect(center=(WIDTH//2, HEIGHT-50))
        self.speed = 5
        self.health = 100
        self.shield = 50
        self.heat = 0
        self.max_heat = 100
        self.cooling_rate = 1.2
        self.shoot_delay = 200  # ms
        self.last_shot = 0
        self.last_movement_sound = 0
        self.movement_sound_delay = 300  # ms
        
    def update(self):
        keys = pygame.key.get_pressed()
        is_moving = False
        
        # Movimento
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
            
        # Tocar som de movimento
        if has_sound and is_moving and movement_sound:
            now = pygame.time.get_ticks()
            if now - self.last_movement_sound > self.movement_sound_delay:
                movement_sound.play()
                self.last_movement_sound = now
        
        # Resfriamento
        self.heat = max(0, self.heat - self.cooling_rate)
        
    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay and self.heat < self.max_heat:
            self.last_shot = now
            self.heat += 10
            bullet = Bullet(self.rect.centerx, self.rect.top)
            all_sprites.add(bullet)
            bullets.add(bullet)
            if has_sound and shoot_sound:
                shoot_sound.play()
            return True
        return False
        
    def take_damage(self, amount):
        if self.shield > 0:
            self.shield = max(0, self.shield - amount)
        else:
            self.health = max(0, self.health - amount)
            if self.health <= 0:
                return True
        return False

# Classe dos Projéteis
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

# Classe dos Inimigos
class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(self.image, RED, (15, 15), 15)
        self.rect = self.image.get_rect(center=(random.randint(20, WIDTH-20), -20))
        self.speed = random.randint(1, 4)
        self.health = 1
        
    def update(self):
        self.rect.y += self.speed
        if self.rect.top > HEIGHT:
            self.kill()
            
    def take_damage(self):
        self.health -= 1
        if self.health <= 0:
            self.kill()
            return True
        return False

# Classe dos Asteroides
class Asteroid(Enemy):
    def __init__(self, size="large"):
        super().__init__()
        self.size = size
        sizes = {"large": 40, "medium": 25, "small": 15}
        self.image = pygame.Surface((sizes[size], sizes[size]), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (150, 150, 150), (sizes[size]//2, sizes[size]//2), sizes[size]//2)
        self.rect = self.image.get_rect(center=(random.randint(20, WIDTH-20), -20))
        self.speed = random.randint(1, 3)
        self.health = {"large": 3, "medium": 2, "small": 1}[size]
        
    def take_damage(self):
        self.health -= 1
        if self.health <= 0:
            if self.size != "small":
                new_size = "medium" if self.size == "large" else "small"
                for _ in range(2):
                    asteroid = Asteroid(new_size)
                    asteroid.rect.center = self.rect.center
                    all_sprites.add(asteroid)
                    enemies.add(asteroid)
            self.kill()
            return True
        return False

# Classe do Boss
class Boss(Enemy):
    def __init__(self):
        super().__init__()
        size = 60
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, PURPLE, [
            (size//2, 0), 
            (size, size//3),
            (size, 2*size//3),
            (size//2, size),
            (0, 2*size//3),
            (0, size//3)
        ])
        self.rect = self.image.get_rect(center=(WIDTH//2, -60))
        self.speed = 2
        self.health = 15
        self.last_shot = 0
        self.shoot_delay = 1500  # ms
        
    def update(self):
        self.rect.y += self.speed
        if self.rect.top > HEIGHT:
            self.kill()
        
        # Tiro do boss
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay:
            self.last_shot = now
            for angle in range(0, 360, 45):
                bullet = EnemyBullet(self.rect.centerx, self.rect.centery, angle)
                all_sprites.add(bullet)
                enemy_bullets.add(bullet)

# Classe dos Projéteis do Boss
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

# Grupos de sprites
all_sprites = pygame.sprite.Group()
enemies = pygame.sprite.Group()
bullets = pygame.sprite.Group()
enemy_bullets = pygame.sprite.Group()

# Cria o jogador
player = Player()
all_sprites.add(player)

# Variáveis do jogo
score = 0
high_score = 0
wave = 1
enemy_spawn_timer = 0
enemy_spawn_interval = 1000  # ms
last_enemy_spawn = 0
game_over = False
font = pygame.font.Font(None, 36)
splash_time = pygame.time.get_ticks()

# Carregar high score
try:
    with open('highscore.dat', 'rb') as f:
        high_score = int.from_bytes(f.read(), 'big')
except:
    high_score = 0

# Função para spawnar inimigos
def spawn_enemy():
    # Chance de spawnar boss a cada 5 waves
    if wave % 5 == 0 and not any(isinstance(e, Boss) for e in enemies):
        enemy = Boss()
        if has_sound and boss_spawn_sound:
            boss_spawn_sound.play()
    else:
        enemy_type = random.choice(["enemy", "asteroid"])
        if enemy_type == "enemy":
            enemy = Enemy()
        else:
            asteroid_size = random.choice(["large", "medium", "small"])
            enemy = Asteroid(asteroid_size)
    
    all_sprites.add(enemy)
    enemies.add(enemy)

# Função para mostrar texto na tela
def draw_text(text, size, x, y, color=WHITE):
    font = pygame.font.Font(None, size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=(x, y))
    screen.blit(text_surface, text_rect)

# Função para mostrar splash screen
def show_splash_screen():
    screen.fill(BLACK)
    draw_text("ASTROSMASH", 72, WIDTH//2, HEIGHT//3)
    draw_text("MVP Edition", 36, WIDTH//2, HEIGHT//2)
    draw_text("Carregando...", 24, WIDTH//2, HEIGHT*3//4)
    pygame.display.flip()

# Loop principal do jogo
running = True
while running:
    # Mantém o loop rodando na velocidade correta
    clock.tick(FPS)
    
    # Processa eventos
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if game_state == PLAYING:
                    game_state = PAUSE
                elif game_state == PAUSE:
                    game_state = PLAYING
            if event.key == pygame.K_SPACE and game_state == PLAYING:
                player.shoot()
            if event.key == pygame.K_RETURN and game_state in [MENU, GAME_OVER, SPLASH]:
                if game_state == SPLASH and (pygame.time.get_ticks() - splash_time) < 2000:
                    continue  # Não permite pular a splash screen muito rápido
                game_state = PLAYING
                all_sprites.empty()
                enemies.empty()
                bullets.empty()
                enemy_bullets.empty()
                player = Player()
                all_sprites.add(player)
                score = 0
                wave = 1
                enemy_spawn_interval = 1000
    
    # Atualiza o jogo
    if game_state == SPLASH:
        if pygame.time.get_ticks() - splash_time > 2000:  # 2 segundos
            game_state = MENU
    
    elif game_state == PLAYING:
        # Atualiza todos os sprites
        all_sprites.update()
        
        # Spawn de inimigos
        now = pygame.time.get_ticks()
        if now - last_enemy_spawn > enemy_spawn_interval:
            last_enemy_spawn = now
            spawn_enemy()
            
            # Aumenta a dificuldade
            if random.random() < 0.1:
                enemy_spawn_interval = max(200, enemy_spawn_interval - 50)
                if enemy_spawn_interval % 500 == 0:
                    wave += 1
        
        # Colisões entre projéteis e inimigos
        hits = pygame.sprite.groupcollide(bullets, enemies, True, False)
        for bullet, enemy_list in hits.items():
            for enemy in enemy_list:
                if enemy.take_damage():
                    score += 10 * (1 if not hasattr(enemy, "size") else {"large": 3, "medium": 2, "small": 1}[enemy.size])
        
        # Colisões entre jogador e inimigos
        hits = pygame.sprite.spritecollide(player, enemies, True)
        for hit in hits:
            if player.take_damage(10):
                game_state = GAME_OVER
                if score > high_score:
                    high_score = score
                    with open('highscore.dat', 'wb') as f:
                        f.write(high_score.to_bytes(4, 'big'))
        
        # Colisões entre jogador e projéteis inimigos
        hits = pygame.sprite.spritecollide(player, enemy_bullets, True)
        for hit in hits:
            if player.take_damage(5):
                game_state = GAME_OVER
                if score > high_score:
                    high_score = score
                    with open('highscore.dat', 'wb') as f:
                        f.write(high_score.to_bytes(4, 'big'))
    
    # Desenha tudo
    screen.fill(BLACK)
    
    # Desenha estrelas de fundo dinâmicas
    for i in range(50):
        x = (pygame.time.get_ticks() // 100 + i * 100) % WIDTH
        y = (i * 20 + pygame.time.get_ticks() // 50) % HEIGHT
        brightness = min(255, 50 + abs((pygame.time.get_ticks() // 10 + i * 50) % 510 - 255))
        pygame.draw.circle(screen, (brightness, brightness, brightness), (x, y), 1)
    
    all_sprites.draw(screen)
    
    # Desenha HUD
    draw_text(f" pontuação: {score}", 30, 70, 20)
    draw_text(f"Recorde: {high_score}", 30, 70, 50)
    draw_text(f"Nível: {wave}", 30, WIDTH - 70, 20)
    
    # Barra de saúde
    pygame.draw.rect(screen, (50, 50, 50), (WIDTH - 120, 50, 104, 20))
    pygame.draw.rect(screen, RED, (WIDTH - 118, 52, player.health, 16))
    
    # Barra de escudo
    pygame.draw.rect(screen, (50, 50, 50), (WIDTH - 120, 80, 104, 10))
    pygame.draw.rect(screen, BLUE, (WIDTH - 118, 82, player.shield, 6))
    
    # Barra de heat
    pygame.draw.rect(screen, (50, 50, 50), (WIDTH//2 - 50, 10, 100, 10))
    pygame.draw.rect(screen, (min(255, player.heat * 2.55), max(0, 255 - player.heat * 2.55), 0), 
                    (WIDTH//2 - 50, 10, player.heat, 10))
    
    # Indicador de boss
    boss_active = any(isinstance(e, Boss) for e in enemies)
    if boss_active:
        draw_text("BOSS ALERT!", 40, WIDTH//2, 80, ORANGE)
    
    # Telas de menu/pause/game over/splash
    if game_state == SPLASH:
        show_splash_screen()
    
    elif game_state == MENU:
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))
        screen.blit(s, (0, 0))
        draw_text("ASTROSMASH", 64, WIDTH//2, HEIGHT//4)
        draw_text(f"Recorde: {high_score}", 36, WIDTH//2, HEIGHT//3)
        draw_text("Pressione ENTER para Jogar", 36, WIDTH//2, HEIGHT//2)
        draw_text("Setas para mover | Espaço para atirar", 24, WIDTH//2, HEIGHT*3//4)
        draw_text("ESC para pausar", 24, WIDTH//2, HEIGHT*3//4 + 30)
    
    elif game_state == PAUSE:
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))
        screen.blit(s, (0, 0))
        draw_text("PAUSADO", 64, WIDTH//2, HEIGHT//2)
        draw_text("Pressione ESC para continuar", 24, WIDTH//2, HEIGHT//2 + 50)
    
    elif game_state == GAME_OVER:
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))
        screen.blit(s, (0, 0))
        draw_text("FIM DE JOGO", 64, WIDTH//2, HEIGHT//2 - 50)
        draw_text(f"Pontuação: {score}", 36, WIDTH//2, HEIGHT//2)
        draw_text(f"Recorde: {high_score}", 36, WIDTH//2, HEIGHT//2 + 30)
        draw_text("Pressione ENTER para recomeçar", 24, WIDTH//2, HEIGHT//2 + 80)
    
    # Atualiza a tela
    pygame.display.flip()

# Encerrar música ao sair
if has_sound and background_music:
    background_music.stop()
pygame.quit()
sys.exit()