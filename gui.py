import pygame
import yaml

SCREEN_SIZE = SCREEN_WIDTH, SCREEN_HEIGHT = 480, 272

# Color theme
C_PRIMARY = None
C_LIGHTER = None
C_LIGHTEST = None
C_DARKER = None
C_DARKEST = None

def load_colors():
    global C_PRIMARY, C_LIGHTER, C_LIGHTEST, C_DARKER, C_DARKEST
    stream = file('themes.yml', 'r')
    theme = yaml.load(stream)['active_theme']
    C_PRIMARY = pygame.Color(format(theme['primary'], '#08x'))
    C_LIGHTER = pygame.Color(format(theme['lighter'], '#08x'))
    C_LIGHTEST = pygame.Color(format(theme['lightest'], '#08x'))
    C_DARKER = pygame.Color(format(theme['darker'], '#08x'))
    C_DARKEST = pygame.Color(format(theme['darkest'], '#08x'))

load_colors()
pygame.font.init()
FONT_BIG = pygame.font.Font("fonts/ProggyClean.ttf", 16)
FONT_MEDIUM = pygame.font.Font("fonts/ProggySmall.ttf", 16)
FONT_SMALL = pygame.font.Font("fonts/ProggyTiny.ttf", 16)

class ActionButton:
    """A regular rectangular button."""

    font = FONT_BIG

    def __init__(self, pos, size, text, center_x=False, center_y=False):
        self.text = text
        self.center_x = center_x
        self.center_y = center_y
        x, y = pos
        width, height = size
        self.rect = pygame.Rect(x, y, width, height)

    def clicked(self, events):
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(e.pos):
                return True
        return False

    def render(self, surface):
        pygame.draw.rect(surface, C_PRIMARY, self.rect)
        text = self.font.render(self.text, False, C_LIGHTEST)
        xoffset = 2
        yoffset = 0
        if self.center_x:
            xoffset = (self.rect.width - text.get_rect().width) / 2
        if self.center_y:
            yoffset = text.get_rect().height / 2
        surface.blit(text, (self.rect.x + xoffset, self.rect.y + yoffset))


class TextField:
    """A one line text field."""
    font = FONT_BIG

    def __init__(self, pos, size, text='', center_x=False, center_y=False):
        self.text = text
        self.center_x = center_x
        self.center_y = center_y
        self.rect = pygame.Rect(pos, size)
        self.focused = False

    def update(self, events):
        for e in events:
            if(e.type == pygame.MOUSEBUTTONDOWN and
               self.rect.collidepoint(e.pos)):
                self.focused = not self.focused
            elif(self.focused and e.type == pygame.KEYDOWN):
                if e.key == pygame.K_RETURN:
                    self.focused = False
                elif e.key == pygame.K_BACKSPACE:
                    if len(self.text):
                        self.text = self.text[:-1]
                else:
                    char = e.unicode.encode('utf-8')
                    self.text += char

    def render(self, surface):
        color = C_PRIMARY
        if self.focused:
            color = C_DARKER
        pygame.draw.rect(surface, color, self.rect)
        text = self.font.render(self.text, False, C_LIGHTEST, color)

        xoffset = 2
        yoffset = 0
        if self.center_x:
            xoffset = (self.rect.width - text.get_rect().width) / 2
        if self.center_y:
            yoffset = text.get_rect().height / 2
        surface.blit(text, (self.rect.x + xoffset, self.rect.y + yoffset))


class Counter:
    """A counter which can be incremented or decremented. Cpunter.value is used to
    get the current value.
    """
    font = FONT_BIG

    def __init__(self, pos, height, text, minimum, maximum, start=None):
        """If start is None it will be set to minimum."""
        self.pos = x, y = pos
        self.minimum = minimum
        self.maximum = maximum
        self.height = height
        self.text = self.font.render(text, False, C_DARKER)
        OFFSET = 5
        self.dec = ActionButton((self.text.get_width() + x + OFFSET, y),
                                (height, height), '-',
                                True, True)
        self.inc = ActionButton((self.text.get_width() + x + height * 2 + OFFSET, y),
                                (height, height), '+',
                                True, True)
        self.value = start
        if self.value is None:
            self.value = minimum

    def update(self, events):
        if self.dec.clicked(events):
            self.value -= 1
            if self.value < self.minimum:
                self.value = self.maximum
        elif self.inc.clicked(events):
            self.value += 1
            if self.value > self.maximum:
                self.value = self.minimum

    def render(self, surface):
        self.dec.render(surface)
        self.inc.render(surface)

        number = self.font.render((str(self.value)), False, C_DARKER)
        yoffset = self.dec.rect.height / 2 - self.text.get_rect().height / 2
        x = self.dec.rect.right + self.height / 2 - number.get_rect().width / 2
        y = self.pos[1] + yoffset
        surface.blit(number, (x, y))

        surface.blit(self.text, (self.pos[0], y))

class RadioButtons:
    """A set of radio buttons, can get the active index by RadioButtons.selected."""

    font = FONT_BIG

    def __init__(self, pos, size, columns, rows, strings=[], spacing=0):
        if len(strings):
            assert len(strings) == columns * rows
        self.strings = strings
        x, y = pos
        width, height = size
        self.arearect = pygame.Rect(x, y,
                                    (width + spacing) * columns,
                                    (height + spacing) * rows)
        self.rects = []
        self.selected = 0
        for r in range(rows):
            for c in range(columns):
                self.rects.append(pygame.Rect(x + c * (width + spacing),
                                              y + r * (height + spacing),
                                              width,
                                              height))

    def update(self, events):
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and self.arearect.collidepoint(e.pos):
                for i, rect in enumerate(self.rects):
                    if rect.collidepoint(e.pos):
                        self.selected = i
                        return self.selected
        return None

    def render(self, surface):
        for i, rect in enumerate(self.rects):
            font_color = C_LIGHTEST
            button_color = C_PRIMARY
            if i == self.selected:
                font_color = C_LIGHTEST
                button_color = C_DARKER
            pygame.draw.rect(surface, button_color, rect)
            try:
                text = self.font.render(self.strings[i], False, font_color)
                surface.blit(text, (rect.x, rect.y))
            except:
                pass

class Slider:
    """A rectangle which is turned into a slider. Slider.get_data() returns the
    percentage filled. The slider will be horizontal or vertical depending on the
    size of the rectangle.
    """
    def __init__(self, rect):
        self.rect = rect
        self.active = False
        self._pixels = 0.0

    def update(self, events, finetune=False):
        # for e in events:
        #     if e.type == pygame.MOUSEBUTTONUP:
        #         self.active = False
        #     elif e.type == pygame.MOUSEBUTTONDOWN:
        #         self.active = self.rect.collidepoint(e.pos)
        #         pygame.mouse.get_rel()
        if self.active:
            relx, rely = pygame.mouse.get_rel()
            if finetune:
                rely *= 0.2
            self._pixels -= rely
            if self._pixels < 0:
                self._pixels = 0.0
            elif self._pixels > self.rect.height:
                self._pixels = float(self.rect.height)
            if pygame.MOUSEBUTTONUP in [e.type for e in events]:
                self.active = False
            return self.get_data()
        else:
            if pygame.MOUSEBUTTONDOWN in [e.type for e in events]:
                self.active = self.rect.collidepoint(e.pos)
                pygame.mouse.get_rel()
            return None

    def render(self, surface):
        pygame.draw.rect(surface, C_PRIMARY, self.rect)
        status = pygame.Rect(self.rect.left,
                             self.rect.bottom - self._pixels,
                             self.rect.width,
                             self._pixels)
        pygame.draw.rect(surface, C_DARKER, status)

    def get_data(self):
        """Return the percentage filled."""
        return self._pixels / self.rect.height

    def set_value(self, value, maximum, minimum=0.0):
        if value > maximum:
            value = maximum
        self._pixels = (float(value - minimum) / (maximum - minimum)) * self.rect.height
