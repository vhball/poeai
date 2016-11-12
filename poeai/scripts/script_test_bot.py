# -*- coding: utf-8 -*-
"""
Created on Fri Sep 23 00:25:15 2016

TODO: refactor into simpler functions

@author: Michael
"""


import time
from itertools import cycle
from random import random

import numpy as np
import matplotlib.pyplot as plt
import win32gui, win32ui, win32con, win32api

import poeai.commands as cmds
from poeai.imaging.screencapture import \
    get_bboxes_to_capture, screen_capture
from poeai.imaging.textparsing import \
    parse_globe_text


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
#    bboxes_to_capture = get_bboxes_to_capture("all")
    bboxes_to_capture = get_bboxes_to_capture("health and mana")

    # thresholds:
    life_pot_theshold = 0.9
    mana_pot_theshold = 0.3
    danger_pot_theshold = 0.3  # unused
    vaal_skill_theshold = 0.1  # shield-based
    alt_f4_threshold = 0.5

    # cooldowns:
    life_pot_cooldown = 0.3
    mana_pot_cooldown = 5.0
    danger_pot_cooldown = 10.0
    vaal_skill_cooldown = 10.0

    life_pot_cooldown_timer = time.clock() - 10
    mana_pot_cooldown_timer = time.clock() - 10
    danger_pot_cooldown_timer = time.clock() - 10
    vaal_skill_cooldown_timer = time.clock() - 10

    # pots to cycle:
    life_pot_key_list = [ord('F')]
    mana_pot_key_list = [ord('D'), ord('S'), ord('A')]
    danger_pot_key_list = [ord('G')]
    vaal_skill_key_list = [ord('T')]

    life_pot_cycle = cycle(life_pot_key_list)
    mana_pot_cycle = cycle(mana_pot_key_list)
    danger_pot_cycle = cycle(danger_pot_key_list)
    vaal_skill_cycle = cycle(vaal_skill_key_list)

    # test action timer:
    test_move_timer = time.clock() - 10
    test_move_time_delay = 0
    is_acting = False
    acting_state = 0

    finished = False
    print("currently assuming:")
    print("-life not reserved")
    print("-mana possibly reserved")
    print("-no eldritch battery")
    print("-vaal skill on 'T'")
    print("press caps lock to exit")
    time_log = []
    stats_log = []
    start_time = time.clock()
    last_time_elapsed = -100
    win32api.GetAsyncKeyState(ord('J'))  # clear recent presses
    win32api.GetAsyncKeyState(ord('K'))  # clear recent presses
    while not finished:
        # Check for key input
        finished = win32api.GetAsyncKeyState(ord('J'))
#        finished = win32api.GetAsyncKeyState(win32con.VK_CAPITAL)
        # or win32api.GetAsyncKeyState(ord('Y')) for alphanumerics

        # Capture screen and parse results
        images = screen_capture(bboxes_to_capture)
        life_results = parse_globe_text(images[0], rows_to_parse=[2,3],
                                        tags_to_find=["life", "shield"])
        mana_results = parse_globe_text(images[1], rows_to_parse=[2,3],
                                        tags_to_find=["reserved", "mana"])
        results = {**life_results, **mana_results}
        life_frac = get_effective_stat_fraction("life", results,
                                                maybe_reserved=False)
        mana_frac = get_effective_stat_fraction("mana", results,
                                                maybe_reserved=True)
        shield_frac = get_effective_stat_fraction("shield", results,
                                                  maybe_reserved=False)

        if life_frac is None or life_frac == 0:
            pass
        elif life_frac < alt_f4_threshold:
            time.sleep(random()/5+.10)
            win32api.keybd_event(win32con.VK_MENU,0,0,0)
            time.sleep(random()/5+.10)
            win32api.keybd_event(win32con.VK_F4,0,0,0)
            time.sleep(random()/4+.20)
            win32api.keybd_event(win32con.VK_F4,0,win32con.KEYEVENTF_KEYUP,0)
            time.sleep(random()/4+.30)
            win32api.keybd_event(win32con.VK_F4,0,0,0)
            time.sleep(random()/4+.20)
            win32api.keybd_event(win32con.VK_F4,0,win32con.KEYEVENTF_KEYUP,0)
            time.sleep(random()/3+.10)
            win32api.keybd_event(win32con.VK_MENU,0,win32con.KEYEVENTF_KEYUP,0)
        elif life_frac < life_pot_theshold:
            time_elapsed = time.clock() - life_pot_cooldown_timer
            if time_elapsed > life_pot_cooldown:
                pot_key = next(life_pot_cycle)
                time.sleep(random()/4+.20)
                win32api.keybd_event(pot_key,0,0,0)
                time.sleep(random()/5+.20)
                win32api.keybd_event(pot_key,0,win32con.KEYEVENTF_KEYUP,0)
                life_pot_cooldown_timer = time.clock()

        if shield_frac is None or shield_frac == 0:
            pass
        elif shield_frac < vaal_skill_theshold:
            time_elapsed = time.clock() - vaal_skill_cooldown_timer
            if time_elapsed > vaal_skill_cooldown:
                pot_key = next(vaal_skill_cycle)
                time.sleep(random()/4+.20)
                win32api.keybd_event(pot_key,0,0,0)
                time.sleep(random()/6+.15)
                win32api.keybd_event(pot_key,0,win32con.KEYEVENTF_KEYUP,0)
                vaal_skill_cooldown_timer = time.clock()
                time.sleep(random()/5+.15)
                win32api.keybd_event(pot_key,0,0,0)
                time.sleep(random()/6+.15)
                win32api.keybd_event(pot_key,0,win32con.KEYEVENTF_KEYUP,0)
                vaal_skill_cooldown_timer = time.clock()

        if mana_frac is None or mana_frac == 0:
            pass
        elif mana_frac < mana_pot_theshold:
            time_elapsed = time.clock() - mana_pot_cooldown_timer
            if time_elapsed > mana_pot_cooldown:
                pot_key = next(mana_pot_cycle)
                time.sleep(random()/4+.20)
                win32api.keybd_event(pot_key,0,0,0)
                time.sleep(random()/5+.20)
                win32api.keybd_event(pot_key,0,win32con.KEYEVENTF_KEYUP,0)
                mana_pot_cooldown_timer = time.clock()

        # NOW TIME FOR NON-POTION STUFF:
        coords = cmds.get_coords()
        angle = cmds.get_angle_from_center(coords)
        if is_acting or win32api.GetAsyncKeyState(ord('K')):
            if acting_state == 0:
                cmds.char_start_move(angle)
                test_move_timer = time.clock()
                test_move_time_delay = random()/5 + .50
                acting_state = 1
                is_acting = True
            elif acting_state == 1:
                time_elapsed = time.clock() - test_move_timer
                if time_elapsed > test_move_time_delay:
                    cmds.char_stop_move(angle)
                    acting_state = 0
                    is_acting = False
            else:  # error, shouldn't get here, cancel everything
                is_acting = False
                acting_state = 0

#==============================================================================
#         # log stats every half second
#         time_elapsed = time.clock() - start_time
#         if time_elapsed - last_time_elapsed >= 0.5:
#             time_log.append(time_elapsed)
#             if life_frac is None or life_frac < 0:
#                 life_frac = 0
#             if mana_frac is None or mana_frac < 0:
#                 mana_frac = 0
#             if shield_frac is None or shield_frac < 0:
#                 shield_frac = 0                
#             stats_log.append((life_frac, mana_frac, shield_frac))
#             last_time_elapsed = time_elapsed
#==============================================================================

#==============================================================================
#     life_log, mana_log, shield_log = zip(*stats_log)
#     plt.plot(time_log, life_log, 'r:.', label="Life")
#     plt.plot(time_log, mana_log, 'b:.', label="Mana")
#     plt.plot(time_log, shield_log, 'g:.', label="Shield")
#     plt.legend()
# #    print("life: {:.2f}%".format(100*life_frac))
# #    print("mana: {:.2f}%".format(100*mana_frac))
# #    print("shield: {:.2f}%".format(100*shield_frac))
#==============================================================================
