import pygame

import seqgrid
import seqdrum
import sequencer
import screen
import settings
import gui

from modeline import Modeline
from choicelist import ChoiceList
from gui import ActionButton, Counter

class TextInput(screen.Screen):
    pygame.font.init()
    STRING_HEIGHT = 20
    KEY_HEIGHT = 32
    keyfont = pygame.font.SysFont('Consolas', 16)
    stringfont = pygame.font.SysFont('Consolas', 16)
    def __init__(self, modelinetext='', default=''):
        self.returnkey = modelinetext.lower().replace(' ', '_')
        self.modeline = Modeline()
        self.modeline.strings = ['<-', '->', 'Delete', 'OK']
        self.text = default
        self.pos = len(default)
        keyrows = ('1234567890',
                   'QWERTYUIOP',
                   'ASDFGHJKL:',
                   'ZXCVBNM_ ')
        self.keyboard = []
        for r, row in enumerate(keyrows):
            for k, key in enumerate(row):
                pos = (self.KEY_HEIGHT * k, self.STRING_HEIGHT + self.KEY_HEIGHT * r)
                rect = pygame.Rect(pos, (self.KEY_HEIGHT, self.KEY_HEIGHT))
                self.keyboard.append((key, rect))

    def insert_letter(self, char):
        self.text = self.text[:self.pos] + char + self.text[self.pos:]
        self.pos += 1

    def _update(self, events):
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN:
                for k in self.keyboard:
                    key, rect = k
                    if rect.collidepoint(e.pos):
                        self.has_changed = True
                        self.insert_letter(key)
                        return

    def _render(self, surface):
        caption = self.stringfont.render(self.text, False, gui.C_DARKER)
        surface.blit(caption, (0, 0))

        for k in self.keyboard:
            key, rect = k
            pos = rect.topleft
            rectcolor = gui.C_PRIMARY
            pygame.draw.rect(surface, rectcolor, rect, True)
            cap = self.keyfont.render(key, False, gui.C_DARKER)
            surface.blit(cap, pos)

        letterwidth, letterheight = self.stringfont.size('A')
        caretx = self.pos * letterwidth
        pygame.draw.line(surface, gui.C_DARKEST, (caretx, 0), (caretx, letterheight))

        self.modeline.render(surface)
        return surface

class PartEdit(screen.Screen):
    pygame.font.init()
    font = pygame.font.SysFont('Arial', 16)

    def __init__(self, part, sequencer):
        self.part = part
        self.sequencer = sequencer
        self.modeline = Modeline()
        self.modeline.strings = ['Grid', 'Drum', '', 'Cancel']

        self.instrument_name = ''

        # Buttons
        button_size = self.button_width, self.button_height = (80, 27)
        self.button_spacing = 5
        instrument_pos = (self.button_spacing, self.button_spacing)
        self.instrument_button = ActionButton(instrument_pos, button_size, "Instrument")
        name_pos = (self.button_spacing,
                    self.button_spacing + (self.button_spacing + self.button_height) * 1)
        self.name_button = ActionButton(name_pos, button_size, "Name")
        channel_pos = (self.button_spacing,
                       self.button_spacing + (self.button_spacing + self.button_height) * 2)
        self.channel_counter = Counter(channel_pos, self.button_height, 'Channel', 1, 16)

    def focus(self, *args, **kwargs):
        if 'part_name' in kwargs:
            self.part.name = kwargs['part_name']
            if self.part.name == '':
                self.part.name = 'Part'
            self.inputtext = ''
        elif 'instrument' in kwargs:
            self.instrument_name = settings.INSTRUMENTS[kwargs['instrument']][0]
            self.part.name = self.instrument_name
            # TODO: Load instrument data

    # def _update_modeline(self, events):
    #     self.modeline.update(events)
    #     if self.modeline.buttons[0].pressed:
    #         self.part.channel = 2
    #         sequencer.parts.append(self.part)
    #         self.part.start()
    #         screen.seqs.append(seqgrid.SeqGrid(self.part))
    #         screen.pop()
    #         screen.stack[0].update_partrects()
    #     elif self.modeline.buttons[1].pressed:
    #         self.part.channel = 2
    #         sequencer.parts.append(self.part)
    #         self.part.start()
    #         screen.seqs.append(seqdrum.SeqDrum(self.part))
    #         screen.pop()
    #         screen.stack[0].update_partrects()
    #     elif self.modeline.buttons[3].pressed:
    #         screen.pop()

    def _update_buttons(self, events):
        if self.instrument_button.clicked(events):
            instruments = [[name[0], i] for i, name in enumerate(settings.INSTRUMENTS)]
            print instruments
            screen.stack.append(ChoiceList(instruments, 'Instrument'))
        elif self.name_button.clicked(events):
            screen.stack.append(TextInput('Part name', self.part.name))
        else:
            self.channel_counter.update(events)

    def _update(self, events):
        self.has_changed = True
        # if self.inputtext:
        #     self.part.name = self.inputtext
        #     if self.part.name == '':
        #         self.part.name = 'Part'
        #     self.inputtext = ''
        self._update_modeline(events)
        self._update_buttons(events)

    def _render_button(self, surface, button, text):
        text = self.font.render(text, False, gui.C_DARKER)
        x = button.rect.x
        y = button.rect.y
        surface.blit(text, (x + self.button_width + self.button_spacing,
                            y))
        button.render(surface)

    def _render(self, surface):
        self._render_button(surface, self.instrument_button, self.instrument_name)
        self._render_button(surface, self.name_button, self.part.name)

        self.channel_counter.render(surface)
        self.modeline.render(surface)
        return surface
