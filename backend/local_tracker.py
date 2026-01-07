from ultralytics import YOLO
import supervision as sv
import pickle
import os
import numpy as np
import pandas as pd
import cv2
import sys
sys.path.append('./src/utils')
from src.utils.bbox_utils import get_center_of_bbox, get_bbox_width, get_foot_position
from team_assigner import TeamAssigner

class LocalTracker:
    def __init__(self, model_path="yolov8s.pt"):
        # Load YOLOv8 model locally (NO API calls!)
        print(f"Loading local YOLOv8 model: {model_path}")
        self.model = YOLO(model_path)
        print(f"Model device: {self.model.device}")
        
        # Initialize ByteTrack
        self.tracker = sv.ByteTrack()
        
        # Initialize team assigner
        self.team_assigner = TeamAssigner()

    def add_position_to_tracks(self, tracks):
        """Add position information to tracking data"""
        for object_type, object_tracks in tracks.items():
            for frame_num, track in enumerate(object_tracks):
                for track_id, track_info in track.items():
                    bbox = track_info['bbox']
                    if object_type == 'ball':
                        position = get_center_of_bbox(bbox)
                    else:
                        position = get_foot_position(bbox)
                    tracks[object_type][frame_num][track_id]['position'] = position

    def interpolate_ball_positions(self, ball_positions):
        """Interpolate missing ball positions"""
        ball_positions = [x.get(1, {}).get('bbox', []) for x in ball_positions]
        df_ball_positions = pd.DataFrame(ball_positions, columns=['x1', 'y1', 'x2', 'y2'])

        # Interpolate missing values
        df_ball_positions = df_ball_positions.interpolate()
        df_ball_positions = df_ball_positions.bfill()

        ball_positions = [{1: {"bbox": x}} for x in df_ball_positions.to_numpy().tolist()]
        return ball_positions

    def detect_frames(self, frames):
        """Detect objects using local YOLOv8 - FAST batch processing"""
        print(f"Running YOLOv8 inference on {len(frames)} frames...")
        
        # Process in batches for speed (like the fast project)
        batch_size = 20
        all_detections = []
        
        for i in range(0, len(frames), batch_size):
            batch_frames = frames[i:i+batch_size]
            
            # Run YOLOv8 on batch (NO API calls, pure local inference)
            results = self.model.predict(batch_frames, conf=0.1, verbose=False)
            
            # Convert YOLOv8 results to our format
            for result in results:
                frame_detections = []
                
                if result.boxes is not None:
                    boxes = result.boxes.xyxy.cpu().numpy()  # [x1, y1, x2, y2]
                    confidences = result.boxes.conf.cpu().numpy()
                    class_ids = result.boxes.cls.cpu().numpy()
                    
                    # Map COCO classes to our classes
                    # COCO: 0=person, 32=sports ball
                    for box, conf, cls_id in zip(boxes, confidences, class_ids):
                        if cls_id == 0:  # person
                            frame_detections.append({
                                'bbox': box.tolist(),
                                'class': 'player',
                                'confidence': float(conf)
                            })
                        elif cls_id == 32:  # sports ball
                            frame_detections.append({
                                'bbox': box.tolist(),
                                'class': 'ball', 
                                'confidence': float(conf)
                            })
                
                all_detections.append(frame_detections)
            
            print(f"Processed batch {i//batch_size + 1}/{(len(frames) + batch_size - 1)//batch_size}")
        
        print(f"YOLOv8 inference complete!")
        return all_detections

    def get_object_tracks(self, frames, read_from_stub=False, stub_path=None):
        """Get tracking data for all objects"""
        
        if read_from_stub and stub_path is not None and os.path.exists(stub_path):
            print(f"Loading cached results from: {stub_path}")
            with open(stub_path, 'rb') as f:
                tracks = pickle.load(f)
            return tracks

        # Run local YOLOv8 detection
        detections = self.detect_frames(frames)

        tracks = {
            "players": [],
            "referees": [], 
            "ball": []
        }

        print("Converting detections to tracks...")
        for frame_num, frame_detections in enumerate(detections):
            tracks["players"].append({})
            tracks["referees"].append({})
            tracks["ball"].append({})
            
            if not frame_detections:
                continue
            
            # Prepare data for supervision
            boxes = []
            class_ids = []
            confidences = []
            
            # Class mapping
            class_map = {'player': 0, 'ball': 1}
            
            for det in frame_detections:
                if det['class'] in class_map:
                    boxes.append(det['bbox'])
                    class_ids.append(class_map[det['class']])
                    confidences.append(det['confidence'])
            
            if boxes:
                # Create supervision detection
                detection_supervision = sv.Detections(
                    xyxy=np.array(boxes),
                    class_id=np.array(class_ids),
                    confidence=np.array(confidences)
                )
                
                # Track objects (only players, not ball)
                trackable_mask = detection_supervision.class_id == 0  # Players only
                if np.any(trackable_mask):
                    trackable_detections = detection_supervision[trackable_mask]
                    detection_with_tracks = self.tracker.update_with_detections(trackable_detections)
                    
                    # Process tracked objects
                    for detection in detection_with_tracks:
                        bbox = detection[0].tolist()
                        track_id = int(detection[4])
                        tracks["players"][frame_num][track_id] = {"bbox": bbox}
                
                # Handle ball separately (no tracking, just detection)
                ball_mask = detection_supervision.class_id == 1
                if np.any(ball_mask):
                    ball_detections = detection_supervision[ball_mask]
                    if len(ball_detections) > 0:
                        bbox = ball_detections.xyxy[0].tolist()
                        tracks["ball"][frame_num][1] = {"bbox": bbox}

        # Interpolate ball positions
        tracks["ball"] = self.interpolate_ball_positions(tracks["ball"])
        
        # Add position information
        self.add_position_to_tracks(tracks)

        # Save cache
        if stub_path is not None:
            os.makedirs(os.path.dirname(stub_path), exist_ok=True)
            with open(stub_path, 'wb') as f:
                pickle.dump(tracks, f)
            print(f"Cached results saved to: {stub_path}")

        return tracks

    def draw_ellipse(self, frame, bbox, color, track_id=None):
        """Draw ellipse around player feet with ID"""
        y2 = int(bbox[3])
        x_center, _ = get_center_of_bbox(bbox)
        width = get_bbox_width(bbox)

        cv2.ellipse(
            frame,
            center=(x_center, y2),
            axes=(int(width), int(0.35 * width)),
            angle=0.0,
            startAngle=-45,
            endAngle=235,
            color=color,
            thickness=2,
            lineType=cv2.LINE_4
        )

        if track_id is not None:
            rectangle_width = 40
            rectangle_height = 20
            x1_rect = x_center - rectangle_width // 2
            x2_rect = x_center + rectangle_width // 2
            y1_rect = (y2 - rectangle_height // 2) + 15
            y2_rect = (y2 + rectangle_height // 2) + 15

            cv2.rectangle(frame,
                         (int(x1_rect), int(y1_rect)),
                         (int(x2_rect), int(y2_rect)),
                         color,
                         cv2.FILLED)

            x1_text = x1_rect + 12
            if track_id > 99:
                x1_text -= 10

            cv2.putText(
                frame,
                f"{track_id}",
                (int(x1_text), int(y1_rect + 15)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 0),
                2
            )

        return frame

    def draw_triangle(self, frame, bbox, color):
        """Draw triangle marker for ball"""
        y = int(bbox[1])
        x, _ = get_center_of_bbox(bbox)

        triangle_points = np.array([
            [x, y],
            [x - 10, y - 20],
            [x + 10, y - 20],
        ])
        cv2.drawContours(frame, [triangle_points], 0, color, cv2.FILLED)
        cv2.drawContours(frame, [triangle_points], 0, (0, 0, 0), 2)

        return frame

    def draw_annotations(self, video_frames, tracks):
        """Draw all annotations on video frames"""
        output_video_frames = []
        
        for frame_num, frame in enumerate(video_frames):
            frame = frame.copy()

            player_dict = tracks["players"][frame_num]
            ball_dict = tracks["ball"][frame_num]

            # Draw Players with ellipses and IDs
            for track_id, player in player_dict.items():
                color = player.get("team_color", (0, 0, 255))
                frame = self.draw_ellipse(frame, player["bbox"], color, track_id)

            # Draw ball
            for track_id, ball in ball_dict.items():
                frame = self.draw_triangle(frame, ball["bbox"], (0, 255, 0))

            output_video_frames.append(frame)

        return output_video_frames

    def process_video(self, video_path, output_path, use_cache=True):
        """Complete video processing pipeline - FAST local inference"""
        print(f"Processing video with LOCAL YOLOv8: {video_path}")
        
        # Create cache filename
        cache_dir = "stubs"
        os.makedirs(cache_dir, exist_ok=True)
        video_name = os.path.basename(video_path).split('.')[0]
        cache_path = os.path.join(cache_dir, f"{video_name}_local_tracks.pkl")
        
        # Read video frames into memory (no disk I/O during processing)
        cap = cv2.VideoCapture(video_path)
        frames = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
        cap.release()
        
        print(f"Read {len(frames)} frames into memory")
        
        # Get object tracks (LOCAL YOLOv8 + ByteTrack)
        print("Running local tracking...")
        tracks = self.get_object_tracks(frames, read_from_stub=use_cache, stub_path=cache_path)
        
        # Assign teams based on jersey colors
        print("Assigning teams based on jersey colors...")
        tracks = self.team_assigner.assign_teams_to_tracks(frames, tracks)
        
        # Draw annotations
        print("Drawing annotations...")
        annotated_frames = self.draw_annotations(frames, tracks)
        
        # Save output video
        print(f"Saving output to: {output_path}")
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        fps = 25
        height, width = frames[0].shape[:2]
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        for frame in annotated_frames:
            out.write(frame)
        out.release()
        
        print("LOCAL YOLOv8 processing complete!")
        return tracks