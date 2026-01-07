import numpy as np
from collections import defaultdict

class IDStabilizer:
    def __init__(self):
        # Master registry - once a player gets an ID and team, it NEVER changes
        self.stable_registry = {}  # {stable_id: {'bytetrack_ids': [list], 'team': 1/2, 'team_color': (r,g,b)}}
        self.bytetrack_to_stable = {}  # {bytetrack_id: stable_id}
        
        # Position tracking for reconnection
        self.position_history = defaultdict(list)  # {stable_id: [(frame, x, y)]}
        self.last_seen = {}  # {stable_id: frame_num}
        
        # ID counters
        self.next_stable_id = 1
        self.max_distance_reconnect = 80  # pixels
        self.max_frames_missing = 10      # frames
    
    def get_position_from_bbox(self, bbox):
        """Get center position from bounding box"""
        return ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)
    
    def find_missing_player_by_position(self, position, frame_num):
        """Find a missing stable player who might be this new detection"""
        x, y = position
        best_match = None
        best_distance = float('inf')
        
        for stable_id, info in self.stable_registry.items():
            # Check if this player has been missing recently
            if (stable_id in self.last_seen and 
                frame_num - self.last_seen[stable_id] <= self.max_frames_missing and
                frame_num - self.last_seen[stable_id] > 0):
                
                # Get their last known position
                if stable_id in self.position_history and self.position_history[stable_id]:
                    last_frame, last_x, last_y = self.position_history[stable_id][-1]
                    distance = np.sqrt((x - last_x)**2 + (y - last_y)**2)
                    
                    if distance < self.max_distance_reconnect and distance < best_distance:
                        best_distance = distance
                        best_match = stable_id
        
        return best_match
    
    def stabilize_frame_tracks(self, raw_tracks, frame_num, team_assigner):
        """Convert unstable ByteTracker IDs to stable consistent IDs"""
        stable_tracks = {}
        
        for bytetrack_id, track_data in raw_tracks.items():
            bbox = track_data['bbox']
            position = self.get_position_from_bbox(bbox)
            
            # Check if we already know this ByteTracker ID
            if bytetrack_id in self.bytetrack_to_stable:
                stable_id = self.bytetrack_to_stable[bytetrack_id]
                
                # Verify the player hasn't moved too far (sanity check)
                if stable_id in self.position_history and self.position_history[stable_id]:
                    last_frame, last_x, last_y = self.position_history[stable_id][-1]
                    distance = np.sqrt((position[0] - last_x)**2 + (position[1] - last_y)**2)
                    
                    if distance > 200:  # Player moved impossibly far
                        print(f"⚠️  Player {stable_id} moved {distance:.0f}px - possible ID switch")
                        # Still use it but log the issue
                
            else:
                # New ByteTracker ID - try to reconnect with missing player
                stable_id = self.find_missing_player_by_position(position, frame_num)
                
                if stable_id is None:
                    # Create new stable player
                    stable_id = self.next_stable_id
                    self.next_stable_id += 1
                    
                    # Get team assignment ONCE and lock it forever
                    team = team_assigner.get_player_team(None, bbox, stable_id) if team_assigner else 1
                    team_color = (255, 255, 255) if team == 1 else (0, 255, 0)
                    
                    self.stable_registry[stable_id] = {
                        'bytetrack_ids': [bytetrack_id],
                        'team': team,
                        'team_color': team_color
                    }
                    
                    print(f"🆕 New stable player {stable_id} (Team {team}) from ByteTracker ID {bytetrack_id}")
                else:
                    # Reconnect with existing stable player
                    self.stable_registry[stable_id]['bytetrack_ids'].append(bytetrack_id)
                    print(f"🔗 Reconnected stable player {stable_id} with ByteTracker ID {bytetrack_id}")
                
                # Map this ByteTracker ID to stable ID
                self.bytetrack_to_stable[bytetrack_id] = stable_id
            
            # Update tracking info
            self.last_seen[stable_id] = frame_num
            self.position_history[stable_id].append((frame_num, position[0], position[1]))
            
            # Keep only recent history
            if len(self.position_history[stable_id]) > 20:
                self.position_history[stable_id] = self.position_history[stable_id][-20:]
            
            # Create stable track with LOCKED team info
            stable_track = track_data.copy()
            stable_track['team'] = self.stable_registry[stable_id]['team']
            stable_track['team_color'] = self.stable_registry[stable_id]['team_color']
            
            stable_tracks[stable_id] = stable_track
        
        # Clean up old mappings
        self.cleanup_old_players(frame_num)
        
        return stable_tracks
    
    def cleanup_old_players(self, frame_num):
        """Remove players not seen for a long time"""
        to_remove = []
        
        for stable_id in list(self.stable_registry.keys()):
            if stable_id in self.last_seen and frame_num - self.last_seen[stable_id] > 120:  # 5 seconds
                # Remove from all mappings
                bytetrack_ids = self.stable_registry[stable_id]['bytetrack_ids']
                for bt_id in bytetrack_ids:
                    if bt_id in self.bytetrack_to_stable:
                        del self.bytetrack_to_stable[bt_id]
                
                to_remove.append(stable_id)
        
        for stable_id in to_remove:
            print(f"🗑️  Removing old player {stable_id}")
            del self.stable_registry[stable_id]
            if stable_id in self.last_seen:
                del self.last_seen[stable_id]
            if stable_id in self.position_history:
                del self.position_history[stable_id]
    
    def get_stats(self):
        """Get current tracking statistics"""
        return {
            'active_players': len(self.stable_registry),
            'bytetrack_mappings': len(self.bytetrack_to_stable),
            'team_1_players': len([p for p in self.stable_registry.values() if p['team'] == 1]),
            'team_2_players': len([p for p in self.stable_registry.values() if p['team'] == 2])
        }