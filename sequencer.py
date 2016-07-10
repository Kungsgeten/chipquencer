import pygame.time
import math
from operator import attrgetter

import midi

MC_NONE = 0
MC_SEND = 1
MC_RECIEVE = 2

parts = []
bpm = 100.0
clock_time = 0 # in ms since start
running_time = 0 # 16th notes pased since start
clock = pygame.time.Clock()
running = True
midiclock = MC_SEND

def start():
    running = True
    for part in parts:
        part.start()
    if midiclock == MC_SEND:
        midi.out.write_short(midi.MC_START)

def stop():
    clock_time = 0
    running_time = 0
    running = False
    for part in parts:
        part.stop()
    if midiclock == MC_SEND:
        midi.out.write_short(midi.MC_STOP)

def update():
    global running_time, clock_time
    delta = clock.tick(100)
    if running:
        clock_time += delta * 0.001
        running_time = clock_time / ((60.0 / bpm) / 4.0)
    for part in parts:
        part.update()
    if midiclock == MC_SEND:
        # 24 ppq
        ppq_length = (60.0 / bpm) / 24.0
        update.deltasum += delta * 0.001
        if update.next_ppq == 0:
            midi.out.write_short(midi.MC_CLOCK)
            update.next_ppq = update.deltasum + ppq_length
        elif update.deltasum >= update.next_ppq:
            midi.out.write_short(midi.MC_CLOCK)
            update.next_ppq += ppq_length
    # TODO: Recieve MIDI clock
    
update.deltasum = 0
update.next_ppq = 0

# Timestamps is measured in 16ths
class Part(object):
    def __init__(self):
        self._events = [] # sorted after the event timestamps
        self.length = 16 # in 16th notes
        self._mute = False # when muted should send note off for playing notes?
        self.next_timestamp = 0
        self.element = 0 # the last element checked
        self.finished = False
        self.channel = 0
        self.toggle = False
        self.name = 'Test'

    @property
    def mute(self):
        return self._mute
        
    @mute.setter
    def mute(self, value):
        if value:
            self.stop()
        self._mute = value

    def debug(self):
        print "Element: ", self.element
        print "Finished: ", self.finished
        print "Next timestamp: ", self.next_timestamp
        midi.out.write_short(midi.PC + self.channel, 50, 0)
        
    def update(self):
        global running_time
        timestamp = running_time % self.length
        if self.finished and math.floor(timestamp) == 0:
            if self.toggle:
                self.toggle = False
                self.mute = not self.mute
            self.finished = False
            self.element = 0
        if self.next_timestamp >=0 and not self.finished and timestamp >= self.next_timestamp:
            self._trigger_event()

    def stop(self):
        midi.out.write_short(midi.CC + self.channel, 120, 127)
        
    def start(self):
        self.element = 0
        self.finished = False
        try:
            self.next_timestamp = self._events[0].timestamp
        except:
            self.next_timestamp = -1

    def append(self, events):
        """Add new events to the part"""
        for e in events:
            while e.timestamp >= self.length:
                e.timestamp -= self.length
        self._events.extend(events)
        self._sort()
        if self.next_timestamp < 0:
            self.next_timestamp = self._events[self.element].timestamp

    def append_notes(self, notes):
        """Add new events created by note() function"""
        for n in notes:
            self.append(n)

    def note_elements(self):
        """Returns all note_on events"""
        return [event for event in self._events if event.off]

    def _sort(self):
        global running_time
        # self._events.sort(key=lambda event: event.timestamp)
        self._events.sort(key=attrgetter('timestamp', 'data1', 'data2'))
        step_in_loop = running_time % self.length
        self.element = len(self._events) - 1
        for i, e in enumerate(self._events):
            if e.timestamp < step_in_loop:
                self.element = i
        if len(self._events) == 0:
            self.start()
            return
        self.next_timestamp = self._events[(self.element + 1) % len(self._events)].timestamp
        self.finished = False 
        if self.element == len(self._events) - 1:
            self.finished = True

    def _trigger_event(self):
        # trigger all events with the correct timestamp
        while self._events[self.element].timestamp == self.next_timestamp:
            if not self.mute:
                event = self._events[self.element]
                midi.out.write_short(event.status + self.channel, event.data1, event.data2)
            self.element += 1
            if self.element == len(self._events):
                self.element = 0
                self.finished = True
                
        self.next_timestamp = self._events[self.element].timestamp
