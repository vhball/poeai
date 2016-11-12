# -*- coding: utf-8 -*-
"""
Created on Sun Oct 16 22:47:12 2016

@author: Michael
"""

import asyncio  # too overcomplicated and probably not a good match either
#from concurrent.futures import ThreadPoolExecutor  # probably better, except 
from itertools import cycle
from random import random
import time

import win32gui, win32ui, win32con, win32api


def get_key_code_cycle(key_list):
    if len(key_list) == 0:
        return None
    cycled_key_code_list = []
    for key in key_list:
        if isinstance(key, int):
            cycled_key_code_list.append(key)
        else:
            try:  # assume single character string
                cycled_key_code_list.append(ord(key.capitalize()))
            except (AttributeError, TypeError):
                print("warning: async_key_trigger: parameter " +
                      "cycled_key_list must be a list of one or more " +
                      "strings each containing a single alphanumeric " +
                      "character. no routine scheduled. parameter " +
                      "given: {}".format(key_list))
                return None
    key_code_cycle = cycle(cycled_key_code_list)
    return key_code_cycle


@asyncio.coroutine
def async_key_trigger(cycled_key_list, trigger_condition_fcn, cooldown):
    key_cycle = get_key_code_cycle(cycled_key_list)
    if key_cycle is None:
        return None  # No keys in list; let this coroutine die
    cooldown_timer = time.clock() - 10
    while True:
        if (time.clock() - cooldown_timer) > cooldown:
            if trigger_condition_fcn():
                cycled_key = next(key_cycle)
                yield from asyncio.sleep(random()/5+.10)
                win32api.keybd_event(cycled_key,0,0,0)
                yield from asyncio.sleep(random()/8+.075)
                win32api.keybd_event(cycled_key,0,win32con.KEYEVENTF_KEYUP,0)
                cooldown_timer = time.clock()
        yield from asyncio.sleep(0.05)


@asyncio.coroutine
def async_mod_key_trigger(mod_key, cycled_key_list,
                          trigger_condition_fcn, cooldown):
    key_cycle = get_key_code_cycle(cycled_key_list)
    if key_cycle is None:
        return None  # No keys in list; let this coroutine die
    cooldown_timer = time.clock() - 10
    while True:
        if (time.clock() - cooldown_timer) > cooldown:
            if trigger_condition_fcn():
                cycled_key = next(key_cycle)
                yield from asyncio.sleep(random()/8+.08)
                win32api.keybd_event(mod_key,0,0,0)
                yield from asyncio.sleep(random()/10+.05)
                win32api.keybd_event(cycled_key,0,0,0)
                yield from asyncio.sleep(random()/8+.075)
                win32api.keybd_event(cycled_key,0,win32con.KEYEVENTF_KEYUP,0)
                yield from asyncio.sleep(random()/10+.1)
                win32api.keybd_event(mod_key,0,win32con.KEYEVENTF_KEYUP,0)
                cooldown_timer = time.clock()
        yield from asyncio.sleep(0.05)
    

# %%
@asyncio.coroutine
def async_toggled_mode_trigger(toggled_mode_coro, trigger_condition_fcn,
                               cancel_condition_fcn, cooldown,
                               **coro_keywords):
    cooldown_timer = time.clock() - 10
    is_toggled_mode_active = False
    toggled_mode_state = {}
    while True:
        if (time.clock() - cooldown_timer) > cooldown:
            if cancel_condition_fcn():
                is_toggled_mode_active = False
                cooldown_timer = time.clock()  # send "just toggled off" flag
                yield from toggled_mode_coro(False, toggled_mode_state,
                                             **coro_keywords)
            elif trigger_condition_fcn():
                is_toggled_mode_active = not is_toggled_mode_active
                cooldown_timer = time.clock()
                if not is_toggled_mode_active:  # send "just toggled off" flag
                    yield from toggled_mode_coro(False, toggled_mode_state,
                                                 **coro_keywords)
        if is_toggled_mode_active:  # send "yes, toggled on" flag
            yield from toggled_mode_coro(True, toggled_mode_state,
                                         **coro_keywords)
        yield from asyncio.sleep(0.05)


# %%
@asyncio.coroutine
def coro_key_repeat_mode(is_key_repeat_active, key_repeat_state,
                         **coro_keywords):
    # First time usage
    default_key_repeat_state = {'key_repeat_timer': time.clock() - 10}
    if len(key_repeat_state) == 0:
        # parse keywords, check for requirements
        if "key_repeat_key_code_list" in coro_keywords.keys():
            if "key_repeat_cooldown" in coro_keywords.keys():
                key_repeat_state['key_repeat_cycle'] = \
                    cycle(coro_keywords["key_repeat_key_code_list"])
                key_repeat_state['key_repeat_cooldown'] = \
                    coro_keywords["key_repeat_cooldown"]
                key_repeat_state['ready_to_run'] = True
            else:
                key_repeat_state['ready_to_run'] = False
                print("coro_key_repeat_mode: missing " +
                      "keyword 'key_repeat_cooldown'")
        else:
            key_repeat_state['ready_to_run'] = False
            print("coro_key_repeat_mode: missing " +
                  "keyword 'key_repeat_key_code_list'")
        key_repeat_state.update(default_key_repeat_state)

    if not key_repeat_state.get('ready_to_run', False):  # default False
        return

    # Run combat mode as appropriate
    if is_key_repeat_active:
        # REPEATED KEYPRESS(ES) GO HERE
        time_elapsed = time.clock() - key_repeat_state['key_repeat_timer']
        if time_elapsed > key_repeat_state['key_repeat_cooldown']:
            # press key or mouse click
            key_code_to_press = next(key_repeat_state['key_repeat_cycle'])
            yield from asyncio.sleep(random()/5+ .25)  # random delay
            if key_code_to_press == "middle click":
                # right click
                win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEDOWN,0,0)
                yield from asyncio.sleep(random()/8+ .20)
                win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEUP,0,0)            
            elif key_code_to_press == "right click":
                # right click
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN,0,0)
                yield from asyncio.sleep(random()/8+ .20)
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP,0,0)            
            else:
                win32api.keybd_event(key_code_to_press,0,0,0)
                yield from asyncio.sleep(random()/8+ .075)
                win32api.keybd_event(key_code_to_press,0,
                                     win32con.KEYEVENTF_KEYUP,0)           
            key_repeat_state['key_repeat_timer'] = time.clock()

    else:
        # SHUTDOWN CODE GOES HERE, IF ANY
        key_repeat_state.update(default_key_repeat_state)


# %%
#@asyncio.coroutine
#def async_combat_mode_trigger(combat_mode_coro, trigger_condition_fcn,
#                              cancel_condition_fcn, cooldown):
#   cooldown_timer = time.clock() - 10
#    is_regroup_mode_active = False
#    regroup_mode_state = {}
#    while True:
#        if (time.clock() - cooldown_timer) > cooldown:
#            if cancel_condition_fcn():
#                is_regroup_mode_active = False
#                cooldown_timer = time.clock()  # send "no regroup" flag
#                yield from regroup_mode_coro(False, regroup_mode_state)
#            elif trigger_condition_fcn():
#                is_regroup_mode_active = not is_regroup_mode_active
#                cooldown_timer = time.clock()
#                if not is_regroup_mode_active:  # send "no regroup" flag
#                    yield from regroup_mode_coro(False, regroup_mode_state)
#        if is_regroup_mode_active:  # send "yes regroup" flag
#            is_regroup_mode_active = \
#                yield from regroup_mode_coro(True, regroup_mode_state)
#        yield from asyncio.sleep(0.05)


#@asyncio.coroutine
#def async_regroup_mode_trigger(regroup_mode_coro, trigger_condition_fcn,
#                               cancel_condition_fcn, cooldown):
#    cooldown_timer = time.clock() - 10
#    is_regroup_mode_active = False
#    regroup_mode_state = {}
#    while True:
#        if (time.clock() - cooldown_timer) > cooldown:
#            if cancel_condition_fcn():
#                is_regroup_mode_active = False
#                cooldown_timer = time.clock()  # send "no regroup" flag
#                yield from regroup_mode_coro(False, regroup_mode_state)
#            elif trigger_condition_fcn():
#                is_regroup_mode_active = not is_regroup_mode_active
#                cooldown_timer = time.clock()
#                if not is_regroup_mode_active:  # send "no regroup" flag
#                    yield from regroup_mode_coro(False, regroup_mode_state)
#        if is_regroup_mode_active:  # send "yes regroup" flag
#            is_regroup_mode_active = \
#                yield from regroup_mode_coro(True, regroup_mode_state)
#        yield from asyncio.sleep(0.05)

@asyncio.coroutine
def coro_combat_mode_summoner_A(is_combat_mode_active, combat_mode_state,
                                **coro_keywords):
    """
    combat mode coroutine for summoner with:
    -key 'R': self-cast summon raging spirit
    -key 'E': convocation
    -key 'W': skeletotem
    -key 'Q': ???? (animate weapon?)
    -key 'T': raise zombie
    -middle mouse: desecrate
    -right click: flesh offering
    """
    # Constants
    channeling_cooldown = 4.0

    # First time usage
    default_combat_mode_state = {'setup_stage': 0,
                                 'channeling SRS?': False,
                                 'channeling_timer': time.clock() - 10,
                                 'channeling_break_stage': 0}
    if len(combat_mode_state) == 0:
        combat_mode_state.update(default_combat_mode_state)

    # Run combat mode as appropriate
    if is_combat_mode_active:
        # COMBAT AI GOES HERE
        if not combat_mode_state['channeling SRS?']:
            # Skeletotem
            if combat_mode_state['setup_stage'] == 0:
                win32api.keybd_event(ord('W'),0,0,0)
                yield from asyncio.sleep(random()/8+ .075)
                win32api.keybd_event(ord('W'),0,win32con.KEYEVENTF_KEYUP,0)           
                yield from asyncio.sleep(random()/5+ 0.35)
                combat_mode_state['setup_stage'] = 3
#                yield from asyncio.sleep(random()/5+ 0.65)
#                combat_mode_state['setup_stage'] = 1

#            # Desecrate
#            if combat_mode_state['setup_stage'] == 1:
#                win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEDOWN,0,0)
#                yield from asyncio.sleep(random()/8+ .20)
#                win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEUP,0,0)            
#                yield from asyncio.sleep(random()/8+ 0.65)
#                combat_mode_state['setup_stage'] = 2
#
#            # Offering
#            if combat_mode_state['setup_stage'] == 2:
#                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN,0,0)
#                yield from asyncio.sleep(random()/8+ .30)
#                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP,0,0)            
#                yield from asyncio.sleep(random()/5+ 0.65)
#                combat_mode_state['setup_stage'] = 3

            # start channeling Summon Raging Spirits
            elif combat_mode_state['setup_stage'] == 3:
                win32api.keybd_event(ord('R'),0,0,0)
                yield from asyncio.sleep(random()/5+.20)
                combat_mode_state['setup_stage'] = 0
                combat_mode_state['channeling SRS?'] = True
                combat_mode_state['channeling_break_stage'] = 0  # quicker 1st
                combat_mode_state['channeling_timer'] = time.clock() - 3
        else:  # if now channeling SRS indefinitely
            time_elapsed = time.clock() - combat_mode_state['channeling_timer']
            if time_elapsed > channeling_cooldown:
                # PAUSE CHANNELING AND CAST SPELLS:
                # pause SRS
                if combat_mode_state['channeling_break_stage'] == 0:
                    win32api.keybd_event(ord('R'),0,win32con.KEYEVENTF_KEYUP,0)
                    yield from asyncio.sleep(random()/8+ .35)
                    combat_mode_state['channeling_break_stage'] = 2
#                    yield from asyncio.sleep(random()/8+ .10)
#                    combat_mode_state['channeling_break_stage'] = 1

#                # desecrate
#                elif combat_mode_state['channeling_break_stage'] == 1:
#                    win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEDOWN,0,0)
#                    yield from asyncio.sleep(random()/8+ .20)
#                    win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEUP,0,0)            
#                    yield from asyncio.sleep(random()/8+ 0.65)
#                    combat_mode_state['channeling_break_stage'] = 2

                # offering
                elif combat_mode_state['channeling_break_stage'] == 2:
                    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN,0,0)
                    yield from asyncio.sleep(random()/8+ .30)
                    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP,0,0)            
                    yield from asyncio.sleep(random()/5+ 0.35)
                    combat_mode_state['channeling_break_stage'] = 3
    
                # resume SRS
                elif combat_mode_state['channeling_break_stage'] == 3:
                    win32api.keybd_event(ord('R'),0,0,0)
                    yield from asyncio.sleep(random()/5+.4)
                    combat_mode_state['channeling_break_stage'] = 0
                    combat_mode_state['channeling_timer'] = time.clock()

    else:
        # COMBAT AI SHUTDOWN GOES HERE
        if combat_mode_state['channeling SRS?']:  # if SRS channeling, stop!
            if combat_mode_state['channeling_break_stage'] == 0:
                win32api.keybd_event(ord('R'),0,win32con.KEYEVENTF_KEYUP,0)
        combat_mode_state.update(default_combat_mode_state)


@asyncio.coroutine
def coro_regroup_mode_summoner_A(is_regroup_mode_active, regroup_mode_state,
                                 **coro_keywords):
    """
    regroup mode coroutine for summoner with:
    -key 'R': self-cast summon raging spirit
    -key 'E': convocation
    -key 'W': skeletotem
    -key 'Q': ???? (animate weapon?)
    -key 'T': raise zombie
    -middle mouse: desecrate
    -right click: flesh offering
    """
    # Constants
    cast_zombie_duration = 5.5

    # First time usage
    default_regroup_mode_state = {'regroup_stage': 0,
                                  'channeling RZ?': False,
                                  'channeling_timer': time.clock() - 10}
    if len(regroup_mode_state) == 0:
        regroup_mode_state.update(default_regroup_mode_state)

    # Run regroup mode as appropriate
    if is_regroup_mode_active:
        # REGROUP AI GOES HERE
        if not regroup_mode_state['channeling RZ?']:
            # Desecrate
            if regroup_mode_state['regroup_stage'] == 0:
                win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEDOWN,0,0)
                yield from asyncio.sleep(random()/8+ .20)
                win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEUP,0,0)            
                yield from asyncio.sleep(random()/8+ 0.65)
                regroup_mode_state['regroup_stage'] = 1

            # Desecrate
            if regroup_mode_state['regroup_stage'] == 1:
                win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEDOWN,0,0)
                yield from asyncio.sleep(random()/8+ .20)
                win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEUP,0,0)            
                yield from asyncio.sleep(random()/8+ 0.65)
                regroup_mode_state['regroup_stage'] = 2

            # start channeling Raise Zombie
            elif regroup_mode_state['regroup_stage'] == 2:
                win32api.keybd_event(ord('T'),0,0,0)
                yield from asyncio.sleep(random()/5+.20)
                regroup_mode_state['regroup_stage'] = 0
                regroup_mode_state['channeling RZ?'] = True
                regroup_mode_state['channeling_timer'] = time.clock()

        else:  # if now channeling RZ for a while
            time_elapsed = time.clock() - regroup_mode_state['channeling_timer']
            if time_elapsed > cast_zombie_duration:
                # STOP CHANNELING AND END REGROUP MODE:
                win32api.keybd_event(ord('T'),0,win32con.KEYEVENTF_KEYUP,0)
                regroup_mode_state.update(default_regroup_mode_state)
                return False  # cancel regroup mode
        return True  # continue regroup mode

    else:
        # REGROUP AI SHUTDOWN GOES HERE
        if regroup_mode_state['channeling RZ?']:  # if RZ channeling, stop!
            win32api.keybd_event(ord('T'),0,win32con.KEYEVENTF_KEYUP,0)
        regroup_mode_state.update(default_regroup_mode_state)
        return False  # continue cancellation of regroup mode


# %%
#class async_trigger():
#    def __init__(self, cycled_key_list, trigger_condition_fcn, cooldown):
#        self.cycled_key_list = cycle(cycled_key_list)
#        self.trigger_condition_fcn = trigger_condition_fcn
#        self.cooldown = cooldown
#        self.cooldown_timer = time.clock() - 10
#
#    def check_condition(self, *condition_args, **condition_kwargs):
#        return self.trigger_condition_fcn(*condition_args, **condition_kwargs)
#
#    def get_async_coroutine(self):
#        return None


# %%
#def test_coro(message_str):
#    print("{}: primed".format(message_str))
#    external_str = (yield)
#    print("{}: received 1st message '{}'".format(message_str, external_str))
#    external_str = (yield)
#    print("{}: received 2nd message '{}'".format(message_str, external_str))
#    print("{}: finished".format(message_str))
#
#
#class coro_mgr():
#    def __init__(self):
#        self.tasks = []
#
#    def add_task(self, task):
#        self.tasks.append(task)
#        next(task)  # prime
#
#    def send_to_tasks(self, value):
#        print("sending {}...".format(str(value)))
#        new_tasks = []
#        for task in self.tasks:
#            try:
#                task.send(value)
#                new_tasks.append(task)
#            except StopIteration:
#                pass
#        self.tasks = new_tasks
#
#
#mgr = coro_mgr()
#mgr.add_task(test_coro("coro_pressA"))
#mgr.add_task(test_coro("coro_pressB"))
#
#print("start main fcn")
#mgr.send_to_tasks("lol hi")
#mgr.add_task(test_coro("coro_pressC"))
#mgr.send_to_tasks("sup y'all")
#mgr.add_task(test_coro("coro_pressD"))
#mgr.send_to_tasks("i said howdy")
#mgr.send_to_tasks("i said howdy dammit")
#mgr.send_to_tasks("fuk")




# %%
#@asyncio.coroutine
#def test_async_fcn(message_list, conditional_fcn, delay):
#    while True:
#        if conditional_fcn():
#            message_list[0] += "."
#        print(message_list[0], flush=True)
#        yield from asyncio.sleep(delay)
#
#
#shared_msg_list = ["."]        
#
#
#def get_get_conditional_fcn_and_shared_state():
#    shared_state = {"add .?": False}
#    def get_conditional_fcn(num):
#        def conditional_fcn():
#            print('status: {}, {}'.format(num, str(shared_state['add .?'])))
#            return shared_state['add .?']
#        return conditional_fcn
#    return shared_state, get_conditional_fcn
#
#shared_state, get_conditional_fcn = get_get_conditional_fcn_and_shared_state()
#
#conditionalfcns = [get_conditional_fcn(1),
#                   get_conditional_fcn(2),
#                   get_conditional_fcn(3)]
#asyncfcns = [test_async_fcn(shared_msg_list, conditionalfcns[0], 0.2),
#             test_async_fcn(shared_msg_list, conditionalfcns[1], 0.3),
#             test_async_fcn(shared_msg_list, conditionalfcns[2], 0.5)]
#loop = asyncio.get_event_loop()
#for fcn in asyncfcns:
#    asyncio.ensure_future(fcn, loop=loop)
#loop.run_until_complete(asyncio.sleep(2))
#print('sleep...', flush=True)
#time.sleep(1)
#shared_state['add .?'] = True
#print('wake up!')
#loop.run_until_complete(asyncio.sleep(2))
#print('sleep...', flush=True)
#time.sleep(1)
#shared_state['add .?'] = False
#print('wake up!')
#loop.run_until_complete(asyncio.sleep(2))
##loop.close()
