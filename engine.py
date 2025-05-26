import pygame
from scripts.constants import DISPLAY_SIZE, FPS
from scripts.game import Game
from scripts.menu import Menu
from scripts.GameManager import game_state_manager
from scripts.editor import EditorMenu

class Engine:
    def __init__(self):
        pygame.init()

        pygame.display.set_caption('Super Terboy')
        self.display = pygame.display.set_mode(DISPLAY_SIZE)
        self.clock = pygame.time.Clock()
        self.game = Game(self.display, self.clock)
        self.editor = EditorMenu(self.display)
        self.menu = Menu(self.display)

        self.state = {'game': self.game, 'editor': self.editor, 'menu': self.menu}


    def run(self):
        previous_state = None

        while True:
            current_state = game_state_manager.getState()

            if previous_state == 'menu' and current_state == 'game':
                self.game.initialize_environment()

            dt = self.clock.tick(FPS) / 1000.0

            if current_state == 'game':
                self.state[current_state].run(dt)
            else:
                self.state[current_state].run()

            previous_state = current_state
            pygame.display.flip()


if __name__ == '__main__':
    Engine().run()