import midi
import sequencer
import screen
import gui

from gui import RadioButtons, Slider
from modeline import Modeline

import math, pygame
from enum import Enum


class SeqGrid(screen.Screen):
    pygame.font.init()
    font = gui.FONT_MEDIUM
    step_clicked = -1
    RADIO_DISTANCE = 2
    RADIO_WIDTH = 41
    RADIO_HEIGHT = 45
    MENU_WIDTH = RADIO_WIDTH * 3 + RADIO_DISTANCE * 5
    VEL_PRESETS = {0: midi.PP, 1: midi.P,
                   2: midi.MP, 3: midi.MF,
                   4: midi.F,  5: midi.FF}
    # '2', '4', '8', '16', '32', '.'
    LEN_PRESETS = {0: 8,
                   1: 4,
                   2: 2,
                   3: 1,
                   4: 0.5}

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

    class Radio:
        VELOCITY = 0
        LENGTH = 1
        OFFSET = 2

    KeyboardMode = Enum("Keyboard mode", "Tap Step RealTime")

    def __init__(self, part, width=4, height=4):
        assert(part.length % (width * height) == 0)
        self.part = part
        self.grid = self.grid_width, self.grid_height = width, height
        self.modeline = Modeline()
        self.modeline.strings = ['', '', '']
        self.measure = 0
        step_width, step_height = self.step_pixels()
        # each step has a rectangle and a list of events
        self.steps = []
        for i in range(part.length):
            row = (i // self.grid_width) % self.grid_height
            col = i % self.grid_width
            pos = (col * step_width, row * step_height)
            self.steps.append([pygame.Rect(pos, (step_width,
                                                 step_height)), list()])
        self.notes_to_steps()
        # selected step numbers
        self.selected = [0]
        # which note of a chord we're editing. negative = all
        self.chordnote = -1
        self.last_step = -1
        SLIDER_WIDTH = self.RADIO_WIDTH
        SLIDER_HEIGHT = gui.SCREEN_HEIGHT - self.RADIO_HEIGHT - self.RADIO_DISTANCE * 3 - Modeline.HEIGHT
        self.slider = Slider(pygame.Rect(gui.SCREEN_WIDTH - SLIDER_WIDTH - self.RADIO_DISTANCE,
                                         self.RADIO_HEIGHT + self.RADIO_DISTANCE * 2,
                                         SLIDER_WIDTH,
                                         SLIDER_HEIGHT))
        strings = 'Vel', 'Len', 'Off'
        distance = self.RADIO_DISTANCE
        self.radios = RadioButtons((step_width * self.grid_width + distance, distance),
                                   (self.RADIO_WIDTH, self.RADIO_HEIGHT), 3, 1, strings, distance)
        self.preset_radios = RadioButtons((step_width * self.grid_width + distance,
                                           distance * 4 + self.RADIO_WIDTH),
                                          (self.RADIO_WIDTH, self.RADIO_WIDTH), 2, 3, [], distance)
        self.last_vel = 120
        self.last_length = 1.0
        self.last_offset = 0.0
        self._change_slider()
        
        self._keyboard_root = 0
        self.keyboard_root = 60
        self.keyboard_mode = self.KeyboardMode.Tap
        self.modeline.strings[2] = self.keyboard_mode.name

    @property
    def keyboard_root(self):
        return self._keyboard_root

    @keyboard_root.setter
    def keyboard_root(self, note):
        self._keyboard_root = note % 127
        self.modeline.strings[1] = midi.note_to_string(self._keyboard_root)
        
    @property
    def measures(self):
        return self.part.length // (self.grid_width * self.grid_height)

    @property
    def measure(self):
        return self._measure
    
    @measure.setter
    def measure(self, measure):
        self._measure = measure % self.measures
        self.modeline.strings[0] = "M:{}/{}".format(self.measure + 1,
                                                    self.measures)

    def step_pixels(self):
        return (int((gui.SCREEN_WIDTH / self.grid_width) -
                    self.MENU_WIDTH / self.grid_width),
                int((gui.SCREEN_HEIGHT / self.grid_height) -
                    Modeline.HEIGHT / self.grid_height))
        
    def keyboard_mode_cycle(self):
        "Cycle between keyboard modes."
        kbm_value = (self.keyboard_mode.value + 1) % len(self.KeyboardMode) + 1
        self.keyboard_mode = self.KeyboardMode(kbm_value)
        self.modeline.strings[2] = self.keyboard_mode.name
        
    def copy_step(self, original, target):
        distance = target - original
        self.delete_step(target)
        for event in self.steps[original][1]:
            copy = midi.MidiEvent(event.status,
                                  event.data1,
                                  event.data2,
                                  event.timestamp + distance)
            if event.off:
                offcopy = midi.MidiEvent(event.off.status,
                                         event.off.data1,
                                         event.off.data2,
                                         event.off.timestamp + distance)
                copy.off = offcopy
                self.part.append([offcopy])
            self.part.append([copy])
            self.steps[target][1].append(copy)

    def delete_step(self, step):
        self.has_changed = True
        # FIX: This is hacky
        for i, event in enumerate(self.steps[step][1]):
            for j, pevent in enumerate(self.part._events):
                if event == pevent:
                    offevent = event.off
                    if offevent:
                        for k, e in enumerate(self.part._events):
                            if offevent == e:
                                if k > j:
                                    del self.part._events[k]
                                    del self.part._events[j]
                                else:
                                    del self.part._events[j]
                                    del self.part._events[k]
                                break
                    else:
                        del self.part._events[j]
                    break
        del self.steps[step][1][:]
        self.part._sort()
        # self.part.start()

    def keyboard_play(self, note):
        self.has_changed = True
        if not sequencer.running or self.keyboard_mode is not self.KeyboardMode.Step:
            midi.out.write_short(self.part.channel + midi.NOTE_ON, note, 127)
        if self.keyboard_mode is self.KeyboardMode.Step:
            new_note = True
            for step in self.selected:
                for i, n in enumerate(self.steps[step][1]):
                    if self.chordnote < 0 or i == self.chordnote:
                        n.set_note(note)
                        new_note = False
            if new_note:
                n = midi.note(note,
                              self.last_vel,
                              step + self.last_offset,
                              self.last_length)
                self.part.append_notes([n])
                self.steps[step][1].append(n[0])
                self._change_slider()
        elif self.keyboard_mode is self.KeyboardMode.RealTime:
            # Quantize step
            if sequencer.running:
                step = int(round(sequencer.running_time)) % self.part.length
            else:
                step = self.selected[0]
            n = midi.note(note,
                          self.last_vel,
                          step + self.last_offset,
                          self.last_length)
            self.part.append_notes([n])
            self.steps[step][1].append(n[0])
            self._change_slider()

    def keydown_events(self, keyevents):
        for e in keyevents:
            if e.key in self.KEYBOARD_KEYS:
                note = self.keyboard_root + self.KEYBOARD_KEYS[e.key]
                self.keyboard_play(note)
            elif e.key == pygame.K_TAB:
                self.keyboard_root -= 12
            elif e.key == pygame.K_RETURN:
                self.keyboard_root += 12
            elif e.key == pygame.K_a:
                self.keyboard_root -= 1
            elif e.key == pygame.K_l:
                self.keyboard_root += 1
            elif e.key == pygame.K_SLASH or e.key == pygame.K_t:
                self.keyboard_mode_cycle()
            elif e.key == pygame.K_p:
                self.measure += 1
    
    def keyup_events(self, keyevents):
        for e in keyevents:
            if e.key in self.KEYBOARD_KEYS:
                note = self.keyboard_root + self.KEYBOARD_KEYS[e.key]
                midi.out.write_short(self.part.channel + midi.NOTE_ON, note, 0)

    def _update(self, events):
        # New step?
        if self.last_step != math.floor(sequencer.running_time):
            self.has_changed = True
        self.last_step = math.floor(sequencer.running_time)

        # Keyboard events
        self.keydown_events((e for e in events if e.type == pygame.KEYDOWN))
        self.keyup_events((e for e in events if e.type == pygame.KEYUP))

        # Radio Buttons
        clicked = self.radios.update(events)
        if clicked is not None:
            self._change_slider()
            self.has_changed = True
            self.preset_radios.selected = -1
            strings = []
            if clicked == self.Radio.VELOCITY:
                strings = 'pp', 'p', 'mp', 'mf', 'f', 'ff'
            elif clicked == self.Radio.LENGTH:
                strings = '2', '4', '8', '16', '32', '.'
            self.preset_radios.strings = strings
            return

        presetclick = None
        presetclick = self.preset_radios.update(events)
        if presetclick is not None:
            if self.radios.selected == self.Radio.VELOCITY:
                self.slider.set_value(self.VEL_PRESETS[presetclick], 127)
            elif self.radios.selected == self.Radio.LENGTH:
                if presetclick == 5:
                    slidervalue = self.slider.get_data() * 15.999
                    self.slider.set_value(slidervalue * 1.5, 15.999)
                else:
                    self.slider.set_value(self.LEN_PRESETS[presetclick], 15.999)
            elif self.radios.selected == self.Radio.OFFSET:
                self.slider.set_value((presetclick / 6.) * 0.9999, 0.9999)

        # Slider
        slided = self.slider.update(events)
        if slided is not None or presetclick is not None:
            slided = self.slider.get_data()
            self.has_changed = True
            for step in self.selected:
                for i, n in enumerate(self.steps[step][1]):
                    if self.chordnote < 0 or i == self.chordnote:
                        if self.radios.selected == self.Radio.VELOCITY:
                            n.data2 = int(slided * 126) + 1
                        elif self.radios.selected == self.Radio.LENGTH:
                            n.off.timestamp = n.timestamp + slided * 15.999
                            while n.off.timestamp >= self.part.length:
                                n.off.timestamp -= self.part.length
                            self.part._sort()
                        elif self.radios.selected == self.Radio.OFFSET:
                            offset = math.floor(n.timestamp)
                            n.timestamp = math.floor(n.timestamp) + slided * 0.9999
                            n.off.timestamp = math.floor(n.off.timestamp) + slided * 0.9999
                            self.part._sort()
                        self.last_vel = n.data2
                        self.last_length = abs(n.off.timestamp - n.timestamp)
                        self.last_offset = n.timestamp % 1.0
            return

        for e in events:
            # if e.type == pygame.KEYDOWN:
            #     self.has_changed = True
            #     # if e.key == pygame.K_z:
            #     #     for step in self.selected:
            #     #         n = midi.note(60, 100, step, 1)
            #     #         self.part.append_notes([n])
            #     #         self.steps[step][1].append(n[0])
            #     #         self._change_slider()
            #     if e.key == pygame.K_b:
            #         print 'Debug:'
            #         self.part.debug()
            #         # for n in self.part.note_elements():
            #         #     print n
            #     # elif e.key == pygame.K_LEFT:
            #     #     if len(self.selected) == 1 and len(self.steps[self.selected[0]][1]) > 1:
            #     #         self._change_slider()
            #     #         self.chordnote += 1
            #     #         if self.chordnote >= len(self.steps[self.selected[0]][1]):
            #     #             self.chordnote = 0
            #     # elif e.key == pygame.K_DELETE:
            #     #     for step in self.selected:
            #     #         self.delete_step(step)
            step_width, step_height = self.step_pixels()
            if e.type == pygame.MOUSEBUTTONDOWN:
                if pygame.Rect(0, 0, step_width * self.grid_width,
                               step_height * self.grid_height).collidepoint(e.pos):
                    self.preset_radios.selected = -1
                    self.selected = []
                    measuresteps = self.grid_width * self.grid_height
                    for i, step in enumerate(self.steps[:measuresteps]):
                        rect = step[0]
                        if rect.collidepoint(e.pos):
                            self._on_step_click(i + measuresteps * self.measure)
                            break
            elif e.type == pygame.MOUSEBUTTONUP:
                if self.step_clicked >= 0:
                    step_clicked = self.step_clicked
                    self.step_clicked = -1
                    # drag to delete
                    if(e.pos[0] > step_width * self.grid_width or
                       e.pos[1] > step_height * self.grid_height):
                        self.delete_step(step_clicked)
                        continue
                    # drag to copy
                    measuresteps = self.grid_width * self.grid_height
                    for i, step in enumerate(self.steps[:measuresteps]):
                        rect = step[0]
                        if rect.collidepoint(e.pos):
                            if step_clicked != i + measuresteps * self.measure:
                                # dragged step
                                self.copy_step(step_clicked, i)
                                self.has_changed = True
                                break

    def _change_slider(self):
        for step in self.selected:
            for i, n in enumerate(self.steps[step][1]):
                if self.radios.selected == self.Radio.VELOCITY:
                    self.slider.set_value(n.data2, 127)
                    return
                elif self.radios.selected == self.Radio.LENGTH:
                    nofft = n.off.timestamp
                    while nofft < n.timestamp:
                        nofft += self.part.length
                    self.slider.set_value(nofft - n.timestamp, 15.999)
                    return
                elif self.radios.selected == self.Radio.OFFSET:
                    self.slider.set_value(n.timestamp % 1.0, 0.9999)
                    return

        if self.radios.selected == self.Radio.VELOCITY:
            self.slider.set_value(self.last_vel, 127)
        elif self.radios.selected == self.Radio.LENGTH:
            self.slider.set_value(self.last_length, 16.)
        elif self.radios.selected == self.Radio.OFFSET:
            self.slider.set_value(self.last_offset, 0.9999)

    def _on_step_click(self, step):
        self.has_changed = True
        self.selected.append(step)
        self.chordnote = -1
        self.step_clicked = step
        if self.keyboard_mode is self.KeyboardMode.Tap:
            notes = []
            pressed_keys = pygame.key.get_pressed()
            for key in self.KEYBOARD_KEYS.keys():
                if pressed_keys[key]:
                    notes.append(self.keyboard_root + self.KEYBOARD_KEYS[key])
            for note in notes:
                n = midi.note(note,
                              self.last_vel,
                              step + self.last_offset,
                              self.last_length)
                self.part.append_notes([n])
                self.steps[step][1].append(n[0])
        self._change_slider()

    def _render(self, surface):
        curstep = math.floor(sequencer.running_time % self.part.length)
        step_width, step_height = self.step_pixels()
        self.slider.render(surface)
        measuresteps = self.grid_width * self.grid_height
        for i, step in enumerate(self.steps[measuresteps * self.measure:
                                            measuresteps * (self.measure + 1)]):
            i += measuresteps * self.measure
            rect, events = step
            rectcolor = gui.C_PRIMARY
            if curstep == i and sequencer.running:
                rectcolor = gui.C_DARKEST
            selected = i in self.selected
            filled = curstep == i if sequencer.running else selected

            # step square
            pygame.draw.rect(surface, rectcolor, rect, 1 - filled)
            # Render length of selected step (based on length slider)
            if self.radios.selected == self.Radio.LENGTH and selected:
                pixel_length = self.slider.get_data() * 16. * step_width
                x = rect.x
                y = rect.y + step_height * 0.25
                while x + pixel_length > step_width * self.grid_width:
                    pixel_length -= (step_width * self.grid_width) - x
                    width = (step_width * self.grid_width) - x
                    lenrect = pygame.Rect(x, y, width, step_height / 2)
                    pygame.draw.rect(surface, gui.C_DARKER, lenrect, False)
                    x = 0
                    y = (y + step_height) % (step_height * self.grid_height)
                if pixel_length:
                    lenrect = pygame.Rect(x, y, pixel_length, step_height / 2)
                    pygame.draw.rect(surface, gui.C_DARKER, lenrect, False)
            # Render offset position
            elif self.radios.selected == self.Radio.OFFSET and selected:
                x = rect.x + self.slider.get_data() * step_width
                y = rect.y
                pygame.draw.line(surface, gui.C_DARKER, (x, y), (x, y + step_height))
            # Render velocity level
            elif self.radios.selected == self.Radio.VELOCITY and selected:
                x = rect.x + step_width * 0.25
                y = rect.y + step_height - step_height * self.slider.get_data()
                velrect = pygame.Rect(x, y, step_width / 2, step_height * self.slider.get_data())
                pygame.draw.rect(surface, gui.C_DARKER, velrect, False)
            # Render note names
            if step[1]:
                notenames = [midi.note_to_string(note.data1) for note in step[1] if note.off]
                for j, notename in enumerate(notenames):
                    # TODO: Why can I not store background in variable?
                    if len(step[1]) > 1 and i in self.selected:
                        if self.chordnote < 0 or self.chordnote == j:
                            text = self.font.render(notename, False, gui.C_LIGHTEST, (0, 0, 201))
                        else:
                            text = self.font.render(notename, False, gui.C_LIGHTEST)
                    else:
                        text = self.font.render(notename, False, gui.C_LIGHTEST)
                    surface.blit(text, (rect.x + 2, rect.y + 2 + j * 8))
        # "Presets" for note option buttons
        self.preset_radios.render(surface)
        self.radios.render(surface)
        self.modeline.render(surface)

        return surface

    def notes_to_steps(self):
        for n in self.part.note_elements():
            self.steps[int(n.timestamp)][1].append(n)
