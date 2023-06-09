#!/usr/bin/env python
# coding: utf-8

# In[626]:


import numpy as np
import cv2
import os


# In[627]:


def draw_tracks(frame_num, frame, mask, points_prev, points_curr, color, folder_path):
    """Draw the tracks and create an image.
    """
    for i, (p_prev, p_curr) in enumerate(zip(points_prev, points_curr)):
        a, b = p_curr.ravel()
        c, d = p_prev.ravel()
        mask = cv2.line(mask, (round(a), round(b)), (round(c), round(d)), color[i].tolist(), 2)
        frame = cv2.circle(
            frame, (round(a), round(b)), 3, color[i].tolist(), -1)

    img = cv2.add(frame, mask)

    cv2.imwrite(os.path.join(folder_path, 'frame_%02d.png'% frame_num), img)
    return img


# In[628]:


def Q5_A(folder_path):
    """Code for question 5a.

    Output:
      [p0, p1, p2, ... p9] : a list of (N,2) numpy arrays representing the
      pixel coordinates of the tracked features. Include the visualization
      and your answer to the questions in the separate PDF.
    """
    # params for ShiTomasi corner detection
    feature_params = dict(
        maxCorners=200,
        qualityLevel=0.01,
        minDistance=7,
        blockSize=7)

    # Parameters for lucas kanade optical flow
    lk_params = dict(
        winSize=(75, 75),
        maxLevel=1,
        criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 100, 0.01),
        flags=(cv2.OPTFLOW_LK_GET_MIN_EIGENVALS))

    # Read the frames.
    frames = []
    for i in range(1, 11):
        frame_path = os.path.join(folder_path, 'rgb%02d.png' % i)
        frames.append(cv2.imread(frame_path))

    # Convert to gray images.
    old_frame = frames[0]
    old_gray = cv2.cvtColor(old_frame, cv2.COLOR_BGR2GRAY)
    p0 = cv2.goodFeaturesToTrack(old_gray, mask=None, **feature_params)
    print("number of features to track:", len(p0))
    assert len(p0) <= 200

    # Create some random colors for drawing
    color = np.random.randint(0, 255, (200, 3))

    # Create a mask image for drawing purposes
    mask = np.zeros_like(old_frame)

    tracks = []

    for i,frame in enumerate(frames[1:]):
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # TODO: Fill in this code
        # BEGIN YOUR CODE HERE
        p1, str, err = cv2.calcOpticalFlowPyrLK(old_gray, frame_gray, p0, None, **lk_params)
        # print(p1)
        # print(str)
        # print(err)
        if p1 is not None:
            previous_value = p0[str == 1]
            present_value = p1[str == 1]
        if i ==0:
            tracks.append(previous_value)
        tracks.append(present_value)
        old_gray = frame_gray.copy()
        p0 = present_value.reshape(-1, 1, 2)
        
        #Once you compute the new feature points for this frame, comment this out
        #to save images for your PDF:
        draw_tracks(i, frame, mask, previous_value, present_value, color, folder_path)
        # END YOUR CODE HERE

    return tracks


# In[629]:


def Q5_B(pts, intrinsic, folder_path):
    """Code for question 5b.

    Note that depth maps contain NaN values.
    Features that have NaN depth value in any of the frames should be excluded
    in the result.

    Input:
      pts: a list of (N,2) numpy arrays, the results from Q5_A.
      intrinsic: (3,3) numpy array representing the camera intrinsic.

    Output:
      pts_3d: a list of (N,3) numpy arrays, the 3D positions of the tracked features in each frame.
      in each frame.
    """
    depth_all = []
    for i in range(1, 11):
        depth_filepath = os.path.join(folder_path, 'depth%02d.txt' % i)
        depth_i = np.loadtxt(depth_filepath)
        depth_all.append(depth_i)
        
    pt_3d_frames = []
    # TODO: Fill in this code
    # BEGIN YOUR CODE HERE
    final_depth = []

    remove_index = []
    lst = []
    K_inv = np.linalg.inv(intrinsic)
    for i, frame in enumerate(pts):
        points_2D = frame
        one_col = np.ones(frame.shape[0])
        points_2D_hom = np.column_stack((points_2D, one_col))
        points_3D = K_inv.dot(points_2D_hom.T).T

        lst.append(points_3D)
        depth_given_frame = []
        for j, pt in enumerate(pts[i]):
            x, y = pt
            depth = depth_all[i][int(y), int(x)]
            if np.isnan(depth) and j not in remove_index:
                remove_index.append(j)
    
    final_pts = pts
    pt_3d_frames = lst
    
    print("Before deletion:", pt_3d_frames[0].shape)
    for i, frame in enumerate(final_pts):
        #for index in remove_index:
        final_pts[i] = np.delete(frame, remove_index, axis=0)
        pt_3d_frames[i] = np.delete(pt_3d_frames[i], remove_index, axis=0)
    
    print("After deletion", pt_3d_frames[0].shape)
    
    for i, frame in enumerate(pts):
        for j, pt in enumerate(frame):
            if pt in final_pts[i]:
                depth = depth_all[i][int(pt[1]), int(pt[0])]
                pt_3d_frames[i][j] *= depth
    # END YOUR CODE HERE

    return pt_3d_frames


# In[630]:


def dense_flow(frame1, frame2, title=None):
    prvs = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    hsv = np.zeros_like(frame1)
    hsv[..., 1] = 255

    next_frame = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
    # computing flow using FlowFarneback
    flow = cv2.calcOpticalFlowFarneback(prvs, next_frame, None, 0.5, 3, 15, 3, 5, 1.2, 0)
    # getting cart to polar coordinates
    mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
    hsv[..., 0] = ang*180/np.pi/2
    hsv[..., 2] = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX)
    bgr = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    cv2.imwrite(f'farneback-{title}.png', bgr)
    print("saved HSV optical flow")


# In[631]:


if __name__ == "__main__":
    # Q5 part(a)
    pts = Q5_A(folder_path="./p5_data/globe1/")
    intrinsic = np.array([[486, 0, 318.5],
                          [0, 491, 237],
                          [0, 0, 1]])

    # Q5 part(b)
    pts_3d = Q5_B(pts, intrinsic, folder_path="./p5_data/globe1/")

    # Q5 part(c) (tracking for books)
    pts_book = Q5_A(folder_path="./p5_data/book/")

    # Q5 part(d)
    frame1 = cv2.imread('p5_data/chairs/frame_1_chairs.png')
    frame2 = cv2.imread('p5_data/chairs/frame_2_chairs.png')
    dense_flow(frame1, frame2, title="chairs")
    frame1 = cv2.imread('p5_data/globe1/rgb04.png')
    frame2 = cv2.imread('p5_data/globe1/rgb05.png')
    dense_flow(frame1, frame2, title="globe")
    frame1 = cv2.imread('p5_data/globe2/rgb01.png')
    frame2 = cv2.imread('p5_data/globe2/rgb02.png')
    dense_flow(frame1, frame2, title="globe2")


# In[ ]:




