import sequencer
import midi
import seqgrid
import seqdrum
import settings
import gui
import screen
import partview
import event

import sys
import pygame
import math
import thread
import yaml

consoling = False


def threadedConsole():
    global consoling
    consoling = True
    read = raw_input(">>> ")
    try:
        print eval(read)
    except:
        try:
            exec(read)
        except Exception as error:
            print error
    consoling = False

# Setup

settings.load_instruments()

w, h = 4, 4
melody = sequencer.Part('Melody', w * h)
sequencer.parts.append(melody)

drums = sequencer.Part('Drums')
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
    if not consoling:
        thread.start_new_thread(threadedConsole, ())
    events = pygame.event.get()
    screen.stack[-1].update(events)
    for e in events:
        if e.type == pygame.QUIT:
            sequencer.stop()
            midi.close()
            sys.exit()
        elif e.type == pygame.KEYDOWN:
            if e.key == pygame.K_q:
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
