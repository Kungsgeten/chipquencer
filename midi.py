import pygame.midi as pm
import yaml

from choicelist import ChoiceList
import screen

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

NOTES = {0: 'C ', 1: 'C#', 2: 'D ', 3: 'D#', 4: 'E ', 5: 'F ',
         6: 'F#', 7: 'G ', 8: 'G#', 9: 'A ', 10: 'A#', 11: 'B '}

# Velocity
PPP = 16
PP = 32
P = 48
MP = 64
MF = 80
F = 96
FF = 112
FFF = 127

out = 0


# class MidiEvent:
#     def __init__(self, status, data1, data2, timestamp):
#         self.status = status
#         self.data1 = data1
#         self.data2 = data2
#         self.timestamp = timestamp
#         self.off = None  # note_on events has an off event too

#     def transpose(self, value, channel=0):
#         """Transposes an event, sends note off for old note"""
#         # TODO: Need to note off here, old note keeps playing
#         if self.off:
#             self.off.data1 += value
#             out.write_short(self.status + channel, self.data1, 0)
#         self.data1 += value

#     def set_note(self, value, channel=0):
#         """Set data1 of an event, sends note off for old note"""
#         if self.off:
#             self.off.data1 = value
#             out.write_short(self.status + channel, self.data1, 0)
#         self.data1 = value

#     def move(self, length):
#         self.timestamp += length
#         if self.off:
#             self.off.timestamp += length

#     def __str__(self):
#         return 'ts: %f, status: %i, data1: %i, data2: %i' % (self.timestamp,
#                                                              self.status,
#                                                              self.data1,
#                                                              self.data2)

# def note(tone, velocity, timestamp, length):
#     on = MidiEvent(NOTE_ON, tone, velocity, timestamp)
#     off = MidiEvent(NOTE_ON, tone, 0, timestamp + length)
#     on.off = off
#     return [on, off]

def outDevices():
    """Return a list of tuples: (device name, output device number)"""
    return [(pm.get_device_info(device_id)[1], device_id)
            for device_id in range(pm.get_count())
            if pm.get_device_info(device_id)[3] == 1]


def inDevices():
    """Return a list of tuples: (device name, input device number)"""
    return [(pm.get_device_info(device_id)[1], device_id)
            for device_id in range(pm.get_count())
            if pm.get_device_info(device_id)[2] == 1]


def sweep_cc(control, start, end, time, offset=0):
    step = -1
    if start <= end:
        step = 1
    events = abs(start - end)
    interval = time / events
    return [[[CC, control, i],
             abs(i-start) * interval] for i in range(start, end, step)]


def note_to_string(note):
    octave = note // 12
    note = NOTES[note % 12]
    if octave == 10:
        return note + 'X'
    return note + str(octave)


def set_out_device(name):
    global out
    for od in outDevices():
        if od[0] == name:
            out = pm.Output(od[1])
            return True
    return False


def init():
    """Initialize MIDI, return False if we haven't set up a MIDI Out Device."""
    pm.init()
    config_yaml = yaml.load(file('config.yml', 'r'))
    if not set_out_device(config_yaml['midi_out']):
        devices = [[od[0], od[0]] for od in outDevices()]
        screen.stack.append(ChoiceList(devices, 'Out Device'))
        return False
    return True


def close():
    out.close()
    pm.quit()
