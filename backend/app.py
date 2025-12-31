from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import logging
from werkzeug.utils import secure_filename
import uuid

from src.services.video_processor import VideoProcessor
from src.services.openai_service import OpenAIService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB max file size

ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET'])
def index():
    """Serve the index page"""
    return send_from_directory('.', 'index.html')

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
        
        # Process video
        processor = VideoProcessor()
        analysis_id = processor.process_video(filepath, sport)
        
        return jsonify({
            'analysis_id': analysis_id,
            'message': 'Video uploaded and analysis completed!',
            'status': 'completed'
        }), 200
        
    except Exception as e:
        logger.error(f"Upload/processing error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/analysis/<analysis_id>/status', methods=['GET'])
def get_analysis_status(analysis_id):
    """Get the status of an analysis"""
    try:
        analysis_data = VideoProcessor.load_analysis(analysis_id)
        
        return jsonify({
            'analysis_id': analysis_id,
            'status': analysis_data.get('status', 'completed'),
            'created_at': analysis_data.get('created_at'),
            'video_info': analysis_data.get('video_info', {}),
            'player_count': len(analysis_data.get('movement_stats', {}).get('individual_stats', [])),
            'possession_leader': analysis_data.get('possession_stats', {}).get('most_possession')
        }), 200
        
    except FileNotFoundError:
        return jsonify({
            'analysis_id': analysis_id,
            'status': 'not_found',
            'error': 'Analysis not found'
        }), 404
    except Exception as e:
        logger.error(f"Error getting analysis status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/analysis/<analysis_id>/query', methods=['POST'])
def query_analysis(analysis_id):
    """Ask questions about the analysis"""
    try:
        data = request.get_json()
        query = data.get('query', 'Give me a summary of this clip')
        
        # Load analysis data
        analysis_data = VideoProcessor.load_analysis(analysis_id)
        
        # Generate response using OpenAI service
        openai_service = OpenAIService()
        
        if 'summary' in query.lower() or len(query.split()) < 3:
            response = openai_service.generate_clip_summary(analysis_data, query)
        else:
            response = openai_service.answer_query(query, analysis_data)
        
        return jsonify({
            'query': query,
            'response': response,
            'analysis_id': analysis_id
        }), 200
        
    except FileNotFoundError:
        return jsonify({'error': 'Analysis not found'}), 404
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/analysis/<analysis_id>/stats', methods=['GET'])
def get_analysis_stats(analysis_id):
    """Get detailed statistics from analysis"""
    try:
        analysis_data = VideoProcessor.load_analysis(analysis_id)
        
        stats = {
            'video_info': analysis_data.get('video_info', {}),
            'possession_stats': analysis_data.get('possession_stats', {}),
            'movement_stats': analysis_data.get('movement_stats', {}),
            'events': analysis_data.get('events', [])[:10],  # First 10 events
            'summary': {
                'total_players': len(analysis_data.get('movement_stats', {}).get('individual_stats', [])),
                'total_events': len(analysis_data.get('events', [])),
                'analysis_duration': analysis_data.get('video_info', {}).get('duration', 0)
            }
        }
        
        return jsonify(stats), 200
        
    except FileNotFoundError:
        return jsonify({'error': 'Analysis not found'}), 404
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/analysis/<analysis_id>/player/<int:player_id>', methods=['GET'])
def get_player_stats(analysis_id, player_id):
    """Get stats for a specific player"""
    try:
        analysis_data = VideoProcessor.load_analysis(analysis_id)
        
        # Find player in movement stats
        movement_stats = analysis_data.get('movement_stats', {})
        individual_stats = movement_stats.get('individual_stats', [])
        
        player_stats = None
        for stats in individual_stats:
            if stats.get('track_id') == player_id:
                player_stats = stats
                break
        
        if not player_stats:
            return jsonify({'error': f'Player {player_id} not found'}), 404
        
        # Get possession data for this player
        possession_stats = analysis_data.get('possession_stats', {})
        possession_percentages = possession_stats.get('possession_percentages', {})
        player_possession = possession_percentages.get(str(player_id), 0)
        
        result = {
            'player_id': player_id,
            'movement': player_stats,
            'possession_percentage': player_possession,
            'rankings': {
                'possession': _get_player_ranking(player_id, possession_percentages, reverse=True),
                'speed': _get_player_ranking(player_id, {str(s['track_id']): s.get('max_speed_mps', 0) for s in individual_stats}, reverse=True),
                'activity': _get_player_ranking(player_id, {str(s['track_id']): s.get('activity_score', 0) for s in individual_stats}, reverse=True)
            }
        }
        
        return jsonify(result), 200
        
    except FileNotFoundError:
        return jsonify({'error': 'Analysis not found'}), 404
    except Exception as e:
        logger.error(f"Error getting player stats: {e}")
        return jsonify({'error': str(e)}), 500

def _get_player_ranking(player_id: int, stats_dict: dict, reverse: bool = True) -> int:
    """Get player's ranking in given stats"""
    sorted_players = sorted(stats_dict.items(), key=lambda x: float(x[1]), reverse=reverse)
    for rank, (pid, _) in enumerate(sorted_players, 1):
        if int(pid) == player_id:
            return rank
    return len(sorted_players) + 1

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs('analysis_results', exist_ok=True)
    
    logger.info("🧠 Starting Sports Analytics API...")
    logger.info("📹 Ready to process sports videos!")
    
    app.run(debug=True, host='0.0.0.0', port=5000)