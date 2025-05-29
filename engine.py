import pygame
from scripts.constants import DISPLAY_SIZE, FPS, FONT, MENUBG
from scripts.game import Game
from scripts.menu import Menu
from scripts.GameManager import game_state_manager
from scripts.editor import EditorMenu
from scripts.assets import AssetManager

class LoadingScreen:
    def __init__(self, display):
        self.display = display
        self.font = pygame.font.Font(FONT, 36)
        self.background = pygame.image.load(MENUBG)
        self.background = pygame.transform.scale(self.background, DISPLAY_SIZE)
        
    def show(self, text="Loading..."):
        self.display.blit(self.background, (0, 0))
        
        # Create loading text
        text_surface = self.font.render(text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(DISPLAY_SIZE[0]//2, DISPLAY_SIZE[1]//2))
        self.display.blit(text_surface, text_rect)
        
        # Simple loading animation dots
        dots = "." * (pygame.time.get_ticks() // 500 % 4)
        dots_surface = self.font.render(dots, True, (255, 255, 255))
        dots_rect = dots_surface.get_rect(center=(DISPLAY_SIZE[0]//2 + 100, DISPLAY_SIZE[1]//2))
        self.display.blit(dots_surface, dots_rect)
        
        pygame.display.flip()

class Engine:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption('Ascent')
        self.display = pygame.display.set_mode(DISPLAY_SIZE)
        self.clock = pygame.time.Clock()
        
        # Show loading screen
        loading_screen = LoadingScreen(self.display)
        loading_screen.show("Initializing...")
        
        # Pre-load all assets during engine initialization
        self.asset_manager = AssetManager()  
        loading_screen.show("Loading game components...")
        
        # Initialize game components
        self.game = Game(self.display, self.clock)
        self.menu = Menu(self.display, self.clock)
        self.editor = None
        
        self.state = {'game': self.game, 'editor': self.editor, 'menu': self.menu}
        
        loading_screen.show("Ready!")
        pygame.time.wait(700)  

    def run(self):
        previous_state = None

        while True:
            current_state = game_state_manager.getState()

            if previous_state == 'menu' and current_state == 'game':
                self.game.initialize_environment()

            dt = self.clock.tick(FPS) / 1000.0

            if current_state == 'game':
                self.state[current_state].run(dt)
            elif current_state == 'menu':
                self.menu.run()
            elif current_state == 'editor':
                editor_menu = EditorMenu(self.display)
                editor_menu.run()

            previous_state = current_state
            pygame.display.flip()


if __name__ == '__main__':
    Engine().run()