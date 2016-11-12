# -*- coding: utf-8 -*-
"""
Created on Tue Nov  1 19:44:30 2016

@author: Michael
"""

import numpy as np
import matplotlib.pyplot as plt
from skimage import io
from skimage.color import rgb2grey
from skimage.morphology import disk
from skimage.feature import canny
from skimage.filters import rank
from skimage.filters import roberts, sobel, scharr, prewitt

from skimage.filters import threshold_adaptive

directory = "C:\\Users\\Michael\\Source\\Repos\\poeai\\images\\"
img1 = io.imread(directory + "siegeballista_screenbottom.png")

img2 = rgb2grey(img1)

selem = disk(1)
img3 = rank.mean(img2, selem=selem)
#img3 = img2

img4 = canny(img3, sigma=0.5)
#img4 = canny(img3)
#img4 = canny(img3)

#img5 = canny(img4)

plt.subplot(1,3,1)
plt.imshow(img1, interpolation="None")
plt.subplot(1,3,2)
plt.imshow(img3, interpolation="None")
plt.subplot(1,3,3)
plt.imshow(img4, interpolation="None")


#thresh = threshold_adaptive(img2, block_size=51)
#binary = img2 > thresh
#
#fig, axes = plt.subplots(ncols=2, figsize=(8, 3))
#ax = axes.ravel()
#
#ax[0].imshow(img2, cmap=plt.cm.gray)
#ax[0].set_title('Original image')
#
#ax[1].imshow(binary, cmap=plt.cm.gray)
#ax[1].set_title('Result')
#
#for a in ax:
#    a.axis('off')
#
#plt.show()