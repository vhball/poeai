# -*- coding: utf-8 -*-
"""
Created on Sun Sep 11 21:21:02 2016

@author: Michael
"""

import time
import random

import numpy as np
import matplotlib.pyplot as plt
import win32gui, win32ui, win32con, win32api

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
    if stat == "life" or stat == "mana":
        if maybe_reserved:
            val_max -= results.get("reserved", 0)
    elif stat != "shield":
        raise ValueError("get_effective_stat_fraction: invalid stat " +
                         "parameter: life, mana, or shield only")
    try:
        return val_cur/val_max
    except ZeroDivisionError:
        return None


# %%
if __name__ == "__main__":
#    bboxes_to_capture = get_bboxes_to_capture("all")
    bboxes_to_capture = get_bboxes_to_capture("health and mana")

    finished = False
    # or win32api.GetAsyncKeyState(ord('Y')) for alphanumerics
    print("currently assuming:")
    print("-life not reserved")
    print("-mana possibly reserved")
    print("-no eldritch battery")
    print("press caps lock to exit")
    time_log = []
    stats_log = []
    start_time = time.clock()
    last_time_elapsed = -100
    while not finished:
        # Check for key input
        finished = win32api.GetAsyncKeyState(win32con.VK_CAPITAL)

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

        if life_frac is not None and life_frac > 0 and life_frac < 0.4:
            time.sleep(random.random()/5+.10)
            win32api.keybd_event(win32con.VK_MENU,0,0,0)
            time.sleep(random.random()/5+.10)
            win32api.keybd_event(win32con.VK_F4,0,0,0)
            time.sleep(random.random()/10+.3)
            win32api.keybd_event(win32con.VK_F4,0,win32con.KEYEVENTF_KEYUP,0)
            time.sleep(random.random()/5+.10)
            win32api.keybd_event(win32con.VK_MENU,0,win32con.KEYEVENTF_KEYUP,0)
            time.sleep(random.random()/5+.10)
            win32api.keybd_event(win32con.VK_MENU,0,0,0)
            time.sleep(random.random()/5+.10)
            win32api.keybd_event(win32con.VK_F4,0,0,0)
            time.sleep(random.random()/10+.3)
            win32api.keybd_event(win32con.VK_F4,0,win32con.KEYEVENTF_KEYUP,0)
            time.sleep(random.random()/5+.10)
            win32api.keybd_event(win32con.VK_MENU,0,win32con.KEYEVENTF_KEYUP,0)
            
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
