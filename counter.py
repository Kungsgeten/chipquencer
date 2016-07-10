import pygame
import settings
from actionbutton import ActionButton

class Counter:
    FONT = "Arial"
    FONT_SIZE = 16

    pygame.font.init()
    font = pygame.font.SysFont(FONT, FONT_SIZE)

    def __init__(self, pos, height, text, minimum, maximum):
        self.pos = pos
        self.text = text
        self.minimum = minimum
        self.maximum = maximum
        self.height = height
        self.text = self.font.render(text, False, settings.C_LIGHTEST)
        self.dec = ActionButton((self.text.get_width() + pos[0], pos[1]),
                                (height, height), '-')
        self.inc = ActionButton((self.text.get_width() + pos[0] + height * 2, pos[1]),
                                (height, height), '+')
        self.value = minimum

    def update(self, events):
        if self.dec.clicked(events):
            self.value -= 1
            if self.value < self.minimum:
                self.value = self.maximum
        elif self.inc.clicked(events):
            self.value += 1
            if self.value > self.maximum:
                self.value = self.minimum

    def render(self, surface):
        self.dec.render(surface)
        self.inc.render(surface)
        text = self.font.render((str(self.value)), False, settings.C_LIGHTEST)
        surface.blit(text, (self.text.get_width() +
                            self.pos[0] + self.height, self.pos[1]))
        surface.blit(self.text, self.pos)
