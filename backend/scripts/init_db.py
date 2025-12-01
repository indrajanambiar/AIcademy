"""
Database initialization script with sample data.
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import Base, engine, SessionLocal
from app.models import User, Course
from app.core.security import get_password_hash
from app.core.logging import get_logger

logger = get_logger(__name__)


def init_db():
    """Initialize database and create tables."""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def seed_sample_data():
    """Seed database with sample data."""
    db = SessionLocal()
    
    try:
        logger.info("Seeding sample data...")
        
        # Create admin user
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                email="admin@example.com",
                password_hash=get_password_hash("admin123"),
                full_name="Admin User",
                is_admin=True,
                is_active=True,
            )
            db.add(admin)
            logger.info("Created admin user")
        
        # Create sample courses
        sample_courses = [
            {
                "title": "Introduction to Python",
                "description": "Learn Python programming from scratch",
                "difficulty": "beginner",
                "estimated_hours": 40,
                "tags": ["programming", "python", "beginner"],
                "syllabus_template": {
                    "modules": [
                        {"title": "Python Basics", "topics": ["Variables", "Data Types", "Control Flow"]},
                        {"title": "Functions and Modules", "topics": ["Functions", "Modules", "Packages"]},
                        {"title": "OOP", "topics": ["Classes", "Objects", "Inheritance"]},
                    ]
                },
            },
            {
                "title": "Machine Learning Fundamentals",
                "description": "Master the basics of machine learning",
                "difficulty": "intermediate",
                "estimated_hours": 60,
                "tags": ["machine-learning", "ai", "data-science"],
                "syllabus_template": {
                    "modules": [
                        {"title": "ML Basics", "topics": ["Supervised Learning", "Unsupervised Learning"]},
                        {"title": "Algorithms", "topics": ["Linear Regression", "Decision Trees", "Neural Networks"]},
                        {"title": "Deep Learning", "topics": ["CNNs", "RNNs", "Transformers"]},
                    ]
                },
            },
            {
                "title": "Web Development with React",
                "description": "Build modern web applications with React",
                "difficulty": "intermediate",
                "estimated_hours": 50,
                "tags": ["web-development", "react", "javascript"],
                "syllabus_template": {
                    "modules": [
                        {"title": "React Basics", "topics": ["Components", "Props", "State"]},
                        {"title": "Advanced React", "topics": ["Hooks", "Context", "Router"]},
                        {"title": "State Management", "topics": ["Redux", "Zustand", "React Query"]},
                    ]
                },
            },
        ]
        
        for course_data in sample_courses:
            existing = db.query(Course).filter(Course.title == course_data["title"]).first()
            if not existing:
                course = Course(**course_data)
                db.add(course)
                logger.info(f"Created course: {course_data['title']}")
        
        db.commit()
        logger.info("Sample data seeded successfully")
        
        # Print credentials
        print("\n" + "="*60)
        print("🎓 AI Learning Coach - Database Initialized!")
        print("="*60)
        print("\nAdmin Credentials:")
        print("  Username: admin")
        print("  Password: admin123")
        print("  Email: admin@example.com")
        print("\nSample Courses Created:")
        for course in sample_courses:
            print(f"  • {course['title']}")
        print("\n" + "="*60 + "\n")
        
    except Exception as e:
        logger.error(f"Error seeding data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    seed_sample_data()
    print("Done!")
