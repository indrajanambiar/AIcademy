"""
LangGraph state definition for the agent workflow.
"""
from typing import TypedDict, List, Dict, Any, Optional
from enum import Enum


class Intent(str, Enum):
    """User intent types."""
    LEARN = "learn"
    QUIZ = "quiz"
    ROADMAP = "roadmap"
    ASSESS = "assess"
    EXPLAIN = "explain"
    PRACTICE = "practice"
    PROGRESS = "progress"
    CHAT = "chat"
    UNKNOWN = "unknown"


class AgentState(TypedDict, total=False):
    """
    State shared across all agents in the workflow.
    
    This is the core data structure passed between agents.
    """
    # User information
    user_id: Optional[str]
    user_profile: Optional[Dict[str, Any]]
    db: Optional[Any]  # SQLAlchemy Session
    
    # Conversation
    user_message: str
    bot_response: str
    intent: Intent
    
    # Knowledge processing
    question: str
    answer: str
    confidence: float
    used_rag: bool
    retrieved_docs: List[Dict[str, Any]]
    evaluation: Dict[str, Any]
    
    # Learning context
    current_course_id: Optional[str]
    current_topic: Optional[str]
    skill_level: str
    target_skill_level: Optional[str]
    onboarding_step: Optional[str]
    
    # Quiz/Assessment
    quiz_questions: List[Dict[str, Any]]
    quiz_results: Optional[Dict[str, Any]]
    assessment_results: Optional[Dict[str, Any]]
    
    # Roadmap
    roadmap_config: Optional[Dict[str, Any]]
    generated_roadmap: Optional[Dict[str, Any]]
    
    # Metadata
    conversation_id: Optional[str]
    timestamp: str
    metadata: Dict[str, Any]
    
    # Control flow
    next_agent: Optional[str]
    error: Optional[str]
    completed: bool
