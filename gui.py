stack = [] # a stack of the current GUIs
seqs = [] # the GUIs of the different sequencer parts

def pop(*args, **kwargs):
    stack.pop()
    stack[-1].focus(*args, **kwargs)

class Screen:
    def update(self, events):
        pass

    def render(self, events):
        pass

    def focus(self, *args, **kwargs):
        """This function is run when the previous screen on the stack pops,
        returning the user to this screen."""
        pass
