# -*- coding: utf-8 -*-
"""
Created on Tue Nov  1 19:44:30 2016

@author: Michael
"""

import numpy as np
import matplotlib.pyplot as plt
from skimage import io
from skimage.transform import downscale_local_mean
from skimage.filters.rank import maximum
from skimage.morphology import disk
from sklearn import preprocessing, svm
#from skimage.color import rgb2grey
#from skimage.morphology import disk
#from skimage.feature import canny
#from skimage.filters import rank
#from skimage.filters import roberts, sobel, scharr, prewitt
#
#from skimage.filters import threshold_adaptive

RED_THRESHOLD = 40
COLOR_DICT = {"garbage": 'b.', "firing": 'r.'}
FEATURE_DICT = {0: "redimgmax",
                1: "redimgmean",
                2: "fracredpixels",
                3: "ratio_red",
                4: "ration_green",
                5: "ratio_blue",
                6: "redarea_mean_red",
                7: "redarea_mean_green",
                8: "redarea_mean_blue",
                9: "notredarea_mean_red",
                10: "notredarea_mean_green",
                11: "notredarea_mean_blue"}

def feature_vector_fcn(image, redness_image):
    redimgmax = np.max(redness_image)
    redimgmean = np.mean(redness_image)

    red_indices = redness_image > RED_THRESHOLD
    numredpixels = np.count_nonzero(red_indices)
    fracredpixels = numredpixels/redness_image.size
    notred_indices = np.logical_not(red_indices)
    if len(red_indices.nonzero()[0]) > 0:
        if len(notred_indices.nonzero()[0]) > 0:
            redcropimgmean_red = \
                np.mean(image.__getitem__([*red_indices.nonzero(), 0]))
            redcropimgmean_green = \
                np.mean(image.__getitem__([*red_indices.nonzero(), 1]))
            redcropimgmean_blue = \
                np.mean(image.__getitem__([*red_indices.nonzero(), 2]))
            notredcropimgmean_red = \
                np.mean(image.__getitem__([*notred_indices.nonzero(), 0]))
            notredcropimgmean_green = \
                np.mean(image.__getitem__([*notred_indices.nonzero(), 1]))
            notredcropimgmean_blue = \
                np.mean(image.__getitem__([*notred_indices.nonzero(), 2]))
    else:
        redcropimgmean_red, notredcropimgmean_red, \
            redcropimgmean_green, notredcropimgmean_green, \
            redcropimgmean_blue, notredcropimgmean_blue = (1, 1, 1, 1, 1, 1)
#    redvsnotred_ratio_red = redcropimgmean_red / (notredcropimgmean_red + .00001)
#    redvsnotred_ratio_green = redcropimgmean_green / (notredcropimgmean_green + .00001)
#    redvsnotred_ratio_blue = redcropimgmean_blue / (notredcropimgmean_blue + .00001)

    features = []
    features.append(redimgmax/255.0)
    features.append(redimgmean/255.0)
    features.append(fracredpixels)
    features.append(redcropimgmean_red/255.0)
    features.append(redcropimgmean_green/255.0)
    features.append(redcropimgmean_blue/255.0)
    features.append(notredcropimgmean_red/255.0)
    features.append(notredcropimgmean_green/255.0)
    features.append(notredcropimgmean_blue/255.0)
#    features.append(np.log(redvsnotred_ratio_red))  # can get log(zero)
#    features.append(np.log(redvsnotred_ratio_green))
#    features.append(np.log(redvsnotred_ratio_blue))
    return features

def get_redness_image(raw_image,
                      rgb_coeffs=[1.0, 2.5, 0.4],
                      rgb_offset=8,
                      threshold_offset=0.8):
    r_coeff, g_coeff, b_coeff = rgb_coeffs
    rg_coeff, rb_coeff = [g_coeff/r_coeff, b_coeff/r_coeff]
    image = raw_image.astype(float, copy=True) + rgb_offset
    new_image = (1.0 + threshold_offset +
                 (-rg_coeff*image[:,:,1])/image[:,:,0] +
                 (-rb_coeff*image[:,:,2])/image[:,:,0])
    upper_bound = np.mean(rgb_coeffs) + threshold_offset
    new_image *= ((1.0 + rgb_offset/255) / upper_bound)
    if np.min(new_image) <= 0.0:  # clip to max/min bounds if needed
        new_image[new_image <= 0.0] = 0.0
    if np.max(new_image) > 1.0:
        new_image[new_image > 1.0] = 1.0
#    new_image = 255.0*np.sqrt(new_image)
    new_image = 255.0*new_image
    new_image = new_image.astype(np.uint8)
    return new_image


def plot_feature_vector_list_2d(img_fvecs, img_cats,
                                category_list, axis1=0, axis2=1):
    plt.hold(True)
    for fvec, category in zip(img_fvecs, img_cats):
        plt.plot([fvec[axis1]], [fvec[axis2]], COLOR_DICT[category])

def plot_processed_images(plot_image_indices,
                          imgs, redness_imgs, red_cropped_imgs):
    nimgs = len(plot_image_indices)
    row_plot_inds = lambda row: [3*row + col for col in range(1, 4)]
    plt.subplot(nimgs, 3, 1)
    plt.title("image", {'fontsize': 20})
    plt.subplot(nimgs, 3, 2)
    plt.title("'reddishness'", {'fontsize': 20})
    plt.subplot(nimgs, 3, 3)
    plt.title("image", {'fontsize': 20})
    for row in range(nimgs):
        col1ind, col2ind, col3ind = row_plot_inds(row)
        plt.subplot(nimgs, 3, col1ind)
        plt.imshow(imgs[plot_image_indices[row]])
        plt.subplot(nimgs, 3, col2ind)
        plt.imshow(redness_imgs[plot_image_indices[row]])
        plt.colorbar()
        plt.subplot(nimgs, 3, col3ind)
        plt.imshow(red_cropped_imgs[plot_image_indices[row]])   

#
#note to self:
#
#whenever I add lists by [] + [], replace by [].extend([])

# %%
red_threshold = RED_THRESHOLD
categories = ["garbage", "firing"]

imgs = []
img_indices = []
img_categories = []
directory = "C:\\Users\\Michael\\Source\\Repos\\poeai\\images\\library\\"

for category in categories:
    failcount = 0
    for img_ind in range(9999):
        filename = "{}_{}.png".format(category, img_ind)
        filepath = directory + filename
        try:
            imgs.append(io.imread(filepath))
#            raw_imgs.append(io.imread(filepath).astype(float))
            img_indices.append(img_ind)
            img_categories.append(category)
        except IOError as e:
            failcount += 1
        if failcount > 200:
            break  # if fail many times in row, probably done now

# resize dimensions by factor of 2
orig_imgs = imgs
imgs = [downscale_local_mean(img, (2, 2, 1)).astype(np.uint8)
        for img in imgs]

redness_imgs = [get_redness_image(img,
                                  rgb_coeffs=[1.0, 2.0, 0.5],
                                  rgb_offset=16,
                                  threshold_offset=0.2)
                for img in imgs]

redness_imgs = [maximum(redness_img, disk(2))
                for redness_img in redness_imgs]

red_cropped_imgs = [img.copy() for img in imgs]
notred_cropped_imgs = [img.copy() for img in imgs]
for redimg, notredimg, redness_img in \
        zip(red_cropped_imgs, notred_cropped_imgs, redness_imgs):
    red_indices = \
        np.outer(redness_img > RED_THRESHOLD,  # note: more lenient after sqrt
                 np.array([True, True, True])).reshape(*redness_img.shape, 3)
    notred_indices = np.logical_not(red_indices)
    redimg[notred_indices] = 0
    notredimg[red_indices] = 0

img_feature_vectors = [feature_vector_fcn(*imgset)
                       for imgset in zip(imgs, redness_imgs)]

#img_feature_vectors = [np.hstack((img.flatten(), redness_img.flatten()))
#                       for img, redness_img in zip(imgs, redness_imgs)]

test_results = []  # for running next code block many times
# %%
testing = True
show_testing_images = True
testing_image_class = "all"
image_max = 40

# Shuffle and copy data
map_to_disordered = np.random.permutation(len(img_feature_vectors))
map_to_reordered = map_to_disordered.argsort()
X = np.array([vec[:]
             for vec in np.array(img_feature_vectors)[map_to_disordered]])
y = np.array([1 if cat=="firing" else 0
             for cat in np.array(img_categories)[map_to_disordered]])

# find anomalous vals (or at least NaNs) and set to 0.0
# pipeline in future?

vec_list = []
ind_list = []
val_list = []
for x_i, x in enumerate(X):
    found = False
    for v_i, val in enumerate(x):
        if np.isnan(val) or np.isinf(val):
            ind_list.append(v_i)
            val_list.append(val)
            found = True
    if found:
        vec_list.append(x_i)

# use anomaly list 
for vec_ind in vec_list:
    vector = X[vec_ind]
    for val_ind in ind_list:
        vector[val_ind] = 0.0

# rescale data intelligently:
scaler = preprocessing.StandardScaler().fit(X)
X = scaler.transform(X)
fvecs = [img_feature_vectors[ind][:]  # unscaled copy in new ordering
         for ind in map_to_disordered]


# separate training vs testing data:
n_training_samples = np.uint16(70.0*len(X)/100.0)
X_training = X[0:n_training_samples]
y_training = y[0:n_training_samples]
X_testing = X[n_training_samples:]
y_testing = y[n_training_samples:]
testing_fvecs = fvecs[n_training_samples:]
testing_imgs = np.array(orig_imgs)[map_to_disordered][n_training_samples:]
testing_redimgs = np.array(redness_imgs)[map_to_disordered][n_training_samples:]

# fit and test!
estimator = svm.SVC(gamma=0.01,
                    C=100.,
                    kernel='rbf',
                    class_weight={0: 0.5, 1: 1.0})
if testing:
    estimator.fit(X_training, y_training)
    y_estimates = estimator.predict(X_testing)
    all_results = np.argwhere(np.logical_and(y_estimates > -1,  # just bein cheeky
                                             y_testing > -1))
    true_negatives = np.argwhere(np.logical_and(y_estimates == 0,
                                                y_testing == 0))
    true_positives = np.argwhere(np.logical_and(y_estimates == 1,
                                                y_testing == 1))
    false_negatives = np.argwhere(np.logical_and(y_estimates == 0,
                                                 y_testing == 1))
    false_positives = np.argwhere(np.logical_and(y_estimates == 1,
                                                 y_testing == 0))
    correct = np.argwhere(y_estimates == y_testing)
    incorrect = np.argwhere(y_estimates != y_testing)
    positive = np.argwhere(y_testing == 1)
    negative = np.argwhere(y_testing == 0)
    indices_by_class = {"all": all_results[:],
                        "true_negatives": true_negatives[:],
                        "true_positives": true_positives[:],
                        "false_negatives": false_negatives[:],
                        "false_positives": false_positives[:],
                        "correct": correct[:],
                        "incorrect": incorrect[:],
                        "positive": positive[:],
                        "negative": negative[:]}
    percent_correct = 100*len(correct)/len(y_testing)
    print("success rate: {:.2f}%".format(
                100 * len(correct) / len(y_testing)))
    print("false negative rate: {:.2f}% of true positives".format(
                100 * len(false_negatives) / len(positive)))
    print("true positive rate: {:.2f}% of true positives".format(
                100 * len(true_positives) / len(positive)))
    print("false positive rate: {:.2f}% of true negatives".format(
                100 * len(false_positives) / len(negative)))
    print("true negative rate: {:.2f}% of true negatives".format(
                100 * len(true_negatives) / len(negative)))
    test_results.append(percent_correct)
    if show_testing_images:
        indices_list = indices_by_class[testing_image_class]
        shown_image_count = min(len(indices_list), image_max)
        plt.figure()
        nrows = int(np.ceil(0.76 * np.sqrt(shown_image_count)))  # ~16:9
        ncols = int(np.floor(1.32 * np.sqrt(shown_image_count))) + 1
        # want an int, not a 1-elem array
        for ind_ind in range(shown_image_count):
            ind = indices_list[ind_ind, 0]
            img = testing_imgs[ind]
            redimg = testing_redimgs[ind]
            actual = y_testing[ind]
            guess = y_estimates[ind]
            axes = plt.subplot(nrows, ncols, ind_ind + 1)
            fvec = testing_fvecs[ind]
            plt.imshow(redimg)
            if ind in true_negatives:
                plt.title("Correct: False", fontdict={'color': 'g'})
                plt.xlabel(str(fvec[2]))
            elif ind in true_positives:
                plt.title("Correct: True", fontdict={'color': 'g'})
                plt.xlabel(str(fvec[2]))
            elif ind in false_negatives:
                plt.title("False Negative", fontdict={'color': 'r'})
                plt.xlabel(str(fvec[2]))
            elif ind in false_positives:
                plt.title("False Positive", fontdict={'color': 'r'})
                plt.xlabel(str(fvec[2]))
            axes.xaxis.set_ticks([])
            axes.yaxis.set_ticks([])
else:
    estimator.fit(X, y)


# %%
plt.figure()
plot_image_names = ["garbage_200", "garbage_52", "garbage_309",
                    "firing_41", "firing_15", "firing_119"]
plot_image_indices = []
for image_name in plot_image_names:
    plot_img_cat, plot_img_ind = image_name.split("_")
    plot_img_ind = int(plot_img_ind)
    for img_ind in range(len(imgs)):
        if img_indices[img_ind] == plot_img_ind:
            if img_categories[img_ind] == plot_img_cat:
                plot_image_indices.append(img_ind)
plot_processed_images(plot_image_indices,
                      imgs, redness_imgs, red_cropped_imgs)

# %%
m = 0  # feature # start
n = 6  # feature # end
for i in range(m, n):
    for j in range(m, i + 1):
        axes = plt.subplot(n-m, n-m, (n-m)*(i-m) + (j-m) + 1)
        feature1ind = j
        feature2ind = i
        plot_feature_vector_list_2d(img_feature_vectors,
                                    img_categories, categories,
                                    feature1ind, feature2ind)
        axes.xaxis.set_ticks([])
        axes.yaxis.set_ticks([])
        if i == n - 1: axes.xaxis.set_label_text(FEATURE_DICT[feature1ind],
                                                 {'fontsize': 14})
        if j == m: axes.yaxis.set_label_text(FEATURE_DICT[feature2ind],
                                             {'fontsize': 14})


# %%

#plt.subplot(1,3,1)
#plt.imshow(img, interpolation="None")
#plt.subplot(1,3,2)
#plt.imshow(imgs[0], interpolation="None")
#plt.title(str(features[0]))
#plt.subplot(1,3,3)
#plt.imshow(imgs[1], interpolation="None")
#plt.title(str(features[1]))





##
#img2 = rgb2grey(img1)
#
#selem = disk(1)
#img3 = rank.mean(img2, selem=selem)
##img3 = img2
#
#img4 = canny(img3, sigma=0.5)
##img4 = canny(img3)
##img4 = canny(img3)
#
##img5 = canny(img4)
#
#plt.subplot(1,3,1)
#plt.imshow(img1, interpolation="None")
#plt.subplot(1,3,2)
#plt.imshow(img3, interpolation="None")
#plt.subplot(1,3,3)
#plt.imshow(img4, interpolation="None")
#
#
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