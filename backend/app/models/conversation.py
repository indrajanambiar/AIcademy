"""
Conversation model for chat history.
"""
from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base


class Conversation(Base):
    """Conversation model for storing chat history."""
    
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Message content
    message = Column(Text, nullable=False)  # User's message
    bot_reply = Column(Text, nullable=False)  # Bot's response
    
    # Context and metadata
    intent = Column(String, nullable=True)  # Detected intent (learn, quiz, roadmap, etc.)
    confidence = Column(Float, nullable=True)  # Confidence score of the answer
    used_rag = Column(String, default=False)  # Whether RAG was used
    
    # Related course/topic
    course_id = Column(String, nullable=True)
    topic = Column(String, nullable=True)
    
    # Additional metadata stored as JSON
    meta_data = Column(JSON, default={})
    
    # Feedback
    user_rating = Column(Float, nullable=True)  # 1-5 stars
    user_feedback = Column(Text, nullable=True)
    
    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    
    def __repr__(self):
        return f"<Conversation user={self.user_id} at={self.timestamp}>"
