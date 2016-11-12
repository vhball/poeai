# -*- coding: utf-8 -*-
"""
Created on Thu Sep 29 22:43:11 2016

@author: Michael
"""

import random
import time
import win32api, win32con

import numpy as np


SKEWFACTOR = 1.85
XPAD = 0
YPAD = 0
WINWIDTH = 1920
WINHEIGHT = 1000
CIRCRAD = int(round(40*WINHEIGHT/100.0))
STARTRAD = int(round(12*WINHEIGHT/100.0))
STOPRAD = int(round(4*WINHEIGHT/100.0))
RESTRAD = int(round(0.1*WINHEIGHT/100.0))    


def set_mouse_pos(coord):
    time.sleep(random.random()/10 + .05)
    win32api.SetCursorPos((XPAD + coord[0],
                           YPAD + coord[1]))


def get_coords():
    x, y = win32api.GetCursorPos()
    x = x - XPAD
    y = y - YPAD
    coords = (x, y)
    return coords


def leftClick():
    time.sleep(random.random()/10+.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0)
    time.sleep(random.random()/10+.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0)
#    print "MouseLeft Click"


def leftDown():
    time.sleep(random.random()/10+.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0)
#    print "MouseLeft Down"

    
def leftUp():
    time.sleep(random.random()/10+.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0)
#    print "MouseLeft Up"


def rightClick():
    time.sleep(random.random()/10+.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN,0,0)
    time.sleep(random.random()/10+.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP,0,0)
#    print "MouseRight Click"


def rightDown():
    time.sleep(random.random()/10+.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN,0,0)
#    print "MouseRight Down"

    
def rightUp():
    time.sleep(random.random()/10+.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP,0,0)
#    print "MouseRight Up"


def get_angle_from_center(coords, unskewed=False):
    if unskewed:
        xdist = (1.0/SKEWFACTOR)*(coords[0] - WINWIDTH/2)
    else:
        xdist = coords[0] - WINWIDTH/2
    ydist = coords[1] - WINHEIGHT/2
    if xdist == 0:
        angle = np.arctan(1.0*ydist)
    if xdist > 0:
        if ydist >= 0:
            angle = np.arctan(1.0*ydist/xdist)
        if ydist < 0:
            angle = 2*np.pi+np.arctan(1.0*ydist/xdist)
    if xdist < 0:
        angle = np.pi + np.arctan(1.0*ydist/xdist)
    return angle


def get_distance_from_center(coords, unskewed=False):
    if unskewed:
        xdist = (1.0/SKEWFACTOR)*(coords[0] - WINWIDTH/2)
    else:
        xdist = coords[0] - WINWIDTH/2
    ydist = coords[1] - WINHEIGHT/2
    dist = np.sqrt(xdist**2 + ydist**2)
    return dist


def set_mouse_relative_to_center(radius, angle, unskewed=False):
    if unskewed:
        stopx = int(round(WINWIDTH/2 + SKEWFACTOR*radius*np.cos(angle)))
        stopy = int(round(WINHEIGHT/2 + SKEWFACTOR*radius*np.sin(angle)))
    else:
        stopx = int(round(WINWIDTH/2 + radius*np.cos(angle)))
        stopy = int(round(WINHEIGHT/2 + radius*np.sin(angle)))    
    newcoords = (stopx, stopy)
    set_mouse_pos(newcoords)


def char_start_move(angle, unskewed=False):
    set_mouse_relative_to_center(STARTRAD, angle, unskewed)
    leftDown()


def char_stop_move(angle, unskewed=False):
    set_mouse_relative_to_center(STOPRAD, angle, unskewed)
    leftUp()


def char_stop_click(angle, unskewed=False):
    set_mouse_relative_to_center(STOPRAD, angle, unskewed)
    leftClick()




