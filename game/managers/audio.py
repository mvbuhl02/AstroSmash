import pygame
import os
from pygame.math import Vector2

class AudioManager:
    def __init__(self):
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
        pygame.mixer.init()
        self.sounds = {}
        self.current_music = None
        self.has_sound = True

    def load_sound(self, filename, volume=1.0):
        try:
            sound_name = os.path.splitext(os.path.basename(filename))[0]
            sound = pygame.mixer.Sound(filename)
            sound.set_volume(volume)
            self.sounds[sound_name] = sound
            return True
        except Exception as e:
            print(f"Erro ao carregar {filename}: {str(e)}")
            return False

    def play_sound(self, sound_name):
        """Para efeitos sonoros (tiros, hits, etc)"""
        if sound_name in self.sounds:
            self.sounds[sound_name].play()

    def play_music(self, sound_name):
        """Para música de fundo"""
        if sound_name in self.sounds:
            self.stop_music()
            self.sounds[sound_name].play(loops=-1)
            self.current_music = sound_name

    def stop_music(self):
        """Para a música de fundo"""
        if self.current_music in self.sounds:
            self.sounds[self.current_music].stop()
            self.current_music = None

    # Método alternativo para compatibilidade
    def play(self, sound_name, loops=0):
        """Método legado - usar play_sound ou play_music no novo código"""
        if loops == -1:
            self.play_music(sound_name)
        else:
            self.play_sound(sound_name)