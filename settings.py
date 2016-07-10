import pygame
import yaml
from os import listdir
from os.path import isfile, join

SCREEN_SIZE = SCREEN_WIDTH, SCREEN_HEIGHT = 320, 240

# Color theme
C_PRIMARY = None
C_LIGHTER = None
C_LIGHTEST = None
C_DARKER = None
C_DARKEST = None

# A list of (Instrument, file)
INSTRUMENTS = []

def load_colors():
    global C_PRIMARY, C_LIGHTER, C_LIGHTEST, C_DARKER, C_DARKEST
    stream = file('themes.yml', 'r')
    theme = yaml.load(stream)['active_theme']
    print hex(theme['darker'])
    C_PRIMARY = pygame.Color(format(theme['primary'], '#08x'))
    C_LIGHTER = pygame.Color(format(theme['lighter'], '#08x'))
    C_LIGHTEST = pygame.Color(format(theme['lightest'], '#08x'))
    C_DARKER = pygame.Color(format(theme['darker'], '#08x'))
    C_DARKEST = pygame.Color(format(theme['darkest'], '#08x'))

def load_instruments():
    global INSTRUMENTS
    INSTRUMENTS = []
    path = 'instruments/'
    instrumentfiles = [f for f in listdir(path) if isfile(join(path,f))]
    for i in instrumentfiles:
        stream = file('instruments/' + i, 'r')
        inst_dict = yaml.load(stream)
        INSTRUMENTS.append((inst_dict['name'], i))
    print INSTRUMENTS
