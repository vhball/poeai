# -*- coding: utf-8 -*-
"""
Created on Mon Dec  5 12:50:10 2016

@author: Michael
"""

import numpy as np
import matplotlib.pyplot as plt
from skimage import io
from skimage.transform import downscale_local_mean
from skimage.filters.rank import maximum
from skimage.morphology import disk, binary_closing, binary_erosion
from sklearn import preprocessing, svm
from skimage import feature
from skimage.color import rgb2grey

# %%

#img = io.imread("images\\snapshot__1480963312-2.png")
#img = io.imread("images\\snapshot__1480960173.png")
#img = io.imread("images\\snapshot__1480960724.png")
#img = io.imread("images\\snapshot__1480960836.png")
#img = io.imread("images\\snapshot__1480963312.png")
img = io.imread("images\\snapshot__1480970830.png")

img = img[7:7+271, 1642:1642+271, 0:3]

is_orange = np.logical_and.reduce(abs(img - (255, 90, 0)) <= 20, 2)
is_yellow = np.logical_and.reduce(abs(img - (255, 174, 0)) <= 20, 2)
is_yellow = binary_erosion(is_yellow, disk(2))
for x, y in zip(*is_yellow.nonzero()):
    for i in range(15):
        is_yellow[x + i, y + i] = True
        is_yellow[x + i, y - i] = True
        is_yellow[x - i, y + i] = True
        is_yellow[x - i, y - i] = True
        is_yellow[x + i + 1, y + i] = True
        is_yellow[x + i + 1, y - i] = True
        is_yellow[x - i + 1, y + i] = True
        is_yellow[x - i + 1, y - i] = True
is_yellow[128:143, 128:143] = np.logical_or(is_yellow[128:143, 128:143],
                                            disk(7))
img2 = img.copy()
img2[is_orange] = (255, 0, 255)
img2[is_yellow] = (255, 255, 255)

greyimg = rgb2grey(img)
edges = feature.canny(greyimg, sigma=1.0)
closed = binary_closing(edges, disk(4))
eroded = binary_erosion(closed, disk(1))
final = eroded.copy()
final[is_yellow] = False

plt.subplot(2,3,1)
plt.imshow(img, interpolation='nearest')
plt.subplot(2,3,2)
plt.imshow(edges, interpolation='nearest')
plt.subplot(2,3,3)
plt.imshow(eroded, interpolation='nearest')
plt.subplot(2,3,4)
plt.imshow(img2, interpolation='nearest')
plt.subplot(2,3,5)
plt.imshow(final, interpolation='nearest')


