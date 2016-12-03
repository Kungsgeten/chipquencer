import pygame

import screen
import gui
import sequencer
import editors
import midi

from modeline import Modeline
from choicelist import ChoiceList
from gui import ActionButton, TextField, Counter

SPACE = 5


class ClipSettings(screen.Screen):
    font = gui.FONT_BIG

    def __init__(self, clip=None):
        self.new = True
        self.clip = clip
        if clip is not None:
            self.new = False

        # General settings
        # - Instrument
        # - Name
        # - Channel
        # - Program
        # - Editor
        # - Measures

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
        channel = clip.part.channel + 1 if clip else 1
        self.channel_counter = Counter((SPACE, ypos),
                                       BUTTON_HEIGHT,
                                       'Channel', 1, 16,
                                       channel)

        ypos += SPACE + BUTTON_HEIGHT
        program = clip.part.program if clip else 0
        self.program_counter = Counter((SPACE, ypos),
                                       BUTTON_HEIGHT,
                                       'Program', 0, 128,
                                       program)


        ypos += SPACE + BUTTON_HEIGHT
        measures = clip.measures if clip else 1
        self.measures_counter = Counter((SPACE, ypos),
                                        BUTTON_HEIGHT,
                                        'Measures', 1, 256,
                                        measures)

        ypos += SPACE + BUTTON_HEIGHT
        editor = clip.__class__.__name__ if clip else 'Editor'
        self.editor_button = ActionButton((SPACE, ypos),
                                          BUTTON_SIZE,
                                          editor,
                                          True, True)
        self.editor_gui = clip.clipsettings_gui(clip) if clip else ()

    def _update(self, events):
        self.has_changed = True
        self.name_field.update(events)
        self.channel_counter.update(events)
        if self.program_counter.update(events) and self.clip is not None:
            part = self.clip.part
            program = self.program_counter.value
            if program > 0:
                midi.out.write_short(midi.PC + part.channel, program)
        self.measures_counter.update(events)
        if self.clip is None and self.editor_button.clicked(events):
            screen.stack.append(ChoiceList(editors.editors, 'Editor'))

        for widget in self.editor_gui:
            widget.update(events)

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
        self.program_counter.render(surface)
        self.measures_counter.render(surface)
        if self.clip is None:
            self.editor_button.render(surface)

        for widget in self.editor_gui:
            widget.render(surface)

        return surface

    def focus(self, *args, **kwargs):
        if 'editor' in kwargs:
            self.clip = kwargs['editor']
            self.editor_gui = self.clip.clipsettings_gui()
            # self.editor_button.text = self.clip.__name__

    def close(self):
        if self.clip is None:
            return
        if self.new:
            clip = self.clip.clipsettings_create(self.name_field.text,
                                                 self.channel_counter.value - 1,
                                                 self.measures_counter.value,
                                                 self.editor_gui)
            program = self.program_counter.value
            clip.part.program = program
            if program > 0:
                midi.out.write_short(midi.PC + self.channel_counter.value - 1,
                                     program)
            sequencer.project['scenes'][sequencer.current_scene].append(clip)
        else:
            self.clip.clipsettings_update(self.name_field.text,
                                          self.channel_counter.value - 1,
                                          self.measures_counter.value,
                                          self.editor_gui)
            self.clip.part.program = self.program_counter.value
