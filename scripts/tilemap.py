# tilemap.py
import json
import pygame
from scripts.constants import *

class Tilemap:
    def __init__(self, game, tile_size=16, env=True):
        self.game = game
        self.tile_size = tile_size
        self.env = env
        self.tilemap = {}
        self.offgrid_tiles = []
        self.lowest_y = 0
    
    def tiles_around(self, pos):
        tiles = []
        tile_loc = (int(pos[0] // self.tile_size), int(pos[1] // self.tile_size))
        for offset in NEIGHBOR_OFFSETS:
            check_loc = str(tile_loc[0] + offset[0]) + ';' + str(tile_loc[1] + offset[1])
            if check_loc in self.tilemap:
                tiles.append(self.tilemap[check_loc])
        return tiles
    
    def extract(self, id_pairs, keep=False):
        matches = []
        
        # Handle offgrid tiles
        for tile in self.offgrid_tiles.copy():
            if (tile[TYPE], tile[VARIANT]) in id_pairs:
                matches.append(tile.copy())
                if not keep:
                    self.offgrid_tiles.remove(tile)
        
        # Handle grid tiles
        processed = set()
        for loc in list(self.tilemap.keys()):
            if loc in processed:
                continue
                
            tile = self.tilemap[loc]
            base_type = tile[TYPE].split()[0]
            
            # Check if this tile matches our search
            if not any(base_type == target_type and tile[VARIANT] == target_variant 
                      for target_type, target_variant in id_pairs):
                continue
            
            # Handle split tiles (finish up/down)
            if tile[TYPE].endswith(UP):
                down_loc = f"{tile[POS][0]};{tile[POS][1] + 1}"
                # Always create match from the 'up' tile position
                match = self._create_match(tile, base_type)
                matches.append(match)
                processed.update([loc, down_loc])
                if not keep:
                    del self.tilemap[loc]
                    if down_loc in self.tilemap:
                        del self.tilemap[down_loc]
            elif not tile[TYPE].endswith(' down'):  # Regular tiles
                match = self._create_match(tile, base_type)
                matches.append(match)
                processed.add(loc)
                if not keep:
                    del self.tilemap[loc]
        
        return matches
    
    def _create_match(self, tile, base_type):
        match = tile.copy()
        match[TYPE] = base_type
        match[POS] = [tile[POS][0] * self.tile_size, tile[POS][1] * self.tile_size]
        return match

    def autotile(self):
        for tile in self.tilemap.values():
            if tile[TYPE] not in AUTOTILE_TYPES:
                continue
                
            neighbors = set()
            for shift in [(1, 0), (-1, 0), (0, -1), (0, 1)]:
                check_loc = f"{tile[POS][0] + shift[0]};{tile[POS][1] + shift[1]}"
                if check_loc in self.tilemap and self.tilemap[check_loc][TYPE] == tile[TYPE]:
                    neighbors.add(shift)
            
            neighbors = tuple(sorted(neighbors))
            if neighbors in AUTOTILE_MAP:
                tile[VARIANT] = AUTOTILE_MAP[neighbors]

    def _handle_spawners(self, path_for_save=False):
        spawner_tiles = self.extract([(SPAWNER, 0), (SPAWNER, 1)], keep=True)
        if len(spawner_tiles) > 1:
            self.extract([(SPAWNER, 0), (SPAWNER, 1)], keep=False)
            spawner = spawner_tiles[0]
            pos = spawner[POS].copy()
            
            # Convert to tile coordinates if needed
            if len(str(pos[0]).split('.')) == 1:
                pos = [pos[0] // self.tile_size, pos[1] // self.tile_size]
            
            tile_loc = f"{int(pos[0])};{int(pos[1])}"
            self.tilemap[tile_loc] = {
                TYPE: spawner[TYPE], 
                VARIANT: spawner[VARIANT], 
                POS: [int(pos[0]), int(pos[1])]
            }

    def save(self, path):
        self.lowest_y = max((tile[POS][1] for tile in self.tilemap.values()), default=0)
        self._handle_spawners()
        
        with open(path, 'w') as f:
            json.dump({
                TILEMAP: self.tilemap, 
                OFFGRID: self.offgrid_tiles,
                LOWEST_Y: self.lowest_y,
            }, f, indent=4)
        
    def load(self, path):
        with open(path, 'r') as f:
            map_data = json.load(f)
        self.tilemap = map_data[TILEMAP]
        self.offgrid_tiles = map_data[OFFGRID]
        self.lowest_y = map_data.get(LOWEST_Y, 0)
        self._handle_spawners()
    
    def physics_rects_around(self, pos):
        rects = []
        for tile in self.tiles_around(pos):
            if tile[TYPE].split()[0] in PHYSICS_TILES:
                rects.append(pygame.Rect(
                    tile[POS][0] * self.tile_size, 
                    tile[POS][1] * self.tile_size, 
                    self.tile_size, self.tile_size
                ))
        return rects
    
    def _get_spike_rect(self, tile):
        spike_w, spike_h = int(self.tile_size * SPIKE_SIZE[0]), int(self.tile_size * SPIKE_SIZE[1])
        rotation = tile.get(ROTATION, 0)
        tile_x, tile_y = tile[POS][0] * self.tile_size, tile[POS][1] * self.tile_size
        offset_fn = SPIKE_POSITION_OFFSETS.get(rotation, SPIKE_POSITION_OFFSETS[0])
        return pygame.Rect(*offset_fn(tile_x, tile_y, spike_w, spike_h, self.tile_size))

    def interactive_rects_around(self, pos):
        tiles = []
        for tile in self.tiles_around(pos):
            base_type = tile[TYPE].split()[0]
            if base_type not in INTERACTIVE_TILES:
                continue
                
            match base_type:
                case 'finish':
                    if tile[TYPE] in ['finish up', 'finish']:
                        rect = pygame.Rect(tile[POS][0] * self.tile_size, tile[POS][1] * self.tile_size, 
                                         self.tile_size, self.tile_size * 2)
                        tiles.append((rect, (base_type, tile[VARIANT])))
                    elif tile[TYPE] == 'finish down':
                        # Only add if no corresponding 'up' tile exists
                        up_loc = f"{tile[POS][0]};{tile[POS][1] - 1}"
                        if up_loc not in self.tilemap or self.tilemap[up_loc][TYPE] != 'finish up':
                            rect = pygame.Rect(tile[POS][0] * self.tile_size, tile[POS][1] * self.tile_size, 
                                             self.tile_size, self.tile_size)
                            tiles.append((rect, (base_type, tile[VARIANT])))
                case 'spikes':
                    tiles.append((self._get_spike_rect(tile), (base_type, tile[VARIANT])))
                case 'kill':
                    rect = pygame.Rect(tile[POS][0] * self.tile_size, tile[POS][1] * self.tile_size, 
                                     self.tile_size, self.tile_size)
                    tiles.append((rect, (base_type, tile[VARIANT])))
        return tiles
    
    def is_below_map(self, entity_pos, tiles_threshold=2):
        return entity_pos[1] > (self.lowest_y + tiles_threshold) * self.tile_size

    def _get_image(self, tile_type, variant):
        if self.env:
            # Use the AssetManager (old style)
            asset = self.game.asset_manager.assets[tile_type]
            return asset.img() if hasattr(asset, 'img') else asset[variant]
        else:
            # Use self.game.assets[tile_type] (editor style)
            asset = self.game.assets[tile_type]
            return asset.img() if hasattr(asset, 'img') else asset[variant]

    def render(self, surf, offset=(0, 0), zoom=10):
        # Render offgrid tiles (keep original logic for these)
        for tile in self.offgrid_tiles:
            if tile[TYPE] == 'spikes' and ROTATION in tile:
                if self.env:
                    img = self.game.asset_manager.get_rotated_image(tile[TYPE], tile[VARIANT], tile[ROTATION])
                else:
                    img = self.game.get_rotated_image(tile[TYPE], tile[VARIANT], tile[ROTATION])
                x = tile[POS][0] * self.tile_size - offset[0] - (img.get_width() - self.tile_size) // 2
                y = tile[POS][1] * self.tile_size - offset[1] - (img.get_height() - self.tile_size) // 2
            else:
                img = self._get_image(tile[TYPE], tile[VARIANT])
                x = tile[POS][0] * self.tile_size - offset[0]
                y = tile[POS][1] * self.tile_size - offset[1]
            surf.blit(img, (x, y))
        
        # PERFORMANCE OPTIMIZATION: Screen culling for grid tiles
        # Only render tiles that are visible on screen
        start_x = offset[0] // self.tile_size - 1  # -1 for buffer
        end_x = (offset[0] + surf.get_width()) // self.tile_size + 2  # +2 for buffer
        start_y = offset[1] // self.tile_size - 1
        end_y = (offset[1] + surf.get_height()) // self.tile_size + 2
        
        # Track processed tiles to avoid rendering 'down' parts separately
        processed_tiles = set()
        
        for x in range(start_x, end_x):
            for y in range(start_y, end_y):
                loc = f"{x};{y}"
                
                if loc not in self.tilemap or loc in processed_tiles:
                    continue
                    
                tile = self.tilemap[loc]
                
                # Skip down parts to avoid duplicates
                if tile[TYPE].endswith(' down'):
                    continue
                
                base_type = tile[TYPE].split()[0]
                x_pos = tile[POS][0] * self.tile_size - offset[0]
                y_pos = tile[POS][1] * self.tile_size - offset[1]
                
                # Handle different tile types
                if base_type == 'spikes' and ROTATION in tile:
                    if self.env:
                        img = self.game.asset_manager.get_rotated_image(base_type, tile[VARIANT], tile[ROTATION])
                    else:
                        img = self.game.get_rotated_image(base_type, tile[VARIANT], tile[ROTATION])
                    x_pos -= (img.get_width() - self.tile_size) // 2
                    y_pos -= (img.get_height() - self.tile_size) // 2
                elif base_type == 'finish':
                    img = self._get_image(base_type, tile[VARIANT])
                    if img.get_height() != self.tile_size * 2:
                        img = pygame.transform.scale(img, (self.tile_size, self.tile_size * 2))
                    
                    # Mark the down tile as processed if it exists
                    down_loc = f"{x};{y + 1}"
                    if down_loc in self.tilemap:
                        processed_tiles.add(down_loc)
                else:
                    img = self._get_image(base_type, tile[VARIANT])
                
                surf.blit(img, (x_pos, y_pos))
                processed_tiles.add(loc)