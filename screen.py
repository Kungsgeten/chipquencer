import pygame

import settings

stack = [] # a stack of the current screens
seqs = [] # a list of each sequencer part

def pop(*args, **kwargs):
    stack.pop()
    stack[-1].focus(*args, **kwargs)
    stack[-1].has_changed = True

class Screen:
    """Screen is meant to be used as an abstract base class for other "screens". A
    screen is the entire screen with all its interface, visible to the user.

    Each subclass should define an _update(self, events) and _render(self,
    surface) method. They may also want to implement the focus() and/or close()
    methods: focus() if the screen itself will trigger other screens, modifying
    its behaviour (for instance a menu or settings screen); close() if something
    should happen before closing the screen.

    """
    def update(self, events):
        """Things that happen before the _update method."""
        self.has_changed = False
        # Close screen if pressing ESC
        if len(stack) > 1:
            for e in events:
                if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    self.close()
                    pop()
                    return
        self._update(events)

    def _update(self, events):
        pass

    def render(self):
        """Things that happen before the _render method."""
        try:
            if not self.has_changed:
                return None
        except:
            self.has_changed = True
        surface = pygame.Surface(settings.SCREEN_SIZE)
        surface.fill(settings.C_LIGHTER)
        return self._render(surface)

    def _render(self, surface):
        return surface

    def close(self):
        """This method is run when you close the screen."""
        pass

    def focus(self, *args, **kwargs):
        """This method is run when the previous screen on the stack pops,
        returning the user to this screen."""
        pass
