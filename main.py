import sequencer
import midi
import editors
import settings
import gui
import screen
import sceneview

import sys
import pygame

editors.import_editor_classes()
settings.load_instruments()
screen.stack.append(sceneview.SceneView())
display = pygame.display.set_mode(gui.SCREEN_SIZE)
if midi.init():
    sequencer.start()

while 1:
    events = pygame.event.get()
    midi.update_input_events()
    screen.stack[-1].update(events)
    for e in events:
        if e.type == pygame.QUIT:
            sequencer.stop()
            midi.close()
            sys.exit()
    pygame.event.pump()
    sequencer.update()

    surface = screen.stack[-1].render()
    if surface is not None:
        display.blit(surface, (0, 0))
        pygame.display.flip()
