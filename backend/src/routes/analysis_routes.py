from flask import Blueprint, jsonify, request
from datetime import datetime
import os
import json
from ..services.analytics_summary import (
    load_analysis_data, 
    generate_summary, 
    answer_specific_question,
    client as openai_client
)

analysis = Blueprint("analysis", __name__)

@analysis.route("/<analysis_id>/summary", methods=["GET"])
def get_analysis_summary(analysis_id):
    """Generate AI summary for the analysis"""
    try:
        # Load analysis data
        analysis_data = load_analysis_data(analysis_id)
        
        # Generate AI summary
        summary = generate_summary(analysis_data)
        
        return jsonify({
            "analysis_id": analysis_id,
            "summary": summary,
            "generated_at": datetime.now().isoformat()
        }), 200
        
    except FileNotFoundError:
        return jsonify({
            "error": "Analysis not found",
            "analysis_id": analysis_id
        }), 404
    except Exception as e:
        return jsonify({
            "error": f"Failed to generate summary: {str(e)}",
            "analysis_id": analysis_id
        }), 500

@analysis.route("/<analysis_id>/query", methods=["POST"])
def query_analysis(analysis_id):
    """Ask specific questions about the analysis"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({"error": "Query cannot be empty"}), 400
        
        # Load analysis data
        analysis_data = load_analysis_data(analysis_id)
        
        # Generate response
        if any(word in query.lower() for word in ['summary', 'overview', 'what happened']):
            response = generate_summary(analysis_data)
        else:
            response = answer_specific_question(query, analysis_data)
        
        return jsonify({
            "query": query,
            "response": response,
            "analysis_id": analysis_id,
            "answered_at": datetime.now().isoformat()
        }), 200
        
    except FileNotFoundError:
        return jsonify({
            "error": "Analysis not found",
            "analysis_id": analysis_id
        }), 404
    except Exception as e:
        return jsonify({
            "error": f"Failed to process query: {str(e)}",
            "analysis_id": analysis_id
        }), 500

@analysis.route("/<analysis_id>/status", methods=["GET"])
def get_analysis_status(analysis_id):
    """Get the status and basic info of an analysis"""
    try:
        analysis_data = load_analysis_data(analysis_id)
        
        return jsonify({
            "analysis_id": analysis_id,
            "status": analysis_data.get("status", "completed"),
            "created_at": analysis_data.get("created_at"),
            "video_info": analysis_data.get("video_info", {}),
            "stats": analysis_data.get("stats", {}),
            "has_possession_data": "possession_stats" in analysis_data,
            "has_movement_data": "movement_stats" in analysis_data,
            "retrieved_at": datetime.now().isoformat()
        }), 200
        
    except FileNotFoundError:
        return jsonify({
            "analysis_id": analysis_id,
            "status": "not_found",
            "error": "Analysis not found"
        }), 404
    except Exception as e:
        return jsonify({
            "error": f"Failed to get analysis status: {str(e)}",
            "analysis_id": analysis_id
        }), 500

@analysis.route("/<analysis_id>/stats", methods=["GET"])
def get_detailed_stats(analysis_id):
    """Get detailed statistics from analysis"""
    try:
        analysis_data = load_analysis_data(analysis_id)
        
        # Structure the response with all available data
        response = {
            "analysis_id": analysis_id,
            "video_info": analysis_data.get("video_info", {}),
            "basic_stats": analysis_data.get("stats", {}),
            "model_metrics": analysis_data.get("model_metrics", {}),
            "possession_stats": analysis_data.get("possession_stats", {}),
            "movement_stats": analysis_data.get("movement_stats", {}),
            "team_analysis": analysis_data.get("team_analysis", {}),
            "events": analysis_data.get("events", []),
            "heat_map_data": analysis_data.get("heat_map_data", {}),
            "retrieved_at": datetime.now().isoformat()
        }
        
        return jsonify(response), 200
        
    except FileNotFoundError:
        return jsonify({
            "error": "Analysis not found",
            "analysis_id": analysis_id
        }), 404
    except Exception as e:
        return jsonify({
            "error": f"Failed to get detailed stats: {str(e)}",
            "analysis_id": analysis_id
        }), 500

@analysis.route("/<analysis_id>/player/<int:player_id>", methods=["GET"])
def get_player_stats(analysis_id, player_id):
    """Get stats for a specific player"""
    try:
        analysis_data = load_analysis_data(analysis_id)
        
        # Extract player-specific data
        movement_stats = analysis_data.get('movement_stats', {})
        individual_stats = movement_stats.get('individual_stats', [])
        
        # Find player in movement stats
        player_stats = None
        for stats in individual_stats:
            if stats.get('track_id') == player_id:
                player_stats = stats
                break
        
        if not player_stats:
            return jsonify({
                "error": f"Player {player_id} not found in analysis",
                "analysis_id": analysis_id,
                "available_players": [s.get('track_id') for s in individual_stats]
            }), 404
        
        # Get possession data for this player
        possession_stats = analysis_data.get('possession_stats', {})
        possession_percentages = possession_stats.get('possession_percentages', {})
        player_possession = possession_percentages.get(str(player_id), 0)
        
        result = {
            "analysis_id": analysis_id,
            "player_id": player_id,
            "movement_stats": player_stats,
            "possession_percentage": player_possession,
            "rankings": {
                "possession": _get_player_ranking(player_id, possession_percentages, reverse=True),
                "speed": _get_player_ranking(
                    player_id, 
                    {str(s['track_id']): s.get('max_speed_mps', 0) for s in individual_stats}, 
                    reverse=True
                ),
                "activity": _get_player_ranking(
                    player_id, 
                    {str(s['track_id']): s.get('activity_score', 0) for s in individual_stats}, 
                    reverse=True
                )
            },
            "retrieved_at": datetime.now().isoformat()
        }
        
        return jsonify(result), 200
        
    except FileNotFoundError:
        return jsonify({
            "error": "Analysis not found",
            "analysis_id": analysis_id
        }), 404
    except Exception as e:
        return jsonify({
            "error": f"Failed to get player stats: {str(e)}",
            "analysis_id": analysis_id
        }), 500

@analysis.route("/ai-status", methods=["GET"])
def get_ai_status():
    """Check if OpenAI API is configured and working"""
    if openai_client is None:
        return jsonify({
            "status": "not_configured",
            "message": "OpenAI client not configured - check OPENAI_API_KEY environment variable"
        }), 503
    
    return jsonify({
        "status": "ready",
        "message": "OpenAI client configured and ready"
    }), 200

def _get_player_ranking(player_id: int, stats_dict: dict, reverse: bool = True) -> int:
    """Get player's ranking in given stats"""
    if not stats_dict:
        return 1
    
    try:
        sorted_players = sorted(stats_dict.items(), key=lambda x: float(x[1]), reverse=reverse)
        for rank, (pid, _) in enumerate(sorted_players, 1):
            if int(pid) == player_id:
                return rank
        return len(sorted_players) + 1
    except (ValueError, TypeError):
        return 1