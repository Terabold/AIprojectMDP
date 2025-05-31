import pygame
import os
from scripts.GameManager import game_state_manager
from scripts.constants import *
from scripts.player import Player
from scripts.humanagent import InputHandler
from scripts.tilemap import Tilemap
from scripts.GameTimer import GameTimer
from scripts.utils import (
    load_images, Animation, 
    draw_debug_info, update_camera_smooth, MenuScreen,
    calculate_ui_constants, scale_font, get_distance_to_finish
)

class PauseMenuScreen(MenuScreen):
    def initialize(self):
        self.title = "Game Paused"
        self.clear_buttons()
        center_x = self.menu.display_size[0] // 2
        start_y = int(self.menu.display_size[1] * 0.4)
        
        self.create_centered_button_list(
            ['Resume Game', 'Restart Level', 'Main Menu'],
            [self.menu.resume_game, self.menu.reset, self.menu.return_to_main],
            center_x, start_y
        )

class CongratulationsScreen(MenuScreen):
    def initialize(self):
        self.title = "Congratulations!"
        self.clear_buttons()
        center_x = self.menu.display_size[0] // 2
        start_y = int(self.menu.display_size[1] * 0.4)
        
        self.create_centered_button_list(
            ['Restart Game', 'Main Menu'],
            [self.menu.restart_game, self.menu.return_to_main],
            center_x, start_y
        )

class GameMenu:
    def __init__(self, environment):
        self.environment = environment
        self.screen = environment.display
        self.display_size = DISPLAY_SIZE
        
        # Get UI constants based on display size
        self.UI_CONSTANTS = calculate_ui_constants(self.display_size)
        
        # Initialize menu screens
        self.pause_menu = PauseMenuScreen(self, "Game Paused")
        self.congratulations_menu = CongratulationsScreen(self, "Congratulations!")
        self.active_menu = None
    
    def resume_game(self):
        self.environment.menu = False
        self.active_menu = None
        self.environment.resume_music()
    
    def reset(self):
        self.environment.reset()

    def return_to_main(self):
        self.environment.return_to_main()
    
    def restart_game(self):
        self.environment.restart_game()
    
    def show_pause_menu(self):
        self.active_menu = self.pause_menu
        self.pause_menu.enable()
        self.congratulations_menu.disable()
        # Pause music when showing pause menu
        self.environment.pause_music()
    
    def show_congratulations_menu(self):
        self.active_menu = self.congratulations_menu
        self.pause_menu.disable()
        self.congratulations_menu.enable()

    def load_next_map(self):
        current_map = game_state_manager.selected_map
        if current_map:
            maps_folder = os.path.join('data', 'maps')
            map_files = sorted([f for f in os.listdir(maps_folder) if f.endswith('.json')])
            current_index = int(os.path.basename(current_map).split('.')[0])
            
            if f'{current_index}.json' in map_files and current_index < len(map_files) - 1:
                self.environment.load_map_id(current_index + 1)
            else:
                self.reset()
        else:
            self.reset()
    
    def update(self, events):
        if self.active_menu:
            self.active_menu.update(events)
    
    def draw(self, surface):
        if self.active_menu:
            # Semi-transparent overlay
            overlay = pygame.Surface(self.display_size, pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 175))
            surface.blit(overlay, (0, 0))
            self.active_menu.draw(surface)

from scripts.assets import AssetManager
from scripts.stars import Stars

class Environment:
    def __init__(self, display, clock, ai_train_mode=False):
        self.player_type = game_state_manager.player_type
        self.ai_train_mode = ai_train_mode if not self.player_type == 1 else True
        self.display = display
        self.clock = clock
        self.menu = False
        
        # Game state variables
        self.death_sound_played = False
        self.finish_sound_played = False
        self.countframes = 0
        self.debug_mode = False
        self.movement_started = False
        self.scroll = [0, 0]
        self.render_scroll = [0, 0]
        self.rotated_assets = {}
        
        # Music state variables
        self.music_playing = False
        self.music_paused = False

        # Initialize fonts only if not in AI mode
        if not self.ai_train_mode:
            pygame.font.init()
            self.fps_font = pygame.font.Font(FONT, scale_font(36, DISPLAY_SIZE))
            self.timer_font = pygame.font.Font(FONT, scale_font(24, DISPLAY_SIZE))
        else:
            self.fps_font = None
            self.timer_font = None

        # Initialize components
        self.tilemap = Tilemap(self, tile_size=TILE_SIZE)
        self.timer = GameTimer()
        self.asset_manager = AssetManager()
        self.assets = self.asset_manager.assets
        self.sfx = self.asset_manager.sfx

        if not self.ai_train_mode:
            star_images = load_images('stars', scale=IMGSCALE)
            self.stars = Stars(star_images, count=25)
        else:
            self.stars = None

        self.load_current_map()
        
        # Only initialize input handler and menu for human players
        if not self.ai_train_mode:
            self.input_handler = InputHandler()
            self.game_menu = GameMenu(self)
            self.start_music()
        else:
            self.input_handler = None
            self.game_menu = None

    def start_music(self):      
        if not self.ai_train_mode and not self.music_playing:
            pygame.mixer.music.load(MUSIC_PATH)
            pygame.mixer.music.set_volume(MUSIC_VOLUME)
            pygame.mixer.music.play(-1)  # Loop indefinitely
            self.music_playing = True
            self.music_paused = False
           
    def play_music(self):     
        self.start_music()

    def pause_music(self):
        if not self.ai_train_mode and self.music_playing and not self.music_paused:
            pygame.mixer.music.pause()
            self.music_paused = True
                               
    def resume_music(self):     
        if not self.ai_train_mode and self.music_playing and self.music_paused:
            pygame.mixer.music.unpause()
            self.music_paused = False

    def stop_music(self):
        if not self.ai_train_mode and self.music_playing:
            pygame.mixer.music.stop()
            self.music_playing = False
            self.music_paused = False

    def update_timer(self):
        # Start timer and music on first movement
        if not self.movement_started and (self.keys['left'] or self.keys['right'] or self.keys['jump']):
            self.movement_started = True
            self.timer.start()
        
        # Handle timer pausing (skip in AI mode)
        if not self.ai_train_mode:
            if self.menu and not self.timer.is_paused:
                self.timer.pause()
            elif not self.menu and self.timer.is_paused and not self.player.death and not self.player.finishLevel:
                self.timer.resume()
        
        # Stop timer on level completion
        if self.player.finishLevel and self.timer.is_running:
            self.timer.stop()
        
        self.timer.update()
    
    def render_timer(self):
        if self.ai_train_mode or not self.timer_font:
            return

        pos = (25, 10)
        time_str = self.timer.get_formatted_time()

        # Render once
        rendered_text = self.timer_font.render(time_str, True, (255, 255, 255))
        shadow = self.timer_font.render(time_str, True, (0, 0, 0))

        self.display.blit(shadow, (pos[0] + 2, pos[1] + 2))
        self.display.blit(rendered_text, pos)

    def reset_timer(self):
        self.timer.reset()
        self.movement_started = False

    def load_current_map(self):
        map_path = game_state_manager.selected_map
        self.tilemap.load(map_path)
        
        # Only reset animations that need it
        finish_scale = (self.tilemap.tile_size, self.tilemap.tile_size * 2)
        self.assets['finish'] = Animation(
            load_images('tiles/finish', scale=finish_scale), 
            img_dur=5, loop=True
        )
        
        # Setup player spawn
        self.pos = self.tilemap.extract([(SPAWNER, 0), (SPAWNER, 1)])
        self.default_pos = self.pos[0]['pos'].copy() if self.pos else [10, 10]
        self.player = Player(self, self.default_pos.copy(), (PLAYERS_SIZE[0], PLAYERS_SIZE[1]), self.sfx)
        
        self.center_scroll_on_player()
        self.keys = {'left': False, 'right': False, 'jump': False}
        self.buffer_times = {'jump': 0}
    
    def center_scroll_on_player(self):
        player_rect = self.player.rect()
        self.scroll[0] = player_rect.centerx - self.display.get_width() // 2
        self.scroll[1] = player_rect.centery - self.display.get_height() // 2
        self.render_scroll = (int(self.scroll[0]), int(self.scroll[1]))
    
    def reset(self):
        # Reset all state variables
        self.death_sound_played = False
        self.finish_sound_played = False
        self.countframes = 0
        self.menu = False
        self.debug_mode = False
        
        # Reset player and input
        self.player.reset()
        self.player.pos = self.default_pos.copy()
        self.keys = {'left': False, 'right': False, 'jump': False}
        self.buffer_times = {'jump': 0}
        
        # Only reset input handler for human players
        if not self.ai_train_mode:
            self.input_handler = InputHandler()
        
        # Reset timer and camera
        self.reset_timer()
        self.center_scroll_on_player()
        
        # Resume music if it was paused (but don't restart if it was stopped)
        if not self.ai_train_mode and self.music_paused:
            self.resume_music()

    def restart_game(self):
        self.load_map_id(0)

    def load_map_id(self, map_id):
        next_map = f'data/maps/{map_id}.json'
        game_state_manager.selected_map = next_map
        self.reset()
        self.tilemap.load(next_map)
        
        # Reset the finish animation
        self.assets['finish'] = Animation(load_images('tiles/finish', scale=FINISHSCALE), img_dur=5, loop=True)
        
        # Update spawn position
        self.pos = self.tilemap.extract([(SPAWNER, 0), (SPAWNER, 1)])
        self.default_pos = self.pos[0]['pos'].copy() if self.pos else [10, 10]
        self.player.pos = self.default_pos.copy()
        
        self.reset_timer()
        self.center_scroll_on_player()
        self.menu = False
        
        # Ensure music is playing when loading a new map (if not in AI mode)
        if not self.ai_train_mode and not self.music_playing:
            self.start_music()
    
    def return_to_main(self):
        self.stop_music()  # Stop music when returning to main menu
        self.reset()
        game_state_manager.returnToPrevState()

    def is_last_map(self):
        current_map = game_state_manager.selected_map
        current_index = int(os.path.basename(current_map).split('.')[0])
        
        maps_folder = os.path.join('data', 'maps')
        map_files = [f for f in os.listdir(maps_folder) if f.endswith('.json')]
        
        # Return True if this is the LAST map (no more maps after this one)
        return current_index >= len(map_files) - 1

    def load_next_map(self):
        current_map = game_state_manager.selected_map
        if current_map:
            maps_folder = os.path.join('data', 'maps')
            map_files = sorted([f for f in os.listdir(maps_folder) if f.endswith('.json')])
            current_index = int(os.path.basename(current_map).split('.')[0])
            
            if f'{current_index}.json' in map_files and current_index < len(map_files) - 1:
                self.load_map_id(current_index + 1)
            else:
                self.reset()
        else:
            self.reset()
    
    def process_human_input(self, events):
        if self.ai_train_mode:
            return
            
        # Handle escape key
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if not self.menu and not self.player.death and not self.player.finishLevel:
                    self.menu = True
                    self.game_menu.show_pause_menu()
                elif self.menu and not self.player.death and not self.player.finishLevel:
                    self.menu = False
                    self.game_menu.active_menu = None
                    self.resume_music()  # Resume music when closing pause menu
                
        self.keys, self.buffer_times = self.input_handler.process_events(events, self.menu)
    
    def update(self, dt):
        self.update_timer()
        
        self.assets['finish'].update()

        if self.stars:
            self.stars.update(dt)
        
        if self.player.death:
            self.countframes += 1
            if not self.death_sound_played:
                if not self.ai_train_mode:  
                    self.sfx['death'].play()
                self.death_sound_played = True
            
            reset_frames = 0 if self.ai_train_mode else 90
            if self.countframes >= reset_frames:
                self.reset()
                return True  
        
        elif self.player.finishLevel:
            self.countframes += 1
            if not self.finish_sound_played:
                if not self.ai_train_mode:  
                    self.sfx['finish'].play()
                self.finish_sound_played = True
            
            completion_frames = 30 if self.ai_train_mode else 90
            if self.countframes >= completion_frames:
                if self.ai_train_mode:
                    if self.is_last_map():
                        self.load_map_id(0) 
                    else:
                        self.load_next_map()  
                    return True  
                else:
                    if not self.is_last_map():
                        self.load_next_map()
                    else:
                        self.menu = True
                        self.game_menu.show_congratulations_menu()
        
        if not self.menu:
            self.player.update(self.tilemap, self.keys, self.countframes)
            
            if not self.ai_train_mode:
                update_camera_smooth(self.player, self.scroll, self.display.get_width(), self.display.get_height())
            else:
                player_rect = self.player.rect()
                self.scroll[0] = player_rect.centerx - self.display.get_width() // 2
                self.scroll[1] = player_rect.centery - self.display.get_height() // 2
                
            self.render_scroll = (int(self.scroll[0]), int(self.scroll[1]))
    
        return False

    def render(self):
        self.display.fill((8, 10, 38))

        if self.ai_train_mode:
            distance, player_pos, finish_pos = get_distance_to_finish(self)
            self.tilemap.render_ai(self.display, offset=self.render_scroll, distance=distance, player_pos=player_pos, finish_pos=finish_pos)
            self.player.render_ai(self.display, offset=self.render_scroll)
        else:
            if self.stars:
                self.stars.render(self.display, offset=self.render_scroll)
            self.tilemap.render(surf=self.display, offset=self.scroll)
            self.player.render(self.display, offset=self.render_scroll) 

            fps = self.clock.get_fps()
            fps_text = self.fps_font.render(f"{int(fps)}", True, (200, 120, 255))
            self.display.blit(fps_text, (DISPLAY_SIZE[0]*0.95, 10))
            self.render_timer()
            

            if self.debug_mode and not self.menu:
                self.debug_render()
            
            if self.menu:
                mouse_pos = pygame.mouse.get_pos()
                if self.game_menu.active_menu:
                    for button in self.game_menu.active_menu.buttons:
                        button.selected = button.is_hovered(mouse_pos)
                        
                self.game_menu.draw(self.display)

    def process_menu_events(self, events):
        if self.ai_train_mode:
            return
            
        if self.menu:
            for event in events:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    if self.player.finishLevel or self.player.death:
                        self.return_to_main()
                    else:
                        self.menu = False
                        self.game_menu.active_menu = None
                        self.resume_music() 
            
            self.game_menu.update(events)

    def debug_render(self):
        if self.ai_train_mode:
            return
            
        draw_debug_info(self, self.display, self.render_scroll)  

        
    def state(self):     
        state_data = []
        
        # === PLAYER STATE (8 values) ===
        player_rect = self.player.rect()
        
        # Player position (normalized to map bounds)
        # Assuming maps are roughly 0-1000 pixels in each direction
        norm_x = player_rect.centerx / 1980.0  # Adjusted for larger maps
        norm_y = player_rect.centery / 1080.0
        state_data.extend([norm_x, norm_y])
        
        # Player velocity (normalized)
        # Max speeds from constants: MAX_X_SPEED, MAX_Y_SPEED
        norm_vel_x = self.player.velocity[0] / MAX_X_SPEED
        norm_vel_y = self.player.velocity[1] / MAX_Y_SPEED
        state_data.extend([norm_vel_x, norm_vel_y])
        
        # Player state flags (binary)
        state_data.extend([
            1.0 if self.player.grounded else 0.0,
            1.0 if self.player.facing_right else 0.0,
            1.0 if self.player.jump_available else 0.0,
            1.0 if (self.player.collisions['left'] or self.player.collisions['right']) else 0.0
        ])
        
        # === FINISH LINE INFORMATION (3 values) ===
        distance, player_pos, finish_pos = get_distance_to_finish(self)
        
        if finish_pos is not None:
            # Direction to finish (normalized)
            dx = finish_pos[0] - player_pos[0]
            dy = finish_pos[1] - player_pos[1]
            
            # Normalize distance (assuming max distance of ~100 tiles)
            norm_distance = min(distance / 100.0, 1.0) if distance else 0.0
            
            # Direction vector (normalized)
            max_dist = max(abs(dx), abs(dy), 1)  # Avoid division by zero
            norm_dx = dx / max_dist
            norm_dy = dy / max_dist
            
            state_data.extend([norm_distance, norm_dx, norm_dy])
        else:
            state_data.extend([1.0, 0.0, 0.0])  # No finish found
        
        # === SURROUNDING TILES (36 values: 6x6 grid) ===
        # Check tiles in a 6x6 grid around player (3 tiles in each direction)
        tile_size = self.tilemap.tile_size
        player_tile_x = int(player_rect.centerx // tile_size)
        player_tile_y = int(player_rect.centery // tile_size)
        
        # Tile type encoding (one-hot style but simplified)
        # 0: empty/air, 1: solid/platform, 2: spikes/danger, 3: finish
        for dy in range(-3, 3):  # 6 rows
            for dx in range(-3, 3):  # 6 columns
                check_x = player_tile_x + dx
                check_y = player_tile_y + dy
                loc = f"{check_x};{check_y}"
                
                tile_value = 0.0  # Default: empty
                
                if loc in self.tilemap.tilemap:
                    tile = self.tilemap.tilemap[loc]
                    tile_type = tile['type'].split()[0]
                    
                    if tile_type in PHYSICS_TILES:
                        tile_value = 0.33  # Solid platform
                    elif tile_type in ['spikes', 'kill']:
                        tile_value = 0.66  # Dangerous
                    elif tile_type == 'finish':
                        tile_value = 1.0   # Goal
                
                # Also check offgrid tiles in this area
                for offgrid_tile in self.tilemap.offgrid_tiles:
                    tile_x = int(offgrid_tile['pos'][0])
                    tile_y = int(offgrid_tile['pos'][1])
                    if tile_x == check_x and tile_y == check_y:
                        tile_type = offgrid_tile['type'].split()[0]
                        if tile_type in ['spikes', 'kill']:
                            tile_value = 0.66
                        break
                
                state_data.append(tile_value)
        
        # === DANGER PROXIMITY (3 values) ===
        # Check for immediate dangers around player
        interactive_tiles = self.tilemap.interactive_rects_around(self.player.pos)
        
        danger_left = 0.0
        danger_right = 0.0 
        danger_below = 0.0
        
        for rect, tile_info in interactive_tiles:
            if tile_info[0] in ['spikes', 'kill']:
                # Check relative position to player
                if rect.centerx < player_rect.centerx:
                    danger_left = max(danger_left, 1.0 - abs(rect.centerx - player_rect.centerx) / (tile_size * 3))
                elif rect.centerx > player_rect.centerx:
                    danger_right = max(danger_right, 1.0 - abs(rect.centerx - player_rect.centerx) / (tile_size * 3))
                
                if rect.centery > player_rect.centery:
                    danger_below = max(danger_below, 1.0 - abs(rect.centery - player_rect.centery) / (tile_size * 3))
        
        state_data.extend([danger_left, danger_right, danger_below])
        
        # Ensure we have exactly 50 values (8 + 3 + 36 + 3 = 50)
        assert len(state_data) == 50, f"Expected 50 state values, got {len(state_data)}"
        
        # Clamp all values to [-1, 1] range for safety
        state_data = [max(-1.0, min(1.0, val)) for val in state_data]
        
        return state_data