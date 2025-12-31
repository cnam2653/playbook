import openai
import os
import json
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class OpenAIService:
    """Service for generating natural language summaries using OpenAI API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.client = openai.OpenAI(
            api_key=api_key or os.getenv('OPENAI_API_KEY')
        )
        
    def generate_clip_summary(self, analysis_data: Dict, custom_query: str = None) -> str:
        """Generate a summary of the entire clip"""
        
        base_prompt = """You are a soccer analyst. Based on the following data from a soccer clip analysis, provide a natural, engaging summary.

Analysis Data:
{}

Please provide insights about:
- Overall game flow and possession
- Key player performances
- Notable events or patterns
- Team dynamics

Keep the summary conversational and insightful, like a sports commentator."""

        if custom_query:
            base_prompt += f"\n\nSpecific question to address: {custom_query}"
        
        try:
            formatted_data = self._format_analysis_data(analysis_data)
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert soccer analyst who provides insightful, engaging commentary on soccer clips."},
                    {"role": "user", "content": base_prompt.format(formatted_data)}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            # Return fallback summary based on data
            return self._generate_fallback_summary(analysis_data)
    
    def answer_query(self, query: str, analysis_data: Dict) -> str:
        """Answer a specific question about the clip"""
        
        prompt = f"""Based on the following sports analysis data, answer this question: {query}

Analysis Data:
{self._format_analysis_data(analysis_data)}

Provide a direct, informative answer based on the available data."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert sports analyst who answers questions about match footage based on tracking and statistical data."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API error for query: {e}")
            return self._generate_fallback_answer(query, analysis_data)
    
    def _format_analysis_data(self, data: Dict) -> str:
        """Format analysis data for LLM consumption"""
        formatted = []
        
        # Video info
        if 'video_info' in data:
            info = data['video_info']
            formatted.append(f"VIDEO INFO:")
            formatted.append(f"  Duration: {info.get('duration', 0):.1f}s")
            formatted.append(f"  Players detected: {info.get('player_count', 0)}")
            formatted.append(f"  Ball detected: {info.get('ball_detected', False)}")
        
        # Possession data
        if 'possession_stats' in data:
            possession = data['possession_stats']
            formatted.append("\nPOSSESSION STATISTICS:")
            if 'possession_percentages' in possession:
                for player_id, percentage in possession['possession_percentages'].items():
                    formatted.append(f"  Player {player_id}: {percentage:.1f}% possession")
            
            if possession.get('most_possession'):
                player_id, percentage = possession['most_possession']
                formatted.append(f"  Most possession: Player {player_id} ({percentage:.1f}%)")
        
        # Movement data
        if 'movement_stats' in data:
            movement = data['movement_stats']
            formatted.append("\nMOVEMENT STATISTICS:")
            
            if 'fastest_player' in movement:
                fastest = movement['fastest_player']
                formatted.append(f"  Fastest player: Player {fastest.get('track_id')} ({fastest.get('max_speed_mps', 0):.1f} m/s)")
            
            if 'most_active_player' in movement:
                active = movement['most_active_player']
                formatted.append(f"  Most active: Player {active.get('track_id')} (activity: {active.get('activity_score', 0):.1f})")
        
        # Events
        if 'events' in data:
            events = data['events']
            formatted.append(f"\nKEY EVENTS ({len(events)} total):")
            for event in events[:5]:  # Show first 5 events
                event_time = event.get('timestamp', 0)
                description = event.get('description', 'Unknown event')
                formatted.append(f"  {event_time:.1f}s: {description}")
        
        return '\n'.join(formatted) if formatted else "No analysis data available"
    
    def _generate_fallback_summary(self, data: Dict) -> str:
        """Generate a basic summary without OpenAI"""
        summary = ["📊 Sports Clip Analysis Summary"]
        
        # Video info
        if 'video_info' in data:
            info = data['video_info']
            summary.append(f"🎬 Duration: {info.get('duration', 0):.1f} seconds")
            summary.append(f"👥 Players detected: {info.get('player_count', 0)}")
            summary.append(f"⚽ Ball detected: {'Yes' if info.get('ball_detected') else 'No'}")
        
        # Possession
        if 'possession_stats' in data and data['possession_stats'].get('most_possession'):
            player_id, percentage = data['possession_stats']['most_possession']
            summary.append(f"🏃‍♂️ Player {player_id} dominated possession with {percentage:.1f}%")
        
        # Speed
        if 'movement_stats' in data and 'fastest_player' in data['movement_stats']:
            fastest = data['movement_stats']['fastest_player']
            summary.append(f"⚡ Fastest player: Player {fastest.get('track_id')} at {fastest.get('max_speed_mps', 0):.1f} m/s")
        
        return "\n".join(summary)
    
    def _generate_fallback_answer(self, query: str, data: Dict) -> str:
        """Generate a basic answer without OpenAI"""
        query_lower = query.lower()
        
        # Possession queries
        if 'possession' in query_lower or 'ball' in query_lower:
            if 'possession_stats' in data and data['possession_stats'].get('most_possession'):
                player_id, percentage = data['possession_stats']['most_possession']
                return f"Player {player_id} had the most ball possession with {percentage:.1f}%"
        
        # Speed/movement queries
        if any(word in query_lower for word in ['fast', 'speed', 'quick']):
            if 'movement_stats' in data and 'fastest_player' in data['movement_stats']:
                fastest = data['movement_stats']['fastest_player']
                return f"Player {fastest.get('track_id')} was the fastest, reaching {fastest.get('max_speed_mps', 0):.1f} m/s"
        
        # Player queries
        if 'player' in query_lower:
            if 'video_info' in data:
                count = data['video_info'].get('player_count', 0)
                return f"I detected {count} players in this clip."
        
        return "I'm having trouble accessing the AI service right now, but I can see your analysis data is ready. Please try asking about possession, speed, or player statistics."