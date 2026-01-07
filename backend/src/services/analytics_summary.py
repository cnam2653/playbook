import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from openai import OpenAI
import logging

load_dotenv()

# OpenAI API configuration
OPENAI_ENDPOINT = os.getenv("OPENAI_ENDPOINT", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-4"

logger = logging.getLogger(__name__)

# Initialize OpenAI client
try:
    client = OpenAI(
        base_url=OPENAI_ENDPOINT,
        api_key=OPENAI_API_KEY
    ) if OPENAI_API_KEY else None
    if client:
        print("OpenAI client initialized successfully")
except Exception as e:
    print(f"Warning: OpenAI client initialization failed: {e}")
    client = None

def load_analysis_data(analysis_id: str):
    """Load analysis data from JSON file"""
    analysis_file = f'analysis_results/{analysis_id}.json'
    
    if not os.path.exists(analysis_file):
        raise FileNotFoundError(f"Analysis {analysis_id} not found")
        
    with open(analysis_file, 'r') as f:
        return json.load(f)

def build_summary_prompt(analysis_data: dict) -> str:
    """Build the user prompt from analysis data"""
    video_info = analysis_data.get('video_info', {})
    stats = analysis_data.get('stats', {})
    
    lines = [
        f"Soccer clip analysis for {video_info.get('filename', 'video')}:",
        f"• Duration: {video_info.get('duration', 0):.1f} seconds",
        f"• Total frames processed: {stats.get('total_frames', 0)}",
        f"• Players detected: {stats.get('unique_players', 0)} unique players",
        f"• Ball tracking: {stats.get('ball_detected_frames', 0)} frames with ball detected",
    ]
    
    # Add possession data if available
    if 'possession_stats' in analysis_data:
        possession = analysis_data['possession_stats']
        lines.append("\nPossession Statistics:")
        for player_id, percentage in possession.get('possession_percentages', {}).items():
            lines.append(f"• Player {player_id}: {percentage:.1f}% possession")
    
    # Add movement data if available
    if 'movement_stats' in analysis_data:
        movement = analysis_data['movement_stats']
        if 'fastest_player' in movement:
            fastest = movement['fastest_player']
            lines.append(f"\nMovement Statistics:")
            lines.append(f"• Fastest player: Player {fastest.get('track_id')} ({fastest.get('max_speed_mps', 0):.1f} m/s)")
    
    lines.append(
        "\nPlease provide a detailed analysis highlighting key tactical insights, "
        "player performances, and notable patterns. Write like a professional soccer analyst."
    )
    
    return "\n".join(lines)

def generate_summary(analysis_data: dict) -> str:
    """Generate AI summary of the soccer clip"""
    if client is None:
        return generate_fallback_summary(analysis_data)
    
    system_prompt = (
        "You are a professional soccer analyst with expertise in match analysis and tactical insights. "
        "Your job is to provide detailed, insightful commentary on soccer clips based on tracking data. "
        "Focus on tactical patterns, player performance, possession dynamics, and strategic insights. "
        "Write in an engaging, professional style as if you're providing analysis for a sports broadcast."
    )
    
    user_prompt = build_summary_prompt(analysis_data) + """

    Provide a comprehensive analysis covering:
    
    • Overall tactical flow and game dynamics
    • Key individual player performances and contributions
    • Possession patterns and ball movement effectiveness
    • Defensive and attacking patterns observed
    • Notable technical or strategic insights
    • Areas for improvement or tactical adjustments
    
    Make it informative and engaging, like a post-match analysis segment.
    """
    
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=600,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return generate_fallback_summary(analysis_data)

def answer_specific_question(query: str, analysis_data: dict) -> str:
    """Answer a specific question about the analysis"""
    if client is None:
        return generate_fallback_answer(query, analysis_data)
    
    system_prompt = (
        "You are an expert soccer analyst who answers specific questions about match footage "
        "based on tracking and statistical data. Provide direct, informative answers that "
        "demonstrate deep understanding of the game."
    )
    
    data_context = build_summary_prompt(analysis_data)
    user_prompt = f"""
    Based on this soccer clip analysis data:

    {data_context}

    Question: {query}

    Please provide a detailed, specific answer based on the available data. If the data doesn't 
    contain enough information to fully answer the question, explain what you can determine 
    and what additional data would be helpful.
    """
    
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=400,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"OpenAI API error for query: {e}")
        return generate_fallback_answer(query, analysis_data)

def generate_fallback_summary(analysis_data: dict) -> str:
    """Generate a basic summary without OpenAI"""
    video_info = analysis_data.get('video_info', {})
    stats = analysis_data.get('stats', {})
    
    summary_parts = [
        f"📊 Soccer Clip Analysis - {video_info.get('filename', 'Video')}",
        f"🎬 Duration: {video_info.get('duration', 0):.1f} seconds",
        f"👥 Players tracked: {stats.get('unique_players', 0)} unique players",
        f"⚽ Ball detection: {stats.get('ball_detected_frames', 0)}/{stats.get('total_frames', 0)} frames"
    ]
    
    # Add possession leader if available
    if 'possession_stats' in analysis_data:
        possession = analysis_data['possession_stats']
        if possession.get('most_possession'):
            player_id, percentage = possession['most_possession']
            summary_parts.append(f"🏃‍♂️ Possession leader: Player {player_id} ({percentage:.1f}%)")
    
    # Add speed info if available
    if 'movement_stats' in analysis_data:
        movement = analysis_data['movement_stats']
        if 'fastest_player' in movement:
            fastest = movement['fastest_player']
            summary_parts.append(f"⚡ Fastest player: Player {fastest.get('track_id')} ({fastest.get('max_speed_mps', 0):.1f} m/s)")
    
    summary_parts.append("🤖 AI analysis temporarily unavailable - showing basic statistics")
    
    return "\n".join(summary_parts)

def generate_fallback_answer(query: str, analysis_data: dict) -> str:
    """Generate a basic answer without OpenAI"""
    query_lower = query.lower()
    
    # Possession queries
    if any(word in query_lower for word in ['possession', 'ball', 'control']):
        if 'possession_stats' in analysis_data:
            possession = analysis_data['possession_stats']
            if possession.get('most_possession'):
                player_id, percentage = possession['most_possession']
                return f"Based on tracking data, Player {player_id} had the most ball possession with {percentage:.1f}% of tracked possession time."
    
    # Speed/movement queries
    if any(word in query_lower for word in ['fast', 'speed', 'quick', 'pace']):
        if 'movement_stats' in analysis_data:
            movement = analysis_data['movement_stats']
            if 'fastest_player' in movement:
                fastest = movement['fastest_player']
                return f"Player {fastest.get('track_id')} was the fastest player, reaching a maximum speed of {fastest.get('max_speed_mps', 0):.1f} meters per second."
    
    # Player count queries
    if any(word in query_lower for word in ['player', 'how many']):
        stats = analysis_data.get('stats', {})
        count = stats.get('unique_players', 0)
        return f"The analysis detected {count} unique players in this soccer clip."
    
    return ("I'm unable to access the AI analysis service at the moment. "
            "The tracking data shows basic statistics are available - please try asking about "
            "specific topics like possession, player speeds, or general clip statistics.")

if __name__ == "__main__":
    # Test with a sample analysis ID
    try:
        analysis_data = load_analysis_data("test-id")
        print(generate_summary(analysis_data))
    except FileNotFoundError:
        print("No test analysis data found")