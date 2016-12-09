# -*- coding: utf-8 -*-
"""
Created on Sun Sep 11 21:23:23 2016

@author: Michael
"""

import numpy as np
import matplotlib.pyplot as plt

from skimage import io
from skimage.feature import match_template

import time


# Load templates module-wide so only happens once
def fetch_templates(resolution):
    # out of 255, what brightness beyond which assume greyscale
    greyscale_tolerance_labels = 130
    greyscale_tolerance = 180
    # Load comparison templates
    directory = "images/" + resolution + "/"
    templates = {}
    for num in range(10):
        filename = directory + str(num) + ".png"
        templates[str(num)] = io.imread(filename)[:, :, 0]
        templates[str(num) + "_mask"] = \
            templates[str(num)] > greyscale_tolerance

    templates['slash'] = io.imread(directory + "slash.png")[:, :, 0]
    templates['life'] = io.imread(directory + "life.png")[:, :, 0]
    templates['shield'] = io.imread(directory + "shield.png")[:, :, 0]
    templates['mana'] = io.imread(directory + "mana.png")[:, :, 0]
    templates['reserved'] = io.imread(directory + "reserved.png")[:, :, 0]

    templates['slash_mask'] = templates['slash'] > greyscale_tolerance
    templates['life_mask'] = templates['life'] > greyscale_tolerance_labels
    templates['shield_mask'] = templates['shield'] > greyscale_tolerance_labels
    templates['mana_mask'] = templates['mana'] > greyscale_tolerance_labels
    templates['reserved_mask'] = templates['reserved'] > greyscale_tolerance_labels

    return templates


#TEMPLATES_720p = fetch_templates("720p")  # haven't made images yet!
TEMPLATES_1080p = fetch_templates("1080p")


# %%
# stolen from http://stackoverflow.com/questions/35777830/
#                 fast-absolute-difference-of-two-uint8-arrays
def uint8_subtract(array1, array2):
  a = array1-array2
  b = np.uint8(array1<array2) * 254 + 1
  return a * b  # gives absolute value!


# %%
def match_template_masked(image, image_mask,
                          template, template_mask, stop_when_found=False):
    template_height, template_width = template_mask.shape
    image_height, image_width = image_mask.shape
    search_width = image_width - template_width + 1
    search_height = image_height - template_height + 1

    tolerance_for_matched_pixels = 7  # on scale of 255, 4 too low, 6-8 ideal?
#    tolerance_for_matched_pixels = 12  # on scale of 255, 4 too low, 6-8 ideal?
    num_test_pixels = np.count_nonzero(template_mask)  # num template pixels

    matchcoords = []
    for dy in range(search_height):
        for dx in range(search_width):
            image_segment = image[dy:dy + template_height,
                                  dx:dx + template_width]
            image_mask_segment = image_mask[dy:dy + template_height,
                                            dx:dx + template_width]
            difference_within_tol = uint8_subtract(image_segment, template) \
                                        < tolerance_for_matched_pixels
            # !3rd arg to np.logical_and is output, NOT a 3rd array to compare!
            greyscale_match = np.logical_and(image_mask_segment, template_mask)
            greyscale_in_tol = np.logical_and(greyscale_match,
                                              difference_within_tol)

#==============================================================================
#             print("({},{}): greyscale pixels in tolerance: {}".format(
#                       dy, dx, np.count_nonzero(greyscale_in_tol)) +
#                   ", {}/{} greyscale pixels found".format(
#                       np.count_nonzero(greyscale_match),
#                       num_test_pixels), flush=True)
#==============================================================================

#            if abs(np.count_nonzero(greyscale_in_tol) - num_test_pixels) > 3:
            if np.count_nonzero(greyscale_in_tol) == num_test_pixels:
                matchcoords.append((dy, dx))
                if stop_when_found:
                    return matchcoords
    return matchcoords


# %%
def parse_globe_text(image, rows_to_parse=[1,2,3],
                     tags_to_find=["reserved", "life", "mana", "shield"]):
    """
    Given an image of the text above a life globe, searches up to all 3 rows
    for the tag(s) given (should be in order of rows if possible).
    
    """
    greyscale_tolerance = 7  # out of 255, how much R/G/B can span, ~5 lowish
    try:
        (height, width, ncolors) = image.shape
    except AttributeError:
        raise ValueError("parse_globe_text: needs a 3D numpy ndarray as input")
    if height==62 and width==160:  # 1080p globe text
        templates = TEMPLATES_1080p
        text_rows = [image[0:18,:,:],
                     image[22:40,:,:],
                     image[44:62,:,:]]
    elif height==40 and width==110:  # 720p globe text
        templates = TEMPLATES_720p
        text_rows = [image[0:12,:,:],
                     image[14:26,:,:],
                     image[28:40,:,:]]
    else:
        raise ValueError("image does not match a known globe text format")

    # For each row, get image & mask passing only greyscale pixels
    text_rows_masks = [np.logical_and(np.logical_and(
        uint8_subtract(row[:, :, 0], row[:, :, 1]) < greyscale_tolerance,
        uint8_subtract(row[:, :, 0], row[:, :, 2]) < greyscale_tolerance),
        uint8_subtract(row[:, :, 1], row[:, :, 2]) < greyscale_tolerance)
                       for row in text_rows]
    text_rows = [row[:, :, 0] for row in text_rows] # flatten to greyscale

    # Search each row for list of tags given:
    row_indices_to_parse = [rownum - 1 for rownum in rows_to_parse]
#==============================================================================
#     start_time = time.clock()  # just for testing
#==============================================================================
    search_count = 0

    results = {}
    for count in range(1):  # only for testing
        tags_left_to_find = tags_to_find[:]  # make copy, or changes original!
        for rownum in row_indices_to_parse:
            row = text_rows[rownum]
            row_mask = text_rows_masks[rownum]
            tag_found = False
            result_labels = []
            number_search_areas = []
            number_search_areas_masks = []
            for tag in tags_left_to_find:  # look for a tag in this row
                search_count += 1
#                print("searching for " + tag + " in " + \
#                      "region of size {}".format(row.shape))
                matchcoords = match_template_masked(row, row_mask,
                                                    templates[tag],
                                                    templates[tag + "_mask"],
                                                    stop_when_found=True)
                if len(matchcoords) > 0:  # a tag is found
                    tag_found = True
                    break
            # now zoom in on region after tag
            if tag_found:
#                print('found ' + tag)
                tags_left_to_find.remove(tag)  # don't need to find again

                # Trim down region to only that to right of tag
                # Thankfully numpy does this without moving actual data around
                start_row, start_col = matchcoords[0]
                end_row = start_row + templates[tag].shape[0]
                start_col += templates[tag].shape[1]
                slash_search_area = row[start_row:end_row, start_col:]
                slash_search_area_mask = row_mask[start_row:end_row,
                                                  start_col:]

                # Unless tag is "reserved", time to divide region
                # into each side of slash, and look for numbers in each
                if tag == "reserved":
                    result_labels.append("reserved")
                    number_search_areas.append(slash_search_area)
                    number_search_areas_masks.append(slash_search_area_mask)
                else:
                    search_count += 1
#                    print("searching for slash in " + \
#                          "region of size {}".format(slash_search_area.shape))
                    matchcoords = match_template_masked(
                                                    slash_search_area,
                                                    slash_search_area_mask,
                                                    templates["slash"],
                                                    templates["slash_mask"],
                                                    stop_when_found=True)
                    if len(matchcoords) > 0:  # slash found
                        _, slash_start_col = matchcoords[0]
                        slash_end_col = \
                            slash_start_col + templates["slash"].shape[1]

#                        print('found slash after {} at cols {}-{}'.format(
#                                  tag, slash_start_col, slash_end_col))
                        # left side of slash
                        result_labels.append(tag + "_current")
                        number_search_areas.append(
                            slash_search_area[:, :slash_start_col])
                        number_search_areas_masks.append(
                            slash_search_area_mask[:, :slash_start_col])
                        # right side of slash
                        result_labels.append(tag + "_max")
                        number_search_areas.append(
                            slash_search_area[:, slash_end_col:])
                        number_search_areas_masks.append(
                            slash_search_area_mask[:, slash_end_col:])
            # parse numbers in these zones
            for label, image, image_mask in zip(result_labels,
                                                number_search_areas,
                                                number_search_areas_masks):
                search_count += 1
#                print("searching for {} in region of size {}".format(
#                          label, image.shape))
                numlist = []
                for numeral in range(10):
                    numeral_template = templates[str(numeral)]
                    numeral_template_mask = templates[str(numeral) + "_mask"]
                    matchcoords = match_template_masked(image,
                                                        image_mask,
                                                        numeral_template,
                                                        numeral_template_mask,
                                                        stop_when_found=False)
                    for match_row, match_col in matchcoords:
                        numlist.append([match_row, match_col, str(numeral)])
                numlist.sort(key=lambda tupl: tupl[1])  # sort in place by col
                numberstring = "".join(num for _, _, num in numlist)
                try:
                    results[label] = int(numberstring)
                except ValueError:
                    results[label] = None

#==============================================================================
#     # for testing: display time elapsed
#     time_elapsed = time.clock() - start_time
#     print("{} template matching searches performed".format(search_count) +
#           " with {:.4} seconds elapsed".format(time_elapsed))
#==============================================================================

    return results
