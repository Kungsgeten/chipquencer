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

midi.init()
settings.load_instruments()

melody = sequencer.Part()
melody.length = 16
# melody.append_notes(arp)
sequencer.parts.append(melody)

drums = sequencer.Part()
drums.length = 16
drums.channel = 9
# pad.append_notes(two_notes)

sequencer.parts.append(drums)

# Pygame stuff

display = pygame.display.set_mode(gui.SCREEN_SIZE)
scroll = 40

selected = set([])
melgrid = seqgrid.SeqGrid(melody)
drumgrid = seqdrum.SeqDrum(drums)

# piano rollish
def render_part(part):
    NOTE_HEIGHT = 5
    sixteenth_width = SCREEN_WIDTH / part.length
    for note in part.note_elements():
        rect = pygame.Rect(note.timestamp * sixteenth_width,
                           SCREEN_HEIGHT - (note.data1 - scroll) * NOTE_HEIGHT,
                           (note.off.timestamp - note.timestamp) * sixteenth_width,
                           NOTE_HEIGHT)
        rectcolor = (0, 0, 0)
        # TODO: This selection is a hack, refactor it?
        mousepos = pygame.mouse.get_pos()
        if pygame.mouse.get_pressed()[0] and rect.collidepoint(mousepos):
            selected.add(note)
        if note in selected:
            rectcolor = (255, 0, 0)
        pygame.draw.rect(display, rectcolor, rect)

sequencer.start()
screen.seqs.append(melgrid)
screen.seqs.append(drumgrid)
screen.stack.append(partview.PartView())

while 1:
    keysPressed = pygame.key.get_pressed()
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

    # if keysPressed[pygame.K_UP]:
    #     scroll -= 0.001
    # if keysPressed[pygame.K_DOWN]:
    #     scroll += 0.001

    sequencer.update()

    # render_part(sequencer.parts[part_to_render])
    surface = screen.stack[-1].render()
    if surface is not None:
        display.blit(surface, (0, 0))
        pygame.display.flip()
