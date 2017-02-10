import yaml

import pygame.midi as pm

import screen
import midi
import sequencer

from gui import Counter, ActionButton
from choicelist import ChoiceList


class ConfigScreen(screen.Screen):
    def __init__(self):
        if sequencer.running:
            sequencer.stop()

        BUTTON_S = BUTTON_W, BUTTON_H = (310, 27)
        SPACE = 5
        ypos = SPACE

        midi_in = 'Midi In: None'
        if midi.m_in:
            name = pm.get_device_info(midi.m_in.device_id)[1]
            midi_in = 'Midi In: {}'.format(name)
        self.midi_in_button = ActionButton((SPACE, ypos),
                                           BUTTON_S,
                                           midi_in,
                                           True, True)
        self.channel_counter = Counter((SPACE * 2 + BUTTON_W, ypos),
                                       BUTTON_H,
                                       'Channel', 1, 16, start=midi.in_channel)

        ypos += SPACE + BUTTON_H
        midi_out = 'Midi Out: None'
        if midi.out:
            name = pm.get_device_info(midi.out.device_id)[1]
            midi_out = 'Midi Out: {}'.format(name)
        self.midi_out_button = ActionButton((SPACE, ypos),
                                            BUTTON_S,
                                            midi_out,
                                            True, True)

        ypos += SPACE + BUTTON_H
        self.bpm_counter = Counter((SPACE, ypos),
                                   BUTTON_H,
                                   'BPM', 20, 320,
                                   start=sequencer.project['bpm'])

    def _update(self, events):
        self.has_changed = True
        if self.midi_in_button.update(events):
            devices = [[od[0], od[0]] for od in midi.inDevices()]
            screen.stack.append(ChoiceList(devices, 'In Device'))
        self.channel_counter.update(events)
        if self.midi_out_button.update(events):
            devices = [[od[0], od[0]] for od in midi.outDevices()]
            screen.stack.append(ChoiceList(devices, 'Out Device'))
        self.bpm_counter.update(events)

    def focus(self, *args, **kwargs):
        if 'in_device' in kwargs:
            ind = kwargs['in_device']
            self.midi_in_button.text = 'Midi In: {}'.format(ind)
            midi.set_in_device(ind)
        elif 'out_device' in kwargs:
            od = kwargs['out_device']
            self.midi_out_button.text = 'Midi Out: {}'.format(od)
            midi.set_out_device(od)

    def close(self):
        sequencer.project['bpm'] = self.bpm_counter.value
        midi.in_channel = self.channel_counter.value
        in_name = None
        out_name = None
        if midi.m_in:
            in_name = pm.get_device_info(midi.m_in.device_id)[1]
        if midi.out:
            out_name = pm.get_device_info(midi.out.device_id)[1]
        config_dict = {'midi_out': out_name,
                       'midi_in': in_name,
                       'midi_in_channel': midi.in_channel}
        stream = file('config.yml', 'w')
        yaml.dump(config_dict, stream)

    def _render(self, surface):
        self.midi_in_button.render(surface)
        self.channel_counter.render(surface)
        self.midi_out_button.render(surface)
        self.bpm_counter.render(surface)

        return surface
