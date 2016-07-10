import pygame
import settings

class ActionButton:
    """A regular button, trigs a function when clicked"""

    FONT = "Arial"
    FONT_SIZE = 16

    pygame.font.init()
    font = pygame.font.SysFont(FONT, FONT_SIZE)

    def __init__(self, pos, size, text):
        self.text = text
        x, y = pos
        width, height = size
        self.rect = pygame.Rect(x, y, width, height)

    def clicked(self, events):
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(e.pos):
                return True
        return False

    def render(self, surface):
        pygame.draw.rect(surface, settings.C_PRIMARY, self.rect)
        text = self.font.render(self.text, False, settings.C_LIGHTEST)
        surface.blit(text, (self.rect.x, self.rect.y))
