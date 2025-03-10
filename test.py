from psychopy.hardware import keyboard
from psychopy import core
kb = keyboard.Keyboard()
# during your trial
kb.clock.reset()  # when you want to start the timer from
keys = kb.getKeys(['right', 'left', 'quit'])
kb.start()
if 'quit' in keys:
    core.quit()
kb.stop()
for key in keys:
    print(key.name, key.rt, key.duration)