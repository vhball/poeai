# -*- coding: utf-8 -*-
"""
Created on Mon Dec  5 12:50:10 2016

@author: Michael
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import binary_fill_holes
from scipy.spatial import Delaunay, delaunay_plot_2d
from skimage import io
from skimage.transform import downscale_local_mean
from skimage.filters.rank import maximum
from skimage.morphology import disk, binary_closing, binary_erosion, binary_dilation
from sklearn import preprocessing, svm
from skimage import feature
from skimage.color import rgb2grey
from skimage.measure import find_contours, approximate_polygon, \
    subdivide_polygon, points_in_poly, grid_points_in_poly

# %% doorway cutting logic
cut_radius = 15
cut_mask_center = (cut_radius, cut_radius)
cut_mask_shape = (2 * cut_radius + 1, 2 * cut_radius + 1)
left_cut_op = np.array([[-1, -1], [1, 1]])
right_cut_op = np.array([[-1, 1], [1, -1]])
left_cut_pixels = np.array([(x, y - offset)
                            for offset in range(2)
                            for rad in range(cut_radius + 1)
                            for x, y in cut_mask_center + rad * left_cut_op
                            if y - offset >= 0])
right_cut_pixels = np.array([(x, y - offset)
                             for offset in range(2)
                             for rad in range(cut_radius + 1)
                             for x, y in cut_mask_center + rad * right_cut_op
                             if y - offset >= 0])
#left_cut_mask = np.zeros(cut_mask_shape, dtype=np.bool)
#right_cut_mask = np.zeros(cut_mask_shape, dtype=np.bool)
#for x, y in left_cut_pixels:
#    left_cut_mask[x, y] = True
#for x, y in right_cut_pixels:
#    right_cut_mask[x, y] = True

def cut_doorways(is_wall_map, is_yellow_map):
    maxindex = is_wall_map.shape[1]
    for yellow_xy in zip(*is_yellow.nonzero()):  # for each yellow pixel
        # get all pixels that would be cut if cut goes through
        xy_offset = np.array(yellow_xy) - cut_radius
        left_xs, left_ys = zip(*[(x, y)
                                 for x, y in left_cut_pixels + xy_offset
                                 if x >= 0
                                 if y < maxindex])
        right_xs, right_ys = zip(*[(x, y)
                                   for x, y in right_cut_pixels + xy_offset
                                   if x >= 0
                                   if y < maxindex])
        left_wall_pixels = np.count_nonzero(is_wall_map[left_xs, left_ys])
        right_wall_pixels = np.count_nonzero(is_wall_map[right_xs, right_ys])
        if left_wall_pixels > right_wall_pixels:
            is_wall_map[right_xs, right_ys] = False
        else:
            is_wall_map[left_xs, left_ys] = False

def fill_exterior_pixels(is_wall_map, interior_x, interior_y):
    temp_map = is_wall_map.copy()
    temp_map = binary_fill_holes(temp_map)
    is_wall_map[np.logical_not(temp_map)] = True

# %%

#img = io.imread("images\\snapshot__1480963312-2.png")
#img = io.imread("images\\snapshot__1480960173.png")
#img = io.imread("images\\snapshot__1480960724.png")
#img = io.imread("images\\snapshot__1480960836.png")
#img = io.imread("images\\snapshot__1480963312.png")
#img = io.imread("images\\snapshot__1480970830.png")
#img = img[7:7+271, 1642:1642+271, 0:3]

img = io.imread("images\\fake_minimaps\\01.png")
cur_x, cur_y = (260, 220)
img = img[:,:,0:3]

#cur_x, cur_y = (135, 135)
#img = img[cur_y - 135:cur_y + 136,
#          cur_x - 135:cur_x + 136, 0:3]

is_orange = np.logical_and.reduce(abs(img - (255, 90, 0)) <= 20, 2)
is_yellow = np.logical_and.reduce(abs(img - (255, 174, 0)) <= 20, 2)
is_yellow = binary_closing(is_yellow, disk(3))

img2 = img.copy()
img2[is_orange] = (255, 0, 255)
img2[is_yellow] = (0, 0, 255)

greyimg = rgb2grey(img)
edges = feature.canny(greyimg, sigma=1.0)
closed = binary_closing(edges, disk(4))
#eroded = binary_erosion(closed, disk(1))
eroded = binary_dilation(closed, disk(2))
final = eroded.copy()
final[128:143, 128:143] = np.logical_and(final[128:143, 128:143],
                                         np.logical_not(disk(7)))


# extend doorways to form cuts in walls
cut_doorways(final, is_yellow)

# fill all unreachable pixels
fill_exterior_pixels(final, cur_x, cur_y)

#final = np.logical_not(final)  # display _walkable_ pixels
contours = find_contours(final, 0.5, 'low', 'low')
contours = [approximate_polygon(contour, 3.0)
            for contour in contours]
contours = np.array(contours)

# pick most large and/or detailed contour containing our interior point
interior_contours = \
    np.nonzero([bool(points_in_poly([[cur_y, cur_x]], contour))
                for contour in contours])[0]

# %% GRID FROM PIXELS

inside_contour_masks = [grid_points_in_poly(final.shape, contour)
                        for contour in contours]
walkable_masks = np.dstack(inside_contour_masks)
for index in range(len(contours)):
    if index not in interior_contours:
        walkable_masks[:, :, index] = \
            np.logical_not(walkable_masks[:, :, index])
walkable_grid = np.logical_and.reduce(walkable_masks, axis=2)

walkable_grid_small = downscale_local_mean(walkable_grid, (4,4))

plt.imshow(walkable_grid_small == 1.0)


# %% CONTOUR MESHING

#plt.subplot(2,3,1)
#plt.imshow(img, interpolation='nearest')
#plt.subplot(2,3,2)
#plt.imshow(edges, interpolation='nearest')
#plt.subplot(2,3,3)
#plt.imshow(eroded, interpolation='nearest')
#plt.subplot(2,3,4)
#plt.imshow(img2, interpolation='nearest')
#plt.subplot(2,3,5)
#plt.imshow(final, interpolation='nearest')
#axes = plt.subplot(2,3,6)
axes = plt.axes()
plt.imshow(edges)
for contour in contours:
    yvals, xvals = contour.T
    plt.plot(xvals, yvals, 'w:d', markersize=5.0)
axes.axis('tight')
axes.set_aspect('equal')
axes.axis('off')

#mesh_pts = np.vstack(contours)

mesh_pts = contours[interior_contours[0]]
for contour in contours[interior_contours]:
    if len(contour) > len(mesh_pts):
        mesh_pts = contour

yvals, xvals = mesh_pts.T
plt.plot(xvals, yvals, ':wo', markersize=4.0)
tri = Delaunay(mesh_pts)
#delaunay_plot_2d(tri)

delaunay_triangles = mesh_pts[tri.simplices]
delaunay_centers = np.add.reduce(delaunay_triangles, axis=1)/3
in_contour_mask = points_in_poly(delaunay_centers, mesh_pts)
useful_simplices = tri.simplices[in_contour_mask]
useful_triangles = mesh_pts[useful_simplices]

old_pts, old_simplices, old_triangles = \
    mesh_pts, useful_simplices, useful_triangles
for i in range(2):
    # optimize triangles to 
    optimized_mesh_pts = old_pts.copy()
    optimized_simplices = []
    for tri_pts, tri_inds in zip(old_triangles, old_simplices):
        four_pt_triangle = np.vstack([tri_pts, [tri_pts[0]]])  # loop around first point
        diffs = four_pt_triangle[1:4] - four_pt_triangle[0:3]
        lengths = np.sqrt(diffs[:,0]**2 + diffs[:,1]**2)
        sharp_index = (np.argmin(lengths) - 1) % 3
        dull_indices = [(sharp_index + 1) % 3, (sharp_index - 1) % 3]
        # add midpoints of long triangle edges, break triangle into three
        new_mesh_pts = [tri_pts[sharp_index] + 0.5*diffs[sharp_index],
                        tri_pts[sharp_index] - 0.5*diffs[dull_indices[1]]]
        new_mesh_pts_indices = [len(optimized_mesh_pts),
                                len(optimized_mesh_pts) + 1]
        new_simplices = \
            [[tri_inds[sharp_index]] + new_mesh_pts_indices,
             [tri_inds[dull_indices[0]], tri_inds[dull_indices[1]],
              new_mesh_pts_indices[0]],
             [new_mesh_pts_indices[1], new_mesh_pts_indices[0], 
              tri_inds[dull_indices[1]]]]
        optimized_mesh_pts = np.vstack([optimized_mesh_pts, new_mesh_pts])
        optimized_simplices.extend(new_simplices)
    optimized_simplices = np.array(optimized_simplices)
    optimized_triangles = optimized_mesh_pts[optimized_simplices]
    old_pts, old_simplices, old_triangles = \
        optimized_mesh_pts, optimized_simplices, optimized_triangles
optimized_centers = np.add.reduce(optimized_triangles, axis=1)/3
in_contour_mask_2 = points_in_poly(optimized_centers, mesh_pts)  # _old_ contour
optimized_simplices = optimized_simplices[in_contour_mask_2]
optimized_triangles = optimized_mesh_pts[optimized_simplices]

## %%
#plt.subplot(1,2,1)
#plt.plot(*four_pt_triangle.T)
#plt.plot(*optimized_mesh_pts[tri_inds].T, 'd')
#plt.subplot(1,2,2)
#plt.plot(*four_pt_triangle.T)
#plt.plot(*optimized_mesh_pts[tri_inds].T, 'd')
#plt.plot(*optimized_mesh_pts[new_mesh_pts_indices].T, 'd')
#plt.plot(*optimized_mesh_pts[optimized_simplices[-3:]].T, 'b')


for tri_pts in useful_triangles:
    four_pt_triangle = np.vstack([tri_pts, [tri_pts[0]]])  # loop around first point
    yvals, xvals = four_pt_triangle.T
    plt.plot(xvals, yvals, 'b')
for tri_pts in optimized_triangles:
    four_pt_triangle = np.vstack([tri_pts, [tri_pts[0]]])  # loop around first point
    yvals, xvals = four_pt_triangle.T
    plt.plot(xvals, yvals, 'g:')
#plt.plot(*delaunay_centers[in_contour_mask].T, 'bd')  # for delaunay_plot
#plt.plot(*delaunay_centers[np.logical_not(in_contour_mask)].T, 'rd')

# get rid of all triangles enclosing spaces exterior to contour...


