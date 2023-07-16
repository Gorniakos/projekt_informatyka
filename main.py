#!/usr/bin/env python
# -*- coding: latin-1 -*-
import csv
import yaml
import random
import atexit
import codecs

from typing import List, Dict, Tuple
from os.path import join
from psychopy import visual, event, logging, gui, core


@atexit.register
def save_beh_results() -> None:
    file_name = PART_ID + '_beh.csv'
    with open(join('results', file_name), 'w', encoding='utf-8') as beh_file:
        beh_writer = csv.writer(beh_file)
        beh_writer.writerows(RESULTS)
    logging.flush()


def read_text_from_file(file_name: str, insert: str = '') -> str:
    if not isinstance(file_name, str):
        logging.error('Problem with file reading, filename must be a string')
        raise TypeError('file_name must be a string')
    msg = list()
    with codecs.open(file_name, encoding='utf-8', mode='r') as data_file:
        for line in data_file:
            if not line.startswith('#'):  # if not commented line
                if line.startswith('<--insert-->'):
                    if insert:
                        msg.append(insert)
                else:
                    msg.append(line)
    return ''.join(msg)


def check_exit(key: str = 'f7') -> None:
    stop = event.getKeys(keyList=[key])
    if stop:
        abort_with_error('Experiment finished by user! {} pressed.'.format(key))


def show_info(win: visual.Window, file_name: str, insert: str = '') -> None:
    msg = read_text_from_file(file_name, insert=insert)
    msg = visual.TextStim(win, color='white', text=msg, height=20, wrapWidth=900)
    msg.draw()
    win.flip()
    key = event.waitKeys(keyList=['f7', 'return', 'space', 'left', 'right'])
    if key == ['f7']:
        abort_with_error('Experiment finished by user on info screen! F7 pressed.')
    win.flip()

def show_info_dynamic(win: visual.Window, instruction: str, key_color_mapping: Dict[str, str]) -> None:
    modified_instruction = instruction
    for key, color in key_color_mapping.items():
        modified_instruction = modified_instruction.replace(key, f"{key}({color})")
    text_stim = visual.TextStim(win, text=modified_instruction, color='white')
    text_stim.draw()
    win.flip()
    key = event.waitKeys(keyList=['f7', 'return', 'space', 'left', 'right'])
    if key == ['f7']:
        abort_with_error('Experiment finished by user on info screen! F7 pressed.')
    win.flip()

def abort_with_error(err: str) -> None:
    logging.critical(err)
    raise Exception(err)

# GLOBALS

RESULTS = list()  # list in which data will be colected
RESULTS.append(['PART_ID', 'Block number', 'Trial number', 'Button pressed', 'Reaction time', 'Correctness', 'Trial type', 'Stim color', 'Stim word', 'Training'])  # ... Results header
clock = core.Clock()

def main():
    global PART_ID  # PART_ID is used in case of error on @atexit, that's why it must be global

    # === Dialog popup ===
    info: Dict = {'ID': '', 'Sex': ['M', "F"], 'Age': ''}
    dict_dlg = gui.DlgFromDict(dictionary=info, title='Experiment title, fill by your name!')
    if not dict_dlg.OK:
        abort_with_error('Info dialog terminated.')

    # load config, all params should be there
    conf: Dict = yaml.load(open('config.yaml', encoding='utf-8'), Loader=yaml.SafeLoader)
    frame_rate: int = conf['FRAME_RATE']
    screen_res: List[int] = conf['SCREEN_RES']
    # === Scene init ===
    win = visual.Window(screen_res, fullscr=True, monitor='testMonitor', units='pix', color=conf['BACKGROUND_COLOR'])
    event.Mouse(visible=False, newPos=None, win=win)  # Make mouse invisible

    PART_ID = info['ID'] + info['Sex'] + info['Age']
    logging.LogFile(join('results', f'{PART_ID}.log'), level=logging.INFO)  # errors logging
    logging.info('FRAME RATE: {}'.format(frame_rate))
    logging.info('SCREEN RES: {}'.format(screen_res))

    colors = ['yellow', 'green', 'blue', 'red']
    keys = ['z', 'x', 'n', 'm']
    random.shuffle(keys)
    pairs = list(zip(colors, keys))
    print(pairs)

    help = 'Zolty: ' + pairs[0][1] + ',  Zielony: ' + pairs[1][1] + ', Niebieski: ' + pairs[2][1] + ', Czerwony: ' + pairs[3][1]

    # === Training ===
    show_info(win, join('.', 'messages', 'Instruction_1.txt'))
    dynamic_instruction = None
    with open('messages/Instruction_2.txt', 'r') as file:
        dynamic_instruction = file.read()
        key_color_mapping = {
            "Zolty: ": pairs[0][1],
            "Zielony: ": pairs[1][1],
            "Niebieski: ": pairs[2][1],
            "Czerwony: ": pairs[3][1]
        }
        if dynamic_instruction:
            show_info_dynamic(win, dynamic_instruction, key_color_mapping)
    if conf['TRAINING'] == 1:
        show_info(win, join('.', 'messages', 'Instruction_3.txt'))

    trial_no = 0

    # === Experiment ===

    trainlist = []
    trainlist.extend(['congruent'] * conf['TRAIN_CONGRUENT_IN_BLOCK'])
    trainlist.extend(['incongruent'] * conf['TRAIN_INCONGRUENT_IN_BLOCK'])
    trainlist.extend(['control'] * conf['TRAIN_CONTROL_IN_BLOCK'])
    random.shuffle(trainlist)

    stimlist = []
    stimlist.extend(['congruent'] * conf['EXP_CONGRUENT_IN_BLOCK'])
    stimlist.extend(['incongruent'] * conf['EXP_INCONGRUENT_IN_BLOCK'])
    stimlist.extend(['control'] * conf['EXP_CONTROL_IN_BLOCK'])


    for block_no in range ((conf['EXP_NO_BLOCKS']) + conf['TRAINING']):
        trainorexp = stimlist
        if conf['TRAINING'] == 1:
            trainorexp = trainlist if block_no == 0 else stimlist

        random.shuffle(stimlist)

        previous_stim_color = None
        previous_stim_word = None

        for stim_type in trainorexp:
            stim_word = None
            stim_color = None
            corr_key = None
            training = 1 if conf['TRAINING'] == 1 and block_no == 0 else 0
            if stim_type == 'congruent':
                stim_word = random.choice(conf['STIM_WORD'])
            elif stim_type == 'incongruent':
                stim_word = random.choice(conf['STIM_WORD'])
            elif stim_type == 'control':
                stim_word = random.choice(conf['CONTROL_WORD'])

            congruent_color = None
            incongruent_color = None

            if stim_word == 'zolty':
                congruent_color = 'yellow'
                incongruent_color = ['red', 'blue', 'green']
            elif stim_word == 'czerwony':
                congruent_color = 'red'
                incongruent_color = ['yellow', 'blue', 'green']
            elif stim_word == 'niebieski':
                congruent_color = 'blue'
                incongruent_color = ['red', 'yellow', 'green']
            elif stim_word == 'zielony':
                congruent_color = 'green'
                incongruent_color = ['red', 'blue', 'yellow']

            if stim_type == "control":
                stim_color = random.choice(conf['STIM_COLOR'])
            if stim_type == 'congruent':
                stim_color = congruent_color
            if stim_type == 'incongruent':
                stim_color = random.choice(incongruent_color)

            if stim_color == 'yellow':
                corr_key = pairs[0][1]
            elif stim_color == 'green':
                corr_key = pairs[1][1]
            elif stim_color == 'blue':
                corr_key = pairs[2][1]
            elif stim_color == 'red':
                corr_key = pairs[3][1]

            if previous_stim_color == stim_color and previous_stim_word == stim_word:
                if stim_type == 'congruent':
                    stim_word = random.choice(conf['STIM_WORD'])
                    stim_color = congruent_color
                elif stim_type == 'incongruent':
                    stim_color = random.choice(incongruent_color)
                elif stim_type == 'control':
                    stim_word = random.choice(conf['CONTROL_WORD'])

            key_pressed, rt, corr, stim_type, stim_word, stim_color, training = run_trial(win, conf, clock, stim_type, stim_word, stim_color, corr_key, help, training) #(, kolor, s?owo)
            trial_no += 1
            previous_stim_color = stim_color
            previous_stim_word = stim_word
            RESULTS.append([PART_ID, block_no, trial_no, key_pressed, rt, corr, stim_type, stim_word, stim_color, training]) # (..., congruent, kolor, s?owo)
            win.flip()
            core.wait(random.choice(conf['WAIT_TIME']))
        block_no +=1
        if block_no != (conf['EXP_NO_BLOCKS'] + conf['TRAINING']):
            if conf['TRAINING'] == 1 and block_no == 1:
                show_info(win, join('.', 'messages', 'after_training.txt'))
                with open('messages/Instruction_2.txt', 'r') as file:
                    dynamic_instruction = file.read()
                    key_color_mapping = {
                        "Zolty: ": pairs[0][1],
                        "Zielony: ": pairs[1][1],
                        "Niebieski: ": pairs[2][1],
                        "Czerwony: ": pairs[3][1]
                    }
                    if dynamic_instruction:
                        show_info_dynamic(win, dynamic_instruction, key_color_mapping)
            else:
                show_info(win, join('.', 'messages', 'Break.txt'))
                with open('messages/Instruction_2.txt', 'r') as file:
                    dynamic_instruction = file.read()
                    key_color_mapping = {
                        "Zolty: ": pairs[0][1],
                        "Zielony: ": pairs[1][1],
                        "Niebieski: ": pairs[2][1],
                        "Czerwony: ": pairs[3][1]
                    }
                    if dynamic_instruction:
                        show_info_dynamic(win, dynamic_instruction, key_color_mapping)


    # === Cleaning time ===
    save_beh_results()
    logging.flush()
    show_info(win, join('.', 'messages', 'end.txt'))
    win.close()


def run_trial(win, conf, clock, stim_type, stim_word, stim_color, corr_key, help, training):
    # === Start pre-trial  stuff (Fixation cross etc.)===
    stim = visual.TextStim(win, text=stim_word, height=conf['STIM_SIZE'], color=stim_color)
    fix = visual.TextStim(win, text='+', height=50, color=conf['FIX_CROSS_COLOR'])
    help_display = visual.TextStim(win, text=help, pos=(0, -40), height=1, color='black')

    for _ in range(conf['FIX_CROSS_TIME']):
        fix.draw()
        win.flip()
        core.wait(1)
    event.clearEvents()
    win.callOnFlip(clock.reset)

    for _ in range(conf['STIM_TIME']):  # present stimuli
        reaction = event.getKeys(keyList=list(conf['REACTION_KEYS']))
        rt = clock.getTime()
        if reaction:  # break if any button was pressed
            break
        stim.draw()
        help_display.draw()
        win.flip()

    # === Trial ended, prepare data for send  ===
    if reaction:
        key_pressed = reaction[0]
        rt = rt
        corr = 1 if key_pressed == corr_key else 0
    else:  # timeout
        key_pressed = 'no_key'
        rt = -1.0
        corr = 2

    if training == 1:
        for _ in range (conf['FIX_CROSS_TIME']):
            feedb = "Poprawnie" if corr == 1 else "Niepoprawnie"
            feedb = "Brak odpowiedzi" if corr == 2 else feedb
            feedb = visual.TextStim(win, text=feedb, height=50, color=conf['FIX_CROSS_COLOR'])
            feedb.draw()
            win.flip()
            core.wait(1)
            win.flip()

    return key_pressed, rt, corr, stim_type, stim_color, stim_word, training  # return all data collected during trial

if __name__ == '__main__':
    PART_ID = ''
    main()