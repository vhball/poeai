# -*- coding: utf-8 -*-
"""
Created on Tue Nov 15 17:50:28 2016

@author: Michael
"""

from skimage.feature import daisy, hog
from skimage import data, io
import matplotlib.pyplot as plt


img = data.camera()[:,:]
directory = "C:\\Users\\Michael\\Source\\Repos\\poeai\\images\\library\\"
img = io.imread(directory + "firing_41.png")[:, :, 0]
fig, ax = plt.subplots()

#==============================================================================
# descs, descs_img = daisy(img, step=40, radius=8, rings=2, histograms=6,
#                          orientations=8, visualize=True)
# descs_num = descs.shape[0] * descs.shape[1]
# ax.set_title('%i DAISY descriptors extracted:' % descs_num)
#==============================================================================

descs, descs_img = hog(img, orientations=9,
                       pixels_per_cell=(10, 10), cells_per_block=(3, 3),
                       visualise=True, transform_sqrt=False,
                       feature_vector=False, normalise=None)



ax.axis('off')
ax.imshow(descs_img)
plt.show()

