import cv2
import uuid
import json
import os
from typing import Dict, List
import logging
from datetime import datetime

from .detector import SportsDetector
from .tracker import ByteTracker
from ..models.detection import VideoAnalysis, FrameAnalysis, TrackedObject
from ..utils.analytics import PossessionCalculator, MovementAnalyzer, EventExtractor

logger = logging.getLogger(__name__)

class VideoProcessor:
    """Main video processing pipeline"""
    
    def __init__(self):
        self.detector = SportsDetector()
        self.tracker = ByteTracker()
        self.possession_calc = PossessionCalculator()
        self.movement_analyzer = MovementAnalyzer()
        self.event_extractor = EventExtractor()
        
        # Initialize detector with your best.pt model
        try:
            self.detector.initialize()
        except Exception as e:
            logger.warning(f"Could not initialize detector: {e}")
    
    def process_video(self, video_path: str, sport: str = 'soccer') -> str:
        """Process video and return analysis ID"""
        analysis_id = str(uuid.uuid4())
        
        try:
            # Get video info
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0
            cap.release()
            
            logger.info(f"Starting analysis {analysis_id} for video: {video_path}")
            
            # Process video with detector
            all_detections = self.detector.process_video(
                video_path, 
                output_callback=lambda f, t, d: self._log_progress(f, t, analysis_id)
            )
            
            # Track objects across frames
            frame_analyses = []
            all_tracked_objects = {}
            
            self.tracker = ByteTracker()  # Reset tracker
            
            for frame_id, detections in enumerate(all_detections):
                timestamp = frame_id / fps
                
                # Update tracker
                tracked_objects = self.tracker.update(detections)
                
                # Store tracked objects
                for obj in tracked_objects:
                    if obj.track_id not in all_tracked_objects:
                        all_tracked_objects[obj.track_id] = TrackedObject(
                            track_id=obj.track_id,
                            detections=[],
                            object_type=obj.object_type
                        )
                    
                    # Add current detection to tracked object
                    all_tracked_objects[obj.track_id].detections.extend(obj.detections)
                
                # Create frame analysis
                frame_analysis = FrameAnalysis(
                    frame_id=frame_id,
                    timestamp=timestamp,
                    detections=detections,
                    tracked_objects=tracked_objects
                )
                frame_analyses.append(frame_analysis)
            
            # Create video analysis
            video_analysis = VideoAnalysis(
                analysis_id=analysis_id,
                video_path=video_path,
                sport=sport,
                fps=fps,
                total_frames=total_frames,
                frame_analyses=frame_analyses,
                tracked_objects=list(all_tracked_objects.values())
            )
            
            # Calculate analytics
            analysis_data = self._perform_analysis(video_analysis)
            
            # Save analysis results
            self._save_analysis(analysis_id, analysis_data)
            
            logger.info(f"Analysis {analysis_id} completed successfully")
            return analysis_id
            
        except Exception as e:
            logger.error(f"Error processing video {video_path}: {e}")
            raise
    
    def _perform_analysis(self, video_analysis: VideoAnalysis) -> Dict:
        """Perform comprehensive analysis on video data"""
        results = {
            'analysis_id': video_analysis.analysis_id,
            'video_info': {
                'sport': video_analysis.sport,
                'duration': video_analysis.total_frames / video_analysis.fps,
                'fps': video_analysis.fps,
                'total_frames': video_analysis.total_frames,
                'player_count': len(video_analysis.get_player_objects()),
                'ball_detected': video_analysis.get_ball_object() is not None
            }
        }
        
        # Calculate possession
        try:
            possession_data = self.possession_calc.calculate_possession(video_analysis)
            results['possession_stats'] = possession_data.get('possession_stats', {})
            results['possession_timeline'] = possession_data.get('possession_timeline', [])
        except Exception as e:
            logger.warning(f"Possession calculation failed: {e}")
            results['possession_stats'] = {}
        
        # Analyze movement
        try:
            movement_data = self.movement_analyzer.analyze_team_movement(
                video_analysis.get_player_objects()
            )
            results['movement_stats'] = movement_data
        except Exception as e:
            logger.warning(f"Movement analysis failed: {e}")
            results['movement_stats'] = {}
        
        # Extract events
        try:
            events = self.event_extractor.extract_events(video_analysis)
            results['events'] = events
        except Exception as e:
            logger.warning(f"Event extraction failed: {e}")
            results['events'] = []
        
        return results
    
    def _log_progress(self, frame_id: int, total_frames: int, analysis_id: str):
        """Log processing progress"""
        if frame_id % 60 == 0:  # Log every 60 frames (2 seconds at 30fps)
            progress = (frame_id / total_frames) * 100
            logger.info(f"Analysis {analysis_id}: {progress:.1f}% complete ({frame_id}/{total_frames})")
    
    def _save_analysis(self, analysis_id: str, analysis_data: Dict):
        """Save analysis results to file"""
        results_dir = 'analysis_results'
        os.makedirs(results_dir, exist_ok=True)
        
        result_file = os.path.join(results_dir, f"{analysis_id}.json")
        
        # Add metadata
        analysis_data['created_at'] = datetime.now().isoformat()
        analysis_data['status'] = 'completed'
        
        with open(result_file, 'w') as f:
            json.dump(analysis_data, f, indent=2, default=str)
        
        logger.info(f"Analysis results saved: {result_file}")
    
    @staticmethod
    def load_analysis(analysis_id: str) -> Dict:
        """Load analysis results from file"""
        result_file = os.path.join('analysis_results', f"{analysis_id}.json")
        
        if not os.path.exists(result_file):
            raise FileNotFoundError(f"Analysis {analysis_id} not found")
        
        with open(result_file, 'r') as f:
            return json.load(f)