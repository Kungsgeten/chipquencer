import pygame
import gui


class Modeline(object):
    HEIGHT = 12
    pygame.font.init()
    font = gui.FONT_SMALL

    def __init__(self, sections=0):
        self.strings = [''] * sections

    def __len__(self):
        return len(self.strings)

    def __getitem__(self, key):
        return self.strings[key]

    def __setitem__(self, key, value):
        self.strings[key] = value

    def __iter__(self):
        for x in self.strings:
            yield x

    def __contains__(self, item):
        return item in self.strings

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
