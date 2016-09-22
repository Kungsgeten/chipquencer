import sequencer
import midi
import seqgrid
import seqdrum
import settings
import gui
import screen
import partview

import sys, pygame, math

# Setup

settings.load_instruments()

melody = sequencer.Part()
w, h = 2, 8
melody.length = w * h * 2
sequencer.parts.append(melody)

drums = sequencer.Part()
drums.length = 16
drums.channel = 9

sequencer.parts.append(drums)

melgrid = seqgrid.SeqGrid(melody, w, h)
drumgrid = seqdrum.SeqDrum(drums)

# Pygame stuff

display = pygame.display.set_mode(gui.SCREEN_SIZE)

screen.seqs.append(melgrid)
screen.seqs.append(drumgrid)

screen.stack.append(partview.PartView())
if midi.init():
    sequencer.start()

while 1:
    events = pygame.event.get()
    screen.stack[-1].update(events)
    for event in events:
        if event.type == pygame.QUIT:
            sequencer.stop()
            midi.close()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                # Send QUIT event instead?
                sequencer.stop()
                midi.close()
                sys.exit()

    pygame.event.pump()
    sequencer.update()

    surface = screen.stack[-1].render()
    if surface is not None:
        display.blit(surface, (0, 0))
        pygame.display.flip()
