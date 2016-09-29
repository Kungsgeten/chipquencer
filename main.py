import sequencer
import midi
import seqgrid
import seqdrum
import settings
import gui
import screen
import partview

import sys
import pygame
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

settings.load_instruments()

w, h = 4, 4
melody = seqgrid.SeqGrid(sequencer.Part('Melody', w * h), w, h)
sequencer.project['scenes'][sequencer.current_scene].append(melody)

screen.stack.append(partview.PartView())
if midi.init():
    sequencer.start()

display = pygame.display.set_mode(gui.SCREEN_SIZE)

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
