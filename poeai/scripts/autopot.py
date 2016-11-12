# -*- coding: utf-8 -*-
"""
Runs a basic loop to watch the screen and use potions
Potion configuration determination method TBD

using some code from automatetheboringstuff.com/chapter18
for now to play around with pyautogui

Created on Thu Jan  7 22:55:58 2016

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
