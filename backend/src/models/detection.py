from dataclasses import dataclass
from typing import List, Optional
import numpy as np

@dataclass
class BoundingBox:
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float
    
    @property
    def center_x(self) -> float:
        return (self.x1 + self.x2) / 2
    
    @property
    def center_y(self) -> float:
        return (self.y1 + self.y2) / 2
    
    @property
    def width(self) -> float:
        return self.x2 - self.x1
    
    @property
    def height(self) -> float:
        return self.y2 - self.y1
    
    @property
    def area(self) -> float:
        return self.width * self.height

@dataclass
class Detection:
    bbox: BoundingBox
    class_name: str
    class_id: int
    frame_id: int
    timestamp: float

@dataclass
class TrackedObject:
    track_id: int
    detections: List[Detection]
    object_type: str  # 'player' or 'ball'
    team_id: Optional[int] = None
    
    @property
    def latest_detection(self) -> Optional[Detection]:
        return self.detections[-1] if self.detections else None
    
    @property
    def trajectory(self) -> List[tuple]:
        return [(d.bbox.center_x, d.bbox.center_y) for d in self.detections]

@dataclass
class FrameAnalysis:
    frame_id: int
    timestamp: float
    detections: List[Detection]
    tracked_objects: List[TrackedObject]
    ball_possession: Optional[int] = None  # track_id of player with ball
    
@dataclass
class VideoAnalysis:
    analysis_id: str
    video_path: str
    sport: str
    fps: float
    total_frames: int
    frame_analyses: List[FrameAnalysis]
    tracked_objects: List[TrackedObject]
    
    def get_player_objects(self) -> List[TrackedObject]:
        return [obj for obj in self.tracked_objects if obj.object_type == 'player']
    
    def get_ball_object(self) -> Optional[TrackedObject]:
        ball_objects = [obj for obj in self.tracked_objects if obj.object_type == 'ball']
        return ball_objects[0] if ball_objects else None