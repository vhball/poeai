# -*- coding: utf-8 -*-
"""
Created on Sat Sep 10 15:19:43 2016

@author: Michael
"""

import io
import time

import matplotlib.pyplot as plt
import numpy as np
import PIL.Image as Image
import PIL.ImageGrab as ImageGrab  # too slow
import os, sys  # for saving images only
import win32gui, win32ui, win32con, win32api


def add_coords(x, y):
    return tuple(x_i + y_i for x_i, y_i in zip(x,y))


def get_bboxes_to_capture(target="health and mana"):
    # Autodetect resolution
    hwin = win32gui.FindWindow(None, "Path of Exile")  # Window handle
    if hwin == 0:
        raise Exception("Unable to detect Path of Exile running! Aborting...")
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
    if border_width > 15 or bar_height > 60:
        raise Exception("get_bboxes_to_capture: " +
                        "resolution does not appear to be 720p or 1080p!")
            
     # define coordinate box to capture relative to POE window
    onscreen_boxes_to_capture = []
    if resolution == "1080p":
        if target == "all":
            onscreen_boxes_to_capture.append(
                (0, 0, 1920, 1080))  # whole window 1920x1080
        elif target == "health and mana":
            onscreen_boxes_to_capture.append(
                (50, 793, 210, 855))  # health/shield text 160x62
            onscreen_boxes_to_capture.append(
                (1740, 793, 1900, 855))  # mana/res. text 160x62
        elif target == "map":
            onscreen_boxes_to_capture.append(
                (1642, 7, 1912, 277))  # map 350x350
    elif resolution == "720p":
        if target == "all":
            onscreen_boxes_to_capture.append(
                (0, 0, 1280, 720))  # whole window 1280x720
        elif target == "health and mana":
            onscreen_boxes_to_capture.append(
                (30, 530, 140, 570))  # health/shield text 110x40
            onscreen_boxes_to_capture.append(
                (1150, 530, 1260, 570))  # mana/res. text 110x40
    if len(onscreen_boxes_to_capture) == 0:
        raise Exception("get_bboxes_to_capture: " +
                        "unable to find bbox(es) for target " +
                        "'{}'".format(target))

    bboxes_to_capture = [add_coords(window_padding, bbox)
                         for bbox in onscreen_boxes_to_capture]
    return bboxes_to_capture
   


if __name__ == "__main__":
    bboxes_to_capture = get_bboxes_to_capture("all")
#    bboxes_to_capture = get_bboxes_to_capture("health and mana")
#    bboxes_to_capture = get_bboxes_to_capture("map")


# %%
    #ScreenCapture boxes_to_capture via win32gui
    capture_widths = []
    capture_heights = []
    for bbox in bboxes_to_capture:
        capture_widths.append(int(bbox[2] - bbox[0]))
        capture_heights.append(int(bbox[3] - bbox[1]))

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
            im.save(os.getcwd() + '\\images\\snapshot__' +
                    str(int(time.time())) + '.png', 'PNG')

        win32gui.DeleteObject(bmp.GetHandle())
        srcdc.DeleteDC()
        memdc.DeleteDC()
        win32gui.ReleaseDC(hwin, hwindc)
    

    #Check time passed during capture:
    time_elapsed = time.clock() - start_time
    print('Time elapsed: {:.3f} seconds'.format(time_elapsed))

    
# %% TEST SPLITTING CAPTURE IN TWO OVERHEAD
#==============================================================================
#     box_to_capture1 = (9, 38, 409, 638)  # left side
#     capture_width1 = box_to_capture1[2] - box_to_capture1[0]
#     capture_height1 = box_to_capture1[3] - box_to_capture1[1]
#     box_to_capture2 = (409, 38, 809, 638)  # right side
#     capture_width2 = box_to_capture2[2] - box_to_capture2[0]
#     capture_height2 = box_to_capture2[3] - box_to_capture2[1]
# 
#     #ScreenCapture via win32gui in two chunks
#     start_time = time.clock()
#     images = []
#     for ind in range(100):
#         hwin = win32gui.FindWindow(None, "Path of Exile")  # Window handle
#         hwindc = win32gui.GetWindowDC(hwin)
#         # left half
#         srcdc = win32ui.CreateDCFromHandle(hwindc)
#         memdc = srcdc.CreateCompatibleDC()
#         bmp = win32ui.CreateBitmap()
#         bmp.CreateCompatibleBitmap(srcdc, capture_width1, capture_height1)
#         memdc.SelectObject(bmp)
#         memdc.BitBlt((0, 0), (capture_width1, capture_height1), srcdc,
#                      (box_to_capture1[0], box_to_capture1[1]), win32con.SRCCOPY)
#         #bmp.SaveBitmapFile(memdc, 'screenshot.bmp')
#         bmpinfo = bmp.GetInfo()
#         images.append(np.fromstring(
#                           bmp.GetBitmapBits(True), dtype=np.uint8).reshape(
#                               capture_height1, capture_width1, 4)[:,:,2::-1])
#         win32gui.DeleteObject(bmp.GetHandle())
#         srcdc.DeleteDC()
#         memdc.DeleteDC()
#         win32gui.ReleaseDC(hwin, hwindc)
#         # right half
#         hwin = win32gui.FindWindow(None, "Path of Exile")  # Window handle
#         hwindc = win32gui.GetWindowDC(hwin)
#         srcdc = win32ui.CreateDCFromHandle(hwindc)
#         memdc = srcdc.CreateCompatibleDC()
#         bmp = win32ui.CreateBitmap()
#         bmp.CreateCompatibleBitmap(srcdc, capture_width2, capture_height2)
#         memdc.SelectObject(bmp)
#         memdc.BitBlt((0, 0), (capture_width2, capture_height2), srcdc,
#                      (box_to_capture2[0], box_to_capture2[1]), win32con.SRCCOPY)
#         #bmp.SaveBitmapFile(memdc, 'screenshot.bmp')
#         bmpinfo = bmp.GetInfo()
#         images.append(np.fromstring(
#                           bmp.GetBitmapBits(True), dtype=np.uint8).reshape(
#                               capture_height2, capture_width2, 4)[:,:,2::-1])
# #        bmpstr = bmp.GetBitmapBits(True)
# #        images.append(Image.frombuffer(
# #                          'RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
# #                          bmpstr, 'raw', 'BGRX', 0, 1))
#         win32gui.DeleteObject(bmp.GetHandle())
#         srcdc.DeleteDC()
#         memdc.DeleteDC()
#         win32gui.ReleaseDC(hwin, hwindc)
# #        images.append(np.hstack((leftimage, rightimage)))
#     
# 
#     #Check time passed during capture:
#     time_elapsed = time.clock() - start_time
#     print('Time elapsed: {:.3f} seconds'.format(time_elapsed))
#==============================================================================


# %%
#==============================================================================
#     # ScreenCapture via ImageGrab  (almost 10x slower)
#     box_to_capture = (9, 38, 809, 638)  # border: 9 left/right/bottom, 29 top
#     capture_width = box_to_capture[2] - box_to_capture[0]
#     capture_height = box_to_capture[3] - box_to_capture[1]
#     start_time = time.clock()
#     images = []
#     for loop in range(10):
#         hwin = win32gui.FindWindow(None, "Path of Exile")  # Window handle
#         bbox = win32gui.GetWindowRect(hwin)
#         images.append(ImageGrab.grab(bbox))
# 
#     #Check time passed during capture:
#     time_elapsed = time.clock() - start_time
#     print('Time elapsed: {:.3f} seconds'.format(time_elapsed))
#==============================================================================
    

# %%
plt.imshow(images[0], interpolation="nearest")