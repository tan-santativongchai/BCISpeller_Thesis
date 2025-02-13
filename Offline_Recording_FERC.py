import os
import sys
path = os.path.dirname(os.path.dirname(__file__)) 
sys.path.append(path)
import logging
import platform
import random
import time
from multiprocessing import Process

import brainflow
import numpy as np
# from beeply.notes import *
from brainflow.board_shim import BoardShim, BrainFlowInputParams
from psychopy import core, event, visual  # import some libraries from PsychoPy
from speller_configFERC import *

from utils.common import drawTextOnScreen, getdata_offline, save_raw
from utils.gui_FERC import Stimuli, get_screen_settings
import mne
##########################
# READ ME
# Following code is from https://github.com/sunsun101/hybrid-ssvep-p300-speller
# The file that should be imported also are: 
# 1) speller_configFERC.py 
# 2) gui_subspellerFERC.py 
# a = beeps(800)
##########################
# Window parameters
system = platform.system()
width, height = get_screen_settings(system)

#create a window
window = visual.Window([width, height], screen=1, color=[1,1,1],blendMode='avg', useFBO=True, units="pix", fullscr=True)

refresh_rate = round(window.getActualFrameRate())
print("Refresh Rate ==>", refresh_rate)

# Time conversion to frames
epoch_frames = int(EPOCH_DURATION * refresh_rate)
print("Epoch frames ==>",epoch_frames)
iti_frames = int(ITI_DURATION * refresh_rate)
iti_frames_cal = int(0.8 * refresh_rate)
cue_frames = int(CUE_DURATION * refresh_rate)   

#Presentation content

cue = visual.Rect(window, width=WIDTH, height=HEIGHT, pos=[0, 0], lineWidth=6, lineColor='red')

calib_text_start = "Starting callibration phase.Please avoid moving or blinking.\n\
You may blink when shifting your gaze.Focus your target on the characters presented with red cue."

calib_text_end = "Calibration phase completed"
cal_start = visual.TextStim(window, text=calib_text_start, color=(-1., -1., -1.))
cal_end = visual.TextStim(window, text=calib_text_end, color=(-1., -1., -1.))

targets = {f"{target}": visual.TextStim(win=window, text=target, pos=pos, color=(-1., -1., -1.), height=HEIGHT_OF_TARGET)
        for pos, target in zip(POSITIONS, TARGET_CHARACTERS)}


wave_type = "sin"
flickers = {f"{target}":Stimuli(window=window, frequency=f, phase=phase, amplitude=AMPLITUDE, 
                                    wave_type=wave_type, duration=EPOCH_DURATION, fps=refresh_rate,
                                    base_pos=pos, height=HEIGHT, width=WIDTH)
            for f, pos, phase, target in zip(FREQS, POSITIONS, PHASES, TARGET_CHARACTERS)}

hori_divider = visual.Line(window, start=HORI_DIVIDER_START, end=HORI_DIVIDER_END, lineColor='black')
ver_divider_1 = visual.Line(window, start=VER_DIVIDER_1_START, end=VER_DIVIDER_1_END, lineColor='black')

block_break_text = f"Block Break {BLOCK_BREAK} sec. Please do not move towards the end of break."
# block_break_start = visual.TextStim(window, text=block_break_text, color=(1., 1., 1.))
# counter = visual.TextStim(window, text='', pos=(0, 50), color=(1., 1., 1.))
block_break_start = visual.TextStim(window, text=block_break_text, color=(-1., -1., -1.))
counter = visual.TextStim(window, text='', pos=(0, 50), color=(-1., -1., -1.))

def get_keypress():
    keys = event.getKeys()
    if keys and keys[0] == 'escape':
        window.close()
        core.quit()
    else: 
        return None

def eegMarking(board,marker):
    print("Inserting marker", marker)
    board.insert_marker(marker)
    time.sleep(0.1)

def flicker(board):
    print("POSITIONS", POSITIONS)
    global frames
    global t0
    # For the flickering
    for target in sequence:
        get_keypress()
        target_flicker = flickers[str(target)]
        target_pos = (target_flicker.base_x, target_flicker.base_y)
        marker = MARKERS[str(target)]


        t0 = trialClock.getTime()  # Retrieve time at start of cue presentation
        #Display the cue
        cue.pos = target_pos
        for frame in range(cue_frames):
                cue.draw()
                window.flip()

        frames = 0
        # eegMarking(board, MARKERS['trial_start'])
        
        # IDEA
        # Generating an entire epoch of frames
        # The shape is (n, m, f) where 
        # n: number of sub-speller
        # m: is each character in the sub speller
        # f: is frame_idx
        start_time = trialClock.getTime()
        # Generate the order of flashing
        timeline = gen_timeline(n=NO_SUBSPELLER, r=NO_ROW, c=NO_COL, overlap=0, isShuffle=False, phase = 3)

        # marked:bool = False
        eegMarking(board,marker)
        for t_idx in range(timeline.shape[2]):
            get_keypress()
            for n_idx in range(timeline.shape[0]):
                frame = timeline[n_idx,:,t_idx]
                chars = SUBSPELLERS[str(n_idx+1)]
                for idx, char in enumerate(chars):
                    get_keypress()
                    if(frame[idx] == -1):
                        flickers[char].draw2(frame=frame[idx], amp_override=-1)
                    else:
                        flickers[char].draw2(frame=frame[idx])
                
            window.flip()
        stop_time = trialClock.getTime()
        print("Elapsed time ==>", stop_time - start_time, timeline.shape)
        print("Timeline Shape ==>", timeline.shape[2], range(timeline.shape[2]))


def gen_timeline(n:int, r:int, c:int, overlap:float, isShuffle:bool=False):
    import numpy as np
    timeline = []
    for _ in range(n):
        timeline.append(gen_timeline_FERC(r, c, overlap, isShuffle))
    timeline = np.vstack(timeline)
    return timeline

def gen_timeline_FERC(r:int, c:int, overlap:float, isShuffle:bool=False, phase = 2):
    # overlap:float
    #   0: No 2 stimuli flicker at the same time
    # 0.5: 2 stimuli overlap by half
    #   1: 2 stimuli flicker at the same time 
    import numpy as np

    # import random
    # characters = list(range(m))
    # if(isShuffle):
    #     random.shuffle(characters)
    m = r*c # row and column must flash by number of rows and columns
    d = epoch_frames//m
    t = int(d*(((m-1) * (1-overlap)) + 1))
    # print(f"{n=} {m=} {d=} {t=}")
    timeline = np.ones((m, t), dtype=int)*-1
    # print(f"{timeline.shape}")
    start = 0
    part_shuffle = []

    # Looping for the order in each rows and columns by col 1- col n and then row 1 - row n
    for i in range(m):
        part = (int(i * d * (1 - overlap)) + d)
        if(i==0):
            part_shuffle.append(list(range(start,part)))
        else:
            part_shuffle.append(list(range(start-phase,part)))
        start = part
    # If we randomise the orther, this following function will shuffle the order above
    if(isShuffle):
        np.random.shuffle(part_shuffle)
    
    # this loop is for generating timeline using order above
    for i in range(m):
        j=0
        if(i>m//r): #in case of column, we skip the order by number of column because we order the alphaet by row in this case.
            j+=c
        if(i < m//r): # ROW FLASHING
            timeline[i::2, part_shuffle[i]] = 1
        else: # COLUMN FLASHING
            timeline[j:j+2, part_shuffle[i]] = 1
        start = part

    timeline = np.expand_dims(timeline, axis=0)
    return timeline


def main():
    global sequence
    global trialClock

    random.seed(42)


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
        window.flip()
        core.wait(10)

        for block in range(NUM_BLOCK):
            # a.hear('A_')
            drawTextOnScreen('Starting block ' + str(block + 1) ,window)
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
                flicker(board_shim)
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
                    window.flip()

            block += 1
            block_break_start.autoDraw = False
            window.flip()
            # window.color = 'white'
            # window.flip()

        drawTextOnScreen('End of experiment, Thank you',window)
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
    window.close()
    core.quit()

if __name__ == "__main__":
    main()