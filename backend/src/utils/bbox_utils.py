import cv2
import numpy as np

def get_center_of_bbox(bbox):
    """Get center point of bounding box"""
    x1, y1, x2, y2 = bbox
    center_x = int((x1 + x2) / 2)
    center_y = int((y1 + y2) / 2)
    return center_x, center_y

def get_bbox_width(bbox):
    """Get width of bounding box"""
    return bbox[2] - bbox[0]

def get_bbox_height(bbox):
    """Get height of bounding box"""
    return bbox[3] - bbox[1]

def get_foot_position(bbox):
    """Get foot position (bottom center) of bounding box"""
    center_x = int((bbox[0] + bbox[2]) / 2)
    foot_y = int(bbox[3])
    return center_x, foot_y