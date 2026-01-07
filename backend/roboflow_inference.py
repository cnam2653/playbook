from roboflow import Roboflow
import cv2
import json
from typing import Dict, List, Any
import os

class FootballAnalyzer:
    def __init__(self):
        # Initialize Roboflow with your API key
        rf = Roboflow(api_key="RHd5EsjN6724YWstHZHh")
        project = rf.workspace().project("football-players-detection-3zvbc-5idyc")
        self.model = project.version(1).model
        
    def analyze_video(self, video_path: str, output_path: str = None, confidence: float = 0.4) -> Dict[str, Any]:
        """
        Analyze a football video for player detection and tracking
        
        Args:
            video_path: Path to input video
            output_path: Path for output video (optional)
            confidence: Detection confidence threshold
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            import cv2
            
            # Read video and process frame by frame
            cap = cv2.VideoCapture(video_path)
            total_detections = []
            frame_count = 0
            
            # Get video properties for output
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Setup output video writer if output path is provided
            out = None
            if output_path:
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
                out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            print(f"Processing video: {video_path}")
            print(f"Video properties: {width}x{height}, {fps} FPS")
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                    
                frame_count += 1
                processed_frame = frame.copy()
                
                # Process every frame for better visualization
                if True:  # Process every frame instead of every 5th
                    # Save frame as temporary image
                    temp_frame_path = f"temp_frame_{frame_count}.jpg"
                    cv2.imwrite(temp_frame_path, frame)
                    
                    try:
                        # Run inference on frame
                        result = self.model.predict(temp_frame_path, confidence=confidence * 100, overlap=30)
                        
                        # Parse frame detections
                        frame_detections = self._parse_detections(result)
                        total_detections.extend(frame_detections)
                        
                        # Draw bounding boxes on frame
                        for detection in frame_detections:
                            bbox = detection['bbox']
                            class_name = detection['class']
                            conf = detection['confidence']
                            
                            # Calculate bounding box coordinates
                            x = int(bbox['x'] - bbox['width']/2)
                            y = int(bbox['y'] - bbox['height']/2)
                            w = int(bbox['width'])
                            h = int(bbox['height'])
                            
                            # Color coding for different classes
                            if class_name == 'player':
                                color = (0, 255, 0)  # Green for players
                            elif class_name == 'ball':
                                color = (0, 0, 255)  # Red for ball
                            elif class_name == 'goalkeeper':
                                color = (255, 0, 0)  # Blue for goalkeeper
                            elif class_name == 'referee':
                                color = (0, 255, 255)  # Yellow for referee
                            else:
                                color = (255, 255, 255)  # White for others
                            
                            # Draw rectangle
                            cv2.rectangle(processed_frame, (x, y), (x + w, y + h), color, 2)
                            
                            # Draw label
                            label = f"{class_name}: {conf:.2f}"
                            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
                            cv2.rectangle(processed_frame, (x, y - label_size[1] - 10), 
                                        (x + label_size[0], y), color, -1)
                            cv2.putText(processed_frame, label, (x, y - 5), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
                        
                        print(f"Frame {frame_count}: {len(frame_detections)} detections")
                        
                    except Exception as e:
                        print(f"Error processing frame {frame_count}: {e}")
                    finally:
                        # Clean up temp file
                        if os.path.exists(temp_frame_path):
                            os.unlink(temp_frame_path)
                
                # Write frame to output video
                if out is not None:
                    out.write(processed_frame)
                
                # Progress indicator
                if frame_count % 100 == 0:
                    print(f"Processed {frame_count} frames...")
            
            cap.release()
            if out is not None:
                out.release()
                print(f"Output video saved to: {output_path}")
            
            print(f"Total detections across all frames: {len(total_detections)}")
            
            # Calculate metrics from all detections
            analytics = self._calculate_metrics(total_detections)
            
            return {
                "detections": total_detections,
                "analytics": analytics,
                "total_frames_processed": frame_count // 5,
                "output_video": output_path if output_path else None,
                "model_metrics": {
                    "mAP@50": 84.5,
                    "precision": 93.3,
                    "recall": 75.2
                }
            }
            
        except Exception as e:
            print(f"Error in analyze_video: {e}")
            # Return basic mock data if analysis fails
            return {
                "detections": [],
                "analytics": {
                    "total_detections": 0,
                    "class_counts": {"player": 0, "ball": 0},
                    "players_detected": 0,
                    "ball_detected": 0,
                    "avg_confidence": 0
                },
                "error": str(e),
                "model_metrics": {
                    "mAP@50": 84.5,
                    "precision": 93.3,
                    "recall": 75.2
                }
            }
    
    def analyze_frame(self, image_path: str, confidence: float = 0.4) -> Dict[str, Any]:
        """
        Analyze a single frame/image
        
        Args:
            image_path: Path to input image
            confidence: Detection confidence threshold
            
        Returns:
            Dictionary containing detection results
        """
        result = self.model.predict(image_path, confidence=confidence * 100)
        return self._parse_detections(result)
    
    def _parse_detections(self, result) -> List[Dict[str, Any]]:
        """Parse Roboflow result into structured format"""
        detections = []
        
        try:
            # Access predictions from Roboflow result
            predictions = result.json()['predictions'] if hasattr(result, 'json') else []
            
            for pred in predictions:
                detection = {
                    "class": pred['class'],
                    "confidence": pred['confidence'],
                    "bbox": {
                        "x": pred['x'],
                        "y": pred['y'],
                        "width": pred['width'],
                        "height": pred['height']
                    }
                }
                detections.append(detection)
                
        except Exception as e:
            print(f"Error parsing detections: {e}")
            
        return detections
    
    def _calculate_metrics(self, detections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate analytics from detections"""
        
        # Count objects by class
        class_counts = {}
        for det in detections:
            class_name = det['class']
            class_counts[class_name] = class_counts.get(class_name, 0) + 1
        
        # Mock additional analytics (you can enhance this)
        analytics = {
            "total_detections": len(detections),
            "class_counts": class_counts,
            "players_detected": class_counts.get('player', 0),
            "ball_detected": class_counts.get('ball', 0),
            "goalkeepers_detected": class_counts.get('goalkeeper', 0),
            "referees_detected": class_counts.get('referee', 0),
            "avg_confidence": sum(det['confidence'] for det in detections) / len(detections) if detections else 0
        }
        
        return analytics

# Example usage
if __name__ == "__main__":
    analyzer = FootballAnalyzer()
    
    # Analyze a video
    video_path = "videos/sample_football.mp4"  # Replace with your video path
    
    if os.path.exists(video_path):
        results = analyzer.analyze_video(video_path, "output/analyzed_video.mp4")
        print(json.dumps(results, indent=2))
    else:
        print(f"Video file not found: {video_path}")
        print("Please place a football video in the videos/ directory")