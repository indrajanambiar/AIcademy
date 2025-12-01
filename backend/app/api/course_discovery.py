"""
API endpoints for course discovery and comprehensive material generation.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.api.auth import get_current_user
from app.models.user import User
from app.services.course_discovery_service import course_discovery_service
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


# Request/Response Models
class ProcessCourseRequest(BaseModel):
    course_name: str
    max_pdfs: Optional[int] = None
    max_pages_per_pdf: Optional[int] = None


class GenerateMaterialsRequest(BaseModel):
    course_name: str
    skill_level: str = "beginner"
    duration_days: int = 30


class ConceptExplanationRequest(BaseModel):
    course_name: str
    concept: str


@router.get("/discover")
async def discover_courses(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Discover all available courses from the PDFs folder.
    
    Returns:
        List of discovered courses with metadata
    """
    try:
        courses = course_discovery_service.discover_courses()
        
        return {
            "success": True,
            "total_courses": len(courses),
            "courses": courses
        }
    
    except Exception as e:
        logger.error("Course discovery failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to discover courses: {str(e)}"
        )


@router.post("/process")
async def process_course(
    request: ProcessCourseRequest,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Process PDFs for a specific course and add to RAG knowledge base.
    
    Args:
        request: Processing configuration
        
    Returns:
        Processing statistics
    """
    try:
        logger.info(
            "Processing course request",
            course=request.course_name,
            user_id=current_user.id
        )
        
        result = await course_discovery_service.process_course_pdfs(
            course_name=request.course_name,
            max_pdfs=request.max_pdfs,
            max_pages_per_pdf=request.max_pages_per_pdf
        )
        
        return {
            "success": True,
            "message": f"Course '{request.course_name}' processed successfully",
            **result
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Course processing failed", error=str(e), course=request.course_name)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process course: {str(e)}"
        )


@router.post("/generate-all")
async def generate_all_materials(
    request: GenerateMaterialsRequest,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Generate all learning materials for a course:
    - Syllabus
    - Roadmap
    - Quiz
    - Notes
    - Lecture Flow
    - Assignment
    
    Args:
        request: Generation configuration
        
    Returns:
        All generated materials
    """
    try:
        logger.info(
            "Generating all materials",
            course=request.course_name,
            skill_level=request.skill_level,
            user_id=current_user.id
        )
        
        materials = await course_discovery_service.generate_all_materials(
            course_name=request.course_name,
            skill_level=request.skill_level,
            duration_days=request.duration_days
        )
        
        if "error" in materials:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=materials["error"]
            )
        
        return {
            "success": True,
            "course": request.course_name,
            "skill_level": request.skill_level,
            "materials": materials
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Material generation failed", error=str(e), course=request.course_name)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate materials: {str(e)}"
        )


@router.post("/generate-syllabus")
async def generate_syllabus(
    request: GenerateMaterialsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Generate only the syllabus for a course.
    
    Args:
        request: Generation configuration
        
    Returns:
        Generated syllabus
    """
    try:
        logger.info(
            "Generating syllabus",
            course=request.course_name,
            skill_level=request.skill_level,
            user_id=current_user.id
        )
        
        # Check if course exists in DB and has syllabus
        from app.models.course import Course
        course_db = db.query(Course).filter(Course.title == request.course_name).first()
        
        if course_db and course_db.syllabus_template and len(course_db.syllabus_template) > 0:
            logger.info("✅ Found existing syllabus in database", course=request.course_name)
            return {
                "success": True,
                "course": request.course_name,
                "skill_level": request.skill_level,
                "syllabus": course_db.syllabus_template
            }
        
        # Import here to avoid circular imports if any
        from app.services.content_generation_service import content_generation_service
        
        syllabus = await content_generation_service.generate_syllabus(
            subject=request.course_name,
            skill_level=request.skill_level
        )
        
        # Save to database
        if not course_db:
            logger.info("Creating new course record", course=request.course_name)
            course_db = Course(
                title=request.course_name,
                description=f"Course on {request.course_name}",
                syllabus_template=syllabus
            )
            db.add(course_db)
        else:
            logger.info("Updating existing course record with syllabus", course=request.course_name)
            course_db.syllabus_template = syllabus
            
        db.commit()
        
        return {
            "success": True,
            "course": request.course_name,
            "skill_level": request.skill_level,
            "syllabus": syllabus
        }
    
    except Exception as e:
        logger.error("Syllabus generation failed", error=str(e), course=request.course_name)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate syllabus: {str(e)}"
        )


@router.post("/explain")
async def explain_concept(
    request: ConceptExplanationRequest,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get an explanation for a specific concept in a course.
    
    Args:
        request: Concept explanation request
        
    Returns:
        Explanation text
    """
    try:
        explanation = await course_discovery_service.get_course_explanation(
            course_name=request.course_name,
            concept=request.concept
        )
        
        return {
            "success": True,
            "course": request.course_name,
            "concept": request.concept,
            "explanation": explanation
        }
    
    except Exception as e:
        logger.error("Concept explanation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate explanation: {str(e)}"
        )


@router.post("/process-all")
async def process_all_courses(
    max_pdfs_per_course: Optional[int] = Body(None),
    max_pages_per_pdf: Optional[int] = Body(None),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Process all discovered courses and add to RAG.
    
    This is a bulk operation that may take significant time.
    
    Args:
        max_pdfs_per_course: Limit PDFs per course
        max_pages_per_pdf: Limit pages per PDF
        
    Returns:
        Processing statistics for all courses
    """
    try:
        # Discover all courses
        courses = course_discovery_service.discover_courses()
        
        if not courses:
            return {
                "success": True,
                "message": "No courses found to process",
                "results": []
            }
        
        results = []
        
        for course in courses:
            try:
                logger.info("Processing course", course=course["name"])
                
                result = await course_discovery_service.process_course_pdfs(
                    course_name=course["name"],
                    max_pdfs=max_pdfs_per_course,
                    max_pages_per_pdf=max_pages_per_pdf
                )
                
                results.append({
                    "course": course["name"],
                    "success": True,
                    **result
                })
                
            except Exception as e:
                logger.error("Failed to process course", course=course["name"], error=str(e))
                results.append({
                    "course": course["name"],
                    "success": False,
                    "error": str(e)
                })
        
        total_chunks = sum(r.get("total_chunks", 0) for r in results if r["success"])
        successful_courses = sum(1 for r in results if r["success"])
        
        return {
            "success": True,
            "message": f"Processed {successful_courses}/{len(courses)} courses",
            "total_courses": len(courses),
            "successful_courses": successful_courses,
            "total_chunks_added": total_chunks,
            "results": results
        }
    
    except Exception as e:
        logger.error("Bulk processing failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process courses: {str(e)}"
        )
