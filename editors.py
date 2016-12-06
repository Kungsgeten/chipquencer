"""This module is used to import all editor classes.
When new editor classes are created, they should be added to the
import_editor_classes function.

The purpose of the module is to keep track of all editor classes (stored as a
ChoiceList in the editors variable), so that they can be used by
clipsettings.py"""

editors = []

def import_editor_classes():
    import seqgrid
