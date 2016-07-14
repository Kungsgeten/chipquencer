import midi
import settings
import sequencer
import gui
from modeline import Modeline

import math, pygame

class SeqDrum(gui.Screen):
    STEP_SIZE = settings.SCREEN_WIDTH // 16
    def __init__(self, part, notes=None):
        self.part = part
        self.steps = []
        if notes is None:
            notes = [36, 37, 38, 39, 40, 41, 42, 43] # test
        self.notes = list(reversed(notes))
        self.grid = [[False] * self.part.length for n in self.notes]

        self.modeline = Modeline()
        self.modeline.buttonstrings = ['', '', '', 'Exit']
        self.modeline.text = 'Drum drum...'

    def update(self, events):
        self.modeline.update(events)
        if self.modeline.buttons[3].pressed:
            gui.pop()
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN:
                x, y = e.pos
                row = y // self.STEP_SIZE
                if row < len(self.grid):
                    col = x // self.STEP_SIZE
                    self.grid[row][col] = not self.grid[row][col]
                    note = self.notes[row]
                    if self.grid[row][col]:
                        n = midi.note(note, 120, col, 1)
                        self.part.append_notes([n])
                    else:
                        # FIX: hacky delete
                        for i, event in enumerate(self.part._events):
                            if event.off and event.timestamp == col and event.data1 == note:
                                offevent = event.off
                                for j, oe in enumerate(self.part._events):
                                    if oe == offevent:
                                        if i > j:
                                            del self.part._events[i]
                                            del self.part._events[j]
                                        else:
                                            del self.part._events[j]
                                            del self.part._events[i]
                                        break
                        self.part._sort()

    def render(self):
        surface = pygame.Surface(settings.SCREEN_SIZE)
        surface.fill(settings.C_LIGHTER)
        curstep = math.floor(sequencer.running_time % self.part.length)
        for row in range(len(self.grid)):
            for col, triggered in enumerate(self.grid[row]):
                pos = ((col % 16) * self.STEP_SIZE, row * self.STEP_SIZE)
                rect = pygame.Rect(pos, (self.STEP_SIZE, self.STEP_SIZE))
                rectcolor = settings.C_PRIMARY
                if col % 4 == 0:
                    rectcolor = settings.C_DARKER
                if curstep == col:
                    rectcolor = settings.C_LIGHTEST
                pygame.draw.rect(surface, rectcolor, rect, 1 - triggered)
        self.modeline.render(surface)
        return surface
