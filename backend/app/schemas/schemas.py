"""
Pydantic schemas for API request/response models.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============= Authentication Schemas =============

class UserCreate(BaseModel):
    """Schema for user registration."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """Schema for user login."""
    username: str
    password: str


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Schema for user data response."""
    id: str
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    preferences: Dict[str, Any] = {}
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============= Conversation Schemas =============

class ChatMessage(BaseModel):
    """Schema for chat message request."""
    message: str = Field(..., min_length=1)
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Schema for chat response."""
    reply: str
    intent: str
    confidence: float
    used_rag: bool
    metadata: Dict[str, Any] = {}
    conversation_id: Optional[str] = None


class ConversationHistory(BaseModel):
    """Schema for conversation history item."""
    id: str
    message: str
    bot_reply: str
    intent: Optional[str]
    confidence: Optional[float]
    timestamp: datetime
    
    class Config:
        from_attributes = True


# ============= Course Schemas =============

class CourseCreate(BaseModel):
    """Schema for creating a course."""
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    syllabus_template: Dict[str, Any] = {}
    difficulty: str = "beginner"
    estimated_hours: int = 40
    tags: List[str] = []


class CourseResponse(BaseModel):
    """Schema for course response."""
    id: str
    title: str
    description: Optional[str]
    difficulty: str
    estimated_hours: int
    tags: List[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserCourseEnroll(BaseModel):
    """Schema for enrolling in a course."""
    course_id: str
    skill_level: str = "beginner"
    duration_days: int = 30


class UserCourseResponse(BaseModel):
    """Schema for user course response."""
    id: str
    course_id: str
    course_title: Optional[str] = None
    skill_level: str
    duration_days: int
    progress: float
    status: str
    current_module: Optional[int] = 0
    current_topic: Optional[int] = 0
    started_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# ============= Roadmap Schemas =============

class RoadmapRequest(BaseModel):
    """Schema for roadmap generation request."""
    topic: str = Field(..., min_length=1)
    duration_days: int = Field(30, ge=1, le=365)
    hours_per_day: float = Field(1.0, ge=0.5, le=8.0)
    skill_level: str = "beginner"
    focus_areas: List[str] = []


class RoadmapResponse(BaseModel):
    """Schema for roadmap response."""
    id: str
    user_course_id: str
    roadmap: Dict[str, Any]
    total_days: int
    hours_per_day: float
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============= Quiz Schemas =============

class QuizRequest(BaseModel):
    """Schema for quiz generation request."""
    topic: str
    num_questions: int = Field(5, ge=1, le=20)
    skill_level: str = "beginner"


class QuizQuestion(BaseModel):
    """Schema for a quiz question."""
    question: str
    options: Dict[str, str]
    correct_answer: str
    explanation: str


class QuizEvaluation(BaseModel):
    """Schema for quiz evaluation request."""
    quiz_id: str
    answers: Dict[int, str]  # question number -> answer letter


class QuizResultResponse(BaseModel):
    """Schema for quiz result response."""
    id: str
    score: float
    total_questions: int
    correct_answers: int
    details: Dict[str, Any]
    taken_at: datetime
    
    class Config:
        from_attributes = True


# ============= Upload Schemas =============

class UploadResponse(BaseModel):
    """Schema for file upload response."""
    filename: str
    size: int
    chunks_added: int
    message: str


# ============= Admin Schemas =============

class MissingKnowledgeResponse(BaseModel):
    """Schema for missing knowledge item."""
    id: str
    topic: str
    context: str
    user_query: Optional[str]
    status: str
    occurrence_count: int
    priority: str
    logged_at: datetime
    
    class Config:
        from_attributes = True


class SystemStats(BaseModel):
    """Schema for system statistics."""
    total_users: int
    total_courses: int
    total_conversations: int
    pending_knowledge_gaps: int
    rag_document_count: int


# ============= Content Generation Schemas =============

class SyllabusRequest(BaseModel):
    """Schema for syllabus generation request."""
    subject: str = Field(..., min_length=1)
    skill_level: str = "beginner"
    target_audience: Optional[str] = None


class NotesRequest(BaseModel):
    """Schema for notes generation request."""
    subject: str
    topic: str
    detail_level: str = "comprehensive"  # brief, comprehensive, deep_dive


class LectureFlowRequest(BaseModel):
    """Schema for lecture flow generation request."""
    subject: str
    topic: str
    duration_minutes: int = 60


class AssignmentRequest(BaseModel):
    """Schema for assignment generation request."""
    subject: str
    topic: str
    difficulty: str = "intermediate"


class ExplanationRequest(BaseModel):
    """Schema for concept explanation request."""
    subject: str
    concept: str
    context: Optional[str] = None


class GenerationResponse(BaseModel):
    """Generic schema for generation response."""
    content: Any
    metadata: Dict[str, Any] = {}
