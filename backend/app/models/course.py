"""
Course-related models for learning paths and progress tracking.
"""
from sqlalchemy import Column, String, Text, Integer, Float, DateTime, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class SkillLevel(str, enum.Enum):
    """Skill level enumeration."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class CourseStatus(str, enum.Enum):
    """Course enrollment status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PAUSED = "paused"


class Course(Base):
    """Course model representing a learning topic/subject."""
    
    __tablename__ = "courses"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    
    # Syllabus template stored as JSON
    # Format: {"modules": [{"title": "Module 1", "topics": [...]}]}
    syllabus_template = Column(JSON, default={})
    
    # Metadata
    difficulty = Column(Enum(SkillLevel), default=SkillLevel.BEGINNER)
    estimated_hours = Column(Integer, default=40)
    tags = Column(JSON, default=[])  # ["python", "programming", "data-science"]
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user_courses = relationship("UserCourse", back_populates="course", cascade="all, delete-orphan")
    topic_contents = relationship("TopicContent", back_populates="course", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Course {self.title}>"


class UserCourse(Base):
    """User enrollment in a course with progress tracking."""
    
    __tablename__ = "user_courses"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    course_id = Column(String, ForeignKey("courses.id"), nullable=False)
    
    # Learning configuration
    skill_level = Column(Enum(SkillLevel), default=SkillLevel.BEGINNER)
    duration_days = Column(Integer, default=30)  # How many days to complete
    
    # Progress tracking
    progress = Column(Float, default=0.0)  # 0-100 percentage
    status = Column(Enum(CourseStatus), default=CourseStatus.NOT_STARTED)
    
    # Current learning state
    current_module = Column(Integer, default=0)
    current_topic = Column(Integer, default=0)
    
    # Performance metrics
    quiz_average = Column(Float, default=0.0)
    total_time_minutes = Column(Integer, default=0)
    
    # Timestamps
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    last_activity = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="user_courses")
    course = relationship("Course", back_populates="user_courses")
    roadmaps = relationship("Roadmap", back_populates="user_course", cascade="all, delete-orphan")
    quiz_results = relationship("QuizResult", back_populates="user_course", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<UserCourse user={self.user_id} course={self.course_id}>"


class Roadmap(Base):
    """Personalized learning roadmap for a user's course."""
    
    __tablename__ = "roadmaps"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_course_id = Column(String, ForeignKey("user_courses.id"), nullable=False)
    
    # Roadmap data stored as JSON
    # Format: {
    #   "day_1": {"topics": ["topic1", "topic2"], "duration_minutes": 60},
    #   "day_2": {...}
    # }
    roadmap = Column(JSON, nullable=False)
    
    # Metadata
    total_days = Column(Integer, nullable=False)
    hours_per_day = Column(Float, default=1.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user_course = relationship("UserCourse", back_populates="roadmaps")
    
    def __repr__(self):
        return f"<Roadmap user_course={self.user_course_id} days={self.total_days}>"


class TopicContent(Base):
    """Cached content for a specific topic in a course."""
    
    __tablename__ = "topic_contents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    course_id = Column(String, ForeignKey("courses.id"), nullable=False)
    
    # Position in syllabus
    module_index = Column(Integer, nullable=False)
    topic_index = Column(Integer, nullable=False)
    topic_name = Column(String, nullable=True)
    
    # The actual generated content
    content = Column(Text, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    course = relationship("Course", back_populates="topic_contents")
    
    def __repr__(self):
        return f"<TopicContent course={self.course_id} module={self.module_index} topic={self.topic_index}>"
