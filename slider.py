import settings

import pygame

class Slider:
    def __init__(self, rect):
        self.rect = rect
        self.active = False
        self._pixels = 0.0

    def update(self, events, finetune=False):
        for e in events:
            if e.type == pygame.MOUSEBUTTONUP:
                self.active = False
            elif e.type == pygame.MOUSEBUTTONDOWN:
                self.active = self.rect.collidepoint(e.pos)
                pygame.mouse.get_rel()
        if self.active:
            relx, rely = pygame.mouse.get_rel()
            if finetune:
                rely *= 0.2
            self._pixels -= rely
            if self._pixels < 0:
                self._pixels = 0.0
            elif self._pixels > self.rect.height:
                self._pixels = float(self.rect.height)
            return self.get_data()
        return None

    def render(self, surface):
        pygame.draw.rect(surface, settings.C_PRIMARY, self.rect)
        status = pygame.Rect(self.rect.left,
                             self.rect.bottom - self._pixels,
                             self.rect.width,
                             self._pixels)
        pygame.draw.rect(surface, settings.C_DARKER, status)

    def get_data(self):
        return self._pixels / self.rect.height

    def set_value(self, value, maximum, minimum=0.0):
        if value > maximum:
            value = maximum
        self._pixels = (float(value - minimum) / (maximum - minimum)) * self.rect.height
