import pygame.time
import math
from operator import attrgetter

parts = []
bpm = 100.0
clock_time = 0 # in ms since start
running_time = 0 # 16th notes passed since start
clock = pygame.time.Clock()
running = True

def start():
    running = True
    for part in parts:
        part.start()

def stop():
    clock_time = 0
    running_time = 0
    running = False
    for part in parts:
        part.stop()

def tick():
    global running_time, clock_time
    delta = clock.tick(100)
    if running:
        clock_time += delta * 0.001
        running_time = clock_time / ((60.0 / bpm) / 4.0)
    for part in parts:
        part.update()

class Part(object):
    """Each part has a list of events.
    An event has a priority, a timestamp, a function pointer and a list of arguments"""

    def __init__(self):
        self.events = []
        self.length = 16 # 16ths per measure
        self.measures = 1
        self.next_timestamp = 0
        self.element = 0 # last element checked
        self.finished = False
        self.measures_run = 0

    def update(self):
        global running_time
        timestamp = running_time % (self.length * self.measures)

    def stop():
        
