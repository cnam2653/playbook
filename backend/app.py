from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import logging
import json
from werkzeug.utils import secure_filename
import uuid
from dotenv import load_dotenv

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
        
        # Save analysis results (excluding tracking data for JSON compatibility)
        analysis_data = {
            'analysis_id': analysis_id,
            'status': 'completed',
            'created_at': str(uuid.uuid4()),
            'video_info': {'filename': unique_filename},
            'stats': {
                'total_players': sum(len(frame) for frame in tracks.get('players', [])),
                'total_frames': len(tracks.get('players', [])),
                'ball_detected_frames': len([f for f in tracks.get('ball', []) if f])
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