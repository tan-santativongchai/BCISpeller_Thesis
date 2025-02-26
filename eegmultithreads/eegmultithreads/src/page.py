from psychopy import visual
from psychopy.visual.basevisual import BaseVisualStim
from psychopy.hardware import keyboard
from psychopy.hardware.keyboard import KeyPress


kb = keyboard.Keyboard()

def show_welcome(window:visual.Window, n_frame:int):
    message = "Hello"
    stim = visual.TextStim(win=window, text=message, color=(0,0,0))
    _flip(window=window, n_frame=n_frame, stim=stim)

def show_blank(window:visual.Window, n_frame:int):
    _flip(window=window, n_frame=n_frame)

def _flip(window:visual.Window, n_frame:int, stim:BaseVisualStim=None):
    if(stim != None):
        for _ in range(n_frame):
            keys = kb.getKeys()
            key:KeyPress
            for key in keys:
                print(key, key.name)
                if(key.name == "escape"):
                    raise KeyboardInterrupt()
            stim.draw()
            window.flip()
    else:
        for _ in range(n_frame):
            keys = kb.getKeys()
            key:KeyPress
            for key in keys:
                if(key.name == "escape"):
                    raise KeyboardInterrupt()
            window.flip()
        