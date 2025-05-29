from pathlib import Path
import pygame
from scripts.constants import (
    BASE_IMG_PATH, FONT, DISPLAY_SIZE, calculate_ui_constants, 
    SOUND_EXTENSIONS, DEFAULT_REMOVE_COLOR, DEFAULT_SOUND_VOLUME, 
    MIN_FONT_SIZE, MAX_FONT_SIZE, REFERENCE_SIZE
)

def load_image(path, scale=None, remove_color=DEFAULT_REMOVE_COLOR):
    img_path = Path(BASE_IMG_PATH) / path
    img = pygame.image.load(str(img_path)).convert()
    if remove_color is not None:
        img.set_colorkey(remove_color)
    if scale is not None:
        img = pygame.transform.scale(img, scale)
    return img

def load_images(path, scale=None, remove_color=DEFAULT_REMOVE_COLOR):
    dir_path = Path(BASE_IMG_PATH) / path
    images = []
    for img_path in sorted(dir_path.iterdir()):
        if img_path.suffix.lower() in ('.png', '.jpg', '.jpeg', '.bmp'):
            relative_path = img_path.relative_to(BASE_IMG_PATH)
            images.append(load_image(str(relative_path), scale, remove_color))
    return images

def load_sound(path, volume=DEFAULT_SOUND_VOLUME):
    sound_path = Path('data') / 'sfx' / path
    sound = pygame.mixer.Sound(str(sound_path))
    sound.set_volume(volume)
    return sound

def load_sounds(path, volume=DEFAULT_SOUND_VOLUME):
    dir_path = Path('data') / 'sfx' / path
    sounds = []
    for snd_path in sorted(dir_path.iterdir()):
        if snd_path.suffix.lower() in SOUND_EXTENSIONS:
            relative_path = snd_path.relative_to(Path('data') / 'sfx')
            sound = load_sound(str(relative_path), volume)
            sounds.append(sound)
    return sounds

def find_next_numeric_filename(directory, extension='.json'):
    dir_path = Path(directory)
    numeric_names = [
        int(f.stem)
        for f in dir_path.iterdir()
        if f.is_file() and f.stem.isdigit() and f.suffix == extension
    ]
    next_number = max(numeric_names, default=-1) + 1
    return f"{next_number}{extension}"

def play_ui_sound(sound_list):
    if sound_list:
        sound_list[0].play()

def render_text_with_shadow(surface, text, font, color, x, y, shadow_offset=1, centered=False):
    text_surface = font.render(text, True, color)
    shadow_surface = font.render(text, True, (0, 0, 0))
    if centered:
        text_rect = text_surface.get_rect(center=(x, y))
        shadow_rect = shadow_surface.get_rect(center=(x + shadow_offset, y + shadow_offset))
    else:
        text_rect = text_surface.get_rect(topleft=(x, y))
        shadow_rect = shadow_surface.get_rect(topleft=(x + shadow_offset, y + shadow_offset))
    surface.blit(shadow_surface, shadow_rect)
    surface.blit(text_surface, text_rect)
    return text_rect

def scale_position(x_percent, y_percent, display_size):
    return (int(display_size[0] * x_percent), int(display_size[1] * y_percent))

def scale_size(width_percent, height_percent, display_size):
    return (int(display_size[0] * width_percent), int(display_size[1] * height_percent))

def scale_font(base_size, display_size, reference_size=REFERENCE_SIZE):
    width_ratio = display_size[0] / reference_size[0]
    height_ratio = display_size[1] / reference_size[1]
    scale_factor = (width_ratio * height_ratio) ** 0.5
    scaled_size = max(MIN_FONT_SIZE, min(MAX_FONT_SIZE, int(base_size * scale_factor)))
    return scaled_size

def draw_debug_info(game, surface, offset):
    player_rect = game.player.rect()
    pygame.draw.rect(
        surface, (255, 0, 0),
        (player_rect.x - offset[0], player_rect.y - offset[1], player_rect.width, player_rect.height), 2
    )
    tile_size = game.tilemap.tile_size
    vsx = offset[0] // tile_size
    vex = (offset[0] + surface.get_width()) // tile_size + 1
    vsy = offset[1] // tile_size
    vey = (offset[1] + surface.get_height()) // tile_size + 1
    for x in range(vsx, vex):
        for y in range(vsy, vey):
            loc = f"{x};{y}"
            if loc in game.tilemap.tilemap:
                tile = game.tilemap.tilemap[loc]
                base_type = tile['type'].split()[0]
                color, rect = None, None
                if base_type == 'spikes':
                    color = (255, 255, 0)
                    rect = game.tilemap._get_spike_rect(tile) if 'rotation' in tile else pygame.Rect(
                        tile['pos'][0] * tile_size, tile['pos'][1] * tile_size, tile_size, tile_size)
                elif base_type == 'finish':
                    color = (0, 255, 0)
                    if tile['type'] in ['finish up', 'finish']:
                        rect = pygame.Rect(tile['pos'][0] * tile_size, tile['pos'][1] * tile_size, tile_size, tile_size * 2)
                    else:
                        rect = pygame.Rect(tile['pos'][0] * tile_size, tile['pos'][1] * tile_size, tile_size, tile_size)
                elif base_type == 'portal':
                    color = (255, 0, 255)
                    rect = pygame.Rect(tile['pos'][0] * tile_size, tile['pos'][1] * tile_size, tile_size, tile_size)
                elif base_type == 'kill':
                    color = (255, 165, 0)
                    rect = pygame.Rect(tile['pos'][0] * tile_size, tile['pos'][1] * tile_size, tile_size, tile_size)
                if color and rect and not tile['type'].endswith(' down'):
                    pygame.draw.rect(
                        surface, color,
                        (rect.x - offset[0], rect.y - offset[1], rect.width, rect.height), 2
                    )
    debug_font = pygame.font.Font(FONT, 20)
    debug_text = debug_font.render("Debug: Hitboxes Visible", True, (0, 255, 0))
    surface.blit(debug_text, (10, 50))

def update_camera_smooth(player, scroll, display_width, display_height):
    player_rect = player.rect()
    target_x = player_rect.centerx - display_width // 2
    target_y = player_rect.centery - display_height // 2
    scroll[0] += (target_x - scroll[0]) / 8
    scroll[1] += (target_y - scroll[1]) / 8
    return scroll

class Animation:
    def __init__(self, images, img_dur=5, loop=True):
        self.images = images
        self.loop = loop
        self.img_duration = img_dur
        self.done = False
        self.frame = 0
        self.enabled = True

    def copy(self):
        new_anim = Animation(self.images, self.img_duration, self.loop)
        new_anim.enabled = self.enabled
        return new_anim

    def update(self, dt=1.0):
        if not self.enabled:
            return
        if self.loop:
            self.frame = (self.frame + dt) % (self.img_duration * len(self.images))
        else:
            self.frame = min(self.frame + dt, self.img_duration * len(self.images) - 1)
            if self.frame >= self.img_duration * len(self.images) - 1:
                self.done = True

    def img(self):
        return self.images[int(self.frame / self.img_duration)]

# --- UI Widgets ---

class Button:
    def __init__(self, rect, text, action, font, menu, bg_color=None):
        self.rect = rect
        self.text = text
        self.action = action
        self.font = font
        self.menu = menu
        self.selected = False
        self.previously_selected = False
        self.bg_color = bg_color
        self.hover_sounds = load_sounds('hover', volume=0.04)
        self.click_sounds = load_sounds('click', volume=0.15)
        self.border_radius = max(6, int(rect.height * 0.1))
        display_height = pygame.display.get_surface().get_height()
        self.shadow_offset = max(2, int(4 * (display_height / 1080)))

    def is_hovered(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)

    def just_hovered(self):
        return self.selected and not self.previously_selected

    def update_hover_state(self, mouse_pos):
        self.previously_selected = self.selected
        self.selected = self.is_hovered(mouse_pos)
        if self.just_hovered():
            play_ui_sound(self.hover_sounds)
        return self.just_hovered()

    def handle_click(self, event):
        if self.selected and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            play_ui_sound(self.click_sounds)
            self.action()
            return True
        return False

    def draw(self, surface):
        shadow_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        shadow_color = (255, 255, 255, 90) if self.selected else (0, 0, 0, 90)
        shadow_surface.fill(shadow_color)
        surface.blit(shadow_surface, (self.rect.x + self.shadow_offset, self.rect.y + self.shadow_offset))
        # Button background
        if self.bg_color:
            if self.selected:
                button_color = tuple(min(c + 40, 255) for c in self.bg_color)
            else:
                button_color = self.bg_color
        else:
            button_color = (
                self.menu.UI_CONSTANTS['BUTTON_HOVER_COLOR'] if self.selected
                else self.menu.UI_CONSTANTS['BUTTON_COLOR']
            )
        button_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        button_surface.fill(button_color)
        surface.blit(button_surface, (self.rect.x, self.rect.y))
        # Text with shadow
        text_shadow = self.font.render(self.text, True, (0, 0, 0, 180))
        text_surf = self.font.render(self.text, True, (255, 255, 255))
        text_x = self.rect.x + (self.rect.width - text_surf.get_width()) // 2
        text_y = self.rect.y + (self.rect.height - text_surf.get_height()) // 2
        text_shadow_offset = max(1, int(2 * pygame.display.get_surface().get_height() / 1080))
        surface.blit(text_shadow, (text_x + text_shadow_offset, text_y + text_shadow_offset))
        surface.blit(text_surf, (text_x, text_y))
        # Highlight border if selected
        if self.selected:
            glow_color = self.menu.UI_CONSTANTS['BUTTON_GLOW_COLOR']
            display_width = pygame.display.get_surface().get_width()
            glow_size = max(2, int(3 * (display_width / 1920)))
            for i in range(glow_size, 0, -1):
                alpha = 60 - i * 10
                glow_rect = self.rect.inflate(i * 4, i * 4)
                glow_surface = pygame.Surface(glow_rect.size, pygame.SRCALPHA)
                pygame.draw.rect(
                    glow_surface,
                    tuple(list(glow_color) + [alpha]),
                    glow_surface.get_rect(),
                    border_radius=self.border_radius
                )
                surface.blit(glow_surface, (
                    self.rect.x - i * 2,
                    self.rect.y - i * 2
                ))

class MenuScreen:
    def __init__(self, menu, title="Menu"):
        self.menu = menu
        self.screen = menu.screen
        self.UI_CONSTANTS = calculate_ui_constants(DISPLAY_SIZE)
        self.click_sounds = load_sounds('click', volume=0.15)
        font_size = scale_font(40, DISPLAY_SIZE)
        title_font_size = scale_font(70, DISPLAY_SIZE)
        self.font = pygame.font.Font(FONT, font_size)
        self.title_font = pygame.font.Font(FONT, title_font_size)
        self.enabled = False
        self.title = title
        self.buttons = []
        self.music_path = 'data/sfx/music/menu.ogg'
        self.play_music()

    def play_music(self):
        pygame.mixer.init()
        pygame.mixer.music.load(str(self.music_path))
        pygame.mixer.music.set_volume(0.2) 
        pygame.mixer.music.play(-1) 

    def enable(self):
        self.enabled = True
        self.initialize()

    def disable(self):
        self.enabled = False

    def initialize(self):
        pass

    def update(self, events):
        if not self.enabled:
            return
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            button.update_hover_state(mouse_pos)
        for button in self.buttons:
            if button.selected:
                for event in events:
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        button.action()
                        play_ui_sound(self.click_sounds)
                        return

    def draw(self, surface):
        if not self.enabled:
            return
        # Title with shadow
        title_shadow = self.title_font.render(self.title, True, (0, 0, 0))
        title_text = self.title_font.render(self.title, True, (255, 255, 255))
        title_x = (surface.get_width() - title_text.get_width()) // 2
        title_y = int(surface.get_height() * 0.1)
        shadow_offset = max(2, int(4 * (surface.get_height() / 1080)))
        surface.blit(title_shadow, (title_x + shadow_offset, title_y + shadow_offset))
        surface.blit(title_text, (title_x, title_y))
        for button in self.buttons:
            button.draw(surface)

    def clear_buttons(self):
        self.buttons.clear()

    def create_button(self, text, action, x, y, width=None, bg_color=None):
        if width is None:
            text_surf = self.font.render(text, True, (255, 255, 255))
            width = text_surf.get_width() + self.UI_CONSTANTS['BUTTON_TEXT_PADDING']
            width = max(width, self.UI_CONSTANTS['BUTTON_MIN_WIDTH'])
        button = Button(
            pygame.Rect(x, y, width, self.UI_CONSTANTS['BUTTON_HEIGHT']),
            text, action, self.font, self.menu, bg_color
        )
        self.buttons.append(button)
        return button

    def create_centered_button_list(self, button_texts, button_actions, center_x, start_y, bg_colors=None):
        max_width = self.UI_CONSTANTS['BUTTON_MIN_WIDTH']
        for text in button_texts:
            text_surf = self.font.render(text, True, (255, 255, 255))
            width = text_surf.get_width() + self.UI_CONSTANTS['BUTTON_TEXT_PADDING']
            max_width = max(max_width, width)
        left_x = center_x - (max_width // 2)
        for i, (text, action) in enumerate(zip(button_texts, button_actions)):
            bg_color = None
            if bg_colors and i < len(bg_colors):
                bg_color = bg_colors[i]
            y_pos = start_y + i * (self.UI_CONSTANTS['BUTTON_HEIGHT'] + self.UI_CONSTANTS['BUTTON_SPACING'])
            self.create_button(text, action, left_x, y_pos, max_width, bg_color)

    def create_grid_buttons(self, texts, actions, start_x, start_y, fixed_width=None, bg_colors=None):
        if fixed_width is None:
            fixed_width = self.UI_CONSTANTS['BUTTON_MIN_WIDTH']
        columns = self.UI_CONSTANTS['GRID_COLUMNS']
        for i, (text, action) in enumerate(zip(texts, actions)):
            bg_color = None
            if bg_colors and i < len(bg_colors):
                bg_color = bg_colors[i]
            row = i // columns
            col = i % columns
            button_x = start_x + col * (fixed_width + self.UI_CONSTANTS['BUTTON_SPACING'])
            button_y = start_y + row * (self.UI_CONSTANTS['BUTTON_HEIGHT'] + self.UI_CONSTANTS['BUTTON_SPACING'])
            self.create_button(text, action, button_x, button_y, fixed_width, bg_color)