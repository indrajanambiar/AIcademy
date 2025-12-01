"""
Missing knowledge tracking model.
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class KnowledgeStatus(str, enum.Enum):
    """Status of missing knowledge entries."""
    PENDING = "pending"
    FILLED = "filled"
    IN_PROGRESS = "in_progress"
    REVIEWED = "reviewed"


class MissingKnowledge(Base):
    """Model for tracking knowledge gaps identified during conversations."""
    
    __tablename__ = "missing_knowledge"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=True)  # Nullable for system-wide gaps
    
    # Knowledge gap details
    topic = Column(String, nullable=False, index=True)
    context = Column(Text, nullable=False)  # Original question/context
    user_query = Column(Text, nullable=True)  # The actual user question
    
    # Processing status
    status = Column(Enum(KnowledgeStatus), default=KnowledgeStatus.PENDING)
    
    # Admin notes and resolution
    admin_notes = Column(Text, nullable=True)
    resolution = Column(Text, nullable=True)  # How it was resolved
    
    # Timestamps
    logged_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    
    # Priority and impact
    occurrence_count = Column(Integer, default=1)  # How many times this gap was hit
    priority = Column(String, default="medium")  # low, medium, high
    
    # Relationships
    user = relationship("User", back_populates="missing_knowledge")
    
    def __repr__(self):
        return f"<MissingKnowledge topic={self.topic} status={self.status}>"
