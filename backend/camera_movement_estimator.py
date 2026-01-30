import pickle
import cv2
import numpy as np
import os
import sys
sys.path.append('./src/utils')
from src.utils.bbox_utils import get_center_of_bbox

def measure_distance(p1, p2):
    """Measure distance between two points"""
    return ((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)**0.5

def measure_xy_distance(p1, p2):
    """Measure x and y distance between two points"""
    return p1[0] - p2[0], p1[1] - p2[1]

class CameraMovementEstimator:
    def __init__(self, frame):
        self.minimum_distance = 5
        
        # Lucas-Kanade optical flow parameters
        self.lk_params = dict(
            winSize=(15, 15),
            maxLevel=2,
            criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03)
        )
        
        # Create mask for feature detection (edges of frame)
        first_frame_grayscale = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mask_features = np.zeros_like(first_frame_grayscale)
        mask_features[:, 0:20] = 1     # Left edge
        mask_features[:, 900:1050] = 1  # Right edge (adjust based on your video width)
        
        self.features = dict(
            maxCorners=100,
            qualityLevel=0.3,
            minDistance=3,
            blockSize=7,
            mask=mask_features
        )
    
    def add_adjust_positions_to_tracks(self, tracks, camera_movement_per_frame):
        """Adjust track positions based on camera movement"""
        for object_type, object_tracks in tracks.items():
            for frame_num, track in enumerate(object_tracks):
                for track_id, track_info in track.items():
                    position = track_info.get('position')
                    if position is None:
                        continue
                    camera_movement = camera_movement_per_frame[frame_num]
                    position_adjusted = (
                        position[0] - camera_movement[0],
                        position[1] - camera_movement[1]
                    )
                    tracks[object_type][frame_num][track_id]['position_adjusted'] = position_adjusted
    
    def get_camera_movement(self, frames, read_from_stub=False, stub_path=None):
        """Calculate camera movement for each frame"""
        # Read from cache if available
        if read_from_stub and stub_path is not None and os.path.exists(stub_path):
            with open(stub_path, 'rb') as f:
                return pickle.load(f)
        
        camera_movement = [[0, 0]] * len(frames)
        
        old_gray = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY)
        old_features = cv2.goodFeaturesToTrack(old_gray, **self.features)
        
        for frame_num in range(1, len(frames)):
            frame_gray = cv2.cvtColor(frames[frame_num], cv2.COLOR_BGR2GRAY)
            new_features, _, _ = cv2.calcOpticalFlowPyrLK(
                old_gray, frame_gray, old_features, None, **self.lk_params
            )
            
            max_distance = 0
            camera_movement_x, camera_movement_y = 0, 0
            
            if new_features is not None and old_features is not None:
                for i, (new, old) in enumerate(zip(new_features, old_features)):
                    new_features_point = new.ravel()
                    old_features_point = old.ravel()

                    distance = measure_distance(new_features_point, old_features_point)
                    if distance > max_distance:
                        max_distance = distance
                        camera_movement_x, camera_movement_y = measure_xy_distance(
                            old_features_point, new_features_point
                        )
            
            if max_distance > self.minimum_distance:
                camera_movement[frame_num] = [camera_movement_x, camera_movement_y]
                old_features = cv2.goodFeaturesToTrack(frame_gray, **self.features)
            
            old_gray = frame_gray.copy()
        
        # Save to cache
        if stub_path is not None:
            with open(stub_path, 'wb') as f:
                pickle.dump(camera_movement, f)
        
        return camera_movement
    
    def draw_camera_movement(self, frames, camera_movement_per_frame):
        """Draw camera movement information on frames - top right with dark background"""
        output_frames = []
        for frame_num, frame in enumerate(frames):
            frame = frame.copy()
            height, width = frame.shape[:2]

            # Position in top right
            box_width = 350
            box_height = 90
            x_start = width - box_width - 20
            y_start = 20

            overlay = frame.copy()
            # Dark teal/cyan background
            cv2.rectangle(overlay, (x_start, y_start), (x_start + box_width, y_start + box_height), (80, 80, 40), -1)
            alpha = 0.85
            cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

            # Border
            cv2.rectangle(frame, (x_start, y_start), (x_start + box_width, y_start + box_height), (120, 120, 80), 2)

            x_movement, y_movement = camera_movement_per_frame[frame_num]

            # Title
            cv2.putText(
                frame,
                "CAMERA MOVEMENT",
                (x_start + 60, y_start + 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (200, 255, 255),
                2
            )

            # X movement
            cv2.putText(
                frame,
                f"X: {x_movement:+.2f}",
                (x_start + 30, y_start + 55),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )

            # Y movement
            cv2.putText(
                frame,
                f"Y: {y_movement:+.2f}",
                (x_start + 180, y_start + 55),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )

            output_frames.append(frame)

        return output_frames