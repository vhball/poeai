# -*- coding: utf-8 -*-
"""
Short key/mouse movement combinations designed to do tedious sequences of
actions upon request (e.g. some keypress).

Examples might include a sequence of less convenient skill buttons mapped to
an easy key (e.g. M4, M5, Mscroll), or combinations requiring tedious mouse
patterns (e.g. )

Created on Fri Jan  8 09:41:39 2016

@author: Michael
"""

import pyautogui
import time

if __name__ == "__main__":
    print('Press Ctrl-C to quit.')
    try:
        while True:
            # Get and print the mouse coordinates.
            x, y = pyautogui.position()
            positionStr = 'X: ' + str(x).rjust(4) + ' Y: ' + str(y).rjust(4)
            print('\b' * len(positionStr), end='', flush=True)
            print(positionStr, end='')
            time.sleep(0.1)
    except KeyboardInterrupt:
        print('\n...\nDone.')
