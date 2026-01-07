import numpy as np
from typing import List, Dict, Optional
import logging
from filterpy.kalman import KalmanFilter
from scipy.optimize import linear_sum_assignment
import math

from ..models.detection import Detection, TrackedObject, BoundingBox

logger = logging.getLogger(__name__)

class KalmanBoxTracker:
    """Individual object tracker using Kalman filter"""
    count = 0
    
    def __init__(self, bbox: BoundingBox, object_type: str):
        self.kf = KalmanFilter(dim_x=7, dim_z=4)
        
        # State: [x, y, s, r, dx, dy, ds] where s=scale, r=aspect ratio
        self.kf.F = np.array([
            [1,0,0,0,1,0,0],
            [0,1,0,0,0,1,0],
            [0,0,1,0,0,0,1],
            [0,0,0,1,0,0,0],
            [0,0,0,0,1,0,0],
            [0,0,0,0,0,1,0],
            [0,0,0,0,0,0,1]
        ])
        
        # Measurement function
        self.kf.H = np.array([
            [1,0,0,0,0,0,0],
            [0,1,0,0,0,0,0],
            [0,0,1,0,0,0,0],
            [0,0,0,1,0,0,0]
        ])
        
        self.kf.R[2:,2:] *= 10.0  # Measurement noise
        self.kf.P[4:,4:] *= 1000.0  # High uncertainty for velocities
        self.kf.P *= 10.0
        self.kf.Q[-1,-1] *= 0.01  # Process noise
        self.kf.Q[4:,4:] *= 0.01
        
        self.kf.x[:4] = self._convert_bbox_to_z(bbox)
        
        self.time_since_update = 0
        self.id = KalmanBoxTracker.count
        KalmanBoxTracker.count += 1
        self.history = []
        self.hits = 0
        self.hit_streak = 0
        self.age = 0
        self.object_type = object_type
        
    def update(self, bbox: BoundingBox):
        """Update tracker with new detection"""
        self.time_since_update = 0
        self.history = []
        self.hits += 1
        self.hit_streak += 1
        self.kf.update(self._convert_bbox_to_z(bbox))
        
    def predict(self):
        """Predict next state"""
        if (self.kf.x[6] + self.kf.x[2]) <= 0:
            self.kf.x[6] *= 0.0
        self.kf.predict()
        self.age += 1
        if self.time_since_update > 0:
            self.hit_streak = 0
        self.time_since_update += 1
        self.history.append(self._convert_x_to_bbox(self.kf.x))
        return self.history[-1]
        
    def get_state(self) -> BoundingBox:
        """Get current bounding box"""
        return self._convert_x_to_bbox(self.kf.x)
    
    @staticmethod
    def _convert_bbox_to_z(bbox: BoundingBox):
        """Convert bounding box to measurement space"""
        w = bbox.x2 - bbox.x1
        h = bbox.y2 - bbox.y1
        x = bbox.x1 + w/2.0
        y = bbox.y1 + h/2.0
        s = w * h
        r = w / float(h) if h != 0 else 1.0
        return np.array([x, y, s, r]).reshape((4, 1))
    
    @staticmethod
    def _convert_x_to_bbox(x):
        """Convert state to bounding box"""
        w = np.sqrt(x[2] * x[3])
        h = x[2] / w if w != 0 else 1.0
        return BoundingBox(
            x1=x[0] - w/2.0,
            y1=x[1] - h/2.0,
            x2=x[0] + w/2.0,
            y2=x[1] + h/2.0,
            confidence=0.0
        )

class ByteTracker:
    """Multi-object tracker based on ByteTrack algorithm"""
    
    def __init__(self, max_lost_time: int = 30, min_hits: int = 3):
        self.max_lost_time = max_lost_time
        self.min_hits = min_hits
        self.trackers: List[KalmanBoxTracker] = []
        self.frame_count = 0
        
    def update(self, detections: List[Detection]) -> List[TrackedObject]:
        """Update tracker with new detections"""
        self.frame_count += 1
        
        # Predict all trackers
        for tracker in self.trackers:
            tracker.predict()
        
        # Separate high and low confidence detections
        high_conf_dets = [d for d in detections if d.bbox.confidence >= 0.6]
        low_conf_dets = [d for d in detections if d.bbox.confidence < 0.6]
        
        # First association with high confidence detections
        matched_trackers, unmatched_dets, unmatched_trks = self._associate_detections_to_trackers(
            high_conf_dets, self.trackers
        )
        
        # Update matched trackers
        for tracker_idx, det_idx in matched_trackers:
            self.trackers[tracker_idx].update(high_conf_dets[det_idx].bbox)
        
        # Second association with low confidence detections and unmatched trackers
        remaining_trackers = [self.trackers[i] for i in unmatched_trks]
        matched_trackers_2, unmatched_dets_2, unmatched_trks_2 = self._associate_detections_to_trackers(
            low_conf_dets, remaining_trackers
        )
        
        # Update remaining matched trackers
        for tracker_idx, det_idx in matched_trackers_2:
            remaining_trackers[tracker_idx].update(low_conf_dets[det_idx].bbox)
        
        # Create new trackers for unmatched high confidence detections
        for det_idx in unmatched_dets:
            detection = high_conf_dets[det_idx]
            tracker = KalmanBoxTracker(detection.bbox, detection.class_name)
            self.trackers.append(tracker)
        
        # Remove dead trackers
        active_trackers = []
        for tracker in self.trackers:
            if tracker.time_since_update < self.max_lost_time:
                active_trackers.append(tracker)
        self.trackers = active_trackers
        
        # Convert to TrackedObject format
        tracked_objects = []
        for tracker in self.trackers:
            if tracker.hits >= self.min_hits or self.frame_count <= self.min_hits:
                bbox = tracker.get_state()
                detection = Detection(
                    bbox=bbox,
                    class_name=tracker.object_type,
                    class_id=0 if tracker.object_type == 'player' else 1,
                    frame_id=self.frame_count,
                    timestamp=self.frame_count / 30.0  # Assume 30fps
                )
                
                tracked_obj = TrackedObject(
                    track_id=tracker.id,
                    detections=[detection],
                    object_type=tracker.object_type
                )
                tracked_objects.append(tracked_obj)
        
        return tracked_objects
    
    def _associate_detections_to_trackers(self, detections: List[Detection], trackers: List[KalmanBoxTracker]):
        """Associate detections to trackers using IoU and Hungarian algorithm"""
        if len(trackers) == 0:
            return [], list(range(len(detections))), []
        
        iou_matrix = np.zeros((len(detections), len(trackers)))
        
        for d, detection in enumerate(detections):
            for t, tracker in enumerate(trackers):
                # Only associate same object types
                if detection.class_name != tracker.object_type:
                    continue
                    
                pred_bbox = tracker.get_state()
                iou = self._calculate_iou(detection.bbox, pred_bbox)
                iou_matrix[d, t] = iou
        
        # Hungarian algorithm for optimal assignment
        threshold = 0.3
        matched_indices = linear_sum_assignment(-iou_matrix)
        matched_trackers = []
        
        for d, t in zip(*matched_indices):
            if iou_matrix[d, t] < threshold:
                continue
            matched_trackers.append((t, d))
        
        unmatched_detections = []
        for d in range(len(detections)):
            if d not in [match[1] for match in matched_trackers]:
                unmatched_detections.append(d)
        
        unmatched_trackers = []
        for t in range(len(trackers)):
            if t not in [match[0] for match in matched_trackers]:
                unmatched_trackers.append(t)
        
        return matched_trackers, unmatched_detections, unmatched_trackers
    
    @staticmethod
    def _calculate_iou(bbox1: BoundingBox, bbox2: BoundingBox) -> float:
        """Calculate Intersection over Union of two bounding boxes"""
        x1 = max(bbox1.x1, bbox2.x1)
        y1 = max(bbox1.y1, bbox2.y1)
        x2 = min(bbox1.x2, bbox2.x2)
        y2 = min(bbox1.y2, bbox2.y2)
        
        if x2 < x1 or y2 < y1:
            return 0.0
        
        intersection = (x2 - x1) * (y2 - y1)
        area1 = bbox1.area
        area2 = bbox2.area
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0