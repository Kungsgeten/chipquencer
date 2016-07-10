import pygame

class RadioButtons:
    FONT = 'consolas'
    FONT_SIZE = 14
    FONT_COLOR_NORMAL = (255, 255, 255)
    FONT_COLOR_SELECTED = (0, 0, 0)
    BUTTON_COLOR_NORMAL = (100, 100, 100)
    BUTTON_COLOR_SELECTED = (0, 255, 0)

    pygame.font.init()
    font = pygame.font.SysFont(FONT, FONT_SIZE)
    def __init__(self, pos, size, columns, rows, strings, spacing=0):
        assert len(strings) == columns * rows
        self.strings = strings
        self.pos = self.x, self.y = pos
        self.bsize = self.bwidth, self.bheight = size
        self.arearect = pygame.Rect(self.x, self.y,
                                    (self.bwidth + spacing) * columns,
                                    (self.bheight + spacing) * rows)
        self.rects = []
        self.selected = 0
        for r in range(rows):
            for c in range(columns):
                self.rects.append(pygame.Rect(self.x + c * (self.bwidth + spacing),
                                              self.y + r * (self.bheight + spacing),
                                              self.bwidth,
                                              self.bheight))

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
            font_color = self.FONT_COLOR_NORMAL
            button_color = self.BUTTON_COLOR_NORMAL
            if i == self.selected:
                font_color = self.FONT_COLOR_SELECTED
                button_color = self.BUTTON_COLOR_SELECTED
            pygame.draw.rect(surface, button_color, rect)
            text = self.font.render(self.strings[i], False, font_color)
            surface.blit(text, (rect.x, rect.y))
