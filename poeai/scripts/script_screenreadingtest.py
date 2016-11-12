# -*- coding: utf-8 -*-
"""
Created on Sun Aug 21 20:46:37 2016

@author: mwmac
"""

import numpy as np
import matplotlib.pyplot as plt

from skimage import io
from skimage.feature import match_template

import PIL.ImageGrab as grabber

import time


# stolen from http://stackoverflow.com/questions/35777830/
#                 fast-absolute-difference-of-two-uint8-arrays
def uint8_subtract(array1, array2):
  a = array1-array2
  b = np.uint8(array1<array2) * 254 + 1
  return a * b


def grab_screen():
    pillow_grab = grabber.grab()
    screencap = np.array(pillow_grab).reshape(
                    pillow_grab.size[1], pillow_grab.size[0], 3)
#    screencap = io.imread("images/example_screenshot3.png")

    # Lifeglobe textbox & mask passing only greyscale pixels
    lifebox = screencap[575:610, 30:140, :]

# INCORRECT!!! 3rd argument is OUTPUT, np.logical_and only compares 2 arrays
    lifebox_mask = np.logical_and(
        uint8_subtract(lifebox[:, :, 0], lifebox[:, :, 1]) < 20,
        uint8_subtract(lifebox[:, :, 0], lifebox[:, :, 1]) < 20,
        uint8_subtract(lifebox[:, :, 0], lifebox[:, :, 1]) < 20)
    lifebox = lifebox[:, :, 0]/255.0  # flatten to 2D greyscale
    
    # Managlobe textbox & mask passing only greyscale pixels
    manabox = screencap[590:610, 1240:1340, :]

# INCORRECT!!! 3rd argument is OUTPUT, np.logical_and only compares 2 arrays
    manabox_mask = np.logical_and(
        uint8_subtract(manabox[:, :, 0], manabox[:, :, 1]) < 20,
        uint8_subtract(manabox[:, :, 0], manabox[:, :, 1]) < 20,
        uint8_subtract(manabox[:, :, 0], manabox[:, :, 1]) < 20)
    manabox = manabox[:, :, 0]/255.0  # flatten to 2D greyscale

    screen_segments = {"lifebox": lifebox,
                       "lifebox_mask": lifebox_mask,
                       "manabox": manabox,
                       "manabox_mask": manabox_mask}
    return screen_segments


def fetch_templates():
    # Load comparison templates
    templates = {}
    for num in range(10):
        filename = "images/" + str(num) + ".png"
        templates[num] = io.imread(filename, as_grey=True)
        templates[str(num) + "_mask"] = templates[num] > 0.75

    templates['slash'] = io.imread("images/slash.png", as_grey=True)
    templates['life'] = io.imread("images/life.png", as_grey=True)
    templates['shield'] = io.imread("images/shield.png", as_grey=True)
    templates['mana'] = io.imread("images/mana.png", as_grey=True)

    templates['slash_mask'] = templates['slash'] > 0.75
    templates['life_mask'] = templates['life'] > 0.75
    templates['shield_mask'] = templates['shield'] > 0.75
    templates['mana_mask'] = templates['mana'] > 0.75

    return templates


def match_template_masked(image, image_mask, template, template_mask):
    width = image_mask.shape[0] - template_mask.shape[0] + 1
    height = image_mask.shape[1] - template_mask.shape[1] + 1
    result = np.full((width, height), False, dtype=bool)
    points_to_check = np.argwhere(template_mask == True)
    for dx in range(width):  # 
        for dy in range(height):
            mismatch_found = False
            for x, y in points_to_check:  # only check where temp. mask is True
                if template_mask[x, y] != image_mask[dx + x, dy + y]:
                    mismatch_found = True
                elif np.abs(template[x, y] - image[dx + x, dy + y]) > 0.05:
                    mismatch_found = True
                if mismatch_found:
                    break
            if not mismatch_found:
                result[dx, dy] = True
    return result


def extract_stat(stat, screen_segments, templates):
    # Pick appropriate template:
    if stat == "life":
        textbox = screen_segments['lifebox']
        textbox_mask = screen_segments['lifebox_mask']
        stat_template = templates['life']
        stat_template_mask = templates['life_mask']
        stat_width = 10
    elif stat == "mana":
        textbox = screen_segments['manabox']
        textbox_mask = screen_segments['manabox_mask']
        stat_template = templates['mana']
        stat_template_mask = templates['mana_mask']
        stat_width = 13
    elif stat == "shield":
        textbox = screen_segments['lifebox']
        textbox_mask = screen_segments['lifebox_mask']
        stat_template = templates['shield']
        stat_template_mask = templates['shield_mask']
        stat_width = 13
    else:
        raise AttributeError("parse_textbox: only 'life', 'mana', and " +
                             "'shield' are valid stats to read")

    # Find life/mana/shield text:
    result = match_template_masked(textbox, textbox_mask,
                                   stat_template,
                                   stat_template_mask)
    matchcoords = np.argwhere(result == True)
    if len(matchcoords) > 0:
#        print("{} matches found: {}".format(stat, len(matchcoords)))
        match_x, match_y = matchcoords[0]
    else:
#        print('stat not found...', flush=True)
        return None, None
    match_y += stat_width  # scroll past stat before searching

    # Find numbers
    numlist = []
    for numeral in range(10):
        result = match_template_masked(textbox, textbox_mask,
                                       templates[numeral],
                                       templates[str(numeral) + "_mask"])
        matchcoords = np.argwhere(result == True)
#        matchcoords = np.argwhere(result > 0.95)
        for x, y in matchcoords:
            numlist.append([x, y, numeral])
#        print("match max for {}: {}".format(str(numeral),
#                                            str(np.max(result))))

    # Find slashes:
    result = match_template_masked(textbox, textbox_mask,
                                   templates['slash'],
                                   templates['slash_mask'])
    matchcoords = np.argwhere(result == True)
#    matchcoords = np.argwhere(result > 0.95)
    slashcoords = tuple(tuple(xypair) for xypair in matchcoords)
#    print("match max for {}: {}".format("slash",
#                                        str(np.max(result))))


    # Sort digits
    scan_startx = max(0, match_x - 5)
    scan_starty = max(0, match_y)
    scan_endx = min(textbox.shape[0], match_x + 5)
    scan_endy = textbox.shape[1]
    numerator_str = ""
    denominator_str = ""
    last_numfound_y = -1
    slash_found = False
    num_found = False
    for y in range(scan_starty, scan_endy):  # find digits in order
        if y - last_numfound_y > 2:  # start looking for another symbol
            num_found = False
        for x in range(scan_startx, scan_endx):  # scan vertically
            if (x, y) in slashcoords:  # remember: syntax for TUPLES ONLY
                slash_found = True
            for num_x, num_y, num in numlist:
                if not num_found and (x, y) == (num_x, num_y):
                    num_found = True
                    last_numfound_y = y
                    if slash_found:
                        denominator_str += str(num)
                    else:
                        numerator_str += str(num)

    try:
        numerator = float(numerator_str)
    except ValueError:
        numerator = None
    try:
        denominator = float(denominator_str)
    except ValueError:
        denominator = None
    return numerator, denominator


# %%
templates = fetch_templates()

start_processing_time = time.time()
stats = []
for x in range(5):
    screen_segments = grab_screen()
    life, lifemax =     extract_stat('life', screen_segments, templates)
    mana, manamax =     extract_stat('mana', screen_segments, templates)
    shield, shieldmax = extract_stat('shield', screen_segments, templates)
#    stats.append([life, lifemax, mana, manamax, shield, shieldmax])
elapsed_processing_time = time.time() - start_processing_time
print("Elapsed time: {}".format(elapsed_processing_time))

#life_list, lifemax_list, \
#    mana_list, manamax_list, \
#        shield_list, shieldmax_list = list(zip(*stats))
#print("life: {}/{}".format(life_list[-1], lifemax_list[-1]))
#print("mana: {}/{}".format(mana_list[-1], manamax_list[-1]))
#print("shield: {}/{}".format(shield_list[-1], shieldmax_list[-1]))


# %%
plt.plot(*zip(*enumerate(shield_list)))


# %%
#    print("-------------------------------")
#    print("life: {}/{}".format(life, lifemax))
#    print("mana: {}/{}".format(mana, manamax))
#    print("shield: {}/{}".format(shield, shieldmax))


# %% SCRATCH TESTS BELOW






# %%
# Show templates
fig = plt.figure()
subplot_axes_list = [plt.subplot(3, 5, x + 1)
                     for x in range(15)]
for axes, image in zip(subplot_axes_list, numerals):
    axes.imshow(image, interpolation="nearest")
subplot_axes_list[10].imshow(slash, interpolation="nearest")
subplot_axes_list[11].imshow(life, interpolation="nearest")
subplot_axes_list[12].imshow(shield, interpolation="nearest")
subplot_axes_list[13].imshow(mana, interpolation="nearest")


# %%
start_processing_time1 = time.time()
for i in range(100):
    pillow_grab = grabber.grab()
    pillow_lifebox = pillow_grab.crop((30, 575, 140, 610))
    pillow_manabox = pillow_grab.crop((1240, 590, 1340, 610))
    lifebox1 = np.array(pillow_lifebox).reshape(
                    pillow_lifebox.size[1], pillow_lifebox.size[0], 3)
    manabox1 = np.array(pillow_manabox).reshape(
                    pillow_manabox.size[1], pillow_manabox.size[0], 3)
elapsed_processing_time1 = time.time() - start_processing_time1

start_processing_time2 = time.time()
for j in range(100):
    pillow_grab = grabber.grab()
    screencap = np.array(pillow_grab).reshape(
                    pillow_grab.size[1], pillow_grab.size[0], 3)
    lifebox2 = screencap[575:610, 30:140, :]
    manabox2 = screencap[590:610, 1240:1340, :]
elapsed_processing_time2 = time.time() - start_processing_time2

print('{} seconds elapsed during processing'.format(elapsed_processing_time1))
print('{} seconds elapsed during processing'.format(elapsed_processing_time2))

# SPEEDTEST RESULT: BOTH SAME WITHIN ERROR, FIRST NOT WORTH LOSS OF CONSISTENCY

#==============================================================================
# fig = plt.figure()
# subaxes = []
# for ind in range(4):
#     subaxes.append(plt.subplot(2, 2, ind + 1))
#     subaxes[ind].set_axis_off()
# subaxes[0].imshow(lifebox1)
# subaxes[1].imshow(manabox1)
# subaxes[2].imshow(lifebox2)
# subaxes[3].imshow(manabox2)
#==============================================================================

# %%
screencap = io.imread("images/example_screenshot2.png")
lifebox = screencap[575:610, 30:140, :]
colored_mask = np.logical_not(
                   np.logical_and(lifebox[:, :, 0] == lifebox[:, :, 1],
                                  lifebox[:, :, 0] == lifebox[:, :, 2]))
lifebox[colored_mask] = 0
lifebox = lifebox[:, :, 0]  # flatten to 2D

plt.imshow(lifebox, interpolation="nearest")


# %%
manabox = screencap[590:610, 1240:1340, :]
colored_mask = np.logical_not(
                   np.logical_and(manabox[:, :, 0] == manabox[:, :, 1],
                                  manabox[:, :, 0] == manabox[:, :, 2]))
manabox[colored_mask] = 0
manabox = manabox[:, :, 0]  # flatten to 2D

plt.imshow(manabox, interpolation="nearest")


# %%
textbox = lifebox

fig = plt.figure()
axes = plt.axes()
axes.hold(True)
xmax, ymax = textbox.shape
axes.set_xlim([0, ymax])
axes.set_ylim([0, xmax])

for numeral in range(10):
    result = match_template(textbox, numerals[numeral])
    peakcoords = np.argwhere(result > 0.8)
    for x, y in peakcoords:
        axes.text(y, x, str(numeral))  # switched for readability

result = match_template(textbox, slash)
peakcoords = np.argwhere(result > 0.8)
for x, y in peakcoords:
    axes.text(y, x, "/")

result = match_template(textbox, life)
peakcoords = np.argwhere(result > 0.8)
for x, y in peakcoords:
    axes.text(y, x, "life")

result = match_template(textbox, shield)
peakcoords = np.argwhere(result > 0.8)
for x, y in peakcoords:
    axes.text(y, x, "shield")

result = match_template(textbox, mana)
peakcoords = np.argwhere(result > 0.8)
for x, y in peakcoords:
    axes.text(y, x, "mana")


# %%
# procedure:
# 0. zoom to target region to look for text
# 1. throw out everything in region not greyscale (?) - make black instead
# 2. create number templates and template masks as areas != 0. Only compare
#    within the != 0 region of the template.
