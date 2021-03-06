import pygame
import yaml

from glob import glob

import screen
import gui
import sequencer
import editors
import midi

from modeline import Modeline
from choicelist import ChoiceList
from gui import ActionButton, TextField, Counter

SPACE = 5
instruments = [[yaml.load(file(f, 'r'))['name'], f]
               for f in glob('instruments/*.yml')]


class ClipSettings(screen.Screen):
    font = gui.FONT_BIG

    def __init__(self, clip=None):
        self.cc = None
        self.new = True
        self.clip = clip
        if clip is not None:
            self.new = False

        # General settings
        # - Instrument
        # - Name
        # - Channel
        # - Bank
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
        bank = clip.part.bank if clip else 0
        self.bank_counter = Counter((SPACE, ypos),
                                    BUTTON_HEIGHT,
                                    'Bank', 0, 128,
                                    bank)

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
        self.editor_gui = clip.clipsettings_gui(instance=clip) if clip else ()

    def _update(self, events):
        self.has_changed = True
        self.name_field.update(events)
        self.channel_counter.update(events)
        self.measures_counter.update(events)
        if self.bank_counter.update(events) and not self.new:
            part = self.clip.part
            bank = self.bank_counter.value
            program = self.program_counter.value
            if bank > 0 and program > 0:
                midi.out.write_short(midi.CC + part.channel, 32, bank - 1)
                midi.out.write_short(midi.PC + part.channel, program - 1)
        if self.program_counter.update(events) and not self.new:
            part = self.clip.part
            program = self.program_counter.value
            if program > 0:
                midi.out.write_short(midi.PC + part.channel, program - 1)
        if self.clip is None and self.editor_button.clicked(events):
            screen.stack.append(ChoiceList(editors.editors, 'Editor'))
        if self.clip is None and self.instrument_button.clicked(events):
            screen.stack.append(ChoiceList(instruments, 'Instrument'))

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
        self.bank_counter.render(surface)
        self.program_counter.render(surface)
        self.measures_counter.render(surface)
        if self.clip is None:
            self.editor_button.render(surface)

        for widget in self.editor_gui:
            widget.render(surface)

        return surface

    def load_editor(self, editor_cls):
        """Set the editor class and load clipsettings_gui."""
        self.clip = editor_cls
        self.editor_gui = self.clip.clipsettings_gui()

    def load_instrument(self, instrument_file):
        """Load clip settings from instrument_file."""
        inst_dict = yaml.load(file(instrument_file, 'r'))
        for key, value in inst_dict.iteritems():
            if key == 'name' and self.name_field.text == 'Unnamed':
                self.name_field.text = value
            elif key == 'channel':
                self.channel_counter.value = value
            elif key == 'program':
                self.program_counter.value = value
            elif key == 'bank':
                self.bank_counter.value = value
            elif key == 'measures':
                self.measures_counter.value = value
            elif key == 'editor':
                editor_cls = dict(editors.editors)[value['type']]
                self.clip = editor_cls
                self.editor_gui = editor_cls.clipsettings_gui(yaml=value)
            elif key == 'cc':
                self.cc = value

    def focus(self, *args, **kwargs):
        for key, value in kwargs.iteritems():
            if key == 'editor':
                self.load_editor(value)
            elif key == 'instrument':
                self.load_instrument(value)

    def close(self):
        if self.clip is None:
            return

        channel = self.channel_counter.value - 1
        bank = self.bank_counter.value
        program = self.program_counter.value
        if self.new:
            clip = self.clip.clipsettings_create(self.name_field.text,
                                                 channel,
                                                 self.measures_counter.value,
                                                 self.editor_gui)
            clip.part.bank = bank
            clip.part.program = program
            if self.cc is not None:
                clip.part.cc = self.cc
            if bank > 0:
                midi.out.write_short(midi.CC + channel, 32, bank - 1)
            if program > 0:
                midi.out.write_short(midi.PC + channel, program - 1)
            sequencer.scene().append(clip)
        else:
            self.clip.clipsettings_update(self.name_field.text,
                                          channel,
                                          self.measures_counter.value,
                                          self.editor_gui)
            self.clip.part.bank = bank
            self.clip.part.program = program
