import numpy as np
from collections import defaultdict
import pickle
import os

class PersistentIDManager:
    def __init__(self):
        # Permanent player registry - once assigned, never changes
        self.player_registry = {}  # {player_id: {'team': 1/2, 'color': (r,g,b), 'last_seen': frame_num}}
        self.next_team1_id = 1    # Next ID for team 1 (1-11)
        self.next_team2_id = 12   # Next ID for team 2 (12-22)
        
        # Track positions for reconnection
        self.position_history = defaultdict(list)  # {player_id: [(frame, x, y), ...]}
        self.max_distance_for_reconnect = 100  # pixels
        self.max_frames_missing = 15  # frames
        
    def get_position_from_bbox(self, bbox):
        """Get center position from bounding box"""
        return ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)
    
    def find_closest_missing_player(self, position, team, frame_num):
        """Find a missing player who might be this detection"""
        x, y = position
        best_match = None
        best_distance = float('inf')
        
        for player_id, info in self.player_registry.items():
            if (info['team'] == team and 
                frame_num - info['last_seen'] <= self.max_frames_missing and
                frame_num - info['last_seen'] > 0):  # Missing for a few frames
                
                # Get their last known position
                if player_id in self.position_history and self.position_history[player_id]:
                    last_frame, last_x, last_y = self.position_history[player_id][-1]
                    distance = np.sqrt((x - last_x)**2 + (y - last_y)**2)
                    
                    if distance < self.max_distance_for_reconnect and distance < best_distance:
                        best_distance = distance
                        best_match = player_id
        
        return best_match
    
    def assign_new_id(self, team):
        """Assign a new ID for a team (1-11 for team 1, 12-22 for team 2)"""
        if team == 1 and self.next_team1_id <= 11:
            new_id = self.next_team1_id
            self.next_team1_id += 1
            return new_id
        elif team == 2 and self.next_team2_id <= 22:
            new_id = self.next_team2_id
            self.next_team2_id += 1
            return new_id
        return None  # Team full
    
    def get_team_color(self, team):
        """Get team color - white for team 1, green for team 2"""
        if team == 1:
            return (255, 255, 255)  # White
        else:
            return (0, 255, 0)      # Green
    
    def process_frame_tracks(self, frame_tracks, frame_num, team_assigner):
        """Process a frame's tracks and assign persistent IDs and colors"""
        stable_tracks = {}
        current_frame_players = set()
        
        for track_id, track_data in frame_tracks.items():
            bbox = track_data['bbox']
            position = self.get_position_from_bbox(bbox)
            
            # Get team assignment
            team = team_assigner.get_player_team(None, bbox, track_id) if team_assigner else 1
            
            # Try to reconnect with existing player
            persistent_id = self.find_closest_missing_player(position, team, frame_num)
            
            if persistent_id is None:
                # Create new player
                persistent_id = self.assign_new_id(team)
                
                if persistent_id is not None:
                    # Register new player with permanent color and team
                    self.player_registry[persistent_id] = {
                        'team': team,
                        'color': self.get_team_color(team),
                        'last_seen': frame_num
                    }
                    print(f"🆕 New player {persistent_id} assigned to team {team}")
            
            if persistent_id is not None:
                # Update player info
                self.player_registry[persistent_id]['last_seen'] = frame_num
                self.position_history[persistent_id].append((frame_num, position[0], position[1]))
                
                # Keep only recent position history
                if len(self.position_history[persistent_id]) > 30:
                    self.position_history[persistent_id] = self.position_history[persistent_id][-30:]
                
                # Create stable track with permanent info
                stable_track = track_data.copy()
                stable_track['team'] = self.player_registry[persistent_id]['team']
                stable_track['team_color'] = self.player_registry[persistent_id]['color']
                stable_track['persistent_id'] = persistent_id
                
                stable_tracks[persistent_id] = stable_track
                current_frame_players.add(persistent_id)
        
        # Clean up old players not seen for too long
        to_remove = []
        for player_id, info in self.player_registry.items():
            if frame_num - info['last_seen'] > 60:  # 60 frames = ~2.4 seconds
                to_remove.append(player_id)
        
        for player_id in to_remove:
            print(f"🗑️ Removing inactive player {player_id}")
            del self.player_registry[player_id]
            if player_id in self.position_history:
                del self.position_history[player_id]
        
        return stable_tracks
    
    def get_current_players(self):
        """Get info about all currently active players"""
        return self.player_registry.copy()
    
    def save_registry(self, path):
        """Save the player registry for caching"""
        data = {
            'player_registry': self.player_registry,
            'next_team1_id': self.next_team1_id,
            'next_team2_id': self.next_team2_id,
            'position_history': dict(self.position_history)
        }
        with open(path, 'wb') as f:
            pickle.dump(data, f)
    
    def load_registry(self, path):
        """Load the player registry from cache"""
        if os.path.exists(path):
            with open(path, 'rb') as f:
                data = pickle.load(f)
                self.player_registry = data.get('player_registry', {})
                self.next_team1_id = data.get('next_team1_id', 1)
                self.next_team2_id = data.get('next_team2_id', 12)
                self.position_history = defaultdict(list, data.get('position_history', {}))
                return True
        return False