import pygame.time
import bisect
import yaml

import midi

MC_NONE = 0
MC_SEND = 1
MC_RECIEVE = 2

parts = []
bpm = 100.0
clock_time = 0  # in ms since start
running_time = 0  # 16th notes pased since start
clock = pygame.time.Clock()
running = False
midiclock = MC_SEND
new_step = False

def start():
    """Start the sequencer."""
    global running
    running = True
    for part in parts:
        part.start()
    if midiclock == MC_SEND:
        midi.out.write_short(midi.MC_START)


def stop():
    """Stop the sequencer."""
    global clock_time, running_time, running, new_step
    clock_time = 0
    running_time = 0
    running = False
    new_step = False
    for part in parts:
        part.stop()
    if midiclock == MC_SEND:
        midi.out.write_short(midi.MC_STOP)


def update():
    """Update the sequencer.

    Should be run every frame if the sequencer has started.
    """
    global running_time, clock_time, new_step
    delta = clock.tick(100)
    if running:
        clock_time += delta * 0.001
        old_running_time = int(running_time)
        running_time = clock_time / ((60.0 / bpm) / 4.0)
        new_step = old_running_time != int(running_time)
    for part in parts:
        part.update()
    if midiclock == MC_SEND and midi.out:
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


# Timestamps are measured in 16ths
class Part(object):
    def __init__(self, name, length=16, channel=0, events=None):
        if events is None:
            self._events = []
        else:
            self._events = events  # events in the loop, sorted by timestamp
        self.length = length  # in 16th notes
        self.name = name

        self.future_events = []
        self._mute = False
        self.next_timestamp = 0
        self.element = 0  # the last element checked
        self.finished = False  # the last event has triggered?
        self.channel = channel
        self.toggle = False
        self.last_measure = -1

    def __repr__(self):
        return 'Part(name={}, length={}, events={})'.format(self.name,
                                                            self.length,
                                                            self._events)

    @property
    def mute(self):
        return self._mute

    @mute.setter
    def mute(self, value):
        if value:
            self.stop()
        self._mute = value

    def update(self):
        """Update the part and trigger new events. Check if part has looped."""
        global running_time, running
        timestamp = running_time % self.length
        measure = running_time // self.length

        # Part has looped?
        if self.finished and measure != self.last_measure and self._events:
            if self.toggle:
                self.toggle = False
                self.mute = not self.mute
            self.finished = False
        if running and not self.finished and timestamp >= self.next_timestamp:
            self._trigger_event()

        # Check future events
        if running:
            while(self.future_events and
                  self.future_events[0].timestamp <= running_time):
                event = self.future_events[0]
                event.call(self)
                self.future_events.pop(0)

        self.last_measure = measure

    def stop(self):
        """When the part is stopped."""
        # Stop all notes
        midi.out.write_short(midi.CC + self.channel, 120, 127)
        self.future_events = []

    def start(self):
        """When the part starts from the beginning."""
        self.element = 0
        self.finished = False
        self.last_measure = -1
        try:
            self.next_timestamp = self._events[0].timestamp
        except:
            self.finished = True

    def append_future(self, event):
        bisect.insort(self.future_events, event)

    def append(self, event):
        """Add new event to the part"""
        print self.name
        event.timestamp = event.timestamp % self.length
        self._events.append(event)
        self._sort()

    def delete(self, event):
        self._events.remove(event)
        self._sort()

    def events(self, type=None):
        """Return all events of given type. All events if type==None."""
        if type:
            return [e for e in self._events if e.type() == type]
        return self._events

    def _sort(self):
        """Sort self._events. Calc self.element and self.next_timestamp."""
        global running_time
        if len(self._events) == 0:
            self.start()
            return
        self._events.sort()
        # Calculate last element played
        step_in_loop = running_time % self.length
        self.element = len(self._events) - 1
        for i, e in enumerate(self._events):
            if e.timestamp < step_in_loop:
                self.element = i
        next_element = (self.element + 1) % len(self._events)
        self.next_timestamp = self._events[next_element].timestamp
        self.finished = False
        if step_in_loop > self._events[-1].timestamp:
            self.finished = True

    def _trigger_event(self):
        """Trigger next/current event. Update self.element. Check if finished."""
        # trigger all events with the correct timestamp
        element_to_play = (self.element + 1) % len(self._events)
        while self._events[element_to_play].timestamp == self.next_timestamp and not self.finished:
            if not self.mute:
                event = self._events[element_to_play]
                event.call(self)
            self.element = element_to_play
            if self.element == len(self._events) - 1:
                self.finished = True
            element_to_play = (self.element + 1) % len(self._events)

        self.next_timestamp = self._events[element_to_play].timestamp


# YAML part representation
def part_representer(dumper, data):
    mapping = {'name': data.name,
               'length': data.length,
               'channel': data.channel,
               'events': data._events}
    return dumper.represent_mapping(u'!part', mapping)


def part_constructor(loader, node):
    m = loader.construct_mapping(node)
    return Part(m['name'], m['length'], m['channel'], m['events'])

yaml.add_representer(Part, part_representer)
yaml.add_constructor(u'!part', part_constructor)
