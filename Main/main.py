import cv2
import numpy as np
import Homography as H_matrix
import cannyedge
import positions as ps
import projectdata as pd
import projection_matrix as pm
import design_shape as ds
import output
import experiments as exp
import sys
import matplotlib.pyplot as plt
import imageio


try:
    sys.path.remove('/opt/ros/kinetic/lib/python2.7/dist-packages')
except:
    pass

def operation():
    video_frames = []
    shape = input("Enter structure Cube, Cuboid, Pyramid")
    shape2 = "pyramid"
    row = col = 512
    frame = cv2.VideoCapture('input/Tag1.mp4')
    response, image = frame.read()
    old_positions = 0
    prev_edge = 0
    flag = 0
    old_frame = None
    while response:
        dims = image.shape
        size = (dims[1], dims[0])

        # Edge detection process
        grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blur_grayscale = cv2.GaussianBlur(grayscale, (3, 3), cv2.BORDER_DEFAULT)



        # threshold and find the contours.
        # Contours can be explained simply as a curve joining
        # all the continuous points (along the boundary), having same color or intensity.
        #edge = cannyedge.canny_edge_detection(image).astype(np.uint8)
        edge1 = cv2.Canny(image, 60, 180)

        if old_frame is not None:
            diff_frame = cv2.absdiff(edge1, old_frame)
            if prev_edge == 0:
                #cv2.imshow('edge',edge1)
                #cv2.imshow('diff', diff_frame)
                #cv2.waitKey(0)
                cv2.imshow('thresh', thresh)
                prev_edge = 1
            diff_frame -= diff_frame.min()
            diff_frame = np.uint8(255.0 * diff_frame / float(diff_frame.max()))


        old_frame = None


        #ret, edge2 = cv2.threshold(edge, 165, 255, cv2.THRESH_BINARY)

        ret, thresh = cv2.threshold(blur_grayscale, 165, 255, cv2.THRESH_BINARY)
        #contours, hierarchy = cv2.findContours(edge, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        #cv2.imshow('thresh', thresh)
        #cv2.waitKey(0)
        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)


        corners = corners_identification(hierarchy, contours)

        if len(corners) == 0:
            corners = old_positions
        if flag == 0:
            print(corners)
            flag = 1

        # Get the homography of the tag
        tag_img_resized = calculate_homography_wrap(corners, image)


        new_corners, tag_val = ps.get_tag_positions(corners, tag_img_resized)
        source = np.array([[0, 0], [row - 1, 0], [row - 1, col - 1], [0, col - 1]])
        destination = np.concatenate(new_corners)
        new_homography_matrix = H_matrix.homography(source, destination)

        project_matrix = pm.projection_matrix(new_homography_matrix)
        cube1, cube2 = exp.design_shape(shape, shape2, project_matrix)
        image = exp.impose_cube(image, cube1, cube2)

        old_positions = corners
        video_frames.append(image)
        response, image = frame.read()
    return video_frames, size


def corners_identification(hierarchy, contours):
    contours_points = []
    for a, data in zip(hierarchy[0], contours):
        epsilon = cv2.arcLength(data, True) * 0.05
        data = cv2.approxPolyDP(data, epsilon, True)
        if cv2.contourArea(data) > 1000 and cv2.isContourConvex(data) and len(data) == 4:
            data = data.reshape(-1, 2)
            if a[0] == -1 and a[1] == -1 and a[3] != -1:
                contours_points.append(data)

    return contours_points


def calculate_homography_wrap(corners, image):
    tag_dest = np.array([[0, 0], [100, 0], [100, 100], [0, 100]], dtype="float32")
    homography_matrix = H_matrix.homography(corners[0], tag_dest)
    warp1 = cv2.warpPerspective(image.copy(), homography_matrix, (100, 100))
    warp1_blur = cv2.GaussianBlur(warp1, (3, 3), cv2.BORDER_DEFAULT)
    tag_img_resized = cv2.resize(warp1_blur, dsize=None, fx=0.08, fy=0.08)
    return tag_img_resized

if __name__ == "__main__":
    frames, size = operation()
    output.create_video(frames, size)