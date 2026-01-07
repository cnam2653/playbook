import cv2
import numpy as np
from ultralytics import YOLO
import os
from typing import List, Tuple, Optional
import logging

from ..models.detection import Detection, BoundingBox

logger = logging.getLogger(__name__)

class SportsDetector:
    def __init__(self, model_path: str = None):
        self.model_path = model_path or os.path.join(os.path.dirname(__file__), '../../../best.pt')
        self.model = None
        self.class_mapping = {
            'person': 0,
            'ball': 1,
            'player': 0,
            'football': 1,
            'soccer_ball': 1
        }
        
    def initialize(self):
        """Initialize YOLOv8 model with your custom best.pt"""
        try:
            if not os.path.exists(self.model_path):
                logger.warning(f"Custom model not found at {self.model_path}, falling back to yolov8n.pt")
                self.model_path = 'yolov8n.pt'
            
            self.model = YOLO(self.model_path)
            logger.info(f"YOLOv8 model loaded: {self.model_path}")
            
            # Print model classes for debugging
            if hasattr(self.model, 'names'):
                logger.info(f"Model classes: {self.model.names}")
            
        except Exception as e:
            logger.error(f"Failed to load YOLOv8 model: {e}")
            raise
            
    def detect_frame(self, frame: np.ndarray, frame_id: int, timestamp: float) -> List[Detection]:
        """Detect players and ball in a single frame"""
        if self.model is None:
            raise RuntimeError("Model not initialized. Call initialize() first")
        
        detections = []
        
        try:
            # Run YOLOv8 prediction
            results = self.model.predict(frame, conf=0.3, verbose=False)
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Extract box coordinates and confidence
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        confidence = float(box.conf[0].cpu().numpy())
                        class_id = int(box.cls[0].cpu().numpy())
                        class_name = self.model.names[class_id]
                        
                        # Determine object type based on class name
                        object_type = self._classify_object(class_name)
                        
                        if object_type:  # Only keep players and balls
                            bbox = BoundingBox(
                                x1=float(x1), y1=float(y1),
                                x2=float(x2), y2=float(y2),
                                confidence=confidence
                            )
                            
                            detection = Detection(
                                bbox=bbox,
                                class_name=object_type,
                                class_id=self.class_mapping.get(object_type, class_id),
                                frame_id=frame_id,
                                timestamp=timestamp
                            )
                            detections.append(detection)
                            
        except Exception as e:
            logger.error(f"Detection failed for frame {frame_id}: {e}")
        
        return detections
    
    def _classify_object(self, class_name: str) -> Optional[str]:
        """Classify detected object as player or ball"""
        class_name_lower = class_name.lower()
        
        # Ball detection
        if any(keyword in class_name_lower for keyword in ['ball', 'football', 'soccer']):
            return 'ball'
        
        # Player detection  
        if any(keyword in class_name_lower for keyword in ['person', 'player', 'human']):
            return 'player'
            
        return None
    
    def process_video(self, video_path: str, output_callback=None) -> List[List[Detection]]:
        """Process entire video and return detections for each frame"""
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        all_detections = []
        frame_id = 0
        
        logger.info(f"Processing video: {video_path} ({total_frames} frames, {fps} fps)")
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            timestamp = frame_id / fps
            detections = self.detect_frame(frame, frame_id, timestamp)
            all_detections.append(detections)
            
            if output_callback:
                output_callback(frame_id, total_frames, detections)
            
            frame_id += 1
            
            if frame_id % 30 == 0:  # Log every 30 frames
                logger.info(f"Processed {frame_id}/{total_frames} frames")
        
        cap.release()
        logger.info(f"Video processing complete: {frame_id} frames processed")
        return all_detections