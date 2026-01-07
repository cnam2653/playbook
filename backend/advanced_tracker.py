import supervision as sv
from ultralytics import YOLO
import pickle
import os
import numpy as np
import pandas as pd
import cv2
import sys
sys.path.append('./src/utils')
from src.utils.bbox_utils import get_center_of_bbox, get_bbox_width, get_foot_position
from team_assigner import TeamAssigner
from smart_tracker import SmartTracker
from player_ball_assigner import PlayerBallAssigner
from camera_movement_estimator import CameraMovementEstimator

class AdvancedTracker:
    def __init__(self, model_path="../runs/soccer-model-yolov8n4/weights/best.pt"):
        # Initialize with your custom trained model
        print(f"Loading custom trained model: {model_path}")
        self.model = YOLO(model_path)
        print(f"Model device: {self.model.device}")
        print(f"Model classes: {self.model.names}")
        # Use ByteTrack with more stable settings
        try:
            # Try newer ByteTrack parameters for better stability
            self.tracker = sv.ByteTrack(
                track_thresh=0.25,    # Lower threshold for keeping tracks
                track_buffer=60,      # Keep tracks alive longer
                match_thresh=0.7      # Lower matching threshold 
            )
        except TypeError:
            # Fallback to default if parameters not supported
            self.tracker = sv.ByteTrack()
        
        # Initialize team assigner
        self.team_assigner = TeamAssigner()
        
        # Initialize smart tracker with team-aware constraints
        self.smart_tracker = SmartTracker(self.tracker)
        
        # Initialize ball assigner
        self.ball_assigner = PlayerBallAssigner()
        
        # Camera movement estimator will be initialized when processing video
        self.camera_estimator = None

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
        """Simple and effective ball position interpolation"""
        ball_positions = [x.get(1, {}).get('bbox', []) for x in ball_positions]
        df_ball_positions = pd.DataFrame(ball_positions, columns=['x1', 'y1', 'x2', 'y2'])

        # Interpolate missing values
        df_ball_positions = df_ball_positions.interpolate()
        df_ball_positions = df_ball_positions.bfill()

        ball_positions = [{1: {"bbox": x}} for x in df_ball_positions.to_numpy().tolist()]
        return ball_positions

    def detect_frames(self, frames):
        """Detect objects using custom trained YOLOv8 model"""
        print(f"Running custom YOLOv8 inference on {len(frames)} frames...")
        
        # Process in batches for speed
        batch_size = 20
        all_detections = []
        
        for i in range(0, len(frames), batch_size):
            batch_frames = frames[i:i+batch_size]
            
            # Run YOLOv8 on batch with higher confidence for more stable detections
            results = self.model.predict(batch_frames, conf=0.2, verbose=False)
            
            # Convert YOLOv8 results to our format
            for result in results:
                frame_detections = []
                
                if result.boxes is not None:
                    boxes = result.boxes.xyxy.cpu().numpy()  # [x1, y1, x2, y2]
                    confidences = result.boxes.conf.cpu().numpy()
                    class_ids = result.boxes.cls.cpu().numpy()
                    
                    # Convert to our class names
                    for box, conf, cls_id in zip(boxes, confidences, class_ids):
                        class_name = self.model.names[int(cls_id)]
                        frame_detections.append({
                            'bbox': box.tolist(),
                            'class': class_name,
                            'confidence': float(conf)
                        })
                
                all_detections.append(frame_detections)
            
            print(f"Processed batch {i//batch_size + 1}/{(len(frames) + batch_size - 1)//batch_size}")
        
        print(f"Custom YOLOv8 inference complete!")
        return all_detections

    def get_object_tracks(self, frames, read_from_stub=False, stub_path=None):
        """Get tracking data for all objects"""
        
        if read_from_stub and stub_path is not None and os.path.exists(stub_path):
            with open(stub_path, 'rb') as f:
                tracks = pickle.load(f)
            return tracks

        detections = self.detect_frames(frames)

        tracks = {
            "players": [],
            "referees": [],
            "ball": []
        }
        
        # Initialize team colors on first good frame
        team_colors_initialized = False

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
            
            # Class mapping - separate players from referees
            class_map = {'player': 0, 'goalkeeper': 0, 'referee': 1, 'ball': 2}
            
            # Debug: Print detected classes for first frame
            if frame_num == 0:
                detected_classes = [det['class'] for det in frame_detections]
                print(f"Frame {frame_num} detected classes: {set(detected_classes)}")
                print(f"Frame {frame_num} class counts: {[(c, detected_classes.count(c)) for c in set(detected_classes)]}")
            
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
                
                # Separate players and referees for different processing
                player_mask = detection_supervision.class_id == 0  # Players only
                referee_mask = detection_supervision.class_id == 1  # Referees only
                
                # Process players with SmartTracker
                if np.any(player_mask):
                    player_detections = detection_supervision[player_mask]
                    
                    # Use SmartTracker for intelligent ID management
                    current_frame = frames[frame_num] if frame_num < len(frames) else None
                    smart_tracks = self.smart_tracker.process_frame_detections(
                        player_detections, frame_num, self.team_assigner, current_frame
                    )
                    
                    # Convert smart tracks to our format
                    for track_id, track_data in smart_tracks.items():
                        bbox = track_data["bbox"]
                        team = track_data["team"]
                        team_color = track_data["team_color"]
                        
                        # Add to tracks with team info
                        tracks["players"][frame_num][track_id] = {
                            "bbox": bbox,
                            "team": team,
                            "team_color": team_color
                        }
                    
                    # Initialize team colors on first frame with enough players
                    if (not team_colors_initialized and 
                        len(tracks["players"][frame_num]) >= 4 and 
                        frame_num < len(frames)):
                        
                        print(f"Initializing team colors from frame {frame_num} with {len(tracks['players'][frame_num])} players")
                        self.team_assigner.assign_team_color(frames[frame_num], tracks["players"][frame_num])
                        self.smart_tracker.set_team_colors(self.team_assigner.team_colors)
                        team_colors_initialized = True
                        print(f"Team colors initialized: {self.team_assigner.team_colors}")
                
                # Process referees separately (simple tracking, no teams)
                if np.any(referee_mask):
                    referee_detections = detection_supervision[referee_mask]
                    referee_tracked = self.tracker.update_with_detections(referee_detections)
                    
                    for detection in referee_tracked:
                        bbox = detection[0].tolist()
                        track_id = int(detection[4])
                        tracks["referees"][frame_num][track_id] = {"bbox": bbox}
                
                # Handle ball separately (no tracking, just detection)
                ball_mask = detection_supervision.class_id == 2
                if np.any(ball_mask):
                    ball_detections = detection_supervision[ball_mask]
                    if len(ball_detections) > 0:
                        bbox = ball_detections.xyxy[0].tolist()
                        tracks["ball"][frame_num][1] = {"bbox": bbox}

        # Interpolate ball positions
        tracks["ball"] = self.interpolate_ball_positions(tracks["ball"])
        
        # Add position information
        self.add_position_to_tracks(tracks)
        
        # Assign ball possession to players
        tracks = self.assign_ball_possession(tracks)
        
        return tracks
    
    def process_video_with_camera_tracking(self, frames, use_cache=True, cache_path=None):
        """Get tracks with camera movement compensation"""
        tracks = self.get_object_tracks(frames, read_from_stub=use_cache, stub_path=cache_path)
        
        # Get camera movement and adjust positions
        print("Calculating camera movement...")
        camera_movement_cache_path = cache_path.replace('_tracks.pkl', '_camera.pkl') if cache_path else None
        camera_movement_per_frame = self.camera_estimator.get_camera_movement(
            frames, read_from_stub=use_cache, stub_path=camera_movement_cache_path
        )
        self.camera_estimator.add_adjust_positions_to_tracks(tracks, camera_movement_per_frame)
        
        return tracks, camera_movement_per_frame
    
    def assign_missing_team_colors(self, frames, tracks):
        """Assign team colors to players who missed SmartTracker processing"""
        if not hasattr(self.team_assigner, 'team_colors') or not self.team_assigner.team_colors:
            print("Warning: Team colors not initialized, skipping post-processing")
            return tracks
        
        missing_count = 0
        assigned_count = 0
        
        for frame_num, player_track in enumerate(tracks['players']):
            if frame_num >= len(frames):
                continue
                
            for player_id, track in player_track.items():
                # Check if player is missing team assignment
                if 'team' not in track or 'team_color' not in track:
                    missing_count += 1
                    
                    # Get team assignment using team assigner directly
                    try:
                        team = self.team_assigner.get_player_team(
                            frames[frame_num], track['bbox'], player_id
                        )
                        team_color = self.team_assigner.team_colors[team]
                        
                        # Ensure color is a tuple
                        if not isinstance(team_color, tuple):
                            team_color = tuple(map(int, team_color))
                        
                        # Assign team and color
                        tracks['players'][frame_num][player_id]['team'] = team
                        tracks['players'][frame_num][player_id]['team_color'] = team_color
                        assigned_count += 1
                        
                    except Exception as e:
                        print(f"Error assigning team to player {player_id}: {e}")
                        # Fallback to default colors
                        tracks['players'][frame_num][player_id]['team'] = 1
                        tracks['players'][frame_num][player_id]['team_color'] = (255, 255, 255)
        
        if missing_count > 0:
            print(f"Post-processed {missing_count} players missing team assignments, successfully assigned {assigned_count}")
        
        return tracks
    
    def initialize_team_colors(self, frames, tracks):
        """Initialize team colors from first frame with players"""
        if not tracks['players'] or not frames:
            return False
            
        # Find a frame with enough players to determine teams
        for frame_idx in range(min(5, len(frames))):
            first_frame_players = tracks['players'][frame_idx]
            if len(first_frame_players) >= 4:  # Need at least 4 players
                print(f"Initializing team colors from frame {frame_idx} with {len(first_frame_players)} players")
                self.team_assigner.assign_team_color(frames[frame_idx], first_frame_players)
                return True
        
        print("Warning: Not enough players found to initialize team colors")
        return False

    def assign_ball_possession(self, tracks):
        """Assign ball possession to the closest player"""
        for frame_num in range(len(tracks["ball"])):
            ball_dict = tracks["ball"][frame_num]
            player_dict = tracks["players"][frame_num]
            
            # Clear previous ball assignments
            for track_id in player_dict:
                tracks["players"][frame_num][track_id]['has_ball'] = False
            
            # Assign ball if it exists
            for _, ball in ball_dict.items():
                assigned_player = self.ball_assigner.assign_ball_to_player(player_dict, ball["bbox"])
                if assigned_player != -1:
                    tracks["players"][frame_num][assigned_player]['has_ball'] = True
                    break  # Only one ball assignment per frame
        
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

    def draw_team_ball_control(self, frame, frame_num, team_ball_control):
        """Draw team ball control statistics"""
        overlay = frame.copy()
        cv2.rectangle(overlay, (1350, 850), (1900, 970), (255, 255, 255), -1)
        alpha = 0.4
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

        team_ball_control_till_frame = team_ball_control[:frame_num + 1]
        team_1_num_frames = team_ball_control_till_frame[team_ball_control_till_frame == 1].shape[0]
        team_2_num_frames = team_ball_control_till_frame[team_ball_control_till_frame == 2].shape[0]
        
        if team_1_num_frames + team_2_num_frames > 0:
            team_1 = team_1_num_frames / (team_1_num_frames + team_2_num_frames)
            team_2 = team_2_num_frames / (team_1_num_frames + team_2_num_frames)
        else:
            team_1 = team_2 = 0.5

        cv2.putText(frame, f"Team 1 Ball Control: {team_1 * 100:.2f}%", (1400, 900), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 3)
        cv2.putText(frame, f"Team 2 Ball Control: {team_2 * 100:.2f}%", (1400, 950), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 3)

        return frame

    def draw_annotations(self, video_frames, tracks, team_ball_control=None):
        """Draw all annotations on video frames"""
        output_video_frames = []
        
        # Generate mock team ball control if not provided
        if team_ball_control is None:
            team_ball_control = np.random.choice([1, 2], size=len(video_frames))
        
        for frame_num, frame in enumerate(video_frames):
            frame = frame.copy()

            player_dict = tracks["players"][frame_num]
            ball_dict = tracks["ball"][frame_num]
            referee_dict = tracks["referees"][frame_num]
            
            # Debug: Print player data structure for first frame
            if frame_num == 0 and player_dict:
                sample_player = next(iter(player_dict.values()))
                print(f"Sample player data: {sample_player.keys()}")

            # Draw Players with ellipses and IDs (now with team colors!)
            for track_id, player in player_dict.items():
                # Get team color with comprehensive fallback logic
                color = None
                
                # First try: Use stored team_color
                if "team_color" in player and player["team_color"] is not None:
                    color = player["team_color"]
                
                # Second try: Get color from team number + team assigner
                elif "team" in player and hasattr(self.team_assigner, 'team_colors'):
                    team_num = player["team"]
                    if team_num in self.team_assigner.team_colors:
                        color = self.team_assigner.team_colors[team_num]
                
                # Third try: Try to assign team on the fly
                elif hasattr(self.team_assigner, 'team_colors') and self.team_assigner.team_colors:
                    try:
                        team = self.team_assigner.get_player_team(
                            video_frames[frame_num] if frame_num < len(video_frames) else None,
                            player["bbox"], 
                            track_id
                        )
                        if team in self.team_assigner.team_colors:
                            color = self.team_assigner.team_colors[team]
                    except:
                        pass  # Fall through to default
                
                # Final fallback: Default colors based on track ID
                if color is None:
                    # Alternate colors based on track ID for visibility
                    if track_id % 2 == 0:
                        color = (255, 255, 255)  # White
                    else:
                        color = (0, 255, 0)      # Green
                
                # Ensure color is a tuple for OpenCV
                if not isinstance(color, tuple):
                    color = tuple(map(int, color)) if hasattr(color, '__iter__') else (255, 255, 255)
                
                frame = self.draw_ellipse(frame, player["bbox"], color, track_id)

                if player.get('has_ball', False):
                    frame = self.draw_triangle(frame, player["bbox"], (0, 0, 255))

            # Draw Referees (yellow)
            for _, referee in referee_dict.items():
                frame = self.draw_ellipse(frame, referee["bbox"], (0, 255, 255))  # Yellow in BGR

            # Draw ball
            for track_id, ball in ball_dict.items():
                frame = self.draw_triangle(frame, ball["bbox"], (0, 255, 0))

            # Draw Team Ball Control
            if frame_num < len(team_ball_control):
                frame = self.draw_team_ball_control(frame, frame_num, team_ball_control)

            output_video_frames.append(frame)

        return output_video_frames

    def process_video(self, video_path, output_path, use_cache=True):
        """Complete video processing pipeline"""
        print(f"Processing video: {video_path}")
        
        # Create cache filename based on video path
        cache_dir = "stubs"
        os.makedirs(cache_dir, exist_ok=True)
        video_name = os.path.basename(video_path).split('.')[0]
        cache_path = os.path.join(cache_dir, f"{video_name}_tracks.pkl")
        
        # Read video frames
        cap = cv2.VideoCapture(video_path)
        frames = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
        cap.release()
        
        print(f"Read {len(frames)} frames")
        
        # Initialize camera movement estimator with first frame
        if self.camera_estimator is None:
            self.camera_estimator = CameraMovementEstimator(frames[0])
        
        # Get object tracks with camera movement compensation
        print("Getting object tracks with camera movement compensation...")
        tracks, camera_movement_per_frame = self.process_video_with_camera_tracking(
            frames, use_cache=use_cache, cache_path=cache_path
        )
        
        # Post-process tracks to ensure all players have team assignments
        print("Post-processing tracks to assign missing team colors...")
        tracks = self.assign_missing_team_colors(frames, tracks)
        
        print("Teams assigned by SmartTracker with persistent IDs...")
        
        # Draw annotations
        print("Drawing annotations...")
        annotated_frames = self.draw_annotations(frames, tracks)
        
        # Add camera movement visualization
        print("Adding camera movement visualization...")
        annotated_frames = self.camera_estimator.draw_camera_movement(
            annotated_frames, camera_movement_per_frame
        )
        
        # Save output video
        print(f"Saving output to: {output_path}")
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        fps = 25  # Default FPS
        height, width = frames[0].shape[:2]
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        for frame in annotated_frames:
            out.write(frame)
        out.release()
        
        print("Video processing complete!")
        return tracks