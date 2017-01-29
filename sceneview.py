import pygame
import yaml
import copy
from glob import glob

from enum import IntEnum

import sequencer
import screen
import gui
import midi

from modeline import Modeline
from clipsettings import ClipSettings
from choicelist import ChoiceList
from save_screen import SaveScreen
from config import ConfigScreen

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
    clip_copy = None

    def __init__(self):
        self.partrects = []
        self.update_partrects()
        self.modeline = Modeline(len(ModelineSections))
        # sequencer.goto_scene = sequencer.current_scene
        scene = 'Scene {}/{}'.format(sequencer.current_scene + 1,
                                     len(sequencer.project['scenes']))
        self.modeline[ModelineSections.Scene] = scene

    def update_partrects(self):
        """Update rectangles showing part information."""
        self.partrects = []
        for i, part in enumerate(sequencer.parts()):
            rect = pygame.Rect(box_pos(i), (PART_BOX_SIZE, PART_BOX_SIZE))
            self.partrects.append(rect)
        i = len(sequencer.parts())
        rect = pygame.Rect(box_pos(i), (PART_BOX_SIZE, PART_BOX_SIZE))
        self.partrects.append(rect)

    def goto_scene(self, index):
        """Switch to another scene."""
        if len(sequencer.project['scenes']) < index:
            return
        if len(sequencer.project['scenes']) == index:
            sequencer.project['scenes'].append([])
        sequencer.goto_scene = index
        if len(sequencer.scene()) == 0 or not sequencer.running:
            sequencer._switch_scene()

    def save_as(self):
        """Show save screen prompt."""
        screen.stack.append(SaveScreen())

    def keydown_events(self, keyevents):
        """Handle pygame keydown events."""
        mods = pygame.key.get_mods()
        for e in keyevents:
            if mods & pygame.KMOD_SHIFT:
                pass
            elif mods & pygame.KMOD_CTRL:
                if e.key == pygame.K_s:
                    self.save_as()
            elif mods & pygame.KMOD_ALT:
                # Change scene
                if e.key == pygame.K_0:
                    self.goto_scene(9)
                else:
                    try:
                        scene = int(e.unicode.encode('utf-8'))
                        self.goto_scene(scene - 1)
                    except:
                        pass
            else:
                if e.key == pygame.K_q:
                    pygame.event.post(pygame.event.Event(pygame.QUIT))
                elif e.key == pygame.K_SPACE:
                    sequencer.toggle()
                elif e.key == pygame.K_o:
                    # Load file
                    files = [[f[len("projects/"):], f]
                             for f in glob('projects/*.yaml')]
                    screen.stack.append(ChoiceList(files, 'Load project'))
                elif e.key == pygame.K_s:
                    # Save
                    path = sequencer.project['path']
                    if path is None:
                        self.save_as()
                    else:
                        sequencer.save(path)
                elif e.key == pygame.K_v:
                    # Paste
                    if self.clip_copy is not None:
                        sequencer.scene().append(self.clip_copy)
                        self.update_partrects()
                elif e.key == pygame.K_p:
                    # Preferences
                    screen.stack.append(ConfigScreen())

    def _partrect_variant_click(self, clip, keys):
        """Change variant of clicked clip, if correct key held."""
        # 49 is pygame.K_1, 57 is pygame.K_9
        for i in range(49, 58):
            if keys[i]:
                clip.part.switch_to_variant = i - 49
                return True
        return False

    def mousedown_events(self, mouseevents):
        scene = sequencer.scene()
        for e in mouseevents:
            x, y = e.pos
            # Upon partrect click
            for i, rect in enumerate(self.partrects):
                if rect.collidepoint(e.pos):
                    keys = pygame.key.get_pressed()
                    clip = scene[i] if i < len(self.partrects) - 1 else None
                    if i == len(self.partrects) - 1:
                        screen.stack.append(ClipSettings())
                    elif keys[pygame.K_e]:
                        # Edit clip
                        screen.stack.append(ClipSettings(clip))
                    elif keys[pygame.K_d]:
                        # Delete clip
                        clip.part.stop()
                        del scene[i]
                        self.update_partrects()
                    elif keys[pygame.K_c]:
                        # Copy clip
                        self.clip_copy = copy.deepcopy(clip)
                    elif keys[pygame.K_t]:
                        # Toggle clip
                        clip.part.toggle = True
                    elif keys[pygame.K_m]:
                        # (un)Mute clip
                        clip.part.mute = not clip.part.mute
                    # Change variant
                    elif keys[pygame.K_0]:
                        clip.part.switch_to_variant = 9
                    elif self._partrect_variant_click(clip, keys):
                        pass
                    else:
                        screen.stack.append(clip)
                    return

    def _update(self, events):
        self.has_changed = True
        self.keydown_events((e for e in events
                             if e.type == pygame.KEYDOWN))
        self.mousedown_events((e for e in events
                               if e.type == pygame.MOUSEBUTTONDOWN))

    def focus(self, *args, **kwargs):
        self.clip_copy = None
        if 'load_project' in kwargs:
            sequencer.load(kwargs['load_project'])
        self.update_partrects()

    def _render(self, surface):
        # Render part boxes
        for i, part in enumerate(sequencer.parts()):
            rect = self.partrects[i]
            if part.toggle:
                color = gui.C_DARKEST
            else:
                color = gui.C_DARKER
            pygame.draw.rect(surface, color, rect, True)
            pos = rect.move(2, 2).topleft
            text = self.font.render(part.name, False, color)
            surface.blit(text, pos)
            variant_text = self.font.render('V:{}'.format(part._variant + 1),
                                            False, color)
            x, y = rect.bottomleft
            surface.blit(variant_text, (x + 4, y - 12))
            # Playtime
            timestamp = sequencer.running_time % part.length
            played_x = timestamp / part.length * PART_BOX_SIZE + rect.x
            pygame.draw.line(surface, gui.C_PRIMARY,
                             (played_x, rect.top),
                             (played_x, rect.bottom))
            if part.mute:
                pygame.draw.line(surface, color,
                                 rect.topleft, rect.bottomright)
                pygame.draw.line(surface, color,
                                 rect.topright, rect.bottomleft)
        # Add box
        rect = self.partrects[-1]
        color = gui.C_DARKER
        pygame.draw.rect(surface, color, rect, True)
        centerx, centery = rect.center
        OFFSET = (PART_BOX_SIZE * 0.8) / 2
        # Draw plus
        pygame.draw.line(surface, color, (centerx, centery - OFFSET),
                         (centerx, centery + OFFSET), 2)
        pygame.draw.line(surface, color, (centerx - OFFSET, centery),
                         (centerx + OFFSET, centery), 2)
        self.modeline.render(surface)
        return surface
