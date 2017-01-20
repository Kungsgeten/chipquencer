import pygame.midi as pm
import yaml

from collections import namedtuple

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
m_in = 0
in_channel = 0

MidiEvent = namedtuple('MidiEvent', 'channel status data1 data2 data3')
input_events = set([])


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
    if out:
        out.close()
    for od in outDevices():
        if od[0] == name:
            out = pm.Output(od[1])
            return True
    return False


def set_in_device(name):
    global m_in
    if m_in:
        m_in.close()
    for in_d in inDevices():
        if in_d[0] == name:
            m_in = pm.Input(in_d[1])
            return True
    return False


def update_input_events():
    """Should be run once per frame in order to keep midi in data fresh."""
    global input_events
    if m_in and m_in.poll():
        input_events = set([MidiEvent(e[0][0] & 0x0f,
                                      e[0][0] & 0xf0,
                                      e[0][1],
                                      e[0][2],
                                      e[0][3])
                            for e in m_in.read(1000)])
    else:
        input_events = set([])


def note_on_events():
    """A list of all note on events this frame."""
    return [e for e in input_events
            if e.channel == in_channel and e.status == NOTE_ON]


def note_off_events():
    """A list of all note off events this frame.
    Note on with velocity 0 is treated as note off."""
    return [e for e in input_events
            if e.channel == in_channel and
            (e.status == NOTE_OFF or
             e.status == NOTE_ON and e.data2 == 0)]


def init():
    """Initialize MIDI, return False if we haven't set up a MIDI Out Device."""
    global m_in, in_channel
    pm.init()
    config_yaml = yaml.load(file('config.yml', 'r'))
    try:
        in_channel = config_yaml['midi_in_channel']
        set_in_device(config_yaml['midi_in'])
    except:
        m_in = 0
    if not set_out_device(config_yaml['midi_out']):
        return False
    return True


def close():
    if out:
        out.close()
    if m_in:
        m_in.close()
    pm.quit()
