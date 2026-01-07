import numpy as np
from collections import defaultdict
import cv2

class IDManager:
    def __init__(self, max_players_per_team=11, max_distance_threshold=50):
        self.max_players_per_team = max_players_per_team
        self.max_distance_threshold = max_distance_threshold
        
        # Track active player IDs per team
        self.active_team1_ids = set()  # IDs 1-11
        self.active_team2_ids = set()  # IDs 12-22
        
        # Position history for track repair
        self.player_positions = defaultdict(list)  # player_id -> list of (frame, x, y)
        self.last_seen = {}  # player_id -> frame_number
        
        # Mapping from original ByteTracker IDs to our consistent IDs
        self.tracker_id_to_consistent_id = {}
        self.consistent_id_to_team = {}
        
    def get_available_id(self, team):
        """Get the next available ID for a team"""
        if team == 1:
            # Team 1: IDs 1-11
            for player_id in range(1, self.max_players_per_team + 1):
                if player_id not in self.active_team1_ids:
                    return player_id
        else:
            # Team 2: IDs 12-22  
            for player_id in range(12, 12 + self.max_players_per_team):
                if player_id not in self.active_team2_ids:
                    return player_id
        
        # If all IDs are taken, return None (shouldn't happen in normal game)
        return None
    
    def add_player_position(self, player_id, frame_num, bbox):
        """Record player position for track repair"""
        x_center = (bbox[0] + bbox[2]) / 2
        y_center = (bbox[1] + bbox[3]) / 2
        
        self.player_positions[player_id].append((frame_num, x_center, y_center))
        self.last_seen[player_id] = frame_num
        
        # Keep only recent positions (last 30 frames)
        if len(self.player_positions[player_id]) > 30:
            self.player_positions[player_id] = self.player_positions[player_id][-30:]
    
    def find_closest_missing_player(self, position, team, frame_num, max_frames_missing=10):
        """Find a missing player from the same team who might be this detection"""
        x, y = position
        best_match = None
        best_distance = float('inf')
        
        # Get IDs for this team
        team_ids = self.active_team1_ids if team == 1 else self.active_team2_ids
        
        for player_id in list(team_ids):
            # Check if this player has been missing for a few frames
            if (player_id in self.last_seen and 
                frame_num - self.last_seen[player_id] <= max_frames_missing and
                frame_num - self.last_seen[player_id] > 0):
                
                # Get their last known position
                if player_id in self.player_positions and self.player_positions[player_id]:
                    last_frame, last_x, last_y = self.player_positions[player_id][-1]
                    distance = np.sqrt((x - last_x)**2 + (y - last_y)**2)
                    
                    if distance < self.max_distance_threshold and distance < best_distance:
                        best_distance = distance
                        best_match = player_id
        
        return best_match
    
    def assign_consistent_ids(self, frame_tracks, frame_num, team_assignments):
        """Assign consistent IDs to players in a frame"""
        consistent_tracks = {}
        
        for tracker_id, track_data in frame_tracks.items():
            bbox = track_data['bbox']
            team = team_assignments.get(tracker_id, 1)
            
            # Get position
            x_center = (bbox[0] + bbox[2]) / 2
            y_center = (bbox[1] + bbox[3]) / 2
            position = (x_center, y_center)
            
            # Check if we already have a mapping for this tracker ID
            if tracker_id in self.tracker_id_to_consistent_id:
                consistent_id = self.tracker_id_to_consistent_id[tracker_id]
            else:
                # Try to reconnect with a missing player from the same team
                consistent_id = self.find_closest_missing_player(position, team, frame_num)
                
                if consistent_id is None:
                    # Assign a new ID
                    consistent_id = self.get_available_id(team)
                
                if consistent_id is not None:
                    self.tracker_id_to_consistent_id[tracker_id] = consistent_id
                    self.consistent_id_to_team[consistent_id] = team
                    
                    # Add to active set
                    if team == 1:
                        self.active_team1_ids.add(consistent_id)
                    else:
                        self.active_team2_ids.add(consistent_id)
            
            if consistent_id is not None:
                # Record position
                self.add_player_position(consistent_id, frame_num, bbox)
                
                # Create new track data with consistent ID
                new_track_data = track_data.copy()
                consistent_tracks[consistent_id] = new_track_data
        
        # Clean up tracker IDs that haven't been seen recently
        self.cleanup_old_mappings(frame_num)
        
        return consistent_tracks
    
    def cleanup_old_mappings(self, frame_num, max_age=60):
        """Remove mappings for players not seen in a while"""
        to_remove = []
        
        for tracker_id, consistent_id in self.tracker_id_to_consistent_id.items():
            if (consistent_id in self.last_seen and 
                frame_num - self.last_seen[consistent_id] > max_age):
                to_remove.append((tracker_id, consistent_id))
        
        for tracker_id, consistent_id in to_remove:
            del self.tracker_id_to_consistent_id[tracker_id]
            
            team = self.consistent_id_to_team.get(consistent_id, 1)
            if team == 1:
                self.active_team1_ids.discard(consistent_id)
            else:
                self.active_team2_ids.discard(consistent_id)
            
            if consistent_id in self.consistent_id_to_team:
                del self.consistent_id_to_team[consistent_id]
    
    def get_team_from_consistent_id(self, consistent_id):
        """Get team number from consistent ID"""
        if 1 <= consistent_id <= 11:
            return 1
        elif 12 <= consistent_id <= 22:
            return 2
        else:
            return 1  # Default