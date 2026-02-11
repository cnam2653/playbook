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
        f"Soccer clip analysis:",
        f"• Duration: {video_info.get('duration', 0):.1f} seconds",
        f"• Players detected: {stats.get('unique_players', 0)} unique players",
    ]

    # Add team possession data if available
    if 'possession_stats' in analysis_data:
        possession = analysis_data['possession_stats']
        team_poss = possession.get('team_possession', {})
        if team_poss:
            lines.append(f"\nTeam Possession:")
            lines.append(f"• Team 1: {team_poss.get('team_1', 50):.1f}%")
            lines.append(f"• Team 2: {team_poss.get('team_2', 50):.1f}%")

        # Top 3 possession players
        poss_pcts = possession.get('possession_percentages', {})
        if poss_pcts:
            sorted_poss = sorted(poss_pcts.items(), key=lambda x: x[1], reverse=True)[:3]
            lines.append(f"\nTop Possession Players:")
            for player_id, pct in sorted_poss:
                if pct > 0:
                    lines.append(f"• Player {player_id}: {pct:.1f}%")

    # Add movement data if available
    if 'movement_stats' in analysis_data:
        movement = analysis_data['movement_stats']
        individual = movement.get('individual_stats', [])

        if individual:
            # Calculate average speed across all players
            all_speeds = [p.get('avg_speed_kmh', 0) for p in individual if p.get('avg_speed_kmh', 0) > 0]
            if all_speeds:
                avg_speed = sum(all_speeds) / len(all_speeds)
                lines.append(f"\nSpeed Statistics:")
                lines.append(f"• Average player speed: {avg_speed:.1f} km/h")

            # Fastest player
            if movement.get('fastest_player'):
                fastest = movement['fastest_player']
                lines.append(f"• Fastest player: Player {fastest.get('track_id')} ({fastest.get('max_speed_kmh', 0):.1f} km/h)")

    # Add pass stats if available
    if 'pass_stats' in analysis_data:
        pass_stats = analysis_data['pass_stats']
        total_passes = pass_stats.get('total_passes', 0)
        if total_passes > 0:
            lines.append(f"\nPass Statistics:")
            lines.append(f"• Total passes: {total_passes}")
            lines.append(f"• Team 1 passes: {pass_stats.get('team_1_passes', 0)}")
            lines.append(f"• Team 2 passes: {pass_stats.get('team_2_passes', 0)}")

            # Top passers
            passes_by_player = pass_stats.get('passes_by_player', {})
            if passes_by_player:
                sorted_passers = sorted(passes_by_player.items(), key=lambda x: x[1], reverse=True)[:3]
                lines.append(f"Top passers:")
                for player_id, count in sorted_passers:
                    lines.append(f"• Player {player_id}: {count} passes")

    lines.append(f"\nDATA NOT AVAILABLE: formations, tactics, heat maps, positions")

    return "\n".join(lines)

def generate_summary(analysis_data: dict) -> str:
    """Generate AI summary of the soccer clip"""
    if client is None:
        return generate_fallback_summary(analysis_data)

    system_prompt = (
        "You are a concise soccer video analyst. Give brief, data-driven insights in 2-3 sentences max. "
        "Only mention facts from the data provided. Use km/h for speeds. No fluff or speculation. "
        "If asked about something not in the data (passes, formations, tactics), say that data isn't tracked. "
        "If asked about non-soccer topics, politely say you only analyze soccer footage."
    )

    user_prompt = build_summary_prompt(analysis_data) + """

    Give a brief summary (2-3 sentences) covering the key stats: possession leader, fastest player, and team balance. Be direct and factual.
    """

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.5,
            max_tokens=150,
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
        "You are a concise soccer video analyst. Answer in 1-2 sentences using only the data provided. "
        "Use km/h for speeds. If the data doesn't have the answer (like passes, formations, tactics), say 'That data isn't tracked.' "
        "If asked about non-soccer topics, say 'I only analyze soccer footage.' No speculation."
    )

    data_context = build_summary_prompt(analysis_data)
    user_prompt = f"""
    Data:
    {data_context}

    Question: {query}

    Answer in 1-2 sentences max, using only the data above.
    """

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.5,
            max_tokens=100,
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
        if 'fastest_player' in movement and movement['fastest_player']:
            fastest = movement['fastest_player']
            summary_parts.append(f"⚡ Fastest player: Player {fastest.get('track_id')} ({fastest.get('max_speed_kmh', 0):.1f} km/h)")
    
    summary_parts.append("🤖 AI analysis temporarily unavailable - showing basic statistics")
    
    return "\n".join(summary_parts)

def generate_fallback_answer(query: str, analysis_data: dict) -> str:
    """Generate a basic answer without OpenAI"""
    query_lower = query.lower()

    # Check for non-soccer topics
    non_soccer_keywords = ['weather', 'news', 'movie', 'food', 'music', 'politics', 'hello', 'hi ', 'hey']
    if any(word in query_lower for word in non_soccer_keywords):
        return "I only analyze soccer footage. Ask me about player stats, possession, or speeds from the video."

    # Check for data we don't track
    not_tracked = ['formation', 'tactic', 'heat map', 'position', 'shot', 'goal', 'assist']
    if any(word in query_lower for word in not_tracked):
        return "That data isn't tracked. I can provide: passes, player speeds, possession stats, and team balance."

    # Pass queries
    if 'pass' in query_lower:
        if 'pass_stats' in analysis_data:
            pass_stats = analysis_data['pass_stats']
            total = pass_stats.get('total_passes', 0)
            t1 = pass_stats.get('team_1_passes', 0)
            t2 = pass_stats.get('team_2_passes', 0)
            return f"{total} passes completed. Team 1: {t1}, Team 2: {t2}."
        return "No pass data available for this clip."

    # Possession queries
    if any(word in query_lower for word in ['possession', 'ball', 'control']):
        if 'possession_stats' in analysis_data:
            possession = analysis_data['possession_stats']
            if possession.get('most_possession'):
                player_id, percentage = possession['most_possession']
                return f"Player {player_id} had the most possession at {percentage:.1f}%."

    # Speed/movement queries
    if any(word in query_lower for word in ['fast', 'speed', 'quick', 'pace', 'average']):
        if 'movement_stats' in analysis_data:
            movement = analysis_data['movement_stats']
            individual = movement.get('individual_stats', [])
            if individual:
                all_speeds = [p.get('avg_speed_kmh', 0) for p in individual if p.get('avg_speed_kmh', 0) > 0]
                if all_speeds:
                    avg = sum(all_speeds) / len(all_speeds)
                    if 'average' in query_lower:
                        return f"Average player speed: {avg:.1f} km/h."
            if movement.get('fastest_player'):
                fastest = movement['fastest_player']
                return f"Player {fastest.get('track_id')} was fastest at {fastest.get('max_speed_kmh', 0):.1f} km/h."

    # Player count queries
    if any(word in query_lower for word in ['player', 'how many']):
        stats = analysis_data.get('stats', {})
        count = stats.get('unique_players', 0)
        return f"{count} unique players detected."

    return "I can answer questions about: possession, player speeds, and team stats from this video."

if __name__ == "__main__":
    # Test with a sample analysis ID
    try:
        analysis_data = load_analysis_data("test-id")
        print(generate_summary(analysis_data))
    except FileNotFoundError:
        print("No test analysis data found")