import pygame

pygame.init()
info = pygame.display.Info()

# Display and tile setup
screen_width, screen_height = info.current_w, info.current_h
DISPLAY_SIZE = (screen_width, screen_height)
aspect_x = DISPLAY_SIZE[0] - (DISPLAY_SIZE[0] % 16)
aspect_y = DISPLAY_SIZE[1] - (DISPLAY_SIZE[1] % 9)
DISPLAY_SIZE = (aspect_x, aspect_y)
TILE_SIZE = DISPLAY_SIZE[0] // 28

FPS = 60

# Physics
PLAYER_SPEED = 0.8 * TILE_SIZE / 36
JUMP_SPEED = 14 * TILE_SIZE / 36
WALLSLIDE_SPEED = 0.7 * TILE_SIZE / 36
WALLJUMP_X_SPEED = 9 * TILE_SIZE / 36
WALLJUMP_Y_SPEED = 15 * TILE_SIZE / 36
GRAVITY_UP = 0.6 * TILE_SIZE / 36
GRAVITY_DOWN = 0.3 * TILE_SIZE / 36
ACCELERAION = 0.001 * TILE_SIZE / 36
DECCELARATION = 0.1 * TILE_SIZE / 36
MAX_X_SPEED = 10 * TILE_SIZE / 36
MAX_Y_SPEED = 18 * TILE_SIZE / 36
WALL_MOMENTUM_PRESERVE = 0.15
WALL_MOMENTUM_FRAMES = 3
PLAYER_BUFFER = 5
COYOTE_TIME = 6
BASE_IMG_DUR = 20

# Hitboxes and scaling
PLAYERS_SIZE = (TILE_SIZE, TILE_SIZE)
PLAYERS_IMAGE_SIZE = (PLAYERS_SIZE[0], PLAYERS_SIZE[1])

# Tile types
PHYSICS_TILES = {'grass', 'stone', 'pinkrock'}
AUTOTILE_TYPES = {'grass', 'stone', 'kill', 'pinkrock'}
INTERACTIVE_TILES = {'finish', 'spikes', 'kill', 'portal up', 'portal down'}

# String
POS = 'pos'
TYPE = 'type'
TILEMAP = 'tilemap'
OFFGRID = 'offgrid'
LOWEST_Y = 'lowest_y'
VARIANT = 'variant'
SPAWNER = 'spawners'
UP = ' up'
ROTATION = 'rotation'

BASE_IMG_PATH = 'data/images/'

# Spike properties
SPIKE_SIZE = (0.6, 0.25)
SPIKE_POSITION_OFFSETS = {
    0: lambda tile_x, tile_y, spike_w, spike_h, tile_size: (
        tile_x + (tile_size - spike_w) // 2, tile_y + (tile_size - spike_h), spike_w, spike_h
    ),
    90: lambda tile_x, tile_y, spike_w, spike_h, tile_size: (
        tile_x + (tile_size - spike_h), tile_y + (tile_size - spike_w) // 2, spike_h, spike_w
    ),
    180: lambda tile_x, tile_y, spike_w, spike_h, tile_size: (
        tile_x + (tile_size - spike_w) // 2, tile_y, spike_w, spike_h
    ),
    270: lambda tile_x, tile_y, spike_w, spike_h, tile_size: (
        tile_x, tile_y + (tile_size - spike_w) // 2, spike_h, spike_w
    ),
}

# Image scaling
IMGSCALE = (TILE_SIZE, TILE_SIZE)
FINISHSCALE = (TILE_SIZE, TILE_SIZE * 2)
FONT = r'data\fonts\Menu.ttf'

# Editor/UI
EDITOR_SCROLL_SPEED = 12
MENUBG = r'data\images\menugbg.png'
MENUTXTCOLOR = (120, 83, 58)
WHITE = (255, 255, 255)

def calculate_ui_constants(display_size):
    ref_width, ref_height = 1920, 1080
    width_scale = display_size[0] / ref_width
    height_scale = display_size[1] / ref_height
    general_scale = min(width_scale, height_scale)
    return {
        'BUTTON_HEIGHT': int(80 * height_scale),
        'BUTTON_MIN_WIDTH': int(200 * width_scale),
        'BUTTON_TEXT_PADDING': int(40 * general_scale),
        'BUTTON_SPACING': int(20 * general_scale),
        'BUTTON_COLOR': (40, 40, 70, 220),
        'BUTTON_HOVER_COLOR': (60, 60, 100, 240),
        'BUTTON_GLOW_COLOR': (100, 150, 255),
        'GRID_COLUMNS': 5,
        'MAPS_PER_PAGE': 20,
    }

AUTOTILE_MAP = {
    tuple(sorted([(1, 0), (0, 1)])): 0,
    tuple(sorted([(1, 0), (0, 1), (-1, 0)])): 1,
    tuple(sorted([(-1, 0), (0, 1)])): 2,
    tuple(sorted([(-1, 0), (0, -1), (0, 1)])): 3,
    tuple(sorted([(-1, 0), (0, -1)])): 4,
    tuple(sorted([(-1, 0), (0, -1), (1, 0)])): 5,
    tuple(sorted([(1, 0), (0, -1)])): 6,
    tuple(sorted([(1, 0), (0, -1), (0, 1)])): 7,
    tuple(sorted([(1, 0), (-1, 0), (0, 1), (0, -1)])): 8,
}

NEIGHBOR_OFFSETS = [(-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (0, 0), (-1, 1), (0, 1), (1, 1)]