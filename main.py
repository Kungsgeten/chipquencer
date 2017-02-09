import sequencer
import midi
import editors
import settings
import gui
import screen
import sceneview

from config import ConfigScreen

import sys
import pygame

editors.import_editor_classes()
settings.load_instruments()
screen.stack.append(sceneview.SceneView())
display = pygame.display.set_mode(gui.SCREEN_SIZE)
if midi.init():
    sequencer.start()
else:
    screen.stack.append(ConfigScreen())
while 1:
    events = pygame.event.get()
    midi.update_input_events()
    screen.stack.top().update(events)
    for e in events:
        if e.type == pygame.QUIT:
            if sequencer.running:
                sequencer.stop()
            midi.close()
            sys.exit()
    pygame.event.pump()
    sequencer.update()

    surface = screen.stack.top().render()
    if surface is not None:
        display.blit(surface, (0, 0))
        pygame.display.flip()
