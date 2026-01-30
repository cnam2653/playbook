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

class TeamAssigner:
    def __init__(self):
        self.team_colors = {}
        self.player_team_dict = {}
        self.kmeans = None

    def get_clustering_model(self, image):
        from sklearn.cluster import KMeans
        image_2d = image.reshape(-1, 3)
        kmeans = KMeans(n_clusters=2, init="k-means++", n_init=1)
        kmeans.fit(image_2d)
        return kmeans

    def get_player_color(self, frame, bbox):
        image = frame[int(bbox[1]):int(bbox[3]), int(bbox[0]):int(bbox[2])]
        if image.size == 0:
            return np.array([0, 0, 0])
        top_half_image = image[0:int(image.shape[0]/2), :]
        if top_half_image.size == 0:
            return np.array([0, 0, 0])

        kmeans = self.get_clustering_model(top_half_image)
        labels = kmeans.labels_
        clustered_image = labels.reshape(top_half_image.shape[0], top_half_image.shape[1])

        corner_clusters = [clustered_image[0,0], clustered_image[0,-1], clustered_image[-1,0], clustered_image[-1,-1]]
        non_player_cluster = max(set(corner_clusters), key=corner_clusters.count)
        player_cluster = 1 - non_player_cluster
        player_color = kmeans.cluster_centers_[player_cluster]
        return player_color

    def assign_team_color(self, frame, player_detections):
        from sklearn.cluster import KMeans
        player_colors = []
        for _, player_detection in player_detections.items():
            bbox = player_detection["bbox"]
            player_color = self.get_player_color(frame, bbox)
            player_colors.append(player_color)

        if len(player_colors) < 2:
            self.team_colors[1] = np.array([255, 255, 255])
            self.team_colors[2] = np.array([0, 255, 0])
            return

        kmeans = KMeans(n_clusters=2, init="k-means++", n_init=10)
        kmeans.fit(player_colors)
        self.kmeans = kmeans
        self.team_colors[1] = kmeans.cluster_centers_[0]
        self.team_colors[2] = kmeans.cluster_centers_[1]

    def get_player_team(self, frame, player_bbox, player_id):
        if player_id in self.player_team_dict:
            return self.player_team_dict[player_id]

        if self.kmeans is None:
            return 1

        player_color = self.get_player_color(frame, player_bbox)
        team_id = self.kmeans.predict(player_color.reshape(1, -1))[0]
        team_id += 1

        self.player_team_dict[player_id] = team_id
        return team_id


class PlayerBallAssigner:
    def __init__(self):
        self.max_player_ball_distance = 70

    def assign_ball_to_player(self, players, ball_bbox):
        ball_position = get_center_of_bbox(ball_bbox)
        minimum_distance = 99999
        assigned_player = -1

        for player_id, player in players.items():
            player_bbox = player['bbox']
            distance_left = self._measure_distance((player_bbox[0], player_bbox[-1]), ball_position)
            distance_right = self._measure_distance((player_bbox[2], player_bbox[-1]), ball_position)
            distance = min(distance_left, distance_right)

            if distance < self.max_player_ball_distance:
                if distance < minimum_distance:
                    minimum_distance = distance
                    assigned_player = player_id

        return assigned_player

    def _measure_distance(self, p1, p2):
        return ((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)**0.5


class AdvancedTracker:
    def __init__(self, model_path="models/best.pt"):
        print(f"Loading custom trained model: {model_path}")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at {model_path}")

        self.model = YOLO(model_path)
        self.tracker = sv.ByteTrack()

        print(f"Model device: {self.model.device}")
        print(f"Model classes: {self.model.names}")

    def detect_frames(self, frames):
        batch_size = 20
        detections = []
        for i in range(0, len(frames), batch_size):
            detections_batch = self.model.predict(frames[i:i+batch_size], conf=0.1)
            detections += detections_batch
        return detections

    def get_object_tracks(self, frames):
        detections = self.detect_frames(frames)

        tracks = {
            "players": [],
            "referees": [],
            "goalkeepers": [],
            "ball": []
        }

        # Track IDs that have EVER been detected as goalkeeper
        goalkeeper_track_ids = set()

        # Single pass: collect all detections
        for frame_num, detection in enumerate(detections):
            cls_names = detection.names
            cls_names_inv = {v: k for k, v in cls_names.items()}

            detection_supervision = sv.Detections.from_ultralytics(detection)
            detection_with_tracks = self.tracker.update_with_detections(detection_supervision)

            tracks["players"].append({})
            tracks["referees"].append({})
            tracks["goalkeepers"].append({})
            tracks["ball"].append({})

            for frame_detection in detection_with_tracks:
                bbox = frame_detection[0].tolist()
                cls_id = frame_detection[3]
                track_id = frame_detection[4]

                # Track goalkeeper IDs
                if cls_id == cls_names_inv.get('goalkeeper'):
                    goalkeeper_track_ids.add(track_id)
                    tracks["goalkeepers"][frame_num][track_id] = {"bbox": bbox}
                elif cls_id == cls_names_inv.get('player'):
                    tracks["players"][frame_num][track_id] = {"bbox": bbox}
                elif cls_id == cls_names_inv.get('referee'):
                    tracks["referees"][frame_num][track_id] = {"bbox": bbox}

            for frame_detection in detection_supervision:
                bbox = frame_detection[0].tolist()
                cls_id = frame_detection[3]

                if cls_id == cls_names_inv.get('ball'):
                    tracks["ball"][frame_num][1] = {"bbox": bbox}

        # Post-process: Move any player detections with goalkeeper IDs to goalkeepers
        # This ensures consistency - once a goalkeeper, always a goalkeeper
        print(f"Identified {len(goalkeeper_track_ids)} goalkeeper track IDs: {goalkeeper_track_ids}")

        for frame_num in range(len(tracks["players"])):
            players_to_move = []
            for track_id in tracks["players"][frame_num]:
                if track_id in goalkeeper_track_ids:
                    players_to_move.append(track_id)

            for track_id in players_to_move:
                # Move from players to goalkeepers
                tracks["goalkeepers"][frame_num][track_id] = tracks["players"][frame_num][track_id]
                del tracks["players"][frame_num][track_id]

        return tracks

    def interpolate_ball_positions(self, ball_positions):
        ball_positions = [x.get(1, {}).get('bbox', []) for x in ball_positions]
        df_ball_positions = pd.DataFrame(ball_positions, columns=['x1', 'y1', 'x2', 'y2'])

        df_ball_positions = df_ball_positions.interpolate()
        df_ball_positions = df_ball_positions.bfill()

        ball_positions = [{1: {"bbox": x}} for x in df_ball_positions.to_numpy().tolist()]
        return ball_positions

    def add_position_to_tracks(self, tracks):
        for object_type, object_tracks in tracks.items():
            for frame_num, track in enumerate(object_tracks):
                for track_id, track_info in track.items():
                    bbox = track_info['bbox']
                    if object_type == 'ball':
                        position = get_center_of_bbox(bbox)
                    else:
                        # Players, goalkeepers, and referees use foot position
                        position = get_foot_position(bbox)
                    tracks[object_type][frame_num][track_id]['position'] = position

    def draw_ellipse(self, frame, bbox, color, track_id=None):
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

    def draw_team_ball_control(self, frame, frame_num, team_ball_control, team_colors=None):
        overlay = frame.copy()

        # Dark semi-transparent background
        cv2.rectangle(overlay, (1350, 830), (1900, 1000), (30, 30, 30), -1)
        alpha = 0.85
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

        # Add border
        cv2.rectangle(frame, (1350, 830), (1900, 1000), (100, 100, 100), 2)

        team_ball_control_till_frame = team_ball_control[:frame_num + 1]
        team_1_num_frames = team_ball_control_till_frame[team_ball_control_till_frame == 1].shape[0]
        team_2_num_frames = team_ball_control_till_frame[team_ball_control_till_frame == 2].shape[0]

        total = team_1_num_frames + team_2_num_frames
        if total > 0:
            team_1_pct = team_1_num_frames / total
            team_2_pct = team_2_num_frames / total
        else:
            team_1_pct = team_2_pct = 0.5

        # Title
        cv2.putText(frame, "BALL POSSESSION", (1480, 860), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Get team colors (default if not provided)
        team_1_color = team_colors.get(1, (255, 255, 255)) if team_colors else (255, 255, 255)
        team_2_color = team_colors.get(2, (0, 255, 0)) if team_colors else (0, 255, 0)

        # Team 1 - with color indicator
        cv2.circle(frame, (1380, 900), 12, team_1_color, -1)
        cv2.circle(frame, (1380, 900), 12, (255, 255, 255), 2)
        cv2.putText(frame, f"Team 1: {team_1_pct*100:.1f}%", (1410, 908), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        # Team 1 progress bar
        bar_width = int(400 * team_1_pct)
        cv2.rectangle(frame, (1410, 915), (1410 + 400, 935), (60, 60, 60), -1)
        cv2.rectangle(frame, (1410, 915), (1410 + bar_width, 935), team_1_color, -1)
        cv2.rectangle(frame, (1410, 915), (1810, 935), (100, 100, 100), 1)

        # Team 2 - with color indicator
        cv2.circle(frame, (1380, 960), 12, team_2_color, -1)
        cv2.circle(frame, (1380, 960), 12, (255, 255, 255), 2)
        cv2.putText(frame, f"Team 2: {team_2_pct*100:.1f}%", (1410, 968), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        # Team 2 progress bar
        bar_width = int(400 * team_2_pct)
        cv2.rectangle(frame, (1410, 975), (1410 + 400, 995), (60, 60, 60), -1)
        cv2.rectangle(frame, (1410, 975), (1410 + bar_width, 995), team_2_color, -1)
        cv2.rectangle(frame, (1410, 975), (1810, 995), (100, 100, 100), 1)

        return frame

    def draw_speed_above_player(self, frame, bbox, speed):
        """Draw speed above a player's head"""
        if speed is None:
            return frame

        x_center, _ = get_center_of_bbox(bbox)
        y_top = int(bbox[1])  # Top of bounding box

        # Position text above the player's head
        text = f"{speed:.1f} km/h"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        thickness = 2

        # Get text size for background
        (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)

        # Position - above player's head
        x_text = x_center - text_width // 2
        y_text = y_top - 10

        # Draw background rectangle
        padding = 3
        cv2.rectangle(frame,
                      (x_text - padding, y_text - text_height - padding),
                      (x_text + text_width + padding, y_text + padding),
                      (0, 0, 0), cv2.FILLED)

        # Draw text
        cv2.putText(frame, text, (x_text, y_text), font, font_scale, (255, 255, 255), thickness)

        return frame

    def draw_annotations(self, video_frames, tracks, team_ball_control, team_colors=None):
        output_video_frames = []

        for frame_num, frame in enumerate(video_frames):
            frame = frame.copy()

            player_dict = tracks["players"][frame_num]
            ball_dict = tracks["ball"][frame_num]
            referee_dict = tracks["referees"][frame_num]
            goalkeeper_dict = tracks.get("goalkeepers", [{}] * len(video_frames))[frame_num]

            # Draw Players with speed
            for track_id, player in player_dict.items():
                color = player.get("team_color", (0, 0, 255))
                frame = self.draw_ellipse(frame, player["bbox"], color, track_id)

                # Draw speed above player
                speed = player.get('speed')
                if speed is not None:
                    frame = self.draw_speed_above_player(frame, player["bbox"], speed)

                if player.get('has_ball', False):
                    frame = self.draw_triangle(frame, player["bbox"], (0, 0, 255))

            # Draw Goalkeepers in BLACK (they don't affect ball possession)
            for track_id, goalkeeper in goalkeeper_dict.items():
                frame = self.draw_ellipse(frame, goalkeeper["bbox"], (0, 0, 0), track_id)  # Black color

                # Draw speed above goalkeeper too
                speed = goalkeeper.get('speed')
                if speed is not None:
                    frame = self.draw_speed_above_player(frame, goalkeeper["bbox"], speed)

            # Draw Referees (yellow/cyan)
            for _, referee in referee_dict.items():
                frame = self.draw_ellipse(frame, referee["bbox"], (0, 255, 255))

            # Draw Ball
            for track_id, ball in ball_dict.items():
                frame = self.draw_triangle(frame, ball["bbox"], (0, 255, 0))

            # Draw Team Ball Control with team colors
            frame = self.draw_team_ball_control(frame, frame_num, team_ball_control, team_colors)

            output_video_frames.append(frame)

        return output_video_frames

    def add_speed_and_distance_to_tracks(self, tracks):
        """Calculate speed and distance for all players and goalkeepers"""
        frame_window = 5
        frame_rate = 24
        total_distance = {}

        for object_type in ['players', 'goalkeepers']:
            if object_type not in tracks:
                continue

            object_tracks = tracks[object_type]
            number_of_frames = len(object_tracks)

            for frame_num in range(0, number_of_frames, frame_window):
                last_frame = min(frame_num + frame_window, number_of_frames - 1)

                for track_id, _ in object_tracks[frame_num].items():
                    if track_id not in object_tracks[last_frame]:
                        continue

                    start_position = object_tracks[frame_num][track_id].get('position_transformed')
                    end_position = object_tracks[last_frame][track_id].get('position_transformed')

                    if start_position is None or end_position is None:
                        # Fallback to regular position
                        start_position = object_tracks[frame_num][track_id].get('position')
                        end_position = object_tracks[last_frame][track_id].get('position')

                    if start_position is None or end_position is None:
                        continue

                    distance_covered = ((start_position[0] - end_position[0])**2 +
                                        (start_position[1] - end_position[1])**2)**0.5

                    time_elapsed = (last_frame - frame_num) / frame_rate
                    if time_elapsed > 0:
                        speed_meters_per_second = distance_covered / time_elapsed
                        # Scale down if using pixel positions (rough estimate)
                        if object_tracks[frame_num][track_id].get('position_transformed') is None:
                            speed_meters_per_second = speed_meters_per_second * 0.05  # Scale factor for pixels
                        speed_km_per_hour = speed_meters_per_second * 3.6
                    else:
                        speed_km_per_hour = 0

                    if object_type not in total_distance:
                        total_distance[object_type] = {}

                    if track_id not in total_distance[object_type]:
                        total_distance[object_type][track_id] = 0

                    total_distance[object_type][track_id] += distance_covered

                    for frame_num_batch in range(frame_num, last_frame):
                        if track_id not in tracks[object_type][frame_num_batch]:
                            continue
                        tracks[object_type][frame_num_batch][track_id]['speed'] = speed_km_per_hour
                        tracks[object_type][frame_num_batch][track_id]['distance'] = total_distance[object_type][track_id]

    def process_video(self, video_path, output_path, use_cache=False):
        print(f"Processing video: {video_path}")

        # Read video frames
        cap = cv2.VideoCapture(video_path)
        frames = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
        cap.release()

        if len(frames) == 0:
            raise ValueError("No frames found in video")

        print(f"Read {len(frames)} frames")

        # Get object tracks
        print("Getting object tracks...")
        tracks = self.get_object_tracks(frames)

        # Add position to tracks
        self.add_position_to_tracks(tracks)

        # Interpolate ball positions
        print("Interpolating ball positions...")
        tracks["ball"] = self.interpolate_ball_positions(tracks["ball"])

        # Assign teams (only for players, not goalkeepers)
        print("Assigning player teams...")
        team_assigner = TeamAssigner()

        if tracks['players'][0]:
            team_assigner.assign_team_color(frames[0], tracks['players'][0])

        for frame_num, player_track in enumerate(tracks['players']):
            for player_id, track in player_track.items():
                team = team_assigner.get_player_team(frames[frame_num], track['bbox'], player_id)
                tracks['players'][frame_num][player_id]['team'] = team
                tracks['players'][frame_num][player_id]['team_color'] = tuple(map(int, team_assigner.team_colors[team]))

        # Calculate speed and distance for players and goalkeepers
        print("Calculating speed and distance...")
        self.add_speed_and_distance_to_tracks(tracks)

        # Assign ball possession (only to players, NOT goalkeepers)
        print("Assigning ball possession...")
        player_assigner = PlayerBallAssigner()
        team_ball_control = []

        for frame_num, player_track in enumerate(tracks['players']):
            ball_bbox = tracks['ball'][frame_num].get(1, {}).get('bbox', [])
            if ball_bbox:
                # Only check players for ball possession, not goalkeepers
                assigned_player = player_assigner.assign_ball_to_player(player_track, ball_bbox)

                if assigned_player != -1:
                    tracks['players'][frame_num][assigned_player]['has_ball'] = True
                    team_ball_control.append(tracks['players'][frame_num][assigned_player]['team'])
                else:
                    if team_ball_control:
                        team_ball_control.append(team_ball_control[-1])
                    else:
                        team_ball_control.append(1)
            else:
                if team_ball_control:
                    team_ball_control.append(team_ball_control[-1])
                else:
                    team_ball_control.append(1)

        team_ball_control = np.array(team_ball_control)

        # Get team colors for display
        team_colors_display = {
            1: tuple(map(int, team_assigner.team_colors[1])),
            2: tuple(map(int, team_assigner.team_colors[2]))
        }

        # Draw annotations
        print("Drawing annotations...")
        output_video_frames = self.draw_annotations(frames, tracks, team_ball_control, team_colors_display)

        # Save output video
        fps = 24
        height, width = frames[0].shape[:2]

        temp_path = output_path.replace('.mp4', '_temp.avi')
        print(f"Saving temp to: {temp_path}")
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(temp_path, fourcc, fps, (width, height))

        for frame in output_video_frames:
            out.write(frame)
        out.release()

        # Convert to MP4 with ffmpeg for web playback
        print(f"Converting to web-compatible MP4: {output_path}")
        import subprocess
        import shutil
        try:
            subprocess.run([
                'ffmpeg', '-y', '-i', temp_path,
                '-c:v', 'libx264', '-preset', 'fast',
                '-crf', '23', '-pix_fmt', 'yuv420p',
                output_path
            ], check=True, capture_output=True)
            os.remove(temp_path)
            print("Conversion successful!")
        except Exception as e:
            print(f"FFmpeg conversion failed: {e}")
            shutil.move(temp_path, output_path)
            print("Using AVI file as fallback")

        print("Video processing complete!")
        return tracks
