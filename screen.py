import pygame

import gui


class ScreenStack:
    def __init__(self):
        self.stack = []

    def __len__(self):
        return len(self.stack)

    def __contains__(self, item):
        return item in self.stack

    def pop(self, *args, **kwargs):
        self.stack.pop()
        self.top().focus(*args, **kwargs)
        self.top().has_changed = True
        return self.top()

    def append(self, element):
        assert isinstance(element, Screen), 'Element must be of type Screen.'
        self.stack.append(element)
        self.top().focus()
        self.top().has_changed = True

    def top(self):
        return self.stack[-1]

stack = ScreenStack()


class Screen(object):
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
                    stack.pop()
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
        surface = pygame.Surface(gui.SCREEN_SIZE)
        surface.fill(gui.C_LIGHTER)
        return self._render(surface)

    def _render(self, surface):
        return surface

    def close(self):
        """This method is run when you close the screen."""
        pass

    def focus(self, *args, **kwargs):
        """Run when the screen is switched to, from the previously active
        screen, for instance using pop."""
        pass
