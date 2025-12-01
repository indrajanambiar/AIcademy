"""
Quiz and assessment models.
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base


class QuizResult(Base):
    """Quiz result model for storing assessment outcomes."""
    
    __tablename__ = "quiz_results"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_course_id = Column(String, ForeignKey("user_courses.id"), nullable=False)
    
    # Quiz metadata
    quiz_type = Column(String, default="adaptive")  # adaptive, checkpoint, final
    week = Column(Integer, nullable=True)  # Week number in the course
    topic = Column(String, nullable=True)  # Specific topic tested
    
    # Results
    score = Column(Float, nullable=False)  # 0-100
    total_questions = Column(Integer, default=10)
    correct_answers = Column(Integer, default=0)
    
    # Detailed results stored as JSON
    # Format: {
    #   "questions": [
    #     {
    #       "question": "What is...",
    #       "user_answer": "A",
    #       "correct_answer": "B",
    #       "is_correct": false,
    #       "explanation": "..."
    #     }
    #   ],
    #   "strengths": ["topic1", "topic2"],
    #   "weaknesses": ["topic3"],
    #   "recommendations": "Focus on..."
    # }
    details = Column(JSON, default={})
    
    # Performance metrics
    time_taken_minutes = Column(Integer, nullable=True)
    difficulty_level = Column(String, default="medium")  # easy, medium, hard
    
    # Timestamps
    taken_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user_course = relationship("UserCourse", back_populates="quiz_results")
    
    def __repr__(self):
        return f"<QuizResult user_course={self.user_course_id} score={self.score}>"
