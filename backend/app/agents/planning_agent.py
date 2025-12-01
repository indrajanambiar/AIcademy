"""
Planning Agent - Creates personalized learning roadmaps.
"""
from typing import Dict, Any
import json
from datetime import datetime, timedelta

from app.agents.state import AgentState
from app.services.llm_service import llm_service
from app.core.logging import get_logger

logger = get_logger(__name__)


class PlanningAgent:
    """Agent responsible for creating personalized learning roadmaps."""
    
    async def __call__(self, state: AgentState) -> AgentState:
        """
        Generate a learning roadmap.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with roadmap
        """
        logger.info("Planning agent activated")
        
        # Extract roadmap parameters
        config = self._extract_roadmap_config(state)
        
        # Generate roadmap
        roadmap = await self._generate_roadmap(config)
        
        state["generated_roadmap"] = roadmap
        state["bot_response"] = self._format_roadmap_response(roadmap, config)
        state["completed"] = True
        state["next_agent"] = None
        
        logger.info(
            "Roadmap generated",
            topic=config["topic"],
            duration_days=config["duration_days"],
        )
        
        return state
    
    def _extract_roadmap_config(self, state: AgentState) -> Dict[str, Any]:
        """Extract roadmap configuration from state and message."""
        message = state["user_message"].lower()
        
        config = {
            "topic": state.get("current_topic", ""),
            "duration_days": 30,  # Default
            "hours_per_day": 1,  # Default
            "skill_level": state.get("skill_level", "beginner"),
            "focus_areas": [],
        }
        
        # Try to extract topic
        if not config["topic"]:
            # Simple extraction - look for "learn X" patterns
            if "learn" in message:
                topic_start = message.find("learn") + 6
                topic_words = message[topic_start:].split()[:3]
                config["topic"] = " ".join(topic_words).strip()
        
        # Try to extract duration
        if "days" in message:
            words = message.split()
            for i, word in enumerate(words):
                if word == "days" and i > 0:
                    try:
                        config["duration_days"] = int(words[i-1])
                    except ValueError:
                        pass
        
        if "weeks" in message:
            words = message.split()
            for i, word in enumerate(words):
                if word in ["week", "weeks"] and i > 0:
                    try:
                        weeks = int(words[i-1])
                        config["duration_days"] = weeks * 7
                    except ValueError:
                        pass
        
        # Try to extract hours per day
        if "hour" in message:
            words = message.split()
            for i, word in enumerate(words):
                if "hour" in word and i > 0:
                    try:
                        config["hours_per_day"] = float(words[i-1])
                    except ValueError:
                        pass
        
        return config
    
    async def _generate_roadmap(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a personalized learning roadmap using LLM."""
        prompt = f"""
Create a 4-week learning roadmap for:

Topic: {config['topic']}
Duration: 4 weeks
Skill level: {config['skill_level']}

IMPORTANT:
1. Be specific with topic names.
2. Include practical exercises.

Format your response as a valid JSON object. Do not include markdown formatting.
{{
  "overview": "Brief description of the learning path",
  "weeks": {{
    "1": {{
      "title": "Week 1 Title",
      "goal": "Main goal for this week",
      "topics": ["Topic 1", "Topic 2", "Topic 3"],
      "exercises": ["Exercise 1", "Exercise 2"]
    }},
    "2": {{
      "title": "Week 2 Title",
      "goal": "Main goal for this week",
      "topics": ["Topic 1", "Topic 2"],
      "exercises": ["Exercise 1"]
    }},
    "3": {{
      "title": "Week 3 Title",
      "goal": "Main goal for this week",
      "topics": ["Topic 1", "Topic 2"],
      "exercises": ["Exercise 1"]
    }},
    "4": {{
      "title": "Week 4 Title",
      "goal": "Main goal for this week",
      "topics": ["Topic 1", "Topic 2"],
      "exercises": ["Exercise 1"]
    }}
  }}
}}
"""
        
        try:
            response = await llm_service.generate(prompt, raw_prompt=True)
            
            # Clean up response
            cleaned_response = response.strip()
            # Remove markdown code blocks if present
            if "```json" in cleaned_response:
                cleaned_response = cleaned_response.split("```json")[1].split("```")[0]
            elif "```" in cleaned_response:
                cleaned_response = cleaned_response.split("```")[1].split("```")[0]
            
            cleaned_response = cleaned_response.strip()
            
            # Find JSON boundaries
            json_start = cleaned_response.find("{")
            json_end = cleaned_response.rfind("}") + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = cleaned_response[json_start:json_end]
                try:
                    roadmap = json.loads(json_str)
                except json.JSONDecodeError:
                    # Try ast.literal_eval for single quotes or python-style dicts
                    import ast
                    try:
                        roadmap = ast.literal_eval(json_str)
                    except:
                        logger.error("Failed to parse roadmap JSON", response=cleaned_response)
                        raise ValueError("Invalid JSON")
                
                return roadmap
            else:
                logger.warning("No JSON found in roadmap response", response=response[:200])
                return self._create_fallback_roadmap(config, response)
                
        except Exception as e:
            logger.error("Roadmap generation failed", error=str(e))
            return self._create_fallback_roadmap(config)
    
    def _create_fallback_roadmap(
        self,
        config: Dict[str, Any],
        llm_response: str = None,
    ) -> Dict[str, Any]:
        """Create a basic fallback roadmap."""
        topic = config["topic"]
        
        roadmap = {
            "overview": f"A 4-week learning path for {topic}",
            "weeks": {},
        }
        
        for week in range(1, 5):
            roadmap["weeks"][str(week)] = {
                "title": f"Week {week}: {topic} Concepts",
                "goal": f"Learn core concepts of {topic}",
                "topics": [f"{topic} basics", "Key principles", "Advanced concepts"],
                "exercises": ["Practice exercises", "Mini-project"],
            }
        
        return roadmap
    
    def _format_roadmap_response(
        self,
        roadmap: Dict[str, Any],
        config: Dict[str, Any],
    ) -> str:
        """Format roadmap for display."""
        response = f"📅 **Learning Roadmap: {config['topic'].title()}**\n\n"
        response += f"{roadmap.get('overview', '')}\n\n"
        
        weeks = roadmap.get("weeks", {})
        for week_num in sorted(weeks.keys(), key=int):
            week = weeks[week_num]
            response += f"**Week {week_num}: {week.get('title', 'Learning Week')}**\n"
            response += f"🎯 Goal: {week.get('goal', '')}\n"
            
            topics = week.get("topics", [])
            if topics:
                response += "📚 Topics:\n"
                for topic in topics:
                    response += f"  • {topic}\n"
            
            exercises = week.get("exercises", [])
            if exercises:
                response += "💻 Exercises:\n"
                for ex in exercises:
                    response += f"  • {ex}\n"
            
            response += "\n"
        
        response += "💪 Ready to start your learning journey? Let me know when you'd like to begin!"
        
        return response


# Global instance
planning_agent = PlanningAgent()
