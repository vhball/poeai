# -*- coding: utf-8 -*-
"""
Created on Fri Sep 23 00:25:15 2016

TODO: refactor into simpler functions

@author: Michael
"""


import asyncio
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import time

import matplotlib.pyplot as plt
import win32con, win32api

import poeai.asynctriggers as asynctriggers
from poeai.imaging.screencapture import \
    get_bboxes_to_capture, screen_capture
from poeai.imaging.textparsing import \
    parse_globe_text


def update_game_state(game_state):
    bbox_names, bboxes_to_capture = \
        get_bboxes_to_capture("life mana", assume_fullscreen_1080p=True)
#        get_bboxes_to_capture("all", assume_fullscreen_1080p=True)
    images = screen_capture(bboxes_to_capture)
    for image_name, image in zip(bbox_names, images):
        if image_name == "life" or image_name == "mana":
            stat_results = parse_globe_text(image, rows_to_parse=[1,2,3],
                                            tags_to_find=["reserved",
                                                          image_name])
            game_state[image_name + '_frac'] = \
                get_effective_stat_fraction(image_name, stat_results,
                                            maybe_reserved=True)
    return game_state            


def get_effective_stat_fraction(stat, results, maybe_reserved=False):
    """
    Returns the fraction current/max of either life, mana, or shield,
    optionally taking into account if stat has its maximum lowered via
    reservation (assumes only this stat is reserved)
    """
    val_cur = results.get(stat + "_current", -1)
    val_max = results.get(stat + "_max", 0)
    if val_cur is None or val_max is None or val_max == 0:
        return None
    if stat == "life" or stat == "mana":
        if maybe_reserved:
            val_max -= results.get("reserved", 0)
    elif stat != "shield":
        raise ValueError("get_effective_stat_fraction: invalid stat " +
                         "parameter: life, mana, or shield only")
    return val_cur/val_max


# %%
if __name__ == "__main__":
    # global variables shared between coroutines
    game_state = {'life_frac': None, 'mana_frac': None}
    
    # thresholds:
    life_pot_threshold = 0.8
    mana_pot_threshold = 0.3
    danger_pot_threshold = 0.7  # health-triggered by default
    alt_f4_threshold = 0.4

    # cooldowns:
    life_pot_cooldown = 0.1
    mana_pot_cooldown = 5.0
    danger_pot_cooldown = 4.0
    key_repeat_cooldown = 4.0
    alt_f4_cooldown = 0.2  # hopefully shouldn't need this
    key_repeat_toggle_cooldown = 1.0
    combat_mode_cooldown = 1.0
    regroup_mode_cooldown = 1.0

    life_pot_cooldown_timer = time.clock() - 10
    mana_pot_cooldown_timer = time.clock() - 10
    danger_pot_cooldown_timer = time.clock() - 10
    key_repeat_cooldown_timer = time.clock() - 10

    # pots to cycle:
    life_pot_key_list = ['S', 'A']
    mana_pot_key_list = ['G']
    danger_pot_key_list = []
    key_repeat_key_code_list = [ord('T')]

    # key-triggered functions
    exit_script_key_code = win32con.VK_DELETE
    key_repeat_toggle_key = '1'
    key_repeat_coroutine = asynctriggers.coro_key_repeat_mode
    key_repeat_coro_keywords = {'key_repeat_key_code_list': 
                                    key_repeat_key_code_list,
                                'key_repeat_cooldown': key_repeat_cooldown}
    combat_mode_key = '2'
    combat_mode_coroutine = asynctriggers.coro_combat_mode_summoner_A
    regroup_mode_key = '3'
    regroup_mode_coroutine = asynctriggers.coro_regroup_mode_summoner_A

    # condition functions that return True when key should be pressed
    def alt_f4_condition_fcn():
        life_frac = game_state['life_frac']
        if life_frac is None or life_frac == 0:
            return False
        elif life_frac < alt_f4_threshold:
            return True
        return False

    def life_pot_condition_fcn():
        life_frac = game_state['life_frac']
        if life_frac is None or life_frac == 0:
            return False
        elif life_frac < alt_f4_threshold:
            return False  # no pots, just alt-f4!
        elif life_frac < life_pot_threshold:
            return True
        return False

    def danger_pot_condition_fcn():
        life_frac = game_state['life_frac']
        if life_frac is None or life_frac == 0:
            return False
        elif life_frac < alt_f4_threshold:
            return False  # no pots, just alt-f4!
        elif life_frac < danger_pot_threshold:
            return True
        return False

    def mana_pot_condition_fcn():
        life_frac = game_state['life_frac']
        mana_frac = game_state['mana_frac']
        if life_frac is None or mana_frac is None or life_frac == 0:
            return False
        elif life_frac < alt_f4_threshold:
            return False  # no pots, just alt-f4!
        elif mana_frac < mana_pot_threshold:
            return True
        return False

    win32api.GetAsyncKeyState(ord(key_repeat_toggle_key))  # clear recent presses
    def key_repeat_condition_fcn():
        if win32api.GetAsyncKeyState(ord(key_repeat_toggle_key)):
            return True
        else:
            return False

    win32api.GetAsyncKeyState(ord(combat_mode_key))  # clear recent presses
    def combat_mode_condition_fcn():
        if win32api.GetAsyncKeyState(ord(combat_mode_key)):
            return True
        else:
            return False

    win32api.GetAsyncKeyState(ord(regroup_mode_key))  # clear recent presses
    def regroup_mode_condition_fcn():
        if win32api.GetAsyncKeyState(ord(regroup_mode_key)):
            return True
        else:
            return False

    win32api.GetAsyncKeyState(win32con.VK_LBUTTON)  # clear recent presses
    win32api.GetAsyncKeyState(win32con.VK_RBUTTON)  # clear recent presses
    def mode_cancel_condition_fcn():
        if win32api.GetAsyncKeyState(win32con.VK_LBUTTON) or \
                    win32api.GetAsyncKeyState(win32con.VK_LBUTTON):
            return True
        else:
            return False

    alt_f4_trigger_coroutine = asynctriggers.async_mod_key_trigger(
                                        win32con.VK_MENU,
                                        [win32con.VK_F4],
                                        alt_f4_condition_fcn,
                                        alt_f4_cooldown)

    life_pot_trigger_coroutine = asynctriggers.async_key_trigger(
                                        life_pot_key_list,
                                        life_pot_condition_fcn,
                                        life_pot_cooldown)

    danger_pot_trigger_coroutine = asynctriggers.async_key_trigger(
                                        danger_pot_key_list,
                                        danger_pot_condition_fcn,
                                        danger_pot_cooldown)

    mana_pot_trigger_coroutine = asynctriggers.async_key_trigger(
                                        mana_pot_key_list,
                                        mana_pot_condition_fcn,
                                        mana_pot_cooldown)

    key_repeat_trigger_coroutine = asynctriggers.async_toggled_mode_trigger(
                                        key_repeat_coroutine,
                                        key_repeat_condition_fcn,
                                        lambda: False,  # no cancel key
                                        key_repeat_toggle_cooldown,
                                        **key_repeat_coro_keywords)

    combat_mode_trigger_coroutine = asynctriggers.async_toggled_mode_trigger(
                                        combat_mode_coroutine,
                                        combat_mode_condition_fcn,
                                        mode_cancel_condition_fcn,
                                        combat_mode_cooldown)

    regroup_mode_trigger_coroutine = asynctriggers.async_toggled_mode_trigger(
                                        regroup_mode_coroutine,
                                        regroup_mode_condition_fcn,
                                        mode_cancel_condition_fcn,
                                        regroup_mode_cooldown)

    loop = asyncio.get_event_loop()
    asyncio.ensure_future(alt_f4_trigger_coroutine, loop=loop)
    asyncio.ensure_future(life_pot_trigger_coroutine, loop=loop)
    asyncio.ensure_future(danger_pot_trigger_coroutine, loop=loop)
    asyncio.ensure_future(mana_pot_trigger_coroutine, loop=loop)
#    asyncio.ensure_future(key_repeat_trigger_coroutine, loop=loop)
    asyncio.ensure_future(combat_mode_trigger_coroutine, loop=loop)
    asyncio.ensure_future(regroup_mode_trigger_coroutine, loop=loop)


    print("currently assuming:")
    print("-using 1920x1080 borderless fullscreen " +
          "(until custom scaling issues fixed)")
    print("-life not reserved")
    print("press delete to exit")
    time_log = []
    screencap_log = []
    start_time = time.clock()
    win32api.GetAsyncKeyState(exit_script_key_code)  # clear recent presses
    with ProcessPoolExecutor(max_workers=2) as executor:
        try:
            while True:
                # Capture screen and parse results
                future = executor.submit(update_game_state, game_state)
                while not future.done():
                    # Check for exit command:
                    if win32api.GetAsyncKeyState(exit_script_key_code):
                        raise KeyboardInterrupt        
                    loop.run_until_complete(asyncio.sleep(0.02))

#                    time_log.append(time.clock() - start_time)
#                    screencap_log.append(0)
#                    if len(time_log) > 50:  # set max log length, delete old
#                        time_log = time_log[1:]
#                        screencap_log = screencap_lvog[1:]
#                screencap_log[-1] = 1
#                time_log.append(time.clock() - start_time)

                game_state = future.result()  # update game state
        except KeyboardInterrupt:
            print('program terminated by user')
        finally:
            loop.run_until_complete(asyncio.sleep(1.0))
            loop.close()

#    try:
#        while True:
#            # Check for exit command:
#            if win32api.GetAsyncKeyState(exit_script_key_code):
#                raise KeyboardInterrupt        
#
#            # Capture screen and parse results
#            game_state = update_game_state(game_state)  # no = required?
#
#            # Run potion scripts briefly
#            loop.run_until_complete(asyncio.sleep(0.04))
#
#    except KeyboardInterrupt:
#        print('program terminated by user')
#    finally:
#        loop.run_until_complete(asyncio.sleep(1.0))
#        loop.close()



#    time_log_diffs = [t2-t1 for t1, t2 in zip(time_log[:-1], time_log[1:])]
#    plt.plot(time_log_diffs, 'b:')
#    plt.plot(screencap_log, 'rd')

