import numpy as np
import cv2

class ViewTransformer:
    def __init__(self, frame_width=1920, frame_height=1080):
        # Court dimensions in meters (standard soccer field visible portion)
        court_width = 68
        court_length = 105

        # Use the full frame as the pixel vertices for maximum coverage
        # These define the corners of the visible field area
        # Adjust these based on your specific video/camera angle
        self.pixel_vertices = np.array([
            [0, frame_height],           # Bottom-left
            [0, 0],                       # Top-left
            [frame_width, 0],             # Top-right
            [frame_width, frame_height]   # Bottom-right
        ])

        self.target_vertices = np.array([
            [0, court_width],
            [0, 0],
            [court_length, 0],
            [court_length, court_width]
        ])

        self.pixel_vertices = self.pixel_vertices.astype(np.float32)
        self.target_vertices = self.target_vertices.astype(np.float32)

        self.perspective_transformer = cv2.getPerspectiveTransform(
            self.pixel_vertices, self.target_vertices
        )

    def transform_point(self, point):
        # Transform all points without polygon check
        # This gives approximate real-world coordinates for all positions
        try:
            reshaped_point = np.array(point).reshape(-1, 1, 2).astype(np.float32)
            transformed_point = cv2.perspectiveTransform(
                reshaped_point, self.perspective_transformer
            )
            return transformed_point.reshape(-1, 2)
        except:
            return None

    def add_transformed_position_to_tracks(self, tracks):
        for object_type, object_tracks in tracks.items():
            for frame_num, track in enumerate(object_tracks):
                for track_id, track_info in track.items():
                    position = track_info.get('position_adjusted')
                    if position is None:
                        position = track_info.get('position')
                    if position is None:
                        tracks[object_type][frame_num][track_id]['position_transformed'] = None
                        continue

                    position = np.array(position)
                    position_transformed = self.transform_point(position)
                    if position_transformed is not None:
                        position_transformed = position_transformed.squeeze().tolist()
                    tracks[object_type][frame_num][track_id]['position_transformed'] = position_transformed
