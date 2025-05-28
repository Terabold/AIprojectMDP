import sys
import pygame
import os
import json
from scripts.utils import load_images, load_image, find_next_numeric_filename, MenuScreen, load_sounds, render_text_with_shadow
from scripts.tilemap import Tilemap
from scripts.constants import TILE_SIZE, DISPLAY_SIZE, FPS, PHYSICS_TILES, FONT, MENUBG, calculate_ui_constants, EDITOR_SCROLL_SPEED
from scripts.GameManager import game_state_manager

class EditorMenu:
    def __init__(self, display):
        self.screen = display
        
        self.background = pygame.transform.scale(
            pygame.image.load(MENUBG).convert(), 
            DISPLAY_SIZE
        )
        
        self.UI_CONSTANTS = calculate_ui_constants(DISPLAY_SIZE)
        self.selected_map = None
        self.editor_active = False
        self.editor = None
        self.map_menu = EditorMapSelectionScreen(self)
        self.map_menu.enable()

    def _select_map(self, map_file):
        self.selected_map = map_file
        self.start_editor(map_file)

    def create_new_map(self):
        # Create a new map directly without edit page
        maps_dir = 'data/maps'
        if not os.path.exists(maps_dir):
            os.makedirs(maps_dir)
            
        # Find next available map ID
        next_filename = find_next_numeric_filename(maps_dir, extension='.json')
        new_map_path = os.path.join(maps_dir, next_filename)
        
        # Create empty map file
        empty_map_data = {
            "tilemap": {},
            "tile_size": TILE_SIZE,
            "offgrid": []
        }
        
        with open(new_map_path, 'w') as f:
            json.dump(empty_map_data, f)
        
        # Start editing the new map
        self.start_editor(next_filename)

    def start_editor(self, map_file):
        self.editor = Editor(self, map_file)  
        self.editor_active = True

    def quit_editor(self):
        # Always return to menu when quitting editor
        self.editor_active = False
        self.editor = None
        game_state_manager.setState('menu')

    def return_to_menu(self):
        self.editor_active = False
        self.editor = None
        self.map_menu = EditorMapSelectionScreen(self)
        self.map_menu.enable()

    def run(self):
        if self.editor_active:
            self.editor.run()
            return

        self.screen.blit(self.background, (0, 0))
            
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.quit_editor()

        self.map_menu.update(events)
        self.map_menu.draw(self.screen)

class EditorMapSelectionScreen(MenuScreen):
    def __init__(self, menu, title="Edit a Map"):
        super().__init__(menu, title)
        self.current_page = 0
        self.total_pages = 0
        self.map_files = []
        self.map_numbers = []

    def initialize(self):
        self.title = "Edit a Map"
        self.load_maps()
        self.create_map_buttons()
        
    def load_maps(self):
        maps_dir = 'data/maps'
        if not os.path.exists(maps_dir):
            os.makedirs(maps_dir)
            
        self.map_files = [f for f in os.listdir(maps_dir) if f.endswith('.json')]
        
        # Sort map files numerically
        def get_map_number(filename):
            try:
                return int(filename.split('.')[0])
            except ValueError:
                return float('inf')
                
        self.map_files.sort(key=get_map_number)
        
        # Fixed at 20 maps per page
        maps_per_page = 20
        self.total_pages = (len(self.map_files) + maps_per_page - 1) // maps_per_page
        
        if self.current_page >= self.total_pages:
            self.current_page = max(0, self.total_pages - 1)
        
        self.map_numbers = [str(index) for index in range(len(self.map_files))]
    
    def create_map_buttons(self):
        self.clear_buttons()
        
        # Fixed at 20 maps per page
        maps_per_page = 20
        # Calculate pagination
        start_index = self.current_page * maps_per_page
        end_index = min(start_index + maps_per_page, len(self.map_files))
        
        # Get maps for current page
        current_page_files = self.map_files[start_index:end_index]
        current_page_numbers = self.map_numbers[start_index:end_index]
        
        # Scale button width with screen size - increased for better text padding
        button_width = int(DISPLAY_SIZE[0] * 0.1)  # 10% of screen width
        padding = self.UI_CONSTANTS['BUTTON_SPACING']
        columns = self.UI_CONSTANTS['GRID_COLUMNS']
        
        grid_width = columns * (button_width + padding) - padding
        start_x = (DISPLAY_SIZE[0] - grid_width) // 2
        
        # Create actions for selecting maps
        actions = [lambda i=i: self.menu._select_map(self.map_files[start_index + i]) 
                  for i in range(len(current_page_files))]
        
        # Create map buttons - use relative positioning with larger size
        self.create_grid_buttons(
            current_page_numbers,
            actions,
            start_x,
            int(DISPLAY_SIZE[1] * 0.25),  # 25% from top
            button_width
        )
        
        # Calculate the position for navigation buttons - use relative positioning
        middle_y = DISPLAY_SIZE[1] * 0.37  # 37% down the screen
        
        # Add "Return" button - position relative to screen size
        back_x = int(DISPLAY_SIZE[0] * 0.02)  # 2% from left
        back_y = int(DISPLAY_SIZE[1] * 0.02)  # 2% from top
        back_width = int(DISPLAY_SIZE[0] * 0.08)  # 8% of screen width
        self.create_button("←", self.menu.quit_editor, back_x, back_y, back_width)
        
        # Add "New Map" button - position relative to screen size
        new_map_x = int(DISPLAY_SIZE[0] * 0.75)  # 75% from left
        new_map_y = int(DISPLAY_SIZE[1] * 0.15)  # 15% from top
        new_map_width = int(DISPLAY_SIZE[0] * 0.1)  # 10% of screen width
        self.create_button("Add", self.menu.create_new_map, new_map_x, new_map_y, new_map_width)
        
        # Previous page button
        if self.current_page > 0:
            prev_x = int(DISPLAY_SIZE[0] * 0.12)  # 12% from left
            nav_button_width = int(DISPLAY_SIZE[0] * 0.08)  # 8% of screen width
            self.create_button("◀", self.previous_page, prev_x, middle_y, nav_button_width)
        
        # Next page button
        if self.current_page < self.total_pages - 1:
            next_x = int(DISPLAY_SIZE[0] * 0.8)  # 80% from left
            nav_button_width = int(DISPLAY_SIZE[0] * 0.08)  # 8% of screen width
            self.create_button("▶", self.next_page, next_x, middle_y, nav_button_width)
        
        # Add pagination info
        if self.total_pages > 1:
            page_info = f"Page {self.current_page + 1}/{self.total_pages}"
            center_x = DISPLAY_SIZE[0] // 2
            page_y = DISPLAY_SIZE[1] * 0.7  # 70% down the screen
            page_width = int(DISPLAY_SIZE[0] * 0.25)  # 25% of screen width
            
            self.create_button(page_info, lambda: None, center_x - (page_width // 2), page_y, page_width)
    
    def next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.create_map_buttons()

    def previous_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.create_map_buttons()

class Editor:
    def __init__(self, menu, map_file=None):
        self.menu = menu
        pygame.init()
        pygame.display.set_caption('editor')
        self.display = pygame.display.set_mode(DISPLAY_SIZE)
        self.clock = pygame.time.Clock()
        
        self.zoom = 10
        self.tilemap = Tilemap(self, tile_size=TILE_SIZE, env=False)
        self.scroll = [0, 0]
        self.current_map_file = map_file
        
        self.assets = self.reload_assets()
        self.background_image = load_image('background/background.png', scale=DISPLAY_SIZE)
        self.rotated_assets = {}
        
        # Menu system
        self.menu_width = 170
        self.menu_scroll = [0, 0, 0]
        self.tile_list = list(self.assets)
        self.tile_group = 0
        self.tile_variant = 0
        self.current_rotation = 0
        self.ongrid = True
        
        self.tile_type_thumbs = self.generate_tile_type_thumbs()
        
        # Input states - simplified
        self.movement = [False] * 4
        self.clicking = False
        self.right_clicking = False
        self.shift = False
        self.ctrl = False
        
        # Save notification
        self.show_save_message = False
        self.save_message_timer = 0
        self.save_message_duration = 80
        
        # Fonts
        self.font = pygame.font.SysFont(FONT, 16)
        self.save_font = pygame.font.SysFont(FONT, 32)
        
        # Load map if provided
        if map_file:
            try:
                self.tilemap.load(os.path.join('data/maps', map_file))
            except FileNotFoundError:
                pass

    def generate_tile_type_thumbs(self):
        thumbs = {}
        for tile_type in self.tile_list:
            thumb_surf = pygame.Surface((100, 24), pygame.SRCALPHA)
            variants = self.assets[tile_type]
            
            if isinstance(variants, dict):
                variant_items = list(variants.items())[:4]
                for i, (variant_key, img) in enumerate(variant_items):
                    thumb_surf.blit(pygame.transform.scale(img, (24, 24)), (i * 24, 0))
            else:
                for i, img in enumerate(variants[:4]):
                    thumb_surf.blit(pygame.transform.scale(img, (24, 24)), (i * 24, 0))
            thumbs[tile_type] = thumb_surf
        return thumbs

    def get_rotated_image(self, tile_type, variant, rotation):
        key = f"{tile_type}_{variant}_{rotation}"
        
        if key not in self.rotated_assets:
            original = self.assets[tile_type][variant]
            self.rotated_assets[key] = pygame.transform.rotate(original, rotation)
        
        return self.rotated_assets[key]
    
    def reload_assets(self):
        IMGscale = (self.tilemap.tile_size, self.tilemap.tile_size)
        assets = {
            'decor': load_images('tiles/decor', scale=IMGscale),
            'grass': load_images('tiles/grass', scale=IMGscale),
            'pinkrock' : load_images('tiles/pinkrock', scale=IMGscale),
            'stone': load_images('tiles/stone', scale=IMGscale),
            'spawners': load_images('tiles/spawners', scale=IMGscale),
            'spikes': load_images('tiles/spikes', scale=IMGscale),
            'finish': load_images('tiles/finish', scale=(IMGscale[0], IMGscale[1]*2)),
            'kill': load_images('tiles/kill', scale=IMGscale),
        }
        self.rotated_assets = {}
        return assets
    
    def setZoom(self, zoom):
        self.zoom = int(zoom)
        new_tile_size = int(TILE_SIZE * self.zoom // 10)
        
        # Simplified zoom calculation
        center_offset_x = DISPLAY_SIZE[0] // 2
        center_offset_y = DISPLAY_SIZE[1] // 2
        
        self.scroll[0] = ((self.scroll[0] + center_offset_x) // self.tilemap.tile_size * 
                         new_tile_size - center_offset_x)
        self.scroll[1] = ((self.scroll[1] + center_offset_y) // self.tilemap.tile_size * 
                         new_tile_size - center_offset_y)
        
        self.tilemap.tile_size = new_tile_size
        self.assets = self.reload_assets()
        self.tile_type_thumbs = self.generate_tile_type_thumbs()
    
    def count_spawners(self):
        return len(self.tilemap.extract([('spawners', 0), ('spawners', 1)], keep=True))
    
    def rotate_spike_at_position(self, pos):
        tile_loc = f"{pos[0]};{pos[1]}"
        if tile_loc in self.tilemap.tilemap:
            tile = self.tilemap.tilemap[tile_loc]
            if tile['type'] == 'spikes':
                current_rot = tile.get('rotation', 0)
                new_rot = (current_rot - 90) % 360
                self.tilemap.tilemap[tile_loc]['rotation'] = new_rot

    def canPlaceTile(self, mpos):
        return mpos[0] >= self.menu_width

    def deleteGridBlock(self, tile_pos):
        tile_loc = str(tile_pos[0]) + ';' + str(tile_pos[1])
        if tile_loc in self.tilemap.tilemap:
            tile = self.tilemap.tilemap[tile_loc]
            tile_type = tile['type'].split()[0]
            
            # Handle 2-tile blocks (portal, finish)
            if tile_type in {'portal', 'finish'}:
                if tile['type'].split()[1] == 'up':
                    # Remove bottom part
                    bottom_loc = str(tile_pos[0]) + ';' + str(tile_pos[1] + 1)
                    if bottom_loc in self.tilemap.tilemap:
                        del self.tilemap.tilemap[bottom_loc]
                else:
                    # Remove top part
                    top_loc = str(tile_pos[0]) + ';' + str(tile_pos[1] - 1)
                    if top_loc in self.tilemap.tilemap:
                        del self.tilemap.tilemap[top_loc]
            
            del self.tilemap.tilemap[tile_loc]

    def placeGridBlock(self, tile_pos, tile_type):
        self.deleteGridBlock(tile_pos)
        self.tilemap.tilemap[str(tile_pos[0]) + ';' + str(tile_pos[1])] = {
            'type': tile_type, 
            'variant': self.tile_variant, 
            'pos': tile_pos
        }
    
    def handle_tile_placement(self, tile_pos, mpos):
        if not (self.clicking and self.ongrid and self.canPlaceTile(mpos)):
            return
            
        tile_type = self.tile_list[self.tile_group]
        
        # Remove existing spawners if placing new one
        if tile_type == 'spawners' and self.count_spawners() > 0:
            self.tilemap.extract([('spawners', 0), ('spawners', 1)], keep=False)
        
        # Handle 2-tile blocks
        if tile_type in {'portal', 'finish'}:
            self.placeGridBlock(tile_pos, tile_type + ' up')
            self.placeGridBlock((tile_pos[0], tile_pos[1] + 1), tile_type + ' down')
        else:
            # Handle single tiles
            tile_data = {
                'type': tile_type,
                'variant': self.tile_variant,
                'pos': tile_pos if self.ongrid else ((mpos[0] + self.scroll[0]) / self.tilemap.tile_size, 
                                                    (mpos[1] + self.scroll[1]) / self.tilemap.tile_size)
            }
            
            if tile_type == 'spikes':
                tile_data['rotation'] = self.current_rotation
            
            if self.ongrid:
                self.tilemap.tilemap[f"{tile_pos[0]};{tile_pos[1]}"] = tile_data
            elif tile_type not in PHYSICS_TILES:
                self.tilemap.offgrid_tiles.append(tile_data)
                
    def save_map(self):
        directory = 'data/maps'
        if not os.path.exists(directory):
            os.makedirs(directory)  
    
        if self.current_map_file:
            filename = os.path.basename(self.current_map_file)  
            file_path = os.path.join(directory, filename)
            self.tilemap.save(file_path)
            saved_map_name = filename
        else:
            next_filename = find_next_numeric_filename(directory, extension='.json')            
            file_path = os.path.join(directory, next_filename)
            
            self.tilemap.save(file_path)
            self.current_map_file = next_filename
            saved_map_name = next_filename
        
        self.show_save_message = True
        self.save_message_timer = 0
        self.saved_map_name = saved_map_name        
        
        if not pygame.key.get_pressed()[pygame.K_o]:
            self.menu.return_to_menu()

    def handle_tile_removal(self, tile_pos, mpos):
        if not self.right_clicking:
            return
            
        # Remove grid tile using new method
        self.deleteGridBlock(tile_pos)
        
        # Remove offgrid tiles
        for tile in self.tilemap.offgrid_tiles.copy():
            tile_img = self.assets[tile['type']][tile['variant']]
            tile_r = pygame.Rect(
                tile['pos'][0] * self.tilemap.tile_size - self.scroll[0], 
                tile['pos'][1] * self.tilemap.tile_size - self.scroll[1], 
                tile_img.get_width(), tile_img.get_height()
            )
            if tile_r.collidepoint(mpos):
                self.tilemap.offgrid_tiles.remove(tile)
    
    def draw_grid(self):
        # Simplified grid drawing
        tile_size = self.tilemap.tile_size
        
        # Vertical lines
        start_x = -self.scroll[0] % tile_size
        for x in range(start_x, DISPLAY_SIZE[0], tile_size):
            pygame.draw.line(self.display, (50, 50, 50), (x, 0), (x, DISPLAY_SIZE[1]))
            
        # Horizontal lines
        start_y = -self.scroll[1] % tile_size
        for y in range(start_y, DISPLAY_SIZE[1], tile_size):
            pygame.draw.line(self.display, (50, 50, 50), (0, y), (DISPLAY_SIZE[0], y))
    
    def handle_mouse_events(self, event, tile_pos, mpos):
        in_menu = mpos[0] < self.menu_width
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                if in_menu:
                    self.handle_menu_click(mpos)
                elif self.ctrl:
                    self.rotate_spike_at_position(tile_pos)
                else:
                    self.clicking = True
            elif event.button == 3 and not in_menu:  # Right click
                self.right_clicking = True
            elif event.button in [4, 5]:  # Scroll
                self.handle_scroll(event.button, mpos, in_menu)

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.clicking = False
            elif event.button == 3:
                self.right_clicking = False
    
    def handle_scroll(self, button, mpos, in_menu):
        scroll_up = button == 4
        
        if in_menu:
            if mpos[1] < 120:  # Tile types section
                self.menu_scroll[0] += -1 if scroll_up else 1
            else:  # Variants section
                scroll_index = 1 if self.shift else 2
                if scroll_up:
                    self.menu_scroll[scroll_index] = max(0, self.menu_scroll[scroll_index] - 1)
                else:
                    self.menu_scroll[scroll_index] += 1
        elif self.shift:
            # Change variant
            current_type = self.tile_list[self.tile_group]
            variants = self.get_variants(current_type)
            self.tile_variant = ((self.tile_variant + (-1 if scroll_up else 1)) % len(variants))
        else:
            # Change tile type
            self.tile_group = ((self.tile_group + (-1 if scroll_up else 1)) % len(self.tile_list))
            self.tile_variant = 0
            self.current_rotation = 0
    
    def get_variants(self, tile_type):
        variants = self.assets[tile_type]
        return list(variants.keys()) if isinstance(variants, dict) else list(range(len(variants)))
    
    def handle_menu_click(self, mpos):
        if mpos[1] < 120:  # Tile type selection
            for i in range(min(4, len(self.tile_list))):
                lookup_i = (self.menu_scroll[0] + i) % len(self.tile_list)
                thumb_rect = pygame.Rect(5, 5 + i * 30, 100, 24)
                
                if thumb_rect.collidepoint(mpos):
                    self.tile_group = lookup_i
                    self.tile_variant = 0
                    self.menu_scroll[1] = self.menu_scroll[2] = 0
                    break
        else:  # Variant selection
            current_type = self.tile_list[self.tile_group]
            variants = self.get_variants(current_type)
            variants_per_row = 4
            
            for y_index in range(10):
                for x_index in range(variants_per_row):
                    variant_x = x_index + self.menu_scroll[1]
                    variant_y = y_index + self.menu_scroll[2]
                    variant_index = variant_y * variants_per_row + variant_x
                    
                    if variant_index >= len(variants):
                        continue
                    
                    tile_rect = pygame.Rect(5 + x_index * 34, 125 + y_index * 34, 30, 30)
                    
                    if tile_rect.collidepoint(mpos):
                        self.tile_variant = variants[variant_index]
                        return
    
    def handle_keyboard_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a:
                self.movement[0] = True
            elif event.key == pygame.K_d:
                self.movement[1] = True
            elif event.key == pygame.K_w:
                self.movement[2] = True
            elif event.key == pygame.K_s:
                self.movement[3] = True
            elif event.key == pygame.K_g:
                self.ongrid = not self.ongrid
            elif event.key == pygame.K_t:
                self.tilemap.autotile()
            elif event.key == pygame.K_o:
                self.save_map()
            elif event.key in {pygame.K_LSHIFT, pygame.K_RSHIFT}:
                self.shift = True
            elif event.key in {pygame.K_LCTRL, pygame.K_RCTRL}:
                self.ctrl = True
            elif event.key == pygame.K_ESCAPE:
                self.menu.return_to_menu()
                return True
            elif event.key == pygame.K_r and self.tile_list[self.tile_group] == 'spikes':
                self.current_rotation = (self.current_rotation + 90) % 360
            elif event.key == pygame.K_UP:
                if self.zoom < 20:
                    self.setZoom(self.zoom + 1)
            elif event.key == pygame.K_DOWN:
                if self.zoom > 1:
                    self.setZoom(self.zoom - 1)
        
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_a:
                self.movement[0] = False
            elif event.key == pygame.K_d:
                self.movement[1] = False
            elif event.key == pygame.K_w:
                self.movement[2] = False
            elif event.key == pygame.K_s:
                self.movement[3] = False
            elif event.key in {pygame.K_LSHIFT, pygame.K_RSHIFT}:
                self.shift = False
            elif event.key in {pygame.K_LCTRL, pygame.K_RCTRL}:
                self.ctrl = False
        
        return False
        
    def update_scroll(self):
        self.scroll[0] += (self.movement[1] - self.movement[0]) * EDITOR_SCROLL_SPEED
        self.scroll[1] += (self.movement[3] - self.movement[2]) * EDITOR_SCROLL_SPEED
        return (int(self.scroll[0]), int(self.scroll[1]))
        
    def draw_save_notification(self):
        if not self.show_save_message:
            return
            
        overlay = pygame.Surface((DISPLAY_SIZE[0], 80), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        
        overlay_y = (DISPLAY_SIZE[1] - 80) // 2
        self.display.blit(overlay, (0, overlay_y))
        
        save_text = self.save_font.render(f"Map saved: {self.saved_map_name}", True, (255, 255, 255))
        text_x = (DISPLAY_SIZE[0] - save_text.get_width()) // 2
        text_y = overlay_y + (80 - save_text.get_height()) // 2
        self.display.blit(save_text, (text_x, text_y))
        
        self.save_message_timer += 1
        if self.save_message_timer >= self.save_message_duration:
            self.show_save_message = False
    
    def draw_menu(self):
        menu_surf = pygame.Surface((self.menu_width, DISPLAY_SIZE[1]), pygame.SRCALPHA)
        menu_surf.fill((0, 40, 60, 180))
        
        # Draw dividers
        pygame.draw.line(menu_surf, (0, 80, 120), (0, 120), (self.menu_width, 120))
        pygame.draw.line(menu_surf, (0, 80, 120), (self.menu_width - 1, 0), (self.menu_width - 1, DISPLAY_SIZE[1]))
        
        # Draw tile type thumbnails
        self._draw_tile_types(menu_surf)
        
        # Draw variants
        self._draw_variants(menu_surf)
        
        self.display.blit(menu_surf, (0, 0))
    
    def _draw_tile_types(self, menu_surf):
        for i in range(min(4, len(self.tile_list))):
            lookup_i = (self.menu_scroll[0] + i) % len(self.tile_list)
            tile_type = self.tile_list[lookup_i]
            thumb = self.tile_type_thumbs[tile_type]
            
            if lookup_i == self.tile_group:
                pygame.draw.rect(menu_surf, (100, 100, 255, 100), pygame.Rect(4, 4 + i * 30, 102, 26))
            
            menu_surf.blit(thumb, (5, 5 + i * 30))
            
            type_text = pygame.font.SysFont(FONT, 20).render(tile_type, True, (200, 200, 200))
            menu_surf.blit(type_text, (109, 9 + i * 30))
    
    def _draw_variants(self, menu_surf):
        current_type = self.tile_list[self.tile_group]
        variants = self.get_variants(current_type)
        variants_per_row = 4
        
        for y_index in range(10):
            for x_index in range(variants_per_row):
                variant_x = x_index + self.menu_scroll[1]
                variant_y = y_index + self.menu_scroll[2]
                variant_index = variant_y * variants_per_row + variant_x
                
                if variant_index >= len(variants):
                    continue
                
                variant = variants[variant_index]
                tile_img = self.assets[current_type][variant]
                
                if variant == self.tile_variant:
                    pygame.draw.rect(menu_surf, (255, 255, 100, 100), 
                                    pygame.Rect(4 + x_index * 34, 124 + y_index * 34, 32, 32))
                
                # Don't show rotation in menu for spikes
                display_img = (pygame.transform.scale(tile_img, (30, 30)) 
                             if current_type != 'spikes' or self.current_rotation == 0
                             else pygame.transform.scale(self.get_rotated_image(current_type, variant, 0), (30, 30)))
                
                menu_surf.blit(display_img, (5 + x_index * 34, 125 + y_index * 34))

    def draw_ui(self, current_tile_img):
        ui_x = self.menu_width + 5
        
        ui_elements = [
            f"Spawners: {self.count_spawners()}/1",
            f"Type: {self.tile_list[self.tile_group]} ({self.tile_variant})",
            f"Grid: {'On' if self.ongrid else 'Off'} (G to toggle)"
        ]
        
        for i, text in enumerate(ui_elements):
            rendered = self.font.render(text, True, (255, 255, 255))
            self.display.blit(rendered, (ui_x, 5 + i * 20))
        
        # Rotation info for spikes
        if self.tile_list[self.tile_group] == 'spikes':
            rotation_text = self.font.render(f"Rotation: {self.current_rotation}° (R to rotate)", True, (255, 255, 255))
            self.display.blit(rotation_text, (ui_x, 65))
        
        # File info
        file_text = (f"Editing: {self.current_map_file}" if self.current_map_file 
                    else "Creating new map")
        file_rendered = self.font.render(file_text, True, (255, 255, 255))
        self.display.blit(file_rendered, (ui_x, DISPLAY_SIZE[1] - 50))
        
        # Controls
        controls = self.font.render("ESC: Return to Menu | O: Save Map", True, (255, 255, 255))
        self.display.blit(controls, (ui_x, DISPLAY_SIZE[1] - 30))
        
    def run(self):
        while True:
            self.display.fill((20, 20, 20))
            
            render_scroll = self.update_scroll()
            
            # Draw grid and tilemap
            self.draw_grid()
            self.tilemap.render(self.display, offset=render_scroll, zoom=self.zoom)
            
            # Get current tile and mouse position
            current_tile_img = self.assets[self.tile_list[self.tile_group]][self.tile_variant].copy()
            
            if self.tile_list[self.tile_group] == 'spikes':
                current_tile_img = pygame.transform.rotate(current_tile_img, self.current_rotation)
            
            current_tile_img.set_alpha(100)
            
            mpos = pygame.mouse.get_pos()
            tile_pos = (int((mpos[0] + self.scroll[0]) // self.tilemap.tile_size), 
                       int((mpos[1] + self.scroll[1]) // self.tilemap.tile_size))
            
            # Show tile preview and handle placement/removal outside menu
            if mpos[0] >= self.menu_width:
                if self.ongrid:
                    self.display.blit(current_tile_img, 
                                    (tile_pos[0] * self.tilemap.tile_size - self.scroll[0], 
                                     tile_pos[1] * self.tilemap.tile_size - self.scroll[1]))
                else:
                    self.display.blit(current_tile_img, mpos)
            
                self.handle_tile_placement(tile_pos, mpos)
                self.handle_tile_removal(tile_pos, mpos)
            
            # Draw UI elements
            self.draw_menu()
            self.draw_ui(current_tile_img)
            self.draw_save_notification()
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if self.handle_keyboard_events(event):
                    return 
                
                self.handle_mouse_events(event, tile_pos, mpos)
            
            pygame.display.update()
            self.clock.tick(FPS)
            