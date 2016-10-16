import pygame

import screen
import gui
import sequencer

from modeline import Modeline
from gui import TextField


class SaveScreen(screen.Screen):
    font = gui.FONT_BIG

    def __init__(self):
        name = sequencer.project['name']
        SIZE = (gui.SCREEN_WIDTH, 30)
        self.name_field = TextField(pos=(2, 2), size=SIZE, text=name)
        self.modeline = Modeline(sections=1)
        self.modeline[0] = 'Save project'

    def _update(self, events):
        self.has_changed = True
        self.name_field.update(events)

    def _render(self, surface):
        self.name_field.render(surface)
        self.modeline.render(surface)
        return surface

    def close(self):
        name = self.name_field.text
        sequencer.project['name'] = name
        path = 'projects/{}.yaml'.format(name.lower().replace(' ', '_'))
        sequencer.project['path'] = path
        sequencer.save(path)
