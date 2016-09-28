import sequencer
import screen
import gui
import event

from modeline import Modeline

import pygame
import math


class SeqDrum(screen.Screen):
    STEP_SIZE = gui.SCREEN_WIDTH // 16

    def __init__(self, part, notes=None):
        self.part = part
        self.steps = []
        if notes is None:
            notes = [36, 37, 38, 39, 40, 41, 42, 43]  # test
        self.notes = list(reversed(notes))
        self.grid = [[False] * self.part.length for n in self.notes]

        self.modeline = Modeline()
        self.last_curstep = -1

    def step_clicked(self, row, col):
        self.grid[row][col] = not self.grid[row][col]
        note = self.notes[row]
        self.has_changed = True
        if self.grid[row][col]:
            self.part.append(event.Event(col,
                                         event.note_on,
                                         [note, 120, 1]))

        else:
            for e in self.part._events:
                if e.timestamp == col and e.type() == 'note_on':
                    if e.note == note:
                        self.part.delete(e)
                        break

    def _update(self, events):
        curstep = math.floor(sequencer.running_time % self.part.length)
        if curstep != self.last_curstep:
            self.has_changed = True
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN:
                x, y = e.pos
                row = y // self.STEP_SIZE
                if row < len(self.grid):
                    col = x // self.STEP_SIZE
                    self.step_clicked(row, col)

    def _render(self, surface):
        curstep = math.floor(sequencer.running_time % self.part.length)
        for row in range(len(self.grid)):
            for col, triggered in enumerate(self.grid[row]):
                pos = ((col % 16) * self.STEP_SIZE, row * self.STEP_SIZE)
                rect = pygame.Rect(pos, (self.STEP_SIZE, self.STEP_SIZE))
                rectcolor = gui.C_PRIMARY
                if col % 4 == 0:
                    rectcolor = gui.C_DARKER
                if curstep == col:
                    rectcolor = gui.C_LIGHTEST
                pygame.draw.rect(surface, rectcolor, rect, 1 - triggered)
        self.modeline.render(surface)
        return surface
