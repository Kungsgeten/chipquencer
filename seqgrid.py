import midi
import sequencer
import gui
import event
import screen
import editors

from gui import RadioButtons, Slider
from modeline import Modeline
from clipsettings import ClipSettings

import pygame
import math
import yaml

from enum import IntEnum
from collections import namedtuple

Step = namedtuple('Step', 'x y index')
Step.pos = lambda self: (self.x, self.y)


class Radio(IntEnum):
    Velocity = 0
    Length = 1
    CC = 2


class KeyboardMode(IntEnum):
    Tap = 0
    Step = 1
    RealTime = 2


class ModelineSections(IntEnum):
    Measure = 0
    Root = 1
    KeyboardMode = 2


class SeqGrid(screen.Screen):
    """A sequencer screen representing a part as a grid.

    The main purpose is melodic content. The part may be split up into equally
    long measures. Often operation will be executed upon the selected steps in
    the grid. There's also a menu where the notes' velocity, offset and length
    can be modified.

    """
    font = gui.FONT_MEDIUM

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

    VEL_PRESETS = {0: midi.PP, 1: midi.P,
                   2: midi.MP, 3: midi.MF,
                   4: midi.F,  5: midi.FF}

    # '2', '4', '8', '16', '32', '.'
    LEN_PRESETS = {0: 8,
                   1: 4,
                   2: 2,
                   3: 1,
                   4: 0.5}

    MENU_WIDTH = 133
    GRID_WIDTH = gui.SCREEN_WIDTH - MENU_WIDTH

    def __init__(self, part, width=4, height=4,
                 kb_root=60, kb_mode=KeyboardMode.Tap):
        self.part = part
        self.modeline = Modeline(len(ModelineSections))
        self.set_grid(width, height)
        self.selected = [Step(0, 0, -1)]
        self.step_dragged = None

        self.keyboard_root = kb_root
        self.keyboard_mode = kb_mode
        self.key_notes_pressed = []
        km_modeline_element = ModelineSections.KeyboardMode
        self.modeline.strings[km_modeline_element] = self.keyboard_mode.name

        # Menu
        SPACE = 2
        ITEM_SIZE = self.MENU_WIDTH / 3 - SPACE

        # Radio buttons
        strings = 'Vel', 'Len', 'CC'
        self.radios = RadioButtons((self.GRID_WIDTH, SPACE),
                                   (ITEM_SIZE, ITEM_SIZE),
                                   3, 1, strings, SPACE)
        self.preset_radios = RadioButtons((self.GRID_WIDTH,
                                           ITEM_SIZE + SPACE * 2),
                                          (ITEM_SIZE, ITEM_SIZE),
                                          2, 3, [], SPACE)

        # Slider
        SLIDER_H = gui.SCREEN_HEIGHT - ITEM_SIZE - SPACE * 3 - Modeline.HEIGHT
        self.slider = Slider(pygame.Rect(gui.SCREEN_WIDTH - ITEM_SIZE - SPACE - 1,
                                         ITEM_SIZE + SPACE * 2,
                                         ITEM_SIZE, SLIDER_H))

        # CC list
        cc_strings = [str(cc) + ' ' + name for cc, name in part.cc]
        self.cc_list = gui.ScrollList((self.GRID_WIDTH,
                                       ITEM_SIZE + SPACE * 2),
                                      (ITEM_SIZE * 2 + SPACE, SLIDER_H),
                                      ITEM_SIZE, cc_strings, SPACE)

        self.last_vel = 120
        self.last_length = 1.0
        self.last_cc = 0.0

        self.measure = 0

    @property
    def keyboard_root(self):
        return self._keyboard_root

    @keyboard_root.setter
    def keyboard_root(self, note):
        self._keyboard_root = note % 127
        note_string = midi.note_to_string(self._keyboard_root)
        self.modeline[ModelineSections.Root] = note_string

    @property
    def measures(self):
        measure_steps = len(self.grid) * len(self.grid[0])
        return self.part.length // measure_steps

    @property
    def measure(self):
        return self._measure

    @measure.setter
    def measure(self, measure):
        self._measure = measure % self.measures
        measure_string = "M:{}/{}".format(self.measure + 1,
                                          self.measures)
        self.modeline[ModelineSections.Measure] = measure_string

    @staticmethod
    def clipsettings_gui(instance=None, yaml=None):
        width = 4
        height = 4
        if instance is not None:
            width = len(instance.grid)
            height = len(instance.grid[0])
        if yaml is not None:
            for key, value in yaml.iteritems():
                if key == 'width':
                    width = value
                elif key == 'height':
                    height = value
        return (gui.Counter((300, 2), 30,
                            'Width', 1, 16, width),
                gui.Counter((300, 34), 30,
                            'Height', 1, 16, height))

    @staticmethod
    def clipsettings_create(name, channel, measures, widgets):
        width_widget, height_widget = widgets
        width = width_widget.value
        height = height_widget.value
        part = sequencer.Part(name, measures * width * height, channel)
        return SeqGrid(part, width, height)

    def clipsettings_update(self, name, channel, measures, widgets):
        width_widget, height_widget = widgets
        width = width_widget.value
        height = height_widget.value
        length = width * height * measures
        self.part.name = name
        self.part.channel = channel
        self.part.length = length
        self.set_grid(width, height)
        self.selected = [Step(0, 0, -1)]
        if self.measure >= self.measures:
            self.measure = 0

    def set_grid(self, width, height):
        """Set the size of self.grid and populate it with rects."""
        assert(self.part.length % (width * height) == 0)
        step_w = self.GRID_WIDTH // width
        step_h = (gui.SCREEN_HEIGHT - Modeline.HEIGHT) // height
        step_size = step_w, step_h

        self.grid = [[pygame.Rect((x * step_w, y * step_h), step_size)
                      for y in range(height)] for x in range(width)]

    def step_timestamp(self, x, y):
        measure_steps = len(self.grid) * len(self.grid[0])
        return x + y * len(self.grid) + measure_steps * self.measure

    def step_events(self, x, y, type=None):
        """Return events at step x, y."""
        ts = self.step_timestamp(x, y)
        return [e for e in self.part.events(type) if int(e.timestamp) == ts]

    def selected_events(self, type=None):
        """Return a list of all selected events of a specific type."""
        return [e for step in self.selected
                for i, e in (enumerate(self.step_events(*step.pos())))
                if (e.type() == type
                    and (step.index < 0 or step.index == i))]

    def step_at_pos(self, pos):
        """Get step at pos' grid position as a (x, y) tuple."""
        cols = len(self.grid)
        rows = len(self.grid[0])
        step_width, step_height = self.grid[0][0].size
        grid_width = cols * step_width  # self.GRID_WIDTH seems to be off
        grid_height = rows * step_height

        x, y = pos

        if(x < grid_width and y < grid_height):
            return (x // self.grid[0][0].width, y // self.grid[0][0].height)
        return None

    def step_clicked(self, x, y):
        self.step_dragged = (x, y)
        self.has_changed = True
        mods = pygame.key.get_mods()
        keys = pygame.key.get_pressed()
        if(mods & pygame.KMOD_CTRL and
           (x, y) in [s.pos() for s in self.selected]):
            for i, step in enumerate(self.selected):
                if step.pos() == (x, y):
                    events = self.step_events(x, y)
                    index = (step.index + 1) % len(events)
                    self.selected[i] = Step(x, y, index)
                    break
        # Hold E and click step to set "end" (length)
        elif keys[pygame.K_e] and len(self.selected) == 1:
            new_ts = self.step_timestamp(x, y)
            for e in self.selected_events('note_on'):
                e.length = new_ts + 1 - e.timestamp
                self.last_length = e.length
        else:
            if not mods & pygame.KMOD_SHIFT:
                self.selected = []
            self.selected.append(Step(x, y, -1))

        if self.keyboard_mode is KeyboardMode.Tap:
            pressed_keys = pygame.key.get_pressed()
            for key in self.KEYBOARD_KEYS.keys():
                if pressed_keys[key]:
                    note = self.keyboard_root + self.KEYBOARD_KEYS[key]
                    self.new_note_at_step(note, x, y)

        step_to_update = None
        for step in self.selected:
            if step.pos() == (x, y):
                step_to_update = step
                break

        self.refresh_slider(step_to_update)

    def delete_step(self, x, y, type=None):
        """Delete all events of given type at self.grid[x][y]."""
        for e in self.step_events(x, y, type=type):
            self.part.delete(e)

    def delete_selected(self):
        for x, y, index in self.selected:
            if index < 0:
                self.delete_step(x, y, type='note_on')
                continue
            events = self.step_events(x, y)
            if len(events):
                self.part.delete(events[index])

    def new_note_at_step(self, note, x, y):
        ts = self.step_timestamp(x, y)
        note_event = event.Event(ts,
                                 event.note_on,
                                 [note, self.last_vel, self.last_length])
        self.part.append(note_event)

    def keyboard_mode_cycle(self):
        """Cycle between keyboard modes."""
        kbm_value = (self.keyboard_mode.value + 1) % len(KeyboardMode)
        self.keyboard_mode = KeyboardMode(kbm_value)
        km_modeline_element = ModelineSections.KeyboardMode
        self.modeline.strings[km_modeline_element] = self.keyboard_mode.name
        self.key_notes_pressed = []

    def keyboard_play(self, note):
        """Act on the keyboard note played, depend on self.keyboard_mode."""
        self.has_changed = True

        if(not sequencer.running or
           self.keyboard_mode is not KeyboardMode.Step):
            midi.out.write_short(self.part.channel + midi.NOTE_ON, note, 127)

        if self.keyboard_mode is KeyboardMode.Step:
            self.key_notes_pressed.append(note)

        elif self.keyboard_mode is KeyboardMode.RealTime:
            if not sequencer.running:
                if self.selected:
                    self.new_note_at_step(note, *self.selected[0].pos())
                return

            ts = int(round(sequencer.running_time)) % self.part.length
            note_event = event.Event(ts,
                                     event.note_on,
                                     [note, self.last_vel, self.last_length])
            self.part.append(note_event)

    def keydown_events(self, keyevents):
        """Handle pygame keydown events."""
        mods = pygame.key.get_mods()
        for e in keyevents:
            if mods & pygame.KMOD_SHIFT:
                # Transpose selected steps one octave
                if e.key == pygame.K_PLUS:
                    for e in self.selected_events('note_on'):
                        e.note += 12
                elif e.key == pygame.K_MINUS:
                    for e in self.selected_events('note_on'):
                        e.note -= 12
            elif mods & pygame.KMOD_CTRL:
                pass
            elif mods & pygame.KMOD_ALT:
                # Transpose entire part one semitone
                if e.key == pygame.K_PLUS:
                    self.part.tranpose(1)
                elif e.key == pygame.K_MINUS:
                    self.part.tranpose(-1)
            else:
                # Play keyboard
                if e.key in self.KEYBOARD_KEYS:
                    note = self.keyboard_root + self.KEYBOARD_KEYS[e.key]
                    self.keyboard_play(note)
                # KB Octave down
                elif e.key == pygame.K_TAB:
                    self.keyboard_root -= 12
                # KB Octave up
                elif e.key == pygame.K_RETURN:
                    self.keyboard_root += 12
                # KB Semitone down
                elif e.key == pygame.K_a:
                    self.keyboard_root -= 1
                # KB Semitone up
                elif e.key == pygame.K_l:
                    self.keyboard_root += 1
                # Cycle keyboard mode
                elif e.key == pygame.K_SLASH or e.key == pygame.K_t:
                    self.keyboard_mode_cycle()
                # Next measure
                elif e.key == pygame.K_DOWN:
                    self.measure += 1
                # Previous measure
                elif e.key == pygame.K_UP:
                    self.measure -= 1
                # Delete selected steps
                elif e.key == pygame.K_y:
                    self.delete_selected()
                # Edit clip
                elif e.key == pygame.K_o:
                    screen.stack.append(ClipSettings(self))
                # Transpose selected steps one semitone
                elif e.key == pygame.K_PLUS:
                    for e in self.selected_events('note_on'):
                        e.note += 1
                elif e.key == pygame.K_MINUS:
                    for e in self.selected_events('note_on'):
                        e.note -= 1

    def keyup_events(self, keyevents):
        for e in keyevents:
            if(self.keyboard_mode is KeyboardMode.Step
               and len(self.key_notes_pressed)):
                self.key_notes_pressed.sort()
                for x, y, index in self.selected:
                    self.delete_step(x, y, 'note_on')
                    for note in self.key_notes_pressed:
                        self.new_note_at_step(note, x, y)
            self.key_notes_pressed = []

            if e.key in self.KEYBOARD_KEYS:
                note = self.keyboard_root + self.KEYBOARD_KEYS[e.key]
                midi.out.write_short(self.part.channel + midi.NOTE_ON, note, 0)

    def refresh_slider(self, step=None):
        """Update shown slider data."""
        self.has_changed = True
        if step is not None:
            if self.radios.selected == Radio.CC:
                for i, e in enumerate(self.step_events(step.x, step.y, 'cc')):
                    if step.index >= 0 and i != step.index:
                        self.slider.set_value(e.data, 127)
                        return
                return
            for i, e in enumerate(self.step_events(step.x, step.y, 'note_on')):
                if step.index >= 0 and i != step.index:
                    continue
                if self.radios.selected == Radio.Velocity:
                    self.slider.set_value(e.velocity, 127)
                    self.last_vel = e.velocity
                    return
                if self.radios.selected == Radio.Length:
                    length_offset = e.length % 1
                    if length_offset == 0.0:
                        length_offset = 1.0
                    self.slider.set_value(length_offset, 1.0)
                    return
            return

        if self.radios.selected == Radio.Velocity:
            self.slider.set_value(self.last_vel, 127)
        elif self.radios.selected == Radio.Length:
            self.slider.set_value(1.0, 1.0)
        elif self.radios.selected == Radio.CC:
            self.slider.set_value(self.last_cc, 127)

    def update_radio_buttons(self, events):
        """Handle events related to self.radios."""
        clicked = self.radios.update(events)
        if clicked is not None:
            self.has_changed = True
            self.preset_radios.selected = -1
            strings = []
            if clicked == Radio.Velocity:
                strings = 'pp', 'p', 'mp', 'mf', 'f', 'ff'
            elif clicked == Radio.Length:
                strings = '2', '4', '8', '16', '32', '.'
            elif clicked == Radio.CC:
                self.cc_list.strings = [str(cc) + ' ' + name
                                        for cc, name in self.part.cc]
            self.preset_radios.strings = strings
            self.refresh_slider()

    def update_slider_and_presets(self, events):
        """Handle events related to self.slider and self.preset_radios."""
        presetclick = None
        cc_clicked = None
        if self.radios.selected == Radio.CC:
            cc_clicked = self.cc_list.update(events)
        else:
            presetclick = self.preset_radios.update(events)
            if presetclick is not None:
                if self.radios.selected == Radio.Velocity:
                    self.slider.set_value(self.VEL_PRESETS[presetclick], 127)
                elif self.radios.selected == Radio.Length:
                    for e in self.selected_events('note_on'):
                        # Dotted
                        if presetclick == 5:
                            e.length *= 1.5
                        else:
                            e.length = self.LEN_PRESETS[presetclick]
                        self.last_length = e.length
                    return

        slided = self.slider.update(events)
        if slided is not None or presetclick is not None or cc_clicked is not None:
            self.has_changed = True

            if self.radios.selected == Radio.CC:
                cc_val = int(127 * self.slider.get_data())
                self.last_cc = cc_val
                # cc_events = self.selected_events('cc')
                cc_number = self.part.cc[self.cc_list.selected][0]
                if slided:
                    # New CC events
                    for step in self.selected:
                        for e in self.step_events(step.x, step.y, 'cc'):
                            if e.cc == cc_number:
                                e.data = cc_val
                                break
                        else:
                            ts = self.step_timestamp(step.x, step.y)
                            new_cc_event = event.Event(ts, event.cc,
                                                       [cc_number, cc_val])
                            self.part.append(new_cc_event)
                return

            vel = int(self.slider.get_data() * 126) + 1
            length_offset = self.slider.get_data() * 1.0
            if self.radios.selected == Radio.Velocity:
                self.last_vel = vel

            for e in self.selected_events('note_on'):
                if self.radios.selected == Radio.Velocity:
                    e.velocity = vel
                elif self.radios.selected == Radio.Length:
                    subtract = 0
                    if e.length % 1 == 0:
                        subtract = 1
                    e.length = math.floor(e.length) + length_offset - subtract
                    self.last_length = e.length

    def _update(self, events):
        self.has_changed = sequencer.new_step

        self.keydown_events((e for e in events if e.type == pygame.KEYDOWN))
        self.keyup_events((e for e in events if e.type == pygame.KEYUP))

        self.update_radio_buttons(events)
        self.update_slider_and_presets(events)

        # keys = pygame.key.get_pressed()

        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN:
                step = self.step_at_pos(e.pos)
                if step:
                    self.step_clicked(*step)
            elif e.type == pygame.MOUSEBUTTONUP:
                if self.step_dragged:
                    step = self.step_at_pos(e.pos)
                    # Drag outside grid to delete
                    if step is None:
                        self.delete_step(*self.step_dragged)
                    # Drag to another step to copy/replace
                    elif step != self.step_dragged:
                        new_ts = self.step_timestamp(*step)
                        self.delete_step(*step)
                        for ev in self.step_events(*self.step_dragged):
                            copy = event.Event(new_ts + ev.timestamp % 1,
                                               ev.function,
                                               ev.params)
                            self.part.append(copy)
                self.step_dragged = None

    def render_step_events(self, surface, x, y):
        xpos, ypos = self.grid[x][y].topleft
        for i, e in enumerate(self.step_events(x, y)):
            string = '???'
            event_type = e.type()
            if event_type == 'note_on':
                string = midi.note_to_string(e.note)
            elif event_type == 'cc':
                string = '{}={}'.format(e.cc, e.data)
            color = gui.C_DARKEST
            if (x, y) in [step.pos() for step in self.selected
                          if step.index < 0 or step.index == i]:
                color = gui.C_LIGHTEST
            text = self.font.render(string, False, color)
            surface.blit(text, (xpos + 2, ypos + 2))
            ypos += text.get_rect().height

    def render_selected_steps_data(self, surface):
        """Render velocity / length / offset data on selected notes."""
        cols = len(self.grid)
        rows = len(self.grid[0])
        step_width, step_height = self.grid[0][0].size
        grid_width = cols * step_width  # self.GRID_WIDTH seems to be off

        for step in self.selected:
            if not self.step_events(step.x, step.y, 'note_on'):
                continue

            xpos, ypos = self.grid[step.x][step.y].topleft

            if self.radios.selected == Radio.Length:
                ypos += step_height * 0.25
                for e in self.step_events(step.x, step.y, 'note_on'):
                    pixel_length = e.length * step_width
                    break
                while xpos + pixel_length >= grid_width:
                    grid_remainder = grid_width - xpos
                    pixel_length -= grid_remainder
                    lenrect = pygame.Rect(xpos, ypos,
                                          grid_remainder, step_height / 2)
                    pygame.draw.rect(surface, gui.C_DARKER, lenrect, False)
                    xpos = 0
                    ypos = (ypos + step_height) % (step_height * rows)
                if pixel_length:
                    lenrect = pygame.Rect(xpos, ypos,
                                          pixel_length, step_height / 2)
                    pygame.draw.rect(surface, gui.C_DARKER, lenrect, False)

            # elif self.radios.selected == Radio.Offset:
            #     xpos += self.slider.get_data() * step_width
            #     pygame.draw.line(surface, gui.C_DARKER,
            #                      (xpos, ypos),
            #                      (xpos, ypos + step_height))

            elif self.radios.selected == Radio.Velocity:
                xpos += step_width * 0.25
                ypos += step_height - step_height * self.slider.get_data()
                velrect = pygame.Rect(xpos, ypos,
                                      step_width / 2,
                                      step_height * self.slider.get_data())
                pygame.draw.rect(surface, gui.C_DARKER, velrect, False)

    def _render(self, surface):
        cols = len(self.grid)
        rows = len(self.grid[0])

        curstep = int(sequencer.running_time % self.part.length)
        current_measure = curstep // (cols * rows)
        # The current active step position
        current_y = (curstep // cols) % rows
        current_x = curstep % cols

        # Render rectangles
        for x in range(cols):
            for y in range(rows):
                rect = self.grid[x][y]
                rectcolor = gui.C_PRIMARY
                filled = (x, y) in [s.pos() for s in self.selected]
                if current_measure == self.measure and sequencer.running:
                    if (current_x, current_y) == (x, y):
                        rectcolor = gui.C_DARKEST
                        filled = True
                pygame.draw.rect(surface, rectcolor, rect, 1 - filled)

        self.render_selected_steps_data(surface)

        # Render event data
        for x in range(cols):
            for y in range(rows):
                self.render_step_events(surface, x, y)

        if self.radios.selected == Radio.CC:
            self.cc_list.render(surface)
        else:
            self.preset_radios.render(surface)
        self.radios.render(surface)
        self.slider.render(surface)
        self.modeline.render(surface)

        return surface


# YAML SeqGrid representation
def seqgrid_representer(dumper, data):
    mapping = {'part': data.part,
               'width': len(data.grid),
               'height': len(data.grid[0]),
               'root': data.keyboard_root,
               'mode': data.keyboard_mode}
    return dumper.represent_mapping(u'!seqgrid', mapping)


def seqgrid_constructor(loader, node):
    m = loader.construct_mapping(node)
    return SeqGrid(m['part'], m['width'], m['height'], m['root'], m['mode'])

editors.editors.append(["Grid", SeqGrid])
yaml.add_representer(SeqGrid, seqgrid_representer)
yaml.add_constructor(u'!seqgrid', seqgrid_constructor)
