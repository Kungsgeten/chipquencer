import pygame

from modeline import Modeline
import sequencer
from partedit import PartEdit
import screen
import settings

class PartView(screen.Screen):
    pygame.font.init()
    font = pygame.font.SysFont('04b03', 16)
    PART_BOX_SIZE = 55
    SPACING = 3

    def __init__(self):
        self.partrects = []
        self.update_partrects()
        self.modeline = Modeline()
        self.modeline.buttonstrings = ['Toggle', 'Mute', 'Solo', 'Other']
        self.modeline.text = 'Rock it out man!'

    def update_partrects(self):
        self.partrects = []
        for i, part in enumerate(sequencer.parts):
            pos = (i * (self.PART_BOX_SIZE + self.SPACING) + self.SPACING,
                   (self.PART_BOX_SIZE + self.SPACING) * (i // 4) + self.SPACING)
            rect = pygame.Rect(pos, (self.PART_BOX_SIZE, self.PART_BOX_SIZE))
            self.partrects.append(rect)
        i = len(sequencer.parts)
        pos = (i * (self.PART_BOX_SIZE + self.SPACING) + self.SPACING,
               (self.PART_BOX_SIZE + self.SPACING) * (i // 4) + self.SPACING)
        rect = pygame.Rect(pos, (self.PART_BOX_SIZE, self.PART_BOX_SIZE))
        self.partrects.append(rect)

    def _update(self, events):
        self.has_changed = True
        self.modeline.update(events)
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN:
                x, y = e.pos
                for i, rect in enumerate(self.partrects):
                    if rect.collidepoint(e.pos):
                        if i == len(self.partrects) - 1:
                            screen.stack.append(PartEdit(sequencer.Part(), None))
                        # Toggle
                        elif self.modeline.buttons[0].down:
                            sequencer.parts[i].toggle = True
                        # Mute button
                        elif self.modeline.buttons[1].down:
                            sequencer.parts[i].mute = not sequencer.parts[i].mute
                        else:
                            screen.stack.append(screen.seqs[i])
                        return

    def _render(self, surface):
        # Render part boxes
        for i, part in enumerate(sequencer.parts):
            rect = self.partrects[i]
            if part.toggle:
                rectcolor = settings.C_DARKEST
            else:
                rectcolor = settings.C_DARKER
            pygame.draw.rect(surface, rectcolor, rect, True)
            pos = rect.topleft
            text = self.font.render(part.name, False, rectcolor)
            surface.blit(text, pos)
            # Playtime
            played_x = ((sequencer.running_time % part.length) / part.length) * self.PART_BOX_SIZE + rect.x
            pygame.draw.line(surface, settings.C_PRIMARY, (played_x, rect.top), (played_x, rect.bottom))
            if part.mute:
                pygame.draw.line(surface, rectcolor, rect.topleft, rect.bottomright)
                pygame.draw.line(surface, rectcolor, rect.topright, rect.bottomleft)
        # Add box
        rect = self.partrects[-1]
        rectcolor = settings.C_DARKER
        pygame.draw.rect(surface, rectcolor, rect, True)
        centerx, centery = rect.center
        OFFSET = (self.PART_BOX_SIZE * 0.8) / 2
        # Draw plus
        pygame.draw.line(surface, rectcolor, (centerx, centery - OFFSET),
                         (centerx, centery + OFFSET), 2)
        pygame.draw.line(surface, rectcolor, (centerx - OFFSET, centery),
                         (centerx + OFFSET, centery), 2)
        self.modeline.render(surface)
        return surface
