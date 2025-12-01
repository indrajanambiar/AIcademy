"""
Intent Detection Agent - Classifies user intent from their message.
"""
from typing import Dict, Any
from app.agents.state import AgentState, Intent
from app.services.llm_service import llm_service
from app.core.logging import get_logger

logger = get_logger(__name__)


class IntentAgent:
    """Agent responsible for detecting user intent."""
    
    def __init__(self):
        self.intent_keywords = {
            Intent.LEARN: ["learn", "teach", "explain", "understand", "tell me about", "what is"],
            Intent.QUIZ: ["quiz", "test", "assess me", "check my knowledge", "exam"],
            Intent.ROADMAP: ["roadmap", "plan", "schedule", "path", "how to learn", "study plan"],
            Intent.ASSESS: ["assess", "level", "skill", "evaluate", "where am i"],
            Intent.EXPLAIN: ["why", "how", "explain", "clarify", "elaborate"],
            Intent.PRACTICE: ["practice", "exercise", "problem", "example"],
            Intent.PROGRESS: ["progress", "status", "how am i doing", "achievement"],
            Intent.CHAT: ["hello", "hi", "hey", "thanks", "thank you", "bye"],
        }
    
    async def __call__(self, state: AgentState) -> AgentState:
        """
        Detect intent from user message.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with detected intent
        """
        # 2. Check for explicit keywords
        message_lower = state["user_message"].lower()
        
        # Check for "No doubts" -> Quiz transition
        # We check for simple "no" or variations that imply "I have no doubts, proceed"
        if message_lower.strip() in ["no", "no.", "no doubt", "no doubts", "nope", "none", "clear", "all clear", "it's clear", "its clear"]:
            # Try to get topic from state
            topic = state.get("current_topic")
            
            # If not in state, try to get from DB (UserCourse)
            if not topic and state.get("db") and state.get("user_id") and state.get("current_course_id"):
                try:
                    from app.models.course import UserCourse, Course
                    db = state["db"]
                    user_course = db.query(UserCourse).filter(
                        UserCourse.user_id == state["user_id"],
                        UserCourse.course_id == state["current_course_id"]
                    ).first()
                    
                    if user_course:
                        course = db.query(Course).filter(Course.id == state["current_course_id"]).first()
                        if course and course.syllabus_template:
                            modules = course.syllabus_template.get("modules", [])
                            curr_mod = user_course.current_module or 0
                            curr_top = user_course.current_topic or 0
                            if curr_mod < len(modules):
                                topics = modules[curr_mod].get("topics", [])
                                if curr_top < len(topics):
                                    topic = topics[curr_top]
                                    # Update state so QuizAgent has it
                                    state["current_topic"] = topic
                except Exception as e:
                    logger.error("Failed to lookup topic in IntentAgent", error=str(e))

            # Fallback: if still no topic but we have course_id, use generic topic
            if not topic and state.get("current_course_id"):
                topic = f"concepts from {state['current_course_id']}"
                state["current_topic"] = topic

            if topic:
                logger.info("Detected 'No doubts' response, routing to QUIZ", topic=topic)
                state["intent"] = Intent.QUIZ
                state["confidence"] = 0.9
                state["next_agent"] = "quiz_agent"
                return state

        if "quiz" in message_lower or "test" in message_lower:
            state["intent"] = Intent.QUIZ
            state["confidence"] = 1.0
            state["next_agent"] = "quiz_agent"
            return state
        
        logger.info("Detecting intent", message=message_lower[:50])
        
        # Rule-based intent detection
        detected_intent = self._rule_based_detection(message_lower)
        
        # If uncertain, use LLM for intent classification
        if detected_intent == Intent.UNKNOWN:
            detected_intent = await self._llm_based_detection(message_lower)
        
        # Extract topic if intent is relevant
        if detected_intent in [Intent.LEARN, Intent.ROADMAP, Intent.QUIZ, Intent.EXPLAIN, Intent.PRACTICE]:
            topic = await self._extract_topic(message_lower)
            if topic and topic.lower() != "unknown":
                state["current_topic"] = topic
                logger.info("Topic extracted", topic=topic)
                
                # Reset onboarding step if a new topic is explicitly requested
                # This ensures we start fresh assessment for new topics
                if "metadata" in state:
                    state["metadata"]["onboarding_step"] = None
        
        state["intent"] = detected_intent
        state["metadata"]["intent_detection_method"] = "rule_based" if detected_intent != Intent.UNKNOWN else "llm_based"
        
        logger.info("Intent detected", intent=detected_intent)
        
        # Set next agent based on intent
        state["next_agent"] = self._get_next_agent(detected_intent)
        
        return state

    async def _extract_topic(self, message: str) -> str:
        """Extract the main topic from the message."""
        prompt = f"""
Extract the main educational topic from this user message.
Message: "{message}"

If a clear topic is present (e.g., "python", "calculus", "history of rome"), return ONLY the topic name.
If no topic is present, return "unknown".
"""
        try:
            response = await llm_service.generate(prompt)
            return response.strip().lower().replace('"', '').replace("'", "")
        except Exception as e:
            logger.error("Topic extraction failed", error=str(e))
            return "unknown"
    
    def _rule_based_detection(self, message: str) -> Intent:
        """Detect intent using keyword matching."""
        scores = {intent: 0 for intent in Intent}
        
        for intent, keywords in self.intent_keywords.items():
            for keyword in keywords:
                if keyword in message:
                    scores[intent] += 1
        
        # Get intent with highest score
        max_score = max(scores.values())
        if max_score > 0:
            for intent, score in scores.items():
                if score == max_score:
                    return intent
        
        return Intent.UNKNOWN
    
    async def _llm_based_detection(self, message: str) -> Intent:
        """Use LLM to classify intent when rules fail."""
        prompt = f"""
Classify the user's intent from their message.

Available intents:
- LEARN: User wants to learn something new
- QUIZ: User wants to take a quiz or test
- ROADMAP: User wants a learning plan or roadmap
- ASSESS: User wants their skill level assessed
- EXPLAIN: User wants deeper explanation
- PRACTICE: User wants practice problems
- PROGRESS: User wants to check their progress
- CHAT: General conversation (greetings, thanks, etc.)

User message: "{message}"

Respond with ONLY the intent name (e.g., "LEARN").
"""
        
        try:
            response = await llm_service.generate(prompt)
            intent_str = response.strip().upper()
            
            # Try to match to Intent enum
            for intent in Intent:
                if intent.value.upper() in intent_str:
                    return intent
        
        except Exception as e:
            logger.error("LLM intent detection failed", error=str(e))
        
        # Default to LEARN if unclear
        return Intent.LEARN
    
    def _get_next_agent(self, intent: Intent) -> str:
        """Determine which agent should handle this intent."""
        routing = {
            Intent.LEARN: "teaching_agent",
            Intent.QUIZ: "quiz_agent",
            Intent.ROADMAP: "planning_agent",
            Intent.ASSESS: "assessment_agent",
            Intent.EXPLAIN: "teaching_agent",
            Intent.PRACTICE: "quiz_agent",
            Intent.PROGRESS: "memory_agent",
            Intent.CHAT: "teaching_agent",
            Intent.UNKNOWN: "teaching_agent",
        }
        
        return routing.get(intent, "teaching_agent")


# Global instance
intent_agent = IntentAgent()
