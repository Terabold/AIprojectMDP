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
    calculate_ui_constants, scale_font
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

class LevelCompleteMenuScreen(MenuScreen):
    def initialize(self):
        self.title = "Level Complete!"
        self.clear_buttons()
        center_x = self.menu.display_size[0] // 2
        start_y = int(self.menu.display_size[1] * 0.4)
        
        self.create_centered_button_list(
            ['Next Map', 'Play Again', 'Main Menu'],
            [self.menu.load_next_map, self.menu.reset, self.menu.return_to_main],
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
        self.level_complete_menu = LevelCompleteMenuScreen(self, "Level Complete!")
        self.congratulations_menu = CongratulationsScreen(self, "Congratulations!")
        self.active_menu = None
    
    def resume_game(self):
        self.environment.menu = False
        self.active_menu = None
    
    def reset(self):
        self.environment.reset()
    
    def return_to_main(self):
        self.environment.return_to_main()
    
    def restart_game(self):
        self.environment.restart_game()
    
    def show_pause_menu(self):
        self.active_menu = self.pause_menu
        self.pause_menu.enable()
        self.level_complete_menu.disable()
        self.congratulations_menu.disable()
    
    def show_level_complete_menu(self):
        self.active_menu = self.level_complete_menu
        self.pause_menu.disable()
        self.level_complete_menu.enable()
        self.congratulations_menu.disable()
    
    def show_congratulations_menu(self):
        self.active_menu = self.congratulations_menu
        self.pause_menu.disable()
        self.level_complete_menu.disable()
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
        
        # Adjust sound volumes for AI mode
        if ai_train_mode:
            for sound_list in self.sfx.values():
                for sound in sound_list:
                    sound.set_volume(0)

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
        else:
            self.input_handler = None
            self.game_menu = None

    def update_timer(self):
        # Start timer on first movement
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
        # Skip timer rendering in AI mode
        if self.ai_train_mode or not self.timer_font:
            return
            
        timer_pos = (25, 10)
        display_time = self.timer.final_time if not self.timer.is_running else self.timer.current_time
        time_str = self.timer.format_time(display_time)
        timer_text = self.timer_font.render(time_str, True, (255, 255, 255))
        
        # Simple shadow effect
        shadow_text = self.timer_font.render(time_str, True, (0, 0, 0))
        self.display.blit(shadow_text, (timer_pos[0] + 2, timer_pos[1] + 2))
        self.display.blit(timer_text, timer_pos)

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
    
    def return_to_main(self):
        self.reset()
        game_state_manager.returnToPrevState()

    def is_last_map(self):
        current_map = game_state_manager.selected_map
        current_index = int(os.path.basename(current_map).split('.')[0])
        
        maps_folder = os.path.join('data', 'maps')
        map_files = [f for f in os.listdir(maps_folder) if f.endswith('.json')]
        
        return current_index < len(map_files) - 1

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
        # Skip input processing in AI mode
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
                
        self.keys, self.buffer_times = self.input_handler.process_events(events, self.menu)
    
    def update(self, dt):
        self.update_timer()
        
        # Update animations (essential for gameplay logic)
        self.assets['finish'].update()

        self.stars.update(dt)
        
        if self.player.death:
            self.countframes += 1
            if not self.death_sound_played:
                if not self.ai_train_mode:  # Only play sound for human players
                    self.sfx['death'].play()
                self.death_sound_played = True
            
            reset_frames = 0 if self.ai_train_mode else 120
            if self.countframes >= reset_frames:
                self.reset()
                return True  
        
        elif self.player.finishLevel:
            self.countframes += 1
            if not self.finish_sound_played:
                if not self.ai_train_mode:  # Only play sound for human players
                    self.sfx['finish'].play()
                self.finish_sound_played = True
            
            # Handle level completion
            completion_frames = 30 if self.ai_train_mode else 90
            if self.countframes >= completion_frames:
                if self.ai_train_mode:
                    # Auto-restart for AI training
                    self.reset()
                    return True  # Signal episode ended for AI
                else:
                    self.menu = True
                    if self.is_last_map():
                        self.game_menu.show_level_complete_menu()
                    else:
                        self.game_menu.show_congratulations_menu()
            
        if not self.menu:
            self.player.update(self.tilemap, self.keys, self.countframes)
            
            # Only update camera smoothly for human players
            if not self.ai_train_mode:
                update_camera_smooth(self.player, self.scroll, self.display.get_width(), self.display.get_height())
            else:
                # Simple camera following for AI (less computation)
                player_rect = self.player.rect()
                self.scroll[0] = player_rect.centerx - self.display.get_width() // 2
                self.scroll[1] = player_rect.centery - self.display.get_height() // 2
                
            self.render_scroll = (int(self.scroll[0]), int(self.scroll[1]))
        
        return False  # Episode continues

    def render(self):
        self.display.fill((8, 10, 38))
    
        if self.stars:
            self.stars.render(self.display, offset=self.render_scroll)

        # Always render player and tilemap (needed for collision detection)
        self.tilemap.render(self.display, offset=self.render_scroll)
        self.player.render(self.display, offset=self.render_scroll)

        # Render UI only for human players
        if not self.ai_train_mode:
            self.render_timer()

            if self.debug_mode and not self.menu:
                self.debug_render()
            
            if self.menu:
                # Update button hover states
                mouse_pos = pygame.mouse.get_pos()
                if self.game_menu.active_menu:
                    for button in self.game_menu.active_menu.buttons:
                        button.selected = button.is_hovered(mouse_pos)
                        
                self.game_menu.draw(self.display)

    def process_menu_events(self, events):
        # Skip menu processing in AI mode
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
            
            self.game_menu.update(events)

    def debug_render(self):
        # Skip debug rendering in AI mode
        if self.ai_train_mode:
            return
            
        draw_debug_info(self, self.display, self.render_scroll)  
        fps = self.clock.get_fps()
        if self.fps_font:
            fps_text = self.fps_font.render(f"FPS: {int(fps)}", True, (255, 255, 0))
            self.display.blit(fps_text, (10, 80))
    
    def get_state(self):
        """Return game state for AI training"""
        if self.ai_train_mode:
            player_rect = self.player.rect()
            return {
                'player_pos': (player_rect.centerx, player_rect.centery),
                'player_vel': self.player.velocity,
                'player_grounded': self.player.grounded,
                'player_air_time': self.player.air_time,
                'physics_tiles': self.tilemap.physics_rects_around(self.player.pos),
                'interactive_tiles': self.tilemap.interactive_rects_around(self.player.pos),
                'collisions': self.player.collisions,
                'finished': self.player.finishLevel,
                'dead': self.player.death,
                'scroll': self.render_scroll  # Include camera position for spatial awareness
            }
        return None
    
    def set_action(self, action):
        """Set AI action"""
        if self.ai_train_mode:
            self.keys = action
            self.buffer_times['jump'] = min(self.buffer_times['jump'] + 1, PLAYER_BUFFER + 1) if action['jump'] else 0
    
    def get_reward(self):
        """Calculate reward for AI training"""
        if not self.ai_train_mode:
            return 0
            
        reward = 0
        
        # Death penalty
        if self.player.death:
            reward -= 100
        
        # Level completion reward
        elif self.player.finishLevel:
            reward += 1000
            # Time bonus (faster completion = higher reward)
            time_bonus = max(0, 100 - self.timer.current_time)
            reward += time_bonus
        
        # Small reward for forward progress
        else:
            # Encourage moving right (assuming levels progress rightward)
            reward += self.player.pos[0] * 0.01
            
            # Small penalty for time to encourage efficiency
            reward -= 0.1
        
        return reward
    
    def is_episode_done(self):
        """Check if episode is complete for AI training"""
        return self.player.death or self.player.finishLevel
    
    def get_action_space_size(self):
        """Return the size of the action space for AI"""
        # Actions: left, right, jump (each can be True/False)
        # This gives us 2^3 = 8 possible action combinations
        return 8
    
    def get_state_space_size(self):
        """Return the size of the state space for AI"""
        # This depends on how you structure your state representation
        # You might want to normalize and flatten the state dict
        return len(self.get_normalized_state()) if self.ai_train_mode else 0
    
    def get_normalized_state(self):
        """Get normalized state as a flat array for AI training"""
        if not self.ai_train_mode:
            return []
            
        state = self.get_state()
        if not state:
            return []
        
        # Normalize and flatten the state
        normalized = []
        
        # Player position (normalized to screen/level size)
        normalized.extend([
            state['player_pos'][0] / 1000,  # Adjust based on your level width
            state['player_pos'][1] / 1000   # Adjust based on your level height
        ])
        
        # Player velocity (normalized)
        normalized.extend([
            max(-1, min(1, state['player_vel'][0] / 10)),  # Adjust max velocity
            max(-1, min(1, state['player_vel'][1] / 10))
        ])
        
        # Player state flags
        normalized.extend([
            1.0 if state['player_grounded'] else 0.0,
            min(1.0, state['player_air_time'] / 60),  # Normalize air time
        ])
        
        # Collision flags  
        collisions = state['collisions']
        normalized.extend([
            1.0 if collisions.get('top', False) else 0.0,
            1.0 if collisions.get('bottom', False) else 0.0,
            1.0 if collisions.get('left', False) else 0.0,
            1.0 if collisions.get('right', False) else 0.0,
        ])
        
        # Game state flags
        normalized.extend([
            1.0 if state['finished'] else 0.0,
            1.0 if state['dead'] else 0.0,
        ])
        
        return normalized