from scripts.utils import load_images, load_sounds, Animation, load_sound
from scripts.constants import PLAYERS_IMAGE_SIZE,IMGSCALE, FINISHSCALE
import pygame

class AssetManager:
    _instance = None
    _assets_loaded = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._assets_loaded:
            self.assets = {}
            self.rotated_cache = {}
            self.load_all_assets()
            AssetManager._assets_loaded = True
    
    def load_all_assets(self):      
        self.assets = {          
            'decor': load_images('tiles/decor', scale=IMGSCALE),
            'grass': load_images('tiles/grass', scale=IMGSCALE),
            'stone': load_images('tiles/stone', scale=IMGSCALE),
            'pinkrock': load_images('tiles/pinkrock', scale=IMGSCALE),
            'spawners': load_images('tiles/spawners', scale=IMGSCALE),
            'spikes': load_images('tiles/spikes', scale=IMGSCALE),
            'finish': load_images('tiles/finish', scale=FINISHSCALE),
            'finishanimation': Animation(load_images('tiles/finish', scale=FINISHSCALE), img_dur=5, loop=True),
            'kill': load_images('tiles/kill', scale=IMGSCALE),
            'player/finish': Animation(load_images('player/finish', scale=PLAYERS_IMAGE_SIZE), img_dur=10, loop=False),
            'player/run': Animation(load_images('player/run', scale=PLAYERS_IMAGE_SIZE), img_dur=5),
            'player/idle': Animation(load_images('player/idle', scale=PLAYERS_IMAGE_SIZE), img_dur=25),
            'player/wallslide': Animation(load_images('player/wallslide', scale=PLAYERS_IMAGE_SIZE), loop=False),
            'player/wallcollide': Animation(load_images('player/wallcollide', scale=PLAYERS_IMAGE_SIZE), loop=False),
            'player/jump_anticipation': Animation(
                load_images('player/jump_anticipation', scale=PLAYERS_IMAGE_SIZE),
                img_dur=2, loop=False  
            ),
            'player/jump_peak': Animation(
                load_images('player/jump_peak', scale=PLAYERS_IMAGE_SIZE),
                img_dur=6, loop=False
            ),
            'player/jump_rising': Animation(
                load_images('player/jump_rising', scale=PLAYERS_IMAGE_SIZE),  
                img_dur=8, loop=False
            ),
            'player/jump_landing': Animation(
                load_images('player/jump_land', scale=PLAYERS_IMAGE_SIZE),
                img_dur=10, loop=False 
            ),
            'player/jump_falling': Animation(
                load_images('player/jump_falling', scale=PLAYERS_IMAGE_SIZE),
                img_dur=4, loop=False 
            ),
            'player/death': Animation(load_images('player/death', scale=(PLAYERS_IMAGE_SIZE[0]*4, PLAYERS_IMAGE_SIZE[1]*4)), img_dur=4, loop=False),
        }
        
        self.sfx = {
            'land': load_sounds('land', volume=0.04),
            'death': load_sounds('death', volume=0.01),
            'collide': load_sound('wallcollide/grab.ogg', volume=0.01),
            'finish': load_sounds('level_complete', volume=0.1),
            'music': load_sound('music/music.ogg', volume=0.1),
            'jump': load_sound('jump/jump.ogg', volume=0.01),
            'wall_jump_left': load_sound('jump/wall_jump_left.ogg', volume=0.01),
            'wall_jump_right': load_sound('jump/wall_jump_right.ogg', volume=0.01)  
        }

    def get_rotated_image(self, tile_type, variant, rotation):
        key = (tile_type, variant, rotation)  
        
        if key not in self.rotated_cache:
            original = self.assets[tile_type][variant]
            self.rotated_cache[key] = pygame.transform.rotate(original, rotation)
        
        return self.rotated_cache[key]
    