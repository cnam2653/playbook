from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import logging
import json
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime
from dotenv import load_dotenv
import cv2

# Load environment variables
load_dotenv()

from advanced_tracker import AdvancedTracker
from src.routes.analysis_routes import analysis

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {"origins": "*"},
    r"/upload": {"origins": "*"},
    r"/outputs/*": {"origins": "*"}
})

# Register blueprints under /api
app.register_blueprint(analysis, url_prefix="/api/analysis")

app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB max file size

ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET'])
def index():
    """Serve the index page"""
    return send_from_directory('..', 'index.html')

@app.route('/outputs/<filename>')
def serve_output_video(filename):
    """Serve processed video files"""
    return send_from_directory('outputs', filename)

@app.route('/uploads/<filename>')
def serve_upload_video(filename):
    """Serve uploaded video files"""
    return send_from_directory('uploads', filename)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': '🧠 Sports Analytics API Ready'}), 200

@app.route('/upload', methods=['POST'])
def upload_video():
    """Upload and process a sports video"""
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400
        
        file = request.files['video']
        sport = request.form.get('sport', 'soccer')
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file or not allowed_file(file.filename):
            return jsonify({
                'error': f'Invalid file type. Supported formats: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        
        logger.info(f"File uploaded: {filepath}")
        
        # Process video with Advanced Tracker (Roboflow API + ellipses + IDs)
        tracker = AdvancedTracker()
        analysis_id = str(uuid.uuid4())
        
        # Generate output video path
        output_filename = f"analyzed_{unique_filename}"
        output_path = os.path.join('outputs', output_filename)
        os.makedirs('outputs', exist_ok=True)
        
        # Run advanced tracking with Roboflow API
        tracks = tracker.process_video(filepath, output_path, use_cache=True)

        # Get video duration and metadata
        cap = cv2.VideoCapture(filepath)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        cap.release()

        # Extract detailed stats from tracking data
        unique_player_ids = set()
        player_stats = {}  # {track_id: {team, speeds, distances, ball_frames}}
        team_possession = {1: 0, 2: 0}

        # Pass tracking
        last_player_with_ball = None
        last_player_team = None
        passes = {'team_1': 0, 'team_2': 0, 'total': 0}
        player_passes = {}  # {track_id: passes_made}

        for frame_num, frame_players in enumerate(tracks.get('players', [])):
            current_ball_holder = None
            current_holder_team = None

            for track_id, player_data in frame_players.items():
                unique_player_ids.add(track_id)

                if track_id not in player_stats:
                    player_stats[track_id] = {
                        'team': player_data.get('team', 1),
                        'speeds': [],
                        'max_speed': 0,
                        'ball_frames': 0,
                        'total_frames': 0
                    }

                player_stats[track_id]['total_frames'] += 1

                # Track speed
                speed = player_data.get('speed')
                if speed is not None:
                    player_stats[track_id]['speeds'].append(speed)
                    if speed > player_stats[track_id]['max_speed']:
                        player_stats[track_id]['max_speed'] = speed

                # Track ball possession
                if player_data.get('has_ball', False):
                    player_stats[track_id]['ball_frames'] += 1
                    team = player_data.get('team', 1)
                    team_possession[team] = team_possession.get(team, 0) + 1
                    current_ball_holder = track_id
                    current_holder_team = team

            # Detect passes: ball changed from one player to another on same team
            if (current_ball_holder is not None and
                last_player_with_ball is not None and
                current_ball_holder != last_player_with_ball and
                current_holder_team == last_player_team):
                # Same team, different player = pass completed
                passes['total'] += 1
                if current_holder_team == 1:
                    passes['team_1'] += 1
                else:
                    passes['team_2'] += 1
                # Credit the pass to the player who had the ball
                if last_player_with_ball not in player_passes:
                    player_passes[last_player_with_ball] = 0
                player_passes[last_player_with_ball] += 1

            # Update last ball holder
            if current_ball_holder is not None:
                last_player_with_ball = current_ball_holder
                last_player_team = current_holder_team

        # Calculate possession percentages
        total_possession_frames = int(sum(team_possession.values()))
        possession_percentages = {}
        for track_id, stats in player_stats.items():
            if total_possession_frames > 0:
                possession_percentages[str(int(track_id))] = float((stats['ball_frames'] / total_possession_frames) * 100)
            else:
                possession_percentages[str(int(track_id))] = 0.0

        # Find player with most possession
        most_possession = None
        if possession_percentages:
            max_player = max(possession_percentages.items(), key=lambda x: x[1])
            if max_player[1] > 0:
                most_possession = [int(max_player[0]), float(max_player[1])]

        # Build individual movement stats
        individual_stats = []
        fastest_player = None
        max_speed_overall = 0

        for track_id, stats in player_stats.items():
            avg_speed = sum(stats['speeds']) / len(stats['speeds']) if stats['speeds'] else 0
            max_speed = stats['max_speed']

            individual_stats.append({
                'track_id': int(track_id),
                'team': int(stats['team']),
                'max_speed_kmh': float(max_speed),
                'max_speed_mps': float(max_speed / 3.6),
                'avg_speed_kmh': float(avg_speed),
                'frames_tracked': int(stats['total_frames']),
                'ball_possession_frames': int(stats['ball_frames'])
            })

            if max_speed > max_speed_overall:
                max_speed_overall = max_speed
                fastest_player = {
                    'track_id': int(track_id),
                    'max_speed_kmh': float(max_speed),
                    'max_speed_mps': float(max_speed / 3.6)
                }

        # Calculate team possession percentages
        team_1_pct = float((team_possession[1] / total_possession_frames * 100) if total_possession_frames > 0 else 50)
        team_2_pct = float((team_possession[2] / total_possession_frames * 100) if total_possession_frames > 0 else 50)

        # Save analysis results with full data
        analysis_data = {
            'analysis_id': analysis_id,
            'status': 'completed',
            'created_at': datetime.now().isoformat(),
            'video_info': {
                'filename': unique_filename,
                'duration': float(duration),
                'fps': float(fps),
                'total_frames': int(total_frames)
            },
            'stats': {
                'total_players': int(sum(len(frame) for frame in tracks.get('players', []))),
                'unique_players': int(len(unique_player_ids)),
                'total_frames': int(len(tracks.get('players', []))),
                'ball_detected_frames': int(len([f for f in tracks.get('ball', []) if f]))
            },
            'possession_stats': {
                'team_possession': {
                    'team_1': team_1_pct,
                    'team_2': team_2_pct
                },
                'possession_percentages': possession_percentages,
                'most_possession': most_possession,
                'total_possession_frames': total_possession_frames
            },
            'movement_stats': {
                'fastest_player': fastest_player,
                'individual_stats': individual_stats
            },
            'pass_stats': {
                'total_passes': int(passes['total']),
                'team_1_passes': int(passes['team_1']),
                'team_2_passes': int(passes['team_2']),
                'passes_by_player': {str(int(k)): int(v) for k, v in player_passes.items()}
            },
            'model_metrics': {
                'mAP@50': 84.5,
                'precision': 93.3,
                'recall': 75.2
            }
        }
        
        # Save to file
        os.makedirs('analysis_results', exist_ok=True)
        with open(f'analysis_results/{analysis_id}.json', 'w') as f:
            json.dump(analysis_data, f)
        
        return jsonify({
            'analysis_id': analysis_id,
            'message': 'Video uploaded and analysis completed!',
            'status': 'completed',
            'output_video': output_filename
        }), 200
        
    except Exception as e:
        logger.error(f"Upload/processing error: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Create necessary directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs('analysis_results', exist_ok=True)
    
    logger.info("🧠 Starting Sports Analytics API...")
    logger.info("📹 Ready to process sports videos!")
    
    app.run(debug=True, host='0.0.0.0', port=5001)