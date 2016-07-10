import pygame.midi

NOTE_OFF = 0x80
NOTE_ON = 0x90
POLY_AFTERTOUCH = 0xA0
CC = 0xB0
PC = 0xC0
AFTERTOUCH = 0xD0
PITCH_WHEEL = 0xE0

# MIDI clock
MC_CLOCK = 0xF8
MC_START = 0xFA
MC_CONTINUE = 0xFB
MC_STOP = 0xFC

NOTES = {0:'C ', 1:'C#', 2:'D ', 3:'D#', 4:'E ', 5:'F ',
         6:'F#', 7:'G ', 8:'G#', 9:'A ', 10:'A#', 11:'B '}

out = 0

class MidiEvent:
    def __init__(self, status, data1, data2, timestamp):
        self.status = status
        self.data1 = data1
        self.data2 = data2
        self.timestamp = timestamp
        self.off = None # note_on events has an off event too

    def transpose(self, value, channel=0):
        """Transposes an event, sends note off for old note"""
        # TODO: Need to note off here, old note keeps playing
        if self.off:
            self.off.data1 += value
            out.write_short(self.status + channel, self.data1, 0)
        self.data1 += value

    def set_note(self, value, channel=0):
        """Set data1 of an event, sends note off for old note"""
        if self.off:
            self.off.data1 = value
            out.write_short(self.status + channel, self.data1, 0)
        self.data1 = value

    def move(self, length):
        self.timestamp += length
        if self.off:
            self.off.timestamp += length

    def __str__(self):
        string = 'timestamp: %f, status: %i, data1: %i, data2: %i' % (self.timestamp,
                                                                      self.status,
                                                                      self.data1,
                                                                      self.data2)
        if self.off:
            string += '\n  note off:\n' + str(self.off)
        return string + '\n---------\n'


def outDevices():
    """Returns a list of tuples: (device name, output device number)"""
    return [(pygame.midi.get_device_info(device_id)[1], device_id)
            for device_id in range(pygame.midi.get_count())
            if pygame.midi.get_device_info(device_id)[3]==1]

def inDevices():
    """Returns a list of tuples: (device name, input device number)"""
    return [(pygame.midi.get_device_info(device_id)[1], device_id)
            for device_id in range(pygame.midi.get_count())
            if pygame.midi.get_device_info(device_id)[2]==1]

def sweep_cc(control, start, end, time, offset=0):
    step = -1
    if start <= end:
        step = 1
    events = abs(start - end)
    interval = time / events
    return [[[CC, control, i],
             abs(i-start) * interval] for i in range(start, end, step)]

def note(tone, velocity, timestamp, length):
    on = MidiEvent(NOTE_ON, tone, velocity, timestamp)
    off = MidiEvent(NOTE_ON, tone, 0, timestamp + length)
    on.off = off
    return [on, off]

def note_to_string(note):
    octave = note // 12
    note = NOTES[note % 12]
    if octave == 10:
        return note + 'X'
    return note + str(octave)

def init():
    global out
    pygame.midi.init()
    print outDevices()
    # out = pygame.midi.Output(0)
    for od in outDevices():
        if 'CME U2MIDI' == od[0]:
            out = pygame.midi.Output(od[1])
            return

def close():
    out.close()
    pygame.midi.quit()
