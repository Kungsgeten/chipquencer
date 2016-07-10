import pygame
import settings

class RadioButtons:
    """A set of radio buttons, can get the active one"""
    FONT = 'Arial'
    FONT_SIZE = 16

    pygame.font.init()
    font = pygame.font.SysFont(FONT, FONT_SIZE)
    def __init__(self, pos, size, columns, rows, strings=[], spacing=0):
        if len(strings):
            assert len(strings) == columns * rows
        self.strings = strings
        x, y = pos
        width, height = size
        self.arearect = pygame.Rect(x, y,
                                    (width + spacing) * columns,
                                    (height + spacing) * rows)
        self.rects = []
        self.selected = 0
        for r in range(rows):
            for c in range(columns):
                self.rects.append(pygame.Rect(x + c * (width + spacing),
                                              y + r * (height + spacing),
                                              width,
                                              height))

    def update(self, events):
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and self.arearect.collidepoint(e.pos):
                for i, rect in enumerate(self.rects):
                    if rect.collidepoint(e.pos):
                        self.selected = i
                        return self.selected
        return None

    def render(self, surface):
        for i, rect in enumerate(self.rects):
            font_color = settings.C_LIGHTEST
            button_color = settings.C_PRIMARY
            if i == self.selected:
                font_color = settings.C_LIGHTEST
                button_color = settings.C_DARKER
            pygame.draw.rect(surface, button_color, rect)
            try:
                text = self.font.render(self.strings[i], False, font_color)
                surface.blit(text, (rect.x, rect.y))
            except:
                pass
