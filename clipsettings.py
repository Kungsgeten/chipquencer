import pygame

import screen
import gui
import sequencer

from modeline import Modeline
from seqgrid import SeqGrid
from gui import ActionButton, TextField, Counter

SPACE = 5


class ClipSettings(screen.Screen):
    font = gui.FONT_BIG

    def __init__(self, clip=None):
        self.new = True
        self.clip = clip
        if clip is not None:
            self.new = False

        BUTTON_SIZE = BUTTON_WIDTH, BUTTON_HEIGHT = (135, 27)

        ypos = SPACE
        self.instrument_button = ActionButton((SPACE, ypos),
                                              BUTTON_SIZE,
                                              "Instrument",
                                              True, True)

        name = clip.part.name if clip else 'Unnamed'
        ypos += SPACE + BUTTON_HEIGHT
        self.name_field = TextField((SPACE, ypos),
                                    BUTTON_SIZE,
                                    name,
                                    True, True)

        ypos += SPACE + BUTTON_HEIGHT
        channel = clip.part.channel if clip else 1
        self.channel_counter = Counter((SPACE, ypos),
                                       BUTTON_HEIGHT,
                                       'Channel', 1, 16,
                                       channel)

        ypos += SPACE + BUTTON_HEIGHT
        editor = clip.__name__ if clip else 'Editor'
        self.editor_button = ActionButton((SPACE, ypos),
                                          BUTTON_SIZE,
                                          editor,
                                          True, True)

    def _update(self, events):
        self.has_changed = True
        self.name_field.update(events)
        self.channel_counter.update(events)

    def _render_button(self, surface, button, text):
        text = self.font.render(text, False, gui.C_DARKER)
        x = button.rect.x
        y = button.rect.centery - text.get_rect().height / 2
        width = button.rect.width
        surface.blit(text, (x + width + SPACE, y))
        button.render(surface)

    def _render(self, surface):
        self.instrument_button.render(surface)
        self.name_field.render(surface)
        self.channel_counter.render(surface)
        self.editor_button.render(surface)
        return surface

    def close(self):
        if self.new:
            part = sequencer.Part(self.name_field.text, 16,
                                  self.channel_counter.value - 1)
            clip = SeqGrid(part, 4, 4)
            sequencer.project['scenes'][sequencer.current_scene].append(clip)
