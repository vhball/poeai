# -*- coding: utf-8 -*-
"""
Created on Sat Sep 10 15:19:43 2016

@author: Michael
"""

import io
import time
import os, sys  # for saving images only
import win32gui, win32ui, win32con, win32api

import matplotlib.pyplot as plt
import numpy as np
import PIL.Image as Image
import PIL.ImageGrab as ImageGrab  # too slow

import poeai.commands as cmds

def add_coords(x, y):
    return tuple(x_i + y_i for x_i, y_i in zip(x,y))


def get_mouse_centered_bbox(fullscreen_bbox, bbox_size=(200, 200)):
    # if can't return proper size bbox, _don't_ fix or fail silently!
    bbox_width, bbox_height = bbox_size
    screen_width = fullscreen_bbox[2] - fullscreen_bbox[0]
    screen_height = fullscreen_bbox[3] - fullscreen_bbox[1]
    if bbox_width > screen_width or bbox_height > screen_height:
        raise ValueError("get_mousepos_bbox: (xwidth, ywidth) larger than " +
                         "fullscreen bbox dimensions")
    if bbox_width % 2 != 0 or bbox_height % 2 != 0:
        raise ValueError("get_mousepos_bbox: xwidth, ywidth must be even")
    mousex, mousey = cmds.get_coords()
    bbox =  (mousex - bbox_width // 2,  mousey - bbox_height // 2,
             mousex + bbox_width // 2,  mousey + bbox_height // 2)
    # check if outside screen bounds
    if bbox[0] < fullscreen_bbox[0]:
        bbox =  (fullscreen_bbox[0],                    bbox[1],
                 fullscreen_bbox[0] + bbox_width,       bbox[3])
    elif bbox[2] > fullscreen_bbox[2]:
        bbox =  (fullscreen_bbox[2] - bbox_width,       bbox[1],
                 fullscreen_bbox[2],                    bbox[3])
    if bbox[1] < fullscreen_bbox[1]:
        bbox =  (bbox[0],               fullscreen_bbox[1],
                 bbox[2],               fullscreen_bbox[1] + bbox_height)
    elif bbox[3] > fullscreen_bbox[3]:
        bbox =  (bbox[0],               fullscreen_bbox[3] - bbox_height,
                 bbox[2],               fullscreen_bbox[3])
    return bbox


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
   



def get_filename(img_lib_category=None):
    if img_lib_category is not None:
        save_dir = os.getcwd() + "\\images\\library"
        for (dirpath, dirnames, filenames) in os.walk(save_dir):
            category_filenames = [filename
                                  for filename in filenames
                                  if img_lib_category in filename]
            break  # only this top level dir
        category_indices = [int(filename.split("_")[-1].split(".png")[0])
                            for filename in category_filenames]
        if len(category_indices) > 0:
            new_index = max(category_indices) + 1
        else:
            new_index = 0
        filename = str(img_lib_category) + "_" + str(new_index) + ".png"
    else:
        save_dir = os.getcwd() + "\\images"
        filename = "snapshot__" + str(int(time.time())) + ".png"
    return save_dir + "\\" + filename


def capture_and_save_bboxes(bboxes_to_capture, img_category=None):
    #ScreenCapture boxes_to_capture via win32gui
    capture_widths = []
    capture_heights = []
    bbox_names, bboxes_to_capture = bboxes_to_capture  # name scheme changed
    for bbox in bboxes_to_capture:
        capture_widths.append(int(bbox[2]) - int(bbox[0]))
        capture_heights.append(int(bbox[3]) - int(bbox[1]))

    start_time = time.clock()
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
        #bmp.SaveBitmapFile(memdc, 'screenshot.bmp')
        bmpinfo = bmp.GetInfo()

         # Over 7x faster than ImageGrab, but not optimized yet:
         # it's actually faster to take multiple smaller images
        images.append(np.fromstring(
                          bmp.GetBitmapBits(True), dtype=np.uint8).reshape(
                              capture_height, capture_width, 4)[:,:,2::-1])
        
#==============================================================================
#         Just as slow. Does not make a difference if we don't resize!
#         images.append(rawimg)
#==============================================================================

        # Rather slow conversion, it turns out, and still not a numpy array
        # USE TO TAKE SCREENSHOTS
        if True:
            time.sleep(1)
            im = Image.frombuffer('RGB',
                                  (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                                  bmp.GetBitmapBits(True),
                                  'raw', 'BGRX', 0, 1)
            filename = get_filename(img_category)
            im.save(filename, 'PNG')

        win32gui.DeleteObject(bmp.GetHandle())
        srcdc.DeleteDC()
        memdc.DeleteDC()
        win32gui.ReleaseDC(hwin, hwindc)
    

    #Check time passed during capture:
    time_elapsed = time.clock() - start_time
    print('Time elapsed: {:.3f} seconds'.format(time_elapsed))

    return images


if __name__ == "__main__":
    bboxes_to_capture = get_bboxes_to_capture("all")
#    bboxes_to_capture = get_bboxes_to_capture("life and mana")
#    bboxes_to_capture = get_bboxes_to_capture("map")
#    img_category = None
    images = capture_and_save_bboxes(bboxes_to_capture)
    plt.imshow(images[0], interpolation="nearest")

#    fullscreen_bbox = get_bboxes_to_capture("all")[0]
#    img_category = "garbage"
    
#    time.sleep(3)

#    for i in range(999):
#        bboxes_to_capture = [get_mouse_centered_bbox(fullscreen_bbox,
#                                                     bbox_size=(200, 200))]
#        images = capture_and_save_bboxes(bboxes_to_capture, img_category)

#    plt.imshow(images[0], interpolation="nearest")


