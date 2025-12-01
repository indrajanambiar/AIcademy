"""
User model for authentication and user management.
"""
from sqlalchemy import Column, String, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base


class User(Base):
    """User model for storing user information and authentication."""
    
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    
    # Profile
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
    # Preferences stored as JSON
    preferences = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    user_courses = relationship("UserCourse", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    missing_knowledge = relationship("MissingKnowledge", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.username}>"
