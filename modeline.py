import pygame
import settings

class ButtonKeyboard:
    def __init__(self, key):
        self.key = key
        self.pressed = False
        self.down = False
        self.released = False

class Modeline():
    HEIGHT = 10
    pygame.font.init()
    font = pygame.font.SysFont('04b03', 8)
    
    def __init__(self):
        self.buttonstrings = ['', '', '', '']
        self.text = ''
        self.buttons = [ButtonKeyboard(pygame.K_a), 
                        ButtonKeyboard(pygame.K_s),
                        ButtonKeyboard(pygame.K_d),
                        ButtonKeyboard(pygame.K_f)]

    def update(self, events):
        for button in self.buttons:
            button.pressed = False
            button.released = False
        for e in events:
            if e.type == pygame.KEYDOWN:
                for button in self.buttons:
                    if e.key == button.key:
                        button.down = True
                        button.pressed = True
            elif e.type == pygame.KEYUP:
                for button in self.buttons:
                    if e.key == button.key:
                        button.down = False
                        button.released = True
        
    def render(self, surface):
        BUTTON_WIDTH = 50
        top = settings.SCREEN_HEIGHT - self.HEIGHT
        rect = pygame.Rect(0, top, settings.SCREEN_WIDTH, self.HEIGHT)
        pygame.draw.rect(surface, settings.C_LIGHTEST, rect)
        for i in range(4):
            text = self.font.render(self.buttonstrings[i], False, settings.C_DARKEST)
            textpos = text.get_rect()
            textpos.centerx = BUTTON_WIDTH * i + (BUTTON_WIDTH / 2)
            surface.blit(text, (textpos.x, top + 1))
        text = self.font.render(self.text, False, settings.C_DARKER)
        surface.blit(text, (BUTTON_WIDTH * 4 + 29, top + 1))
