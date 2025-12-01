"""
Course management API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.course import Course, UserCourse, CourseStatus
from app.schemas.schemas import (
    CourseCreate,
    CourseResponse,
    UserCourseEnroll,
    UserCourseResponse,
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/", response_model=List[CourseResponse])
async def list_courses(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List all available courses."""
    courses = db.query(Course).offset(skip).limit(limit).all()
    return courses


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(course_id: str, db: Session = Depends(get_db)):
    """Get a specific course by ID."""
    course = db.query(Course).filter(Course.id == course_id).first()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )
    
    return course


@router.post("/{course_id}/enroll", response_model=UserCourseResponse)
async def enroll_in_course(
    course_id: str,
    enrollment: UserCourseEnroll,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Enroll current user in a course."""
    # Check if course exists by ID or Title
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        # Try finding by title
        course = db.query(Course).filter(Course.title == course_id).first()
        
    if not course:
        # If course doesn't exist in DB but is being enrolled in (likely from discovery),
        # we should create it if it exists in the file system (verified by caller usually, but here we trust the title)
        # For now, let's create a basic record for it
        logger.info(f"Course {course_id} not found in DB, creating new record")
        course = Course(
            title=course_id,
            description=f"Course on {course_id}",
            syllabus_template={} # Empty initially, will be filled by generate-syllabus
        )
        db.add(course)
        db.commit()
        db.refresh(course)
    
    # Check if already enrolled
    existing = db.query(UserCourse).filter(
        UserCourse.user_id == current_user.id,
        UserCourse.course_id == course.id,
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already enrolled in this course",
        )
    
    # Create enrollment
    user_course = UserCourse(
        user_id=current_user.id,
        course_id=course.id,
        skill_level=enrollment.skill_level,
        duration_days=enrollment.duration_days,
        status=CourseStatus.NOT_STARTED,
    )
    
    db.add(user_course)
    db.commit()
    db.refresh(user_course)
    
    logger.info(
        "User enrolled in course",
        user_id=current_user.id,
        course_id=course.id,
        course_title=course.title
    )
    
    return user_course


@router.get("/my/enrolled", response_model=List[UserCourseResponse])
async def get_my_courses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get courses the current user is enrolled in."""
    user_courses = db.query(UserCourse).filter(
        UserCourse.user_id == current_user.id
    ).all()
    
    # Manually construct response to include course title
    response = []
    for uc in user_courses:
        # Pydantic will handle the conversion from dict to UserCourseResponse
        uc_dict = {
            "id": uc.id,
            "course_id": uc.course_id,
            "course_title": uc.course.title if uc.course else uc.course_id,
            "skill_level": uc.skill_level,
            "duration_days": uc.duration_days,
            "progress": uc.progress,
            "status": uc.status,
            "current_module": uc.current_module,
            "current_topic": uc.current_topic,
            "started_at": uc.started_at
        }
        response.append(uc_dict)
    
    return response


@router.get("/my/details/{course_identifier}")
async def get_my_course_details(
    course_identifier: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get detailed progress and syllabus for a specific enrolled course.
    Identifier can be Course ID or Title.
    """
    # Find the course first
    course = db.query(Course).filter(Course.id == course_identifier).first()
    if not course:
        course = db.query(Course).filter(Course.title == course_identifier).first()
        
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    # Find enrollment
    user_course = db.query(UserCourse).filter(
        UserCourse.user_id == current_user.id,
        UserCourse.course_id == course.id
    ).first()
    
    if not user_course:
        raise HTTPException(status_code=404, detail="Not enrolled in this course")
        
    # Get quiz results
    quiz_results = []
    for qr in user_course.quiz_results:
        quiz_results.append({
            "id": qr.id,
            "score": qr.score,
            "total_questions": qr.total_questions,
            "correct_answers": qr.correct_answers,
            "topic": qr.topic,
            "week": qr.week,
            "taken_at": qr.taken_at
        })

    return {
        "course": {
            "id": course.id,
            "title": course.title,
            "syllabus": course.syllabus_template
        },
        "progress": {
            "status": user_course.status,
            "current_module": user_course.current_module,
            "current_topic": user_course.current_topic,
            "progress_percent": user_course.progress,
            "last_activity": user_course.last_activity
        },
        "quiz_results": quiz_results
    }


@router.post("/{course_id}/start")
async def start_course(
    course_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Start a course (mark as in progress)."""
    # Support title lookup
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        course = db.query(Course).filter(Course.title == course_id).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    user_course = db.query(UserCourse).filter(
        UserCourse.user_id == current_user.id,
        UserCourse.course_id == course.id,
    ).first()
    
    if not user_course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not enrolled in this course",
        )
    
    from datetime import datetime
    user_course.status = CourseStatus.IN_PROGRESS
    user_course.started_at = datetime.utcnow()
    user_course.last_activity = datetime.utcnow()
    
    db.commit()
    
    logger.info("Course started", user_id=current_user.id, course_id=course.id)
    
    return {"message": "Course started successfully"}
