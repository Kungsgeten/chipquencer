import settings
import gui
from modeline import Modeline

import pygame

class ChoiceList(gui.Screen):
    SCROLL_WIDTH = 25
    ITEM_HEIGHT = 25
    font = pygame.font.SysFont('Consolas', 16)
    
    def __init__(self, choices, modelinetext=''):
        self.scrolling = False
        self.choices = choices
        self.returnkey = modelinetext.lower().replace(' ', '_')
        self.modeline = Modeline()
        self.modeline.buttonstrings = ['', '', '', 'Cancel']
        self.modeline.text = modelinetext
        self.rects = []
        self.surface = pygame.Surface(settings.SCREEN_SIZE)
        self.surface.fill(settings.C_LIGHTER)
        self.listsurface = pygame.Surface((settings.SCREEN_WIDTH - self.SCROLL_WIDTH,
                                       self.ITEM_HEIGHT * len(choices)))
        self.listsurface.fill(settings.C_LIGHTER)
        self.scrolled = 0 # pixels scrolled
        for i, choice in enumerate(choices):
            rect = pygame.Rect((0, i * self.ITEM_HEIGHT),
                               (settings.SCREEN_WIDTH - self.SCROLL_WIDTH,
                                self.ITEM_HEIGHT))
            self.rects.append(rect)
            pygame.draw.rect(self.listsurface, settings.C_PRIMARY, rect, 1)
            if type(choice) is list:
                text = self.font.render(choice[0], False, settings.C_DARKER)
            else:
                text = self.font.render(choice, False, settings.C_DARKER)
            self.listsurface.blit(text, (0, i * self.ITEM_HEIGHT))
    
    def update(self, events):
        self.modeline.update(events)
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN:
                x, y = e.pos
                pygame.mouse.get_rel()
                if x < settings.SCREEN_WIDTH - self.SCROLL_WIDTH:
                    index_clicked = (y + self.scrolled) // self.ITEM_HEIGHT
                    if index_clicked >= len(self.choices):
                        return
                    value = None
                    if type(self.choices[index_clicked]) is list:
                        gui.pop(**{self.returnkey: self.choices[index_clicked][1]})
                    else:
                        gui.pop(**{self.returnkey: self.choices[index_clicked]})
                else:
                    self.scrolling = True
            elif e.type == pygame.MOUSEBUTTONUP:
                self.scrolling = False
            if self.scrolling:
                relx, rely = pygame.mouse.get_rel()
                self.scrolled -= rely * 3
                listheight = len(self.choices) * self.ITEM_HEIGHT - settings.SCREEN_HEIGHT + self.modeline.HEIGHT
                if self.scrolled > 0:
                    self.scrolled = 0
                elif abs(self.scrolled) > listheight:
                    self.scrolled = -listheight

    def render(self):
        self.surface.blit(self.listsurface, (0, self.scrolled))
        self.modeline.render(self.surface)
        return self.surface
