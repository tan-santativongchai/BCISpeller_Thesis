import numpy as np
from window import WindowBuilder, SystemScreen
from page import *
from psychopy.visual.elementarray import ElementArrayStim


# Keep in mind about timing
# https://psychopy.org/coder/codeStimuli.html
# TL;DR. The best method to do timing is framing.
# Eseentially, we use `window.flip()`. 
# Behind the scence, Psychopy will handle the synchrinized with the refreash rate.

# Stimuli
# https://psychopy.org/general/timing/reducingFrameDrops.html


NUM_STIMULI:int = 8
STIMULI_SIZE:int = 50
POSITIONS:list[tuple[int,int]] = [
    (-800, 300), 
    (0, 300), 
    (800, 300), 
    (-800, 0), 
    (800, 0), 
    (-800, -300), 
    (0, -300), 
    (800, -300)
    ]
FREQS :list[float] = [1,    2,    3,  8.6,  8.8,    9,  9.2,  9.4]
PHASES:list[float] = [0, 0.35, 0.70, 1.05, 1.40, 1.75, 0.10, 0.45]
EPOCH_DURATION:float = 2

pos:np.ndarray = np.array(POSITIONS)
assert pos.shape   == (NUM_STIMULI, 2)
assert len(FREQS)  == NUM_STIMULI
assert len(PHASES) == NUM_STIMULI
colors = np.zeros( (NUM_STIMULI,3) )


### Before Anything Start ####
# Initiation step.

# ### Method 1: Create window with Screen object
# # Helper class that detect your screen
# sys_screen = SystemScreen()
# # Create window object with helper class
# REFRESH_RATE:int = sys_screen.get_screen(0).refresh_rate
# win_builder = WindowBuilder(screen=sys_screen.get_screen(0))

### Method 2: create window manually
REFRESH_RATE:int = 60
win_builder = WindowBuilder(size=(1920,1080), refresh_rate=REFRESH_RATE)
WINDOW = win_builder.get_window()

def get_frames() -> np.ndarray:
    # frames is a shape of (n_frame, n_stimuli, n_color)
    n_frames = REFRESH_RATE * EPOCH_DURATION
    frames = []
    for sti in range(NUM_STIMULI):
        phase = PHASES[sti]
        freq = FREQS[sti]
        flick = np.sin(2 * np.pi * freq * np.arange(0,EPOCH_DURATION,1/REFRESH_RATE) + (phase * np.pi))
        # adjust range to fit [-1,1]
        flick = np.expand_dims(((flick * 2) - 1), axis=1)
        color = np.concatenate([flick,flick,flick], axis=1)
        frames.append(np.expand_dims(color, axis=0))
    frames = np.concatenate(frames, axis=0)
    return frames

FRAMES:np.ndarray = get_frames()
assert FRAMES.shape == (NUM_STIMULI, REFRESH_RATE * EPOCH_DURATION, 3)
# Swap axis for easy operation
FRAMES = np.swapaxes(FRAMES, 0,1)

STIMULUS = ElementArrayStim(win=WINDOW, 
            nElements=NUM_STIMULI, 
            fieldShape="square", 
            elementMask=None,
            elementTex=None,
            sizes=STIMULI_SIZE, 
            colors=colors,
            xys=pos,
            units="pix")

def main():
    show_welcome(window=WINDOW, n_frame=REFRESH_RATE * 2)
    show_blank(window=WINDOW, n_frame=REFRESH_RATE * 2)

    WINDOW.flip()
    for frame in FRAMES:
        STIMULUS.draw()
        STIMULUS.setColors(colors=frame, colorSpace='rgb')
        WINDOW.flip()

if __name__ == "__main__":

    try:
        main()
    except KeyboardInterrupt:
        print("Keyboard Interrupt")
    finally:
        print("==== REPORT ====")
        print(f'Overall, {WINDOW.nDroppedFrames} frames were dropped.')