import pygame
import yaml

from enum import IntEnum

import sequencer
import screen
import gui
import midi

from modeline import Modeline
from partedit import PartEdit

PART_BOX_SIZE = 55

def box_pos(index):
    SPACING = 3
    BOX_H = gui.SCREEN_WIDTH / (PART_BOX_SIZE + SPACING)

    return ((index % BOX_H) * (PART_BOX_SIZE + SPACING) + SPACING,
            (PART_BOX_SIZE + SPACING) * (index // BOX_H) + SPACING)

class ModelineSections(IntEnum):
    Scene = 0


class SceneView(screen.Screen):
    pygame.font.init()
    font = gui.FONT_MEDIUM

    def __init__(self):
        self.partrects = []
        self.update_partrects()
        self.modeline = Modeline(len(ModelineSections))
        self.goto_scene(sequencer.current_scene)

    def update_partrects(self):
        self.partrects = []
        for i, part in enumerate(sequencer.parts()):
            rect = pygame.Rect(box_pos(i), (PART_BOX_SIZE, PART_BOX_SIZE))
            self.partrects.append(rect)
        i = len(sequencer.parts())
        rect = pygame.Rect(box_pos(i), (PART_BOX_SIZE, PART_BOX_SIZE))
        self.partrects.append(rect)

    def goto_scene(self, index):
        if len(sequencer.project['scenes']) < index:
            return
        if len(sequencer.project['scenes']) == index:
            sequencer.project['scenes'].append([])
        sequencer.current_scene = index
        self.update_partrects()

        scene = 'Scene {}/{}'.format(sequencer.current_scene + 1,
                                     len(sequencer.project['scenes']))
        self.modeline[ModelineSections.Scene] = scene

    def keydown_events(self, keyevents):
        """Handle pygame keydown events."""
        mods = pygame.key.get_mods()
        for e in keyevents:
            if mods & pygame.KMOD_SHIFT:
                pass
            elif mods & pygame.KMOD_CTRL:
                pass
            elif mods & pygame.KMOD_ALT:
                pass
            else:
                if e.key == pygame.K_q:
                    pygame.event.post(pygame.event.Event(pygame.QUIT))
                elif e.key == pygame.K_1:
                    self.goto_scene(0)
                elif e.key == pygame.K_2:
                    self.goto_scene(1)
                elif e.key == pygame.K_3:
                    self.goto_scene(2)
                elif e.key == pygame.K_4:
                    self.goto_scene(3)
                elif e.key == pygame.K_5:
                    self.goto_scene(4)
                elif e.key == pygame.K_6:
                    self.goto_scene(5)
                elif e.key == pygame.K_7:
                    self.goto_scene(6)
                elif e.key == pygame.K_8:
                    self.goto_scene(7)
                elif e.key == pygame.K_9:
                    self.goto_scene(8)
                elif e.key == pygame.K_0:
                    self.goto_scene(9)

    def mousedown_events(self, mouseevents):
        for e in mouseevents:
            x, y = e.pos
            for i, rect in enumerate(self.partrects):
                if rect.collidepoint(e.pos):
                    if i == len(self.partrects) - 1:
                        screen.stack.append(PartEdit(sequencer.Part(), None))
                    # Toggle
                    # elif self.modeline.buttons[0].down:
                    #     sequencer.parts()[i].toggle = True
                    # # Mute button
                    # elif self.modeline.buttons[1].down:
                    #     sequencer.parts()[i].mute = not sequencer.parts()[i].mute
                    else:
                        clip = sequencer.project['scenes'][sequencer.current_scene][i]
                        screen.stack.append(clip)
                        # screen.stack.append(screen.seqs[i])
                    return


    def _update(self, events):
        self.has_changed = True
        self.keydown_events((e for e in events if e.type == pygame.KEYDOWN))
        self.mousedown_events((e for e in events if e.type == pygame.MOUSEBUTTONDOWN))

    def focus(self, *args, **kwargs):
        # Update midi out device, see midi.py
        if 'out_device' in kwargs:
            midi.set_out_device(kwargs['out_device'])
            stream = file('config.yml', 'w')
            data = {'midi_out':kwargs['out_device']}
            yaml.dump(data, stream)
            sequencer.start()

    def _render(self, surface):
        # Render part boxes
        for i, part in enumerate(sequencer.parts()):
            rect = self.partrects[i]
            if part.toggle:
                rectcolor = gui.C_DARKEST
            else:
                rectcolor = gui.C_DARKER
            pygame.draw.rect(surface, rectcolor, rect, True)
            pos = rect.move(2, 2).topleft
            text = self.font.render(part.name, False, rectcolor)
            surface.blit(text, pos)
            # Playtime
            played_x = ((sequencer.running_time % part.length) / part.length) * PART_BOX_SIZE + rect.x
            pygame.draw.line(surface, gui.C_PRIMARY, (played_x, rect.top), (played_x, rect.bottom))
            if part.mute:
                pygame.draw.line(surface, rectcolor, rect.topleft, rect.bottomright)
                pygame.draw.line(surface, rectcolor, rect.topright, rect.bottomleft)
        # Add box
        rect = self.partrects[-1]
        rectcolor = gui.C_DARKER
        pygame.draw.rect(surface, rectcolor, rect, True)
        centerx, centery = rect.center
        OFFSET = (PART_BOX_SIZE * 0.8) / 2
        # Draw plus
        pygame.draw.line(surface, rectcolor, (centerx, centery - OFFSET),
                         (centerx, centery + OFFSET), 2)
        pygame.draw.line(surface, rectcolor, (centerx - OFFSET, centery),
                         (centerx + OFFSET, centery), 2)
        self.modeline.render(surface)
        return surface