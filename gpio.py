import RPi.GPIO as GPIO

# The four buttons on the pitft
BUTTON1 = 23
BUTTON2 = 22
BUTTON3 = 27
BUTTON4 = 18

class Button:
    def __init__(self, pin):
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        self.pin = pin
        self.last_state = False
        self.pressed = False
        self.down = False
        self.released = False

    def update(self):
        self.down = not GPIO.input(self.pin)
        self.pressed = False
        self.released = False
        if self.down != self.last_state:
            self.last_state = self.down
            if self.down:
                self.pressed = True
                return
            self.released = True

button1 = None
button2 = None
button3 = None
button4 = None

def init():
    global button1, button2, button3, button4
    GPIO.setmode(GPIO.BCM)
    button1 = Button(23)
    button2 = Button(22)
    button3 = Button(27)
    button4 = Button(18)

def update():
    global button1, button2, button3, button4
    button1.update()
    button2.update()
    button3.update()
    button4.update()

def close():
    GPIO.cleanup()
