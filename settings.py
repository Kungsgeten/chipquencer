import yaml
from os import listdir
from os.path import isfile, join

# A list of (Instrument, file)
INSTRUMENTS = []


def load_instruments():
    global INSTRUMENTS
    INSTRUMENTS = []
    path = 'instruments/'
    instrumentfiles = [f for f in listdir(path) if isfile(join(path, f))]
    for i in instrumentfiles:
        stream = file('instruments/' + i, 'r')
        inst_dict = yaml.load(stream)
        INSTRUMENTS.append((inst_dict['name'], i))
    print INSTRUMENTS
