import pygame
import gui

class Modeline():
    HEIGHT = 12
    pygame.font.init()
    font = gui.FONT_SMALL

    def __init__(self):
        self.strings = []

    def render(self, surface):
        top = gui.SCREEN_HEIGHT - self.HEIGHT
        rect = pygame.Rect(0, top, gui.SCREEN_WIDTH, self.HEIGHT)
        pygame.draw.rect(surface, gui.C_LIGHTEST, rect)
        x = 2
        OFFSET = 10
        for i, s in enumerate(self.strings):
            COLOR = gui.C_DARKEST if i % 2 == 0 else gui.C_DARKER
            text = self.font.render(s, False, COLOR)
            surface.blit(text, (x, top + 1))
            x += text.get_rect().width + OFFSET
        # for i in range(4):
        #     text = self.font.render(self.buttonstrings[i], False, gui.C_DARKEST)
        #     textpos = text.get_rect()
        #     textpos.centerx = BUTTON_WIDTH * i + (BUTTON_WIDTH / 2)
        #     surface.blit(text, (textpos.x, top + 1))
        # text = self.font.render(self.text, False, gui.C_DARKER)
