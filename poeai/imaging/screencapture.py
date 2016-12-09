# -*- coding: utf-8 -*-
"""
Created on Sat Sep 10 15:19:43 2016

@author: Michael
"""

import numpy as np
import win32api, win32gui, win32ui, win32con


# %%
def add_coords(x, y):
    """
    Quick helper function that adds 4-tuples and returns a 4-tuple
    """
    return tuple(x_i + y_i for x_i, y_i in zip(x,y))


# %%
def get_bboxes_to_capture(target="all", assume_fullscreen_1080p=False):
    """
    Returns a list of 4-tuples (xstart, ystart, xend, yend) showing the
    coordinate regions that should be captured given the user's detected
    resolution (must be either 720p or 1080p, windowed is okay).
    
    Parameter options:
    target: default is "all"
        "all": capture entire window (sans borders if windowed)
        "life and mana": capture the 3 lines of text above life/mana globes
            as two images, one for each globe. can just put "life" or "mana"
            as well to just capture one.
    """
    # Autodetect resolution
    if assume_fullscreen_1080p:
        resolution = "1080p"
        screen_width = 1920
        screen_height = 1080
        window_padding = (0, 0, 0, 0)
    else:
        hwin = win32gui.FindWindow(None, "Path of Exile")  # Window handle
        if hwin == 0:
            raise Exception("Unable to detect Path of Exile running! " +
                            "Aborting...")
        bbox = win32gui.GetWindowRect(hwin)
        screen_width = bbox[2] - bbox[0]
        screen_height = bbox[3] - bbox[1]
        if screen_width >= 1920 and screen_height >= 1080:
            resolution = "1080p"
            border_width = int((screen_width - 1920)/2)
            bar_height = int(screen_height - 2*border_width - 1080)
            window_padding = (border_width, bar_height + border_width,
                              border_width, bar_height + border_width)
        elif screen_width >= 1280 and screen_height >= 720:
            resolution = "720p"
            border_width = int((screen_width - 1280)/2)
            bar_height = int(screen_height - 2*border_width - 720)
            window_padding = (border_width, bar_height + border_width,
                              border_width, bar_height + border_width)
        else:
            raise Exception("get_bboxes_to_capture: resolution " +
                            "does not appear to be 720p or 1080p! " +
                            "detected resultion: {}x{}".format(screen_width,
                                                               screen_height))        
        if border_width > 15 or bar_height > 60:
            raise Exception("get_bboxes_to_capture: resolution " +
                            "does not appear to be 720p or 1080p! " +
                            "detected resultion: {}x{}".format(screen_width,
                                                               screen_height))
            
     # define coordinate box to capture relative to POE window
    box_names = []
    onscreen_boxes_to_capture = []
    if resolution == "1080p":
        if target == "all":
            target = "life, mana"
            box_names.append("full screen")
            onscreen_boxes_to_capture.append(
                (0, 0, 1920, 1080))  # whole window 1920x1080
        if "life" in target:
            box_names.append("life")
            onscreen_boxes_to_capture.append(
                (50, 795, 210, 857))  # life/shield text 160x62
        if "mana" in target:
            box_names.append("mana")
            onscreen_boxes_to_capture.append(
                (1740, 795, 1900, 857))  # mana/res. text 160x62
    elif resolution == "720p":
        if target == "all":
            box_names.append("full screen")
            onscreen_boxes_to_capture.append(
                (0, 0, 1280, 720))  # whole window 1280x720
        if "life" in target:
            box_names.append("life")
            onscreen_boxes_to_capture.append(
                (30, 530, 140, 570))  # life/shield text 110x40
        if "mana" in target:
            box_names.append("mana")
            onscreen_boxes_to_capture.append(
                (1150, 530, 1260, 570))  # mana/res. text 110x40
    if len(onscreen_boxes_to_capture) == 0:
        raise Exception("get_bboxes_to_capture: " +
                        "unable to find bbox(es) for target " +
                        "'{}'".format(target))

    bboxes_to_capture = [add_coords(window_padding, bbox)
                         for bbox in onscreen_boxes_to_capture]
    return box_names, bboxes_to_capture
   

# %%
def screen_capture(bboxes_to_capture):
    """
    Given a set of bounding boxes, will capture the contents of those boxes
    from the Path of Exile window.

    Returns a list of numpy arrays corresponding to images (w/RGB dim).
    """
    capture_widths = []
    capture_heights = []
    for bbox in bboxes_to_capture:
        capture_widths.append(int(bbox[2] - bbox[0]))
        capture_heights.append(int(bbox[3] - bbox[1]))

    images = []
    for box_to_capture, capture_width, capture_height in \
            zip(bboxes_to_capture, capture_widths, capture_heights):
        hwin = win32gui.FindWindow(None, "Path of Exile")  # Window handle
        hwindc = win32gui.GetWindowDC(hwin)
        srcdc = win32ui.CreateDCFromHandle(hwindc)
        memdc = srcdc.CreateCompatibleDC()
        bmp = win32ui.CreateBitmap()
        bmp.CreateCompatibleBitmap(srcdc, capture_width, capture_height)
        memdc.SelectObject(bmp)
        memdc.BitBlt((0, 0), (capture_width, capture_height), srcdc,
                     (box_to_capture[0], box_to_capture[1]), win32con.SRCCOPY)
        images.append(np.fromstring(
                          bmp.GetBitmapBits(True), dtype=np.uint8).reshape(
                              capture_height, capture_width, 4)[:,:,2::-1])
        win32gui.DeleteObject(bmp.GetHandle())
        srcdc.DeleteDC()
        memdc.DeleteDC()
        win32gui.ReleaseDC(hwin, hwindc)

    return images
