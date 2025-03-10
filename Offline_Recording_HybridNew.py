import os
import sys
path = os.path.dirname(os.path.dirname(__file__)) 
sys.path.append(path)
import logging
import platform
import random
import time
from math import sqrt

import brainflow
import numpy as np
# from beeply.notes import *
from brainflow.board_shim import BoardShim, BrainFlowInputParams
from psychopy import core, event, visual  # import some libraries from PsychoPy
from psychopy.visual.elementarray import ElementArrayStim
from speller_configHybridNew import *

from utils.common import drawTextOnScreen, getdata_offline, save_raw
from utils.gui_hybridNew import *
import mne

pos = np.array(POSITIONS)
assert pos.shape   == (NUM_STIMULI, 2)
assert len(FREQS)  == NUM_STIMULI
assert len(PHASES) == NUM_STIMULI
colors = np.zeros( (NUM_STIMULI,3) )
# a = beeps(800)

#create a window
system = platform.system()
width, height = get_screen_settings(system)

REFRESH_RATE = 60
# Window parameters
win_builder = WindowBuilder(size=(width, height), refresh_rate=REFRESH_RATE)
WINDOW = win_builder.get_window()
STIMULUS = ElementArrayStim(win=WINDOW, 
            nElements=NUM_STIMULI, 
            fieldShape="square", 
            elementMask=None,
            elementTex=None,
            sizes=SIZE, 
            colors=colors,
            xys=pos,
            units="pix")

refresh_rate = round(WINDOW.getActualFrameRate())
print("Refresh Rate ==>", refresh_rate)

epoch_frames = int(EPOCH_DURATION * refresh_rate)
print("Epoch frames ==>",epoch_frames)
iti_frames = int(ITI_DURATION * refresh_rate)
iti_frames_cal = int(0.8 * refresh_rate)
cue_frames = int(CUE_DURATION * refresh_rate) 
#Presentation content

cue = visual.Rect(WINDOW, width=WIDTH, height=HEIGHT, pos=[0, 0], lineWidth=6, lineColor='red')

calib_text_start = "Starting callibration phase.Please avoid moving or blinking.\n\
You may blink when shifting your gaze.Focus your target on the characters presented with red cue."

calib_text_end = "Calibration phase completed"
cal_start = visual.TextStim(WINDOW, text=calib_text_start, color=(-1., -1., -1.))
cal_end = visual.TextStim(WINDOW, text=calib_text_end, color=(-1., -1., -1.))

targets = {f"{target}": visual.TextStim(win=WINDOW, text=target, pos=pos, color=(-1., -1., -1.), height=HEIGHT_OF_TARGET)
        for pos, target in zip(POSITIONS, TARGET_CHARACTERS)}


wave_type = "sin"
flickers = {f"{target}":Stimuli(window=WINDOW, frequency=f, phase=phase, amplitude=AMPLITUDE, 
                                    wave_type=wave_type, duration=EPOCH_DURATION, fps=refresh_rate,
                                    base_pos=pos, height=HEIGHT, width=WIDTH)
            for f, pos, phase, target in zip(FREQS, POSITIONS, PHASES, TARGET_CHARACTERS)}

hori_divider = visual.Line(WINDOW, start=HORI_DIVIDER_START, end=HORI_DIVIDER_END, lineColor='black')
ver_divider_1 = visual.Line(WINDOW, start=VER_DIVIDER_1_START, end=VER_DIVIDER_1_END, lineColor='black')

block_break_text = f"Block Break {BLOCK_BREAK} sec. Please do not move towards the end of break."
# block_break_start = visual.TextStim(window, text=block_break_text, color=(1., 1., 1.))
# counter = visual.TextStim(window, text='', pos=(0, 50), color=(1., 1., 1.))
block_break_start = visual.TextStim(WINDOW, text=block_break_text, color=(-1., -1., -1.))
counter = visual.TextStim(WINDOW, text='', pos=(0, 50), color=(-1., -1., -1.))

def get_keypress():
    keys = event.getKeys()
    if keys and keys[0] == 'escape':
        WINDOW.close()
        core.quit()
    else: 
        return None

def get_frames(order):
    # frames is a shape of (n_frame, n_stimuli, n_color)
    num_char = 1
    frames = []
    for sti in range(NUM_STIMULI):
        phase = PHASES[sti]
        freq = FREQS[sti]
        # flick = np.ones(EPOCH_DURATION*REFRESH_RATE)
        flick = np.sin(2 * np.pi * freq * np.arange(0,EPOCH_DURATION,1/REFRESH_RATE) + (phase * np.pi))
        # adjust range to fit [-1,1]
        flick[order[sti]] = 1
        flick = np.expand_dims(((flick * 2) - 1), axis=1)
        color = np.concatenate([flick,flick,flick], axis=1)
        frames.append(np.expand_dims(color, axis=0))
    frames = np.concatenate(frames, axis=0)
    return frames

def eegMarking(board,marker):
    print("Inserting marker", marker)
    board.insert_marker(marker)
    time.sleep(0.1)

def flicker(board, timeline, order):
    print("POSITIONS", POSITIONS)
    global frames
    global t0
    # For the flickering
    for target in sequence:
        get_keypress()
        target_flicker = flickers[str(target)]
        target_pos = (target_flicker.base_x, target_flicker.base_y)
        marker = MARKERS[str(target)]

        #Display the cue
        cue.pos = target_pos
        for frame in range(cue_frames):
                cue.draw()
                WINDOW.flip()

        frames = 0
        # eegMarking(board, MARKERS['trial_start'])
        
        # IDEA
        # Generating an entire epoch of frames
        # The shape is (n, m, f) where 
        # n: number of sub-speller
        # m: is each character in the sub speller
        # f: is frame_idx
        # Generate the order of flashing
        FRAMES = get_frames(order)
        FRAMES = np.swapaxes(FRAMES, 0,1)

        for frame in FRAMES:
            STIMULUS.draw()
            STIMULUS.setColors(colors=frame, colorSpace='rgb')
            WINDOW.flip()
    try:
        main()
    except KeyboardInterrupt:
        print("Keyboard Interrupt")
    finally:
        print("==== REPORT ====")
        print(f'Overall, {WINDOW.nDroppedFrames} frames were dropped.')


def drawDisplayBox():
    # Drawing the grid
    hori_divider.autoDraw = True
    ver_divider_1.autoDraw = True
    # Display target characters
    for target in targets.values():
        target.autoDraw = True
        # get_keypress()
    print("Sequence is", sequence)

def main():
    global sequence
    global trialClock

    random.seed(42)
    # set the order to white then will add one later.
    default_order = [True]*EPOCH_DURATION*REFRESH_RATE
    pt = int(EPOCH_DURATION*REFRESH_RATE/(NO_CHARACTER+1))
    unarranged_order = []
    order = []
    _ = []
    
    if sqrt(NO_SUBSPELLER)%1!=0:
        hori_sub_no = int(sqrt(NO_SUBSPELLER)+1)
    else:
        hori_sub_no = int(sqrt(NO_SUBSPELLER))

    for ch in range(NO_CHARACTER):
        default_order[ch*pt:pt*(2+ch)] = [False]*pt*2
        unarranged_order.append(default_order)
        default_order = [True]*EPOCH_DURATION*REFRESH_RATE

    for i in range(NO_SUBSPELLER):
        random.shuffle(unarranged_order)
        if i >= hori_sub_no:
            order+=_
            _=[]
        for j in range(NO_CHARACTER):
            if j < NO_CHARACTER/2:
                order.append(unarranged_order[j])
            else:
                _.append(unarranged_order[j])
    order+=_
            
    BoardShim.enable_dev_board_logger()

    #brainflow initialization 
    params = BrainFlowInputParams()
    board_shim = BoardShim(BOARD_ID, params)

    #prepare board
    try:
        board_shim.prepare_session()
    except brainflow.board_shim.BrainFlowError as e:
        print(f"Error: {e}")
        print("The end")
        time.sleep(1)
        sys.exit()
    #board start streaming
    board_shim.start_stream(num_samples=700000)

    logging.info('Begining the experiment')

    while True:

        # Starting the display
        trialClock = core.Clock()
        cal_start.draw()
        WINDOW.flip()
        core.wait(10)
        timeline = []

        for block in range(NUM_BLOCK):
            # a.hear('A_')
            drawTextOnScreen('Starting block ' + str(block + 1) ,WINDOW)
            core.wait(0.5)
            sequence = TARGET_CHARACTERS
            for trials in range(NUM_TRIAL):
                get_keypress()
                # Drawing the grid
                hori_divider.autoDraw = True
                ver_divider_1.autoDraw = True
                # Display target characters
                for target in targets.values():
                    target.autoDraw = True
                    # get_keypress()
                print("Sequence is", sequence)
                flicker(board_shim, timeline, order)
                # At the end of the trial, calculate real duration and amount of frames
                t1 = trialClock.getTime()  # Time at end of trial
                elapsed = t1 - t0
                print(f"Time elapsed: {elapsed}")
                print(f"Total frames: {frames}")

           
            # clearing the screen
            hori_divider.autoDraw = False
            ver_divider_1.autoDraw = False
            for target in targets.values():
                target.autoDraw = False

            # window.color = 'black'
            # window.flip()
            countdown_timer = core.CountdownTimer(BLOCK_BREAK)
            if (block + 1) < NUM_BLOCK: 
                block_break_start.autoDraw = True
                while countdown_timer.getTime() > 0:
                    get_keypress()
                    time_remaining = countdown_timer.getTime()
                    counter.text = f'Time remaining: {int(time_remaining)}'
                    counter.draw()
                    WINDOW.flip()

            block += 1
            block_break_start.autoDraw = False
            WINDOW.flip()
            # window.color = 'white'
            # window.flip()

        drawTextOnScreen('End of experiment, Thank you',WINDOW)
        #Adding buffer of 10 sec at the end
        core.wait(10)
        # saving the data from 1 block
        block_name = f'{PARTICIPANT_ID}'
        data = board_shim.get_board_data()
        # data_copy = data.copy()
        raw = getdata_offline(data,BOARD_ID,n_samples = 250,dropEnable = False)
        events = mne.find_events(raw)
        print(len(events))
        save_raw(raw,block_name,RECORDING_DIR, PARTICIPANT_ID)
        # save_csv(data, RECORDING_DIR, PARTICIPANT_ID)
        
        break


    if board_shim.is_prepared():
        logging.info('Releasing session')
        # stop board to stream
        board_shim.stop_stream()
        board_shim.release_session()

    #cleanup
    WINDOW.close()
    core.quit()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Keyboard Interrupt")
    finally:
        print("==== REPORT ====")
        print(f'Overall, {WINDOW.nDroppedFrames} frames were dropped.')