import cv2
import numpy as np
from sklearn.cluster import KMeans

class TeamAssigner:
    def __init__(self):
        self.team_colors = {}
        self.player_team_dict = {}
        self.kmeans = None
    
    def get_clustering_model(self, image):
        """Create K-means clustering model for jersey color detection"""
        # Reshape the image to 2D array
        image_2d = image.reshape(-1, 3)
        
        # Perform K-means with 2 clusters
        kmeans = KMeans(n_clusters=2, init="k-means++", n_init=1, random_state=42)
        kmeans.fit(image_2d)
        
        return kmeans
    
    def get_player_color(self, frame, bbox):
        """Extract the dominant jersey color from player's bounding box"""
        try:
            # Extract player image from bounding box
            x1, y1, x2, y2 = map(int, bbox)
            
            # Validate bbox coordinates
            if x2 <= x1 or y2 <= y1 or x1 < 0 or y1 < 0:
                return np.array([128, 128, 128])  # Default gray
            
            # Ensure bbox is within frame bounds
            h, w = frame.shape[:2]
            x1, x2 = max(0, x1), min(w, x2)
            y1, y2 = max(0, y1), min(h, y2)
            
            image = frame[y1:y2, x1:x2]
        except Exception as e:
            print(f"Error extracting player image: {e}")
            return np.array([128, 128, 128])
        
        # Take only the top third (chest area - most reliable for jersey)
        top_third_image = image[0:int(image.shape[0]/3), :]
        
        # Handle small images
        if top_third_image.shape[0] < 5 or top_third_image.shape[1] < 5:
            return np.array([128, 128, 128])  # Default gray
        
        # Get clustering model
        kmeans = self.get_clustering_model(top_third_image)
        
        # Get cluster labels for each pixel
        labels = kmeans.labels_
        
        # Reshape labels to image shape
        clustered_image = labels.reshape(top_third_image.shape[0], top_third_image.shape[1])
        
        # Better background detection - use center region instead of just corners
        h, w = clustered_image.shape
        center_region = clustered_image[h//4:3*h//4, w//4:3*w//4]
        
        if center_region.size > 0:
            # The center region should contain mostly jersey
            jersey_cluster_candidate = np.bincount(center_region.flatten()).argmax()
            
            # Verify this isn't background by checking if it's too common on edges
            edge_pixels = np.concatenate([
                clustered_image[0, :], clustered_image[-1, :],
                clustered_image[:, 0], clustered_image[:, -1]
            ])
            edge_cluster_counts = np.bincount(edge_pixels)
            
            # If the center cluster appears too much on edges, it's likely background
            if len(edge_cluster_counts) > jersey_cluster_candidate:
                edge_ratio = edge_cluster_counts[jersey_cluster_candidate] / len(edge_pixels)
                if edge_ratio > 0.6:  # More than 60% of edge is this color = background
                    player_cluster = 1 - jersey_cluster_candidate
                else:
                    player_cluster = jersey_cluster_candidate
            else:
                player_cluster = jersey_cluster_candidate
        else:
            # Fallback to original corner method
            corner_clusters = [
                clustered_image[0, 0], clustered_image[0, -1], 
                clustered_image[-1, 0], clustered_image[-1, -1]
            ]
            non_player_cluster = max(set(corner_clusters), key=corner_clusters.count)
            player_cluster = 1 - non_player_cluster
        
        # Return the jersey color (BGR format)
        player_color = kmeans.cluster_centers_[player_cluster]
        
        return player_color
    
    def assign_team_color(self, frame, player_detections):
        """Assign team colors based on all players in first frame"""
        player_colors = []
        
        # Extract jersey colors from all players
        for _, player_detection in player_detections.items():
            bbox = player_detection["bbox"]
            player_color = self.get_player_color(frame, bbox)
            player_colors.append(player_color)
        
        if len(player_colors) < 2:
            # Not enough players to determine teams
            self.team_colors[1] = np.array([255, 0, 0])    # Red team
            self.team_colors[2] = np.array([0, 0, 255])    # Blue team
            return
        
        # Cluster all player colors into 2 teams
        kmeans = KMeans(n_clusters=2, init="k-means++", n_init=10, random_state=42)
        kmeans.fit(player_colors)
        
        # Determine which cluster is "white" vs "colored" based on brightness
        cluster1_brightness = np.mean(kmeans.cluster_centers_[0])
        cluster2_brightness = np.mean(kmeans.cluster_centers_[1])
        
        # Assign cluster labels so that Team 1 = lighter team, Team 2 = darker/more colored team
        if cluster1_brightness > cluster2_brightness:
            # Cluster 0 is lighter (white), Cluster 1 is darker (green)
            white_cluster_id = 0
            colored_cluster_id = 1
        else:
            # Cluster 1 is lighter (white), Cluster 0 is darker (green)  
            white_cluster_id = 1
            colored_cluster_id = 0
        
        self.kmeans = kmeans
        self.white_cluster_id = white_cluster_id
        self.colored_cluster_id = colored_cluster_id
        
        # Assign team colors and convert to tuples for OpenCV
        color1 = self.convert_to_display_color(kmeans.cluster_centers_[white_cluster_id])
        color2 = self.convert_to_display_color(kmeans.cluster_centers_[colored_cluster_id])
        
        self.team_colors[1] = tuple(map(int, color1))    # White team
        self.team_colors[2] = tuple(map(int, color2))    # Colored team
        
        print(f"Team 1 Color: {self.team_colors[1]}")
        print(f"Team 2 Color: {self.team_colors[2]}")
    
    def convert_to_display_color(self, color):
        """Use the actual detected jersey color, just make it more visible"""
        r, g, b = color
        
        # Boost saturation and brightness for better visibility
        # Convert to int to avoid numpy int64 issues
        r = min(255, int(r * 1.2))  # Boost by 20%
        g = min(255, int(g * 1.2)) 
        b = min(255, int(b * 1.2))
        
        # Ensure minimum brightness for visibility
        if r + g + b < 150:  # Too dark
            r = min(255, r + 50)
            g = min(255, g + 50)  
            b = min(255, b + 50)
        
        return np.array([b, g, r])  # Return in BGR format for OpenCV
    
    def get_player_team(self, frame, player_bbox, player_id):
        """Get team assignment for a specific player"""
        # CRITICAL: Once a player gets a team, they NEVER change teams
        if player_id in self.player_team_dict:
            return self.player_team_dict[player_id]
        
        if self.kmeans is None:
            # Teams not initialized yet, return default
            return 1
        
        if frame is None:
            # Can't analyze color without frame, return default
            return 1
        
        # Get player's jersey color
        player_color = self.get_player_color(frame, player_bbox)
        
        # Debug: Print color for player 21
        if player_id == 21:
            print(f"Player 21 detected color: {player_color}")
        
        # Predict which team cluster this color belongs to
        cluster_id = self.kmeans.predict(player_color.reshape(1, -1))[0]
        
        # Convert cluster ID to team ID using our mapping
        if cluster_id == self.white_cluster_id:
            team_id = 1  # White team
        else:
            team_id = 2  # Colored team
        
        # LOCK this player to this team permanently
        self.player_team_dict[player_id] = team_id
        print(f"🔒 Player {player_id} locked to Team {team_id}")
        
        return team_id
    
    def assign_teams_to_tracks(self, video_frames, tracks):
        """Assign teams to all players in all tracks"""
        if not tracks['players'] or not video_frames:
            return tracks
        
        # Use first frame to determine team colors
        first_frame = video_frames[0]
        first_frame_players = tracks['players'][0]
        
        if first_frame_players:
            # Initialize team colors based on first frame
            self.assign_team_color(first_frame, first_frame_players)
            
            # Assign teams to all players across all frames
            for frame_num, player_track in enumerate(tracks['players']):
                for player_id, track in player_track.items():
                    # Get team assignment
                    team = self.get_player_team(video_frames[frame_num], track['bbox'], player_id)
                    
                    # Add team info to track
                    tracks['players'][frame_num][player_id]['team'] = team
                    tracks['players'][frame_num][player_id]['team_color'] = self.team_colors[team]
        
        return tracks