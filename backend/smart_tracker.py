import numpy as np
from collections import defaultdict
import cv2

class SmartTracker:
    """
    Enhanced ByteTracker with team awareness and motion constraints
    Prevents most ID switching during overlaps
    """
    
    def __init__(self, base_tracker):
        self.base_tracker = base_tracker
        
        # Track history for smart decisions
        self.track_history = {}  # {track_id: {'team': 1/2, 'positions': [(x,y), ...], 'last_frame': N}}
        self.team_colors = {1: (255, 255, 255), 2: (0, 255, 0)}  # Default colors
        
        # Smart constraints
        self.max_velocity = 150  # Max pixels per frame a player can move
        self.team_lock_enabled = True
        self.motion_constraint_enabled = True
        
    def get_position_from_bbox(self, bbox):
        """Get center position from bounding box"""
        return ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)
    
    def calculate_distance(self, pos1, pos2):
        """Calculate distance between two positions"""
        return np.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
    
    def validate_track_assignment(self, track_id, new_bbox, new_team, frame_num):
        """
        Validate if a track assignment makes sense based on:
        1. Team consistency
        2. Motion constraints
        """
        if track_id not in self.track_history:
            return True  # New track, allow
        
        history = self.track_history[track_id]
        
        # 1. TEAM LOCK: Players cannot change teams
        if self.team_lock_enabled and 'team' in history:
            if history['team'] != new_team:
                print(f"🚫 BLOCKED: Track {track_id} trying to switch from Team {history['team']} to Team {new_team}")
                return False
        
        # 2. MOTION CONSTRAINT: Players cannot teleport
        if self.motion_constraint_enabled and 'positions' in history and history['positions']:
            last_pos = history['positions'][-1]
            new_pos = self.get_position_from_bbox(new_bbox)
            distance = self.calculate_distance(last_pos, new_pos)
            
            if distance > self.max_velocity:
                print(f"⚡ BLOCKED: Track {track_id} moved {distance:.0f}px (max: {self.max_velocity}px)")
                return False
        
        return True
    
    def update_track_history(self, track_id, bbox, team, frame_num):
        """Update the history for a track"""
        position = self.get_position_from_bbox(bbox)
        
        if track_id not in self.track_history:
            team_color = self.team_colors.get(team, (128, 128, 128))
            # Ensure color is a tuple
            if not isinstance(team_color, tuple):
                team_color = tuple(map(int, team_color)) if hasattr(team_color, '__iter__') else (128, 128, 128)
            
            self.track_history[track_id] = {
                'team': team,
                'positions': [position],
                'last_frame': frame_num,
                'team_color': team_color
            }
            print(f"🆕 New smart track {track_id} (Team {team})")
        else:
            history = self.track_history[track_id]
            
            # Lock team on first assignment
            if 'team' not in history:
                team_color = self.team_colors.get(team, (128, 128, 128))
                # Ensure color is a tuple
                if not isinstance(team_color, tuple):
                    team_color = tuple(map(int, team_color)) if hasattr(team_color, '__iter__') else (128, 128, 128)
                
                history['team'] = team
                history['team_color'] = team_color
                print(f"🔒 Locked track {track_id} to Team {team}")
            
            # Update position history (keep last 10 positions)
            history['positions'].append(position)
            if len(history['positions']) > 10:
                history['positions'] = history['positions'][-10:]
            
            history['last_frame'] = frame_num
    
    def cleanup_old_tracks(self, frame_num, max_age=60):
        """Remove tracks not seen for a while"""
        to_remove = []
        for track_id, history in self.track_history.items():
            if frame_num - history['last_frame'] > max_age:
                to_remove.append(track_id)
        
        for track_id in to_remove:
            print(f"🗑️ Removing old track {track_id}")
            del self.track_history[track_id]
    
    def process_frame_detections(self, raw_detections, frame_num, team_assigner, current_frame=None):
        """
        Process a frame's detections with smart tracking
        """
        # First, run standard ByteTracker
        tracked_detections = self.base_tracker.update_with_detections(raw_detections)
        
        # Now apply smart filtering
        smart_tracks = {}
        rejected_tracks = []
        
        for detection in tracked_detections:
            bbox = detection[0].tolist()
            track_id = int(detection[4])
            
            # Get team assignment
            try:
                team = team_assigner.get_player_team(current_frame, bbox, track_id) if team_assigner else 1
                if team is None:
                    team = 1
            except Exception as e:
                print(f"Error getting team for track {track_id}: {e}")
                team = 1
            
            # Validate this assignment
            if self.validate_track_assignment(track_id, bbox, team, frame_num):
                # Use locked team if available
                if track_id in self.track_history and 'team' in self.track_history[track_id]:
                    locked_team = self.track_history[track_id]['team']
                    locked_color = self.track_history[track_id]['team_color']
                else:
                    locked_team = team
                    locked_color = self.team_colors.get(team, (128, 128, 128))
                
                # Ensure color is a tuple for OpenCV
                if not isinstance(locked_color, tuple):
                    locked_color = tuple(map(int, locked_color)) if hasattr(locked_color, '__iter__') else (128, 128, 128)
                
                smart_tracks[track_id] = {
                    "bbox": bbox,
                    "team": locked_team,
                    "team_color": locked_color
                }
                
                # Update history
                self.update_track_history(track_id, bbox, locked_team, frame_num)
            else:
                rejected_tracks.append(track_id)
        
        # Clean up old tracks
        self.cleanup_old_tracks(frame_num)
        
        if rejected_tracks:
            print(f"🛡️ Smart tracker rejected {len(rejected_tracks)} invalid assignments")
        
        return smart_tracks
    
    def set_team_colors(self, team_colors):
        """Update team colors from team assigner"""
        self.team_colors.update(team_colors)
    
    def get_stats(self):
        """Get tracking statistics"""
        total_tracks = len(self.track_history)
        team_1_count = sum(1 for h in self.track_history.values() if h.get('team') == 1)
        team_2_count = sum(1 for h in self.track_history.values() if h.get('team') == 2)
        
        return {
            'total_tracks': total_tracks,
            'team_1_tracks': team_1_count,
            'team_2_tracks': team_2_count,
            'constraints_active': {
                'team_lock': self.team_lock_enabled,
                'motion_limit': self.motion_constraint_enabled
            }
        }