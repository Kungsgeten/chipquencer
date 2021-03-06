import midi

import pygame.time
import bisect
import yaml

MC_NONE = 0
MC_SEND = 1
MC_RECIEVE = 2

clock_time = 0  # in ms since start
running_time = 0  # 16th notes pased since start
clock = pygame.time.Clock()
running = False
midiclock = MC_SEND
new_step = False

project = {'name': 'Unnamed',
           'path': None,
           'bpm': 135,
           'midi_clock': None,
           'scenes': [[]]}
current_scene = 0
goto_scene = None


def scene(scene_nr=None):
    """Get scene[scene_nr] from the project.

    If scene_nr=None, get current scene.
    """
    if scene_nr is None:
        scene_nr = current_scene
    return project['scenes'][scene_nr]


def _switch_scene():
    global current_scene, goto_scene
    from screen import stack
    current_scene = goto_scene
    goto_scene = None
    topclass = stack.top()
    if topclass.__class__.__name__ == 'SceneView':
        topclass.update_partrects()
    scene = 'Scene {}/{}'.format(current_scene + 1, len(project['scenes']))
    topclass.modeline[0] = scene


def start():
    """Start the sequencer."""
    global running
    running = True
    if midiclock == MC_SEND:
        midi.out.write_short(midi.MC_START)
    for part in parts():
        part.start()


def stop():
    """Stop the sequencer."""
    global clock_time, running_time, running, new_step
    clock_time = 0
    running_time = 0
    running = False
    new_step = False

    if midiclock == MC_SEND:
        midi.out.write_short(midi.MC_STOP)

    for part in parts():
        part.stop()


def toggle():
    """Starts/stops the sequencer."""
    stop() if running else start()


def parts():
    return [clip.part for clip in project['scenes'][current_scene]]


def save(path):
    """The path is relative to the projects folder."""
    with open(path, 'w') as f:
        yaml.dump(project, f)


def load(path):
    global project
    with open(path, 'r') as f:
        stop()
        project = yaml.load(f)
        start()


def update():
    """Update the sequencer.

    Should be run every frame if the sequencer has started.
    """
    global running_time, clock_time, new_step
    delta = clock.tick()
    bpm = project['bpm']

    if running:
        clock_time += delta * 0.001
        old_running_time = int(running_time)
        running_time = clock_time / ((60.0 / bpm) / 4.0)
        new_step = old_running_time != int(running_time)

    if midiclock == MC_SEND and midi.out:
        # 24 ppq
        ppq_length = (60.0 / bpm) / 24.0
        update.deltasum += delta * 0.001
        if update.deltasum >= update.next_ppq:
            midi.out.write_short(midi.MC_CLOCK)
            update.next_ppq += ppq_length
    # TODO: Recieve MIDI clock

    for part in parts():
        part.update()

update.deltasum = 0
update.next_ppq = 0


# Timestamps are measured in 16ths
class Part(object):
    def __init__(self, name, length=16, channel=0,
                 bank=0, program=0, cc=None, events=None, variant=0):
        if events is None:
            # Every element is a variant. A variant is a list of events,
            # sorted by timestamp. 10 variants is possible per Part.
            self._events = [list() for i in range(10)]
        else:
            self._events = events
        if cc is None:
            self.cc = [(i, '') for i in range(120)]
        else:
            self.cc = cc
        self.length = length  # in 16th notes
        self.name = name
        self._variant = variant

        self.future_events = []
        self._mute = False
        self.next_timestamp = 0
        self.element = -1  # the last element checked
        self.finished = False  # the last event has triggered?
        self._channel = channel
        self.channel = channel
        self.bank = bank
        self.program = program
        self.toggle = False
        self.last_measure = -1
        self.switch_to_variant = None

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

    @property
    def length(self):
        return self._length

    @length.setter
    def length(self, value):
        for variant_events in self._events:
            if variant_events:
                variant_events = [e for e in variant_events
                                  if e.timestamp < value]
        self._length = value

    @property
    def channel(self):
        return self._channel

    @channel.setter
    def channel(self, value):
        self.stop()
        self._channel = value

    def _change_variant(self):
        self.stop(kill_all=False)
        self._variant = self.switch_to_variant
        self.switch_to_variant = None
        self.start(program_change=False)

    def update(self):
        """Update the part and trigger new events. Check if part has looped."""
        global running_time, running, goto_scene

        timestamp = running_time % self.length
        measure = running_time // self.length

        # Check future events
        if running:
            while(self.future_events and
                  self.future_events[0].timestamp <= running_time):
                event = self.future_events[0]
                event.call(self)
                self.future_events.pop(0)

        # Part has looped?
        if self.finished and measure != self.last_measure:
            if self.toggle:
                self.toggle = False
                self.mute = not self.mute
            if goto_scene is not None:
                _switch_scene()
            if self.switch_to_variant is not None:
                self._change_variant()
            self.finished = False

        if not self._events[self._variant]:
            if(self.switch_to_variant is not None
               and measure != self.last_measure):
                self._change_variant()
            if(goto_scene is not None
               and measure != self.last_measure):
                _switch_scene()
            self.last_measure = measure
            return

        self.last_measure = measure

        if running and not self.finished and timestamp >= self.next_timestamp:
            self._trigger_event()

    def stop(self, kill_all=True):
        """Stop all notes."""
        for e in self.future_events:
            if e.type() == 'note_off':
                e.call(self)
        if kill_all:
            midi.out.write_short(midi.CC + self.channel, 120, 127)
        self.future_events = []

    def start(self, program_change=True):
        """When the part starts from the beginning."""
        self.finished = False
        self.last_measure = -1
        self.element = -1
        if program_change:
            if self.bank > 0:
                midi.out.write_short(midi.CC + self.channel, 32, self.bank - 1)
            if self.program > 0:
                midi.out.write_short(midi.PC + self.channel, self.program - 1)
        try:
            self.next_timestamp = self._events[self._variant][0].timestamp
        except:
            self.finished = True

    def append_future(self, event):
        bisect.insort(self.future_events, event)

    def append(self, event):
        """Add new event to the part"""
        event.timestamp = event.timestamp % self.length
        self._events[self._variant].append(event)
        self._sort()

    def delete(self, event):
        self._events[self._variant].remove(event)
        self._sort()

    def events(self, type=None):
        """Return all events of given type. All events if type==None."""
        if type:
            return [e for e in self._events[self._variant] if e.type() == type]
        return self._events[self._variant]

    def tranpose(self, semitones):
        """Transpose all note properties of the parts events."""
        for e in self._events[self._variant]:
            try:
                e.note += semitones
            except:
                pass

    def _sort(self):
        """Sort self._events. Calc self.element and self.next_timestamp."""
        global running_time
        if len(self._events[self._variant]) == 0:
            self.start()
            return
        self._events[self._variant].sort()
        # Calculate last element played
        step_in_loop = running_time % self.length
        self.element = len(self._events[self._variant]) - 1
        for i, e in enumerate(self._events[self._variant]):
            if e.timestamp < step_in_loop:
                self.element = i
        next_elmt = (self.element + 1) % len(self._events[self._variant])
        self.next_timestamp = self._events[self._variant][next_elmt].timestamp
        self.finished = False
        if step_in_loop > self._events[self._variant][-1].timestamp:
            self.finished = True

    def _trigger_event(self):
        """Trigger event(s). Update self.element. Check if finished."""
        # trigger all events with the correct timestamp
        play_elmt = (self.element + 1) % len(self._events[self._variant])
        while(self._events[self._variant][play_elmt].timestamp ==
              self.next_timestamp and not self.finished):
            if not self.mute:
                event = self._events[self._variant][play_elmt]
                event.call(self)
            self.element = play_elmt
            if self.element == len(self._events[self._variant]) - 1:
                self.finished = True
            play_elmt = (self.element + 1) % len(self._events[self._variant])

        self.next_timestamp = self._events[self._variant][play_elmt].timestamp


# YAML Part representation
def part_representer(dumper, data):
    mapping = {'name': data.name,
               'length': data.length,
               'channel': data.channel,
               'bank': data.bank,
               'program': data.program,
               'cc': data.cc,
               'events': data._events,
               'variant': data._variant}
    return dumper.represent_mapping(u'!part', mapping)


def part_constructor(loader, node):
    m = loader.construct_mapping(node)
    return Part(m['name'], m['length'], m['channel'],
                m['bank'], m['program'], m['cc'],
                m['events'], m['variant'])

yaml.add_representer(Part, part_representer)
yaml.add_constructor(u'!part', part_constructor)
