import pygame
from config import *

class GameState:
    def __init__(self, game):
        self.game = game
        self.screen = game.screen
        self.font = pygame.font.Font(None, 36)
        
    def handle_events(self, events):
        pass
        
    def update(self):
        pass
        
    def draw(self):
        pass
        
    def draw_text(self, text, size, x, y, color=WHITE):
        font = pygame.font.Font(None, size)
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(center=(x, y))
        self.screen.blit(text_surface, text_rect)