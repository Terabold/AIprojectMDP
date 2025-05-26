import pygame
from scripts.constants import PLAYER_BUFFER
class InputHandler:
    def __init__(self):
        self.keys = {'left': False, 'right': False, 'jump': False}
        self.buffer_times = {'jump': 0}
        
    def process_events(self, events, menu_active=False):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if not menu_active:
                    if event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                        self.keys['right'] = True
                    if event.key == pygame.K_a or event.key == pygame.K_LEFT:
                        self.keys['left'] = True
                    if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                        self.keys['jump'] = True
                        
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                    self.keys['right'] = False
                if event.key == pygame.K_a or event.key == pygame.K_LEFT:
                    self.keys['left'] = False
                if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                    self.keys['jump'] = False
                    self.buffer_times['jump'] = 0
        
            if self.keys['jump']:
                self.buffer_times['jump'] += 1
                if self.buffer_times['jump'] > PLAYER_BUFFER:
                    self.buffer_times['jump'] = PLAYER_BUFFER + 1
                                
        return self.keys, self.buffer_times