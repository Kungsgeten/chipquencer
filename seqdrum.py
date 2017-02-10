import midi
import sequencer
import gui
import event
import screen
import editors

from modeline import Modeline

import pygame
import yaml
import math

from enum import IntEnum

class ModelineSections(IntEnum):
    Measure = 0
    Velocity = 1


class SeqDrum(screen.Screen):
    STEP_HEIGHT = gui.SCREEN_WIDTH // 16
    font = gui.FONT_MEDIUM

    def __init__(self, part, width=16, rows=None):
        assert(part.length % width == 0)
        self.part = part
        self.modeline = Modeline(len(ModelineSections))
        self.width = width
        self.measure = 0
        self.velocity_input = 104
        self.last_curstep = -1
        if rows is None:
            self.rows = list()
        else:
            self.rows = rows
        self.grid = None

    @property
    def measures(self):
        return self.part.length // self.width

    @property
    def measure(self):
        return self._measure

    @measure.setter
    def measure(self, measure):
        self._measure = measure % self.measures
        measure_string = "M:{}/{}".format(self.measure + 1,
                                          self.measures)
        self.modeline[ModelineSections.Measure] = measure_string

    @property
    def velocity_input(self):
        return self._velocity_input

    @velocity_input.setter
    def velocity_input(self, value):
        self._velocity_input = value
        velocity_string = "Vel:{}".format(self._velocity_input)
        self.modeline[ModelineSections.Velocity] = velocity_string

    @staticmethod
    def clipsettings_gui(instance=None, yaml=None):
        """GUI for setting the width of the grid."""
        width = 16
        if instance is not None:
            width = instance.width
        if yaml is not None:
            for key, value in yaml.iteritems():
                if key == 'width':
                    width = value
        return (gui.Counter((300, 2), 30,
                            'Width', 4, 30, width),)

    @staticmethod
    def clipsettings_create(name, channel, measures, widgets):
        width_widget = widgets[0]
        width = width_widget.value
        part = sequencer.Part(name, measures * width, channel)
        return SeqDrum(part, width=width)

    def clipsettings_update(self, name, channel, measures, widgets):
        width_widget = widgets[0]
        width = width_widget.value
        length = width * measures
        self.part.name = name
        self.part.channel = channel
        self.part.length = length
        # TODO: Need to update the grid
        # self.set_grid(width, height)
        # self.selected = [Step(0, 0, -1)]
        if self.measure >= self.measures:
            self.measure = 0

    def step_width(self):
        return gui.SCREEN_WIDTH // self.width

    def _populate_grid_with_event(self, note_on_event):
        for i, row in enumerate(self.rows):
            for char, note in row.iteritems():
                if note == note_on_event.note:
                    col = int(note_on_event.timestamp)
                    if char == 'normal':
                        self.grid[i][col] = ' '
                    else:
                        self.grid[i][col] = char
                    return

    def part_to_grid(self):
        """Convert self.part data to self.grid"""
        self.grid = [[None] * self.part.length for r in self.rows]
        events = self.part.events('note_on')
        for e in events:
            self._populate_grid_with_event(e)

    def note_char_pressed(self, row):
        """Return if a key is pressed which matches a note in the row."""
        keys = pygame.key.get_pressed()
        for k in self.rows[row]:
            if k != 'normal' and keys[ord(k)]:
                return k
        return False

    def velocity_key(self):
        """Return a velocity if a number key is pressed."""
        keys = pygame.key.get_pressed()
        if keys[48]:  # The zero button
            return 127
        for i in range(49, 58):
            if keys[i]:
                i -= 48
                return i * 13
        return False

    def step_clicked(self, row, col):
        """Update status of a clicked step."""
        if self.grid[row][col] is None:  # Empty step
            char = self.note_char_pressed(row)
            if not char:
                char = ' '
            self.grid[row][col] = char
            if char == ' ':
                char = 'normal'

            note = self.rows[row][char]
            note_event = event.Event(col, event.note_on,
                                     [note, self.velocity_input, 1])
            self.part.append(note_event)
        else:
            new_velocity = self.velocity_key()
            for e in self.part.events('note_on'):
                if(e.timestamp == col
                   and e.note in self.rows[row].values()):
                    if new_velocity:
                        e.velocity = new_velocity
                        return
                    self.grid[row][col] = None
                    self.part.delete(e)
                    return

    def _update(self, events):
        curstep = math.floor(sequencer.running_time % self.part.length)
        self.has_changed = curstep != self.last_curstep
        self.last_curstep = curstep
        self.velocity_input = self.velocity_key() or self.velocity_input
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and len(self.rows):
                x, y = e.pos
                row = y // self.STEP_HEIGHT
                if row < len(self.grid):
                    col = x // self.step_width() + self.measure * self.width
                    self.step_clicked(row, col)
            elif e.type == pygame.KEYDOWN:
                mods = pygame.key.get_mods()
                if mods & pygame.KMOD_SHIFT:
                    if e.key == pygame.K_o:  # Options
                        screen.stack.append(RowEditor(self))

    def _render(self, surface):
        self.modeline.render(surface)
        if len(self.rows) == 0:
            string = 'Press Shift + O to add rows.'
            text = self.font.render(string, False, gui.C_DARKEST)
            surface.blit(text, (10, 10))
            return surface
        curstep = math.floor(sequencer.running_time % self.part.length)
        for row in range(len(self.grid)):
            for col, data in enumerate(self.grid[row]):
                pos = ((col % self.width) * self.step_width(),
                       row * self.STEP_HEIGHT)
                rect = pygame.Rect(pos, (self.step_width(), self.STEP_HEIGHT))
                rectcolor = gui.C_PRIMARY
                if col % 4 == 0:
                    rectcolor = gui.C_DARKER
                if curstep == col + self.measure * self.width:
                    rectcolor = gui.C_LIGHTEST
                pygame.draw.rect(surface, rectcolor, rect, not bool(data))
                if data is not None and data != ' ':
                    text = self.font.render(data, False, gui.C_DARKEST)
                    surface.blit(text, pos)
        return surface

    def focus(self, *args, **kwargs):
        self.part_to_grid()


# YAML SeqDrum representation
def seqdrum_representer(dumper, data):
    mapping = {'part': data.part,
               'width': data.width,
               'rows': data.rows}
    return dumper.represent_mapping(u'!seqdrum', mapping)


def seqdrum_constructor(loader, node):
    m = loader.construct_mapping(node)
    return SeqDrum(m['part'], m['width'], m['rows'])

editors.editors.append(["Drums", SeqDrum])
yaml.add_representer(SeqDrum, seqdrum_representer)
yaml.add_constructor(u'!seqdrum', seqdrum_constructor)


class RowEditor(screen.Screen):
    """Class for editing/inserting rows in a SeqDrum."""
    rowfont = gui.FONT_BIG
    KEYBOARD_KEYS = {pygame.K_z: 0,
                     pygame.K_s: 1,
                     pygame.K_x: 2,
                     pygame.K_d: 3,
                     pygame.K_c: 4,
                     pygame.K_v: 5,
                     pygame.K_g: 6,
                     pygame.K_b: 7,
                     pygame.K_h: 8,
                     pygame.K_n: 9,
                     pygame.K_j: 10,
                     pygame.K_m: 11,
                     pygame.K_PERIOD: 12}

    def __init__(self, seqdrum):
        self.modeline = Modeline(2)
        self.seqdrum = seqdrum
        self.row = 0
        self.STEP_SIZE = seqdrum.STEP_HEIGHT
        self.keyboard_root = 36
        self.note = 36

    @property
    def keyboard_root(self):
        return self._kb_root

    @keyboard_root.setter
    def keyboard_root(self, note):
        self._kb_root = note % 127
        octave_string = 'Octave: ' + midi.note_to_string(self._kb_root)[2]
        self.modeline[0] = octave_string

    @property
    def note(self):
        return self._note

    @note.setter
    def note(self, value):
        self._note = value
        note_string = 'Note:{} ({})'.format(value, midi.note_to_string(value))
        self.modeline[1] = note_string

    def _update(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN:
                self.has_changed = True
                mods = pygame.key.get_mods()
                note = None
                # Key corresponds to the virtual keyboard?
                if e.key in self.KEYBOARD_KEYS:
                    note = self.keyboard_root + self.KEYBOARD_KEYS[e.key]
                # Navigate between/move rows
                if e.key == pygame.K_DOWN and len(self.seqdrum.rows):
                    if mods & pygame.KMOD_SHIFT:
                        rows = self.seqdrum.rows
                        rows.insert((self.row + 1) % len(rows),
                                    rows.pop(self.row))
                    self.row += 1
                    self.row = self.row % len(self.seqdrum.rows)
                elif e.key == pygame.K_UP and len(self.seqdrum.rows):
                    if mods & pygame.KMOD_SHIFT:
                        rows = self.seqdrum.rows
                        rows.insert((self.row - 1) % len(rows),
                                    rows.pop(self.row))
                    self.row -= 1
                    self.row = self.row % len(self.seqdrum.rows)
                # Insert note in selected row
                elif mods & pygame.KMOD_SHIFT:
                    if e.key in range(97, 123):
                        self.seqdrum.rows[self.row][chr(e.key)] = self.note
                    elif e.key == pygame.K_SPACE:
                        self.seqdrum.rows[self.row]['normal'] = self.note
                # Transpose the virtual keyboard
                elif e.key == pygame.K_TAB:
                    self.keyboard_root -= 12
                    self.keyboard_root = self.keyboard_root % 127
                elif e.key == pygame.K_RETURN:
                    self.keyboard_root += 12
                    self.keyboard_root = self.keyboard_root % 127
                # Insert new row
                elif e.key == pygame.K_RIGHT:
                    self.seqdrum.rows.append({'normal': self.note})
                # Delete selected row
                elif e.key == pygame.K_LEFT:
                    self.seqdrum.rows.pop(self.row)
                # Play the virtual keyboard
                elif note is not None:
                    msg = self.seqdrum.part.channel + midi.NOTE_ON
                    ts = pygame.midi.time()
                    data = [[[msg, note, 127], ts],
                            [[msg, note, 0], ts + 500]]
                    midi.out.write(data)
                    self.note = note

    def _render(self, surface):
        for i, row in enumerate(self.seqdrum.rows):
            rect = pygame.Rect((0, i * self.STEP_SIZE),
                               (self.STEP_SIZE, self.STEP_SIZE))
            rectcolor = gui.C_PRIMARY
            if self.row == i:
                rectcolor = gui.C_DARKER
            pygame.draw.rect(surface, rectcolor, rect, self.row != i)
            string = ', '.join(['{}={}'.format(c, n)
                                for c, n in self.seqdrum.rows[i].iteritems()])
            text = self.rowfont.render(string, False, gui.C_DARKEST)
            surface.blit(text, (self.STEP_SIZE + 3, i * self.STEP_SIZE + 7))
        self.modeline.render(surface)
        return surface
