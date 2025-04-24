import pygame
import os
from pygame.math import Vector2

class AudioManager:
    def __init__(self):
        pygame.mixer.init()
        self.sounds = {}
        self.has_sound = True
        
    def load_sound(self, name, path):
        try:
            if os.path.exists(path):
                self.sounds[name] = pygame.mixer.Sound(path)
                return True
            return False
        except Exception as e:
            print(f"Erro ao carregar som {name}: {str(e)}")
            self.has_sound = False
            return False
    
    def play_sound(self, name):
        if self.has_sound and name in self.sounds:
            try:
                self.sounds[name].play()
            except:
                self.has_sound = False
    
    def play_music(self, name):
        if self.has_sound and name in self.sounds:
            try:
                self.sounds[name].play(loops=-1)
            except:
                self.has_sound = False
    
    def stop_music(self):
        pygame.mixer.music.stop()