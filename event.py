import sequencer
import midi


class Event(object):
    def __init__(self, timestamp, function, params):
        # Using __dict__ directly to override __setattr__
        self.__dict__['timestamp'] = timestamp
        self.__dict__['function'] = function
        self.__dict__['params'] = params

    def type(self):
        return self.function.__name__

    def __getattr__(self, name):
        # Checks if attribute is in self.params
        for i, n in enumerate(self.function.__code__.co_varnames):
            if n == name:
                return self.params[i]
        error = "'{}' event has no '{}' attribute".format(self.type(), name)
        raise AttributeError(error)

    def __setattr__(self, name, value):
        # Checks if attribute is in self.params
        for i, n in enumerate(self.function.__code__.co_varnames):
            if n == name:
                self.params[i] = value
                return

        object.__setattr__(self, name, value)

    def __lt__(self, other):
        return self.timestamp < other.timestamp

    def __gt__(self, other):
        return self.timestamp > other.timestamp

    def __le__(self, other):
        return self.timestamp <= other.timestamp

    def __ge__(self, other):
        return self.timestamp >= other.timestamp

    def __ne__(self, other):
        return self.timestamp != other.timestamp

def note_off(part, note):
    midi.out.write_short(midi.NOTE_ON + part.channel, note, 0)

def note_on(part, note, velocity, length):
    midi.out.write_short(midi.NOTE_ON + part.channel, note, velocity)
    part.append_future(Event(sequencer.running_time + length,
                             note_off,
                             [part, note]))
