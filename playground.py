from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
import pygame.midi as pm

import midi2

class MidiKey(Button):
    note = NumericProperty(60)

class Keybed(FloatLayout):
    channel = NumericProperty(0)
    root = NumericProperty(40)
    octaves = NumericProperty(2)
    velocity = NumericProperty(100)
    mout = None

    def set_device(self, name):
        for d in midi2.outDevices():
            if d[0] == name:
                self.mout = pm.Output(d[1])
                return

    def key_pressed(self, button):
        self.mout.write_short(0x90 + self.channel, self.root + button.note, self.velocity)

    def key_released(self, button):
        self.mout.write_short(0x80 + self.channel, self.root + button.note, self.velocity)

    def on_octaves(self, instance, value):
        # Create the keys of the keybed
        KEY_WIDTH = (self.width / (self.octaves * 7.)) / self.width
        black_offset = -1
        for i in range(self.octaves * 12):
            button = Button()
            button.note = i
            button.bind(on_press=self.key_pressed)
            button.bind(on_release=self.key_released)
            # white keys
            if i % 12 in [0, 2, 4, 5, 7, 9, 11]:
                index = [0, 2, 4, 5, 7, 9, 11].index(i % 12)
                button.size_hint = (KEY_WIDTH, 1)
                button.pos_hint = {'x': KEY_WIDTH * index + KEY_WIDTH * 7 * (i // 12)}
                self.add_widget(button, 100)
            # black keys
            else:
                button.size_hint = (KEY_WIDTH * 0.75, 0.5)
                if i % 12 in [1, 6]:
                    black_offset += 1
                button.pos_hint = {'x': KEY_WIDTH * (i + black_offset) * 0.5 + KEY_WIDTH * 0.125, 'top': 1}
                self.add_widget(button)


class ButtonGrid(Widget):
    mout = None
    keyboard = ObjectProperty

    def set_midi_out(self, device):
        if self.mout:
            self.mout.close()
        self.mout = pm.Output(device)

    def device_names(self):
        return [d[0] for d in midi2.outDevices()]

    def set_device(self, name):
        for d in midi2.outDevices():
            if d[0] == name:
                self.set_midi_out(d[1])
                return

    def play_note(self, note, vel=100):
        if self.mout:
            self.mout.write_short(0x90, note, vel)

    def stop_note(self, note, vel=100):
        if self.mout:
            self.mout.write_short(0x80, note, vel)

class PlayApp(App):
    def build(self):
        return ButtonGrid()

if __name__ == '__main__':
    midi2.init()
    PlayApp().run()
    midi2.close()
