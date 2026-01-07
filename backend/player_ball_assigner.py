import sys
sys.path.append('./src/utils')
from src.utils.bbox_utils import get_center_of_bbox

def measure_distance(p1, p2):
    """Measure distance between two points"""
    return ((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)**0.5

class PlayerBallAssigner:
    def __init__(self):
        self.max_player_ball_distance = 70
    
    def assign_ball_to_player(self, players, ball_bbox):
        """Assign ball to the closest player within range"""
        ball_position = get_center_of_bbox(ball_bbox)

        minimum_distance = 99999
        assigned_player = -1

        for player_id, player in players.items():
            player_bbox = player['bbox']

            # Check distance from both left and right sides of player
            distance_left = measure_distance((player_bbox[0], player_bbox[3]), ball_position)
            distance_right = measure_distance((player_bbox[2], player_bbox[3]), ball_position)
            distance = min(distance_left, distance_right)

            if distance < self.max_player_ball_distance:
                if distance < minimum_distance:
                    minimum_distance = distance
                    assigned_player = player_id

        return assigned_player