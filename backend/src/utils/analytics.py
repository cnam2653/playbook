import numpy as np
import math
from typing import List, Dict, Tuple, Optional
from ..models.detection import TrackedObject, VideoAnalysis, FrameAnalysis

class PossessionCalculator:
    """Calculate ball possession for teams and individual players"""
    
    def __init__(self, proximity_threshold: float = 50.0):
        self.proximity_threshold = proximity_threshold  # pixels
        
    def calculate_possession(self, video_analysis: VideoAnalysis) -> Dict:
        """Calculate possession statistics for entire video"""
        ball_obj = video_analysis.get_ball_object()
        if not ball_obj:
            return {"error": "No ball detected"}
        
        player_objects = video_analysis.get_player_objects()
        if not player_objects:
            return {"error": "No players detected"}
        
        possession_timeline = []
        total_frames = len(video_analysis.frame_analyses)
        
        for frame_analysis in video_analysis.frame_analyses:
            possession_player = self._get_ball_possessor(
                frame_analysis, ball_obj, player_objects
            )
            possession_timeline.append({
                'frame_id': frame_analysis.frame_id,
                'timestamp': frame_analysis.timestamp,
                'possessor_id': possession_player
            })
        
        # Calculate statistics
        possession_stats = self._calculate_possession_stats(possession_timeline, player_objects)
        
        return {
            'possession_timeline': possession_timeline,
            'possession_stats': possession_stats,
            'total_frames': total_frames
        }
    
    def _get_ball_possessor(self, frame_analysis: FrameAnalysis, ball_obj: TrackedObject, 
                           player_objects: List[TrackedObject]) -> Optional[int]:
        """Determine which player has ball possession in a frame"""
        ball_detection = None
        for detection in frame_analysis.detections:
            if detection.class_name == 'ball':
                ball_detection = detection
                break
        
        if not ball_detection:
            return None
        
        ball_center = (ball_detection.bbox.center_x, ball_detection.bbox.center_y)
        closest_player = None
        min_distance = float('inf')
        
        for detection in frame_analysis.detections:
            if detection.class_name == 'player':
                player_center = (detection.bbox.center_x, detection.bbox.center_y)
                distance = self._calculate_distance(ball_center, player_center)
                
                if distance < min_distance and distance < self.proximity_threshold:
                    min_distance = distance
                    # Find corresponding track_id
                    for obj in frame_analysis.tracked_objects:
                        if (obj.object_type == 'player' and 
                            obj.latest_detection and
                            abs(obj.latest_detection.bbox.center_x - player_center[0]) < 5 and
                            abs(obj.latest_detection.bbox.center_y - player_center[1]) < 5):
                            closest_player = obj.track_id
                            break
        
        return closest_player
    
    def _calculate_possession_stats(self, possession_timeline: List[Dict], 
                                  player_objects: List[TrackedObject]) -> Dict:
        """Calculate possession statistics from timeline"""
        player_possession_frames = {}
        total_possession_frames = 0
        
        for entry in possession_timeline:
            possessor_id = entry['possessor_id']
            if possessor_id is not None:
                player_possession_frames[possessor_id] = player_possession_frames.get(possessor_id, 0) + 1
                total_possession_frames += 1
        
        possession_percentages = {}
        for player_id, frames in player_possession_frames.items():
            possession_percentages[player_id] = (frames / total_possession_frames * 100) if total_possession_frames > 0 else 0
        
        return {
            'player_possession_frames': player_possession_frames,
            'possession_percentages': possession_percentages,
            'total_possession_frames': total_possession_frames,
            'most_possession': max(possession_percentages.items(), key=lambda x: x[1]) if possession_percentages else None
        }
    
    @staticmethod
    def _calculate_distance(point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """Calculate Euclidean distance between two points"""
        return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

class MovementAnalyzer:
    """Analyze player movement, speed, and activity"""
    
    def __init__(self, fps: float = 30.0, pixels_per_meter: float = 20.0):
        self.fps = fps
        self.pixels_per_meter = pixels_per_meter
        
    def analyze_player_movement(self, tracked_object: TrackedObject) -> Dict:
        """Analyze movement metrics for a single player"""
        if len(tracked_object.detections) < 2:
            return {"error": "Insufficient data points"}
        
        positions = []
        timestamps = []
        speeds = []
        
        for detection in tracked_object.detections:
            positions.append((detection.bbox.center_x, detection.bbox.center_y))
            timestamps.append(detection.timestamp)
        
        # Calculate instantaneous speeds
        for i in range(1, len(positions)):
            distance_pixels = self._calculate_distance(positions[i-1], positions[i])
            distance_meters = distance_pixels / self.pixels_per_meter
            time_diff = timestamps[i] - timestamps[i-1]
            
            if time_diff > 0:
                speed_mps = distance_meters / time_diff  # meters per second
                speeds.append(speed_mps)
        
        if not speeds:
            return {"error": "Could not calculate speeds"}
        
        # Calculate metrics
        total_distance = sum([s * (1/self.fps) for s in speeds])  # approximate
        avg_speed = np.mean(speeds)
        max_speed = max(speeds)
        sprint_threshold = 5.0  # m/s
        sprint_count = len([s for s in speeds if s > sprint_threshold])
        
        return {
            'total_distance_meters': total_distance,
            'average_speed_mps': avg_speed,
            'max_speed_mps': max_speed,
            'sprint_count': sprint_count,
            'total_detections': len(tracked_object.detections),
            'activity_score': self._calculate_activity_score(speeds, positions)
        }
    
    def analyze_team_movement(self, player_objects: List[TrackedObject]) -> Dict:
        """Analyze movement for entire team/all players"""
        team_stats = []
        
        for player in player_objects:
            player_stats = self.analyze_player_movement(player)
            if 'error' not in player_stats:
                player_stats['track_id'] = player.track_id
                team_stats.append(player_stats)
        
        if not team_stats:
            return {"error": "No valid player movement data"}
        
        # Aggregate statistics
        total_distance = sum([p['total_distance_meters'] for p in team_stats])
        avg_team_speed = np.mean([p['average_speed_mps'] for p in team_stats])
        fastest_player = max(team_stats, key=lambda x: x['max_speed_mps'])
        most_active = max(team_stats, key=lambda x: x['activity_score'])
        
        return {
            'individual_stats': team_stats,
            'team_total_distance': total_distance,
            'team_average_speed': avg_team_speed,
            'fastest_player': fastest_player,
            'most_active_player': most_active
        }
    
    def _calculate_activity_score(self, speeds: List[float], positions: List[Tuple]) -> float:
        """Calculate activity score based on movement variance and speed"""
        if len(speeds) < 2 or len(positions) < 2:
            return 0.0
        
        speed_variance = np.var(speeds)
        position_variance = np.var([p[0] for p in positions]) + np.var([p[1] for p in positions])
        avg_speed = np.mean(speeds)
        
        # Combine metrics for activity score
        activity_score = (avg_speed * 0.4) + (speed_variance * 0.3) + (position_variance * 0.3)
        return float(activity_score)
    
    @staticmethod
    def _calculate_distance(point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """Calculate Euclidean distance between two points"""
        return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

class EventExtractor:
    """Extract high-level events from tracking data"""
    
    def __init__(self):
        self.events = []
        
    def extract_events(self, video_analysis: VideoAnalysis) -> List[Dict]:
        """Extract events from video analysis"""
        events = []
        
        # Ball possession changes
        possession_events = self._extract_possession_changes(video_analysis)
        events.extend(possession_events)
        
        # High-speed events (sprints)
        sprint_events = self._extract_sprint_events(video_analysis)
        events.extend(sprint_events)
        
        # Clustering events (formations)
        clustering_events = self._extract_clustering_events(video_analysis)
        events.extend(clustering_events)
        
        return sorted(events, key=lambda x: x['timestamp'])
    
    def _extract_possession_changes(self, video_analysis: VideoAnalysis) -> List[Dict]:
        """Extract ball possession change events"""
        events = []
        calculator = PossessionCalculator()
        possession_data = calculator.calculate_possession(video_analysis)
        
        if 'possession_timeline' not in possession_data:
            return events
        
        current_possessor = None
        for entry in possession_data['possession_timeline']:
            new_possessor = entry['possessor_id']
            
            if new_possessor != current_possessor and new_possessor is not None:
                events.append({
                    'type': 'possession_change',
                    'timestamp': entry['timestamp'],
                    'frame_id': entry['frame_id'],
                    'from_player': current_possessor,
                    'to_player': new_possessor,
                    'description': f"Ball possession changed to player {new_possessor}"
                })
                current_possessor = new_possessor
        
        return events
    
    def _extract_sprint_events(self, video_analysis: VideoAnalysis) -> List[Dict]:
        """Extract sprint/high-speed events"""
        events = []
        analyzer = MovementAnalyzer()
        
        for player in video_analysis.get_player_objects():
            movement_data = analyzer.analyze_player_movement(player)
            
            if 'error' not in movement_data and movement_data['sprint_count'] > 0:
                # Find approximate sprint timing (simplified)
                mid_timestamp = player.detections[len(player.detections)//2].timestamp if player.detections else 0
                
                events.append({
                    'type': 'sprint',
                    'timestamp': mid_timestamp,
                    'player_id': player.track_id,
                    'max_speed': movement_data['max_speed_mps'],
                    'description': f"Player {player.track_id} sprinted at {movement_data['max_speed_mps']:.1f} m/s"
                })
        
        return events
    
    def _extract_clustering_events(self, video_analysis: VideoAnalysis) -> List[Dict]:
        """Extract player clustering/formation events"""
        events = []
        
        # Simplified clustering detection
        for i, frame_analysis in enumerate(video_analysis.frame_analyses[::30]):  # Every 30 frames
            player_positions = []
            
            for detection in frame_analysis.detections:
                if detection.class_name == 'player':
                    player_positions.append((detection.bbox.center_x, detection.bbox.center_y))
            
            if len(player_positions) >= 3:
                # Calculate spread/clustering
                center_x = np.mean([p[0] for p in player_positions])
                center_y = np.mean([p[1] for p in player_positions])
                
                distances = [math.sqrt((p[0] - center_x)**2 + (p[1] - center_y)**2) for p in player_positions]
                avg_distance = np.mean(distances)
                
                # Detect tight clustering
                if avg_distance < 80:  # Tight formation
                    events.append({
                        'type': 'tight_formation',
                        'timestamp': frame_analysis.timestamp,
                        'frame_id': frame_analysis.frame_id,
                        'spread': avg_distance,
                        'description': f"Players in tight formation (spread: {avg_distance:.1f}px)"
                    })
        
        return events