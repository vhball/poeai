# -*- coding: utf-8 -*-
"""
Created on Sun Oct 16 17:12:01 2016

@author: Michael
"""


import numpy as np
import matplotlib.pyplot as plt

from skimage import io
from skimage.feature import match_template

import time


# stolen from http://stackoverflow.com/questions/35777830/
#                 fast-absolute-difference-of-two-uint8-arrays
def uint8_subtract(array1, array2):
  a = array1-array2
  b = np.uint8(array1<array2) * 254 + 1
  return a * b  # gives absolute value!


# %%






















# %%def match_template_masked(image, image_mask, template, template_mask):
    template_height, template_width = template_mask.shape[0:2]
    image_height, image_width = image_mask.shape[0:2]
    search_width = image_width - template_width + 1
    search_height = image_height - template_height + 1

    rgb_sum_diff_tol = 12  # tolerance on scale of 0-3*255
#    num_test_pixels = np.count_nonzero(template_mask)  # num template pixels

    num_matched_pixels_mat = np.zeros((search_height, search_width))
    num_matched_pixels_max = 0
    max_matched_pixels_mat = None
    for dy in range(search_height):
        for dx in range(search_width):
            image_segment = image[dy:dy + template_height,
                                  dx:dx + template_width]
            image_mask_segment = image_mask[dy:dy + template_height,
                                            dx:dx + template_width]
            color_differences = uint8_subtract(image_segment, template)
            matched_pixels = sum(1.0*color_differences[:, :, i]
                                 for i in range(3)) <= rgb_sum_diff_tol
            # !3rd arg to np.logical_and is output, NOT a 3rd array to compare!
            mask_match = np.logical_and(image_mask_segment[:, :, 0],
                                        template_mask[:, :, 0])
            masked_matched_pixels = np.logical_and(mask_match,
                                                   matched_pixels)
#==============================================================================
#             print("({},{}): greyscale pixels in tolerance: {}".format(
#                       dy, dx, np.count_nonzero(greyscale_in_tol)) +
#                   ", {}/{} greyscale pixels found".format(
#                       np.count_nonzero(greyscale_match),
#                       num_test_pixels), flush=True)
#==============================================================================
            num_matched_pixels = np.count_nonzero(masked_matched_pixels)
            num_matched_pixels_mat[dy, dx] = num_matched_pixels
            if num_matched_pixels > num_matched_pixels_max:
                num_matched_pixels_max = num_matched_pixels
                max_matched_pixels_mat = image_segment.copy()
                max_matched_pixels_mat[
                    np.logical_not(masked_matched_pixels)] = 0

    return max_matched_pixels_mat


# %%
def get_map_displacement(image1, image2):
    if image1.shape != (270, 270, 3) or image2.shape != (270, 270, 3):
        raise ValueError("get_map_displacement: images must be of shape " +
                         "(270, 270, 3), only 1080p supported currently")
    # exclude y:133:139, x:132:140 of full map image (player indicator)
    image = image2[35:235, 35:235, :]
    image_mask = np.full((200, 200, 3), True, dtype=bool)
    image_mask[98:104, 97:105, :] = False
    template = image1[80:190, 80:190, :]
    template_mask = np.full((110, 110, 3), True, dtype=bool)
    template_mask[53:59, 52:60, :] = False
    max_matched_pixels_mat = match_template_masked(image, image_mask,
                                                   template, template_mask)
    plt.imshow(max_matched_pixels_mat, interpolation="nearest")
    return max_matched_pixels_mat
