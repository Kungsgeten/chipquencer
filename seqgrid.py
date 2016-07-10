import midi
import settings
import sequencer
import slider
import radiob
import gui
from modeline import Modeline

import math, pygame, copy

class Keyboard():
    pygame.font.init()
    font = pygame.font.SysFont('04b03', 10)    
    KEY_WIDTH = 20
    KEY_HEIGHT = 40

    def __init__(self):
        self.scale = [0, 2, 4, 5, 7, 9, 11]
        self.octave = 5
        self._init_keys()

    def _init_keys(self):
        self.keys = []
        for i in range(settings.SCREEN_WIDTH // self.KEY_WIDTH):
            rect = pygame.Rect(i * self.KEY_WIDTH, 0, self.KEY_WIDTH, self.KEY_HEIGHT)
            tone = self.scale[i % len(self.scale)] + (i // len(self.scale)) * 12
            self.keys.append((rect, tone))

    def update(self, events, ypos=0):
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN:
                for key in self.keys:
                    rect, tone = key
                    # FIX: Ugly hack
                    x, y = e.pos
                    y -= ypos
                    pos = x, y
                    if rect.collidepoint(pos):
                        return tone + self.octave * 12
        return None

    def render(self):
        surface = pygame.Surface((len(self.keys) * self.KEY_WIDTH,
                                  self.KEY_HEIGHT))
        surface.fill(settings.C_PRIMARY)
        for key in self.keys:
            rect, tone = key
            root = tone % 12 == self.scale[0] % 12
            pygame.draw.rect(surface, settings.C_DARKER, rect, 1 - root)
            text = self.font.render(midi.note_to_string(tone)[:2], False, settings.C_LIGHTEST)
            surface.blit(text, (rect.x + 2, rect.y + self.KEY_HEIGHT - text.get_height()))
        return surface

class SeqGrid(gui.Screen):
    pygame.font.init()
    font = pygame.font.SysFont('04b03', 10)
    step_clicked = -1
    STEP_SIZE = (settings.SCREEN_HEIGHT - Keyboard.KEY_HEIGHT - Modeline.HEIGHT) // 4 # width/height of step rect
    VEL_PRESETS = {0: 32, 1: 48,
                   2: 64, 3: 80,
                   4: 96, 5: 112} # pp, p, mp, mf, f, ff
    LEN_PRESETS = {0: 8,
                   1: 4,
                   2: 2,
                   3: 1,
                   4: 0.5} # '2', '4', '8', '16', '32', '.'
    
    class Radio:
        VELOCITY = 0
        LENGTH = 1
        OFFSET = 2
    
    def __init__(self, part):
        self.has_changed = False # If the GUI should render or not
        self.keyboard = Keyboard()
        self.modeline = Modeline()
        self.modeline.buttonstrings = ['Shift', 'Options', 'Mode', 'Exit']
        self.modeline.text = 'Measure 1'
        self.part = part
        self.steps = [] # each step has a rectangle and a list of events
        for i in range(part.length):
            row = i // 4
            col = i % 4
            pos = (col * self.STEP_SIZE, row * self.STEP_SIZE)
            self.steps.append([pygame.Rect(pos, (self.STEP_SIZE, self.STEP_SIZE)), list()])
        self.notes_to_steps()
        self.selected = [0] # selected step numbers
        self.chordnote = -1 # which note of a chord we're editing. negative = all
        self.last_step = -1 # step the prior update
        SLIDER_WIDTH = 30
        self.slider = slider.Slider(pygame.Rect(settings.SCREEN_WIDTH - SLIDER_WIDTH - 8,
                                                settings.SCREEN_HEIGHT - Keyboard.KEY_HEIGHT - 143,
                                                SLIDER_WIDTH,
                                                127))
        strings = 'Vel', 'Len', 'Off'
        distance = 2
        self.radios = radiob.RadioButtons((self.STEP_SIZE*4 + distance, distance),
                                          (41, 45), 3, 1, strings, distance)
        self.preset_radios = radiob.RadioButtons((self.STEP_SIZE*4 + distance, distance*4 + 41),
                                              (41, 41), 2, 3, [], distance)
        self.last_vel = 120
        self.last_length = 1.0
        self.last_offset = 0.0
        self._change_slider()

    def copy_step(self, original, target):
        distance = target - original
        self.delete_step(target)
        for event in self.steps[original][1]:
            copy = midi.MidiEvent(event.status, event.data1, event.data2, event.timestamp + distance)
            if event.off:
                offcopy = midi.MidiEvent(event.off.status, event.off.data1,
                                         event.off.data2, event.off.timestamp + distance)
                copy.off = offcopy
                self.part.append([offcopy])
            self.part.append([copy])
            self.steps[target][1].append(copy)

    def delete_step(self, step):
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

    def update(self, events):
        self.modeline.update(events)
        self.has_changed = False
        # New step?
        if self.last_step != math.floor(sequencer.running_time):
            self.has_changed = True
        self.last_step = math.floor(sequencer.running_time)

        # Keyboard
        keytone = self.keyboard.update(events, self.steps[-1][0].bottom)
        if keytone:
            self.has_changed = True
            new_note = True
            for step in self.selected:
                for i, n in enumerate(self.steps[step][1]):
                    if self.chordnote < 0 or i == self.chordnote:
                        n.set_note(keytone)
                        new_note = False
            if new_note:
                n = midi.note(keytone, self.last_vel, step + self.last_offset, self.last_length)
                self.part.append_notes([n])
                self.steps[step][1].append(n[0])
                self._change_slider()
            return

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

        if self.modeline.buttons[3].pressed:
            gui.pop()
        
        for e in events:
            if e.type == pygame.KEYDOWN:
                self.has_changed = True
                # if e.key == pygame.K_z:
                #     for step in self.selected:
                #         n = midi.note(60, 100, step, 1)
                #         self.part.append_notes([n])
                #         self.steps[step][1].append(n[0])
                #         self._change_slider()
                if e.key == pygame.K_b:
                    print 'Debug:'
                    self.part.debug()
                    # for n in self.part.note_elements():
                    #     print n
                # elif e.key == pygame.K_LEFT:
                #     if len(self.selected) == 1 and len(self.steps[self.selected[0]][1]) > 1:
                #         self._change_slider()
                #         self.chordnote += 1
                #         if self.chordnote >= len(self.steps[self.selected[0]][1]):
                #             self.chordnote = 0
                # elif e.key == pygame.K_DELETE:
                #     for step in self.selected:
                #         self.delete_step(step)
            elif e.type == pygame.MOUSEBUTTONDOWN:
                if pygame.Rect(0, 0, self.STEP_SIZE * 4, self.STEP_SIZE * 4).collidepoint(e.pos):
                    self.preset_radios.selected = -1
                    self.selected = []
                    for i, step in enumerate(self.steps):
                        rect = step[0]
                        if rect.collidepoint(e.pos):
                            self._on_step_click(i)
                            break
            elif e.type == pygame.MOUSEBUTTONUP:
                if self.step_clicked >= 0:
                    step_clicked = self.step_clicked
                    self.step_clicked = -1
                    # drag to delete
                    if e.pos[0] > self.STEP_SIZE * 4 or e.pos[1] > self.STEP_SIZE * 4:
                        self.delete_step(step_clicked)
                        continue
                    # drag to copy
                    for i, step in enumerate(self.steps):
                        rect = step[0]
                        if rect.collidepoint(e.pos):
                            if not step_clicked == i:
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
        self._change_slider()

    def render(self):
        if not self.has_changed:
            return None
        surface = pygame.Surface(settings.SCREEN_SIZE)
        surface.fill(settings.C_LIGHTER)
        curstep = math.floor(sequencer.running_time % self.part.length)
        self.slider.render(surface)
        for i, step in enumerate(self.steps):
            rect, events = step
            rectcolor = settings.C_PRIMARY
            if curstep == i:
                rectcolor = settings.C_DARKEST
            selected = i in self.selected
            pygame.draw.rect(surface, rectcolor, rect, 1 - (selected or curstep == i)) # step square
            # Render length of selected step (based on length slider)
            if self.radios.selected == self.Radio.LENGTH and selected:
                pixel_length = self.slider.get_data() * 16. * self.STEP_SIZE
                x = rect.x
                y = rect.y + self.STEP_SIZE * 0.25
                while x + pixel_length > self.STEP_SIZE * 4:
                    pixel_length -= (self.STEP_SIZE * 4) - x
                    width = (self.STEP_SIZE * 4) - x
                    lenrect = pygame.Rect(x, y, width, self.STEP_SIZE / 2)
                    pygame.draw.rect(surface, settings.C_DARKER, lenrect, False)
                    x = 0
                    y = (y + self.STEP_SIZE) % (self.STEP_SIZE * 4)
                if pixel_length:
                    lenrect = pygame.Rect(x, y, pixel_length, self.STEP_SIZE / 2)
                    pygame.draw.rect(surface, settings.C_DARKER, lenrect, False)
            # Render offset position
            elif self.radios.selected == self.Radio.OFFSET and selected:
                x = rect.x + self.slider.get_data() * self.STEP_SIZE
                y = rect.y
                pygame.draw.line(surface, settings.C_DARKER, (x, y), (x, y + self.STEP_SIZE))
            # Render velocity level
            elif self.radios.selected == self.Radio.VELOCITY and selected:
                x = rect.x + self.STEP_SIZE * 0.25
                y = rect.y + self.STEP_SIZE - self.STEP_SIZE * self.slider.get_data()
                velrect = pygame.Rect(x, y, self.STEP_SIZE / 2, self.STEP_SIZE * self.slider.get_data())
                pygame.draw.rect(surface, settings.C_DARKER, velrect, False)
            # Render note names
            if step[1]:
                notenames = [midi.note_to_string(note.data1) for note in step[1] if note.off]
                for j, notename in enumerate(notenames):
                    # TODO: Why can I not store background in variable?
                    if len(step[1]) > 1 and i in self.selected:
                        if self.chordnote < 0 or self.chordnote == j:
                            text = self.font.render(notename, False, settings.C_LIGHTEST, (0, 0, 201))
                        else:
                            text = self.font.render(notename, False, settings.C_LIGHTEST)
                    else:
                        text = self.font.render(notename, False, settings.C_LIGHTEST)
                    surface.blit(text, (rect.x + 2, rect.y + 2 + j * 8))
        # "Presets" for note option buttons
        self.preset_radios.render(surface)
        self.radios.render(surface)
        surface.blit(self.keyboard.render(), (0, self.steps[-1][0].bottom))
        self.modeline.render(surface)

        return surface

    def notes_to_steps(self):
        for n in self.part.note_elements():
            self.steps[int(n.timestamp)][1].append(n)
