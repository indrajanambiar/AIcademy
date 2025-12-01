"""
API endpoints for content generation (Syllabus, Roadmap, Quizzes, etc.).
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import Dict, Any

from app.api.auth import get_current_user
from app.models.user import User
from app.services.content_generation_service import content_generation_service
from app.schemas.schemas import (
    SyllabusRequest,
    RoadmapRequest,
    QuizRequest,
    NotesRequest,
    LectureFlowRequest,
    AssignmentRequest,
    ExplanationRequest,
    GenerationResponse
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/identify-subject", response_model=GenerationResponse)
async def identify_subject(
    text: str = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
):
    """Identify the subject from a text sample."""
    subject = await content_generation_service.identify_subject(text)
    return GenerationResponse(content=subject)


@router.post("/syllabus", response_model=GenerationResponse)
async def generate_syllabus(
    request: SyllabusRequest,
    current_user: User = Depends(get_current_user),
):
    """Generate a course syllabus."""
    syllabus = await content_generation_service.generate_syllabus(
        subject=request.subject,
        skill_level=request.skill_level,
        target_audience=request.target_audience
    )
    return GenerationResponse(content=syllabus)


@router.post("/roadmap", response_model=GenerationResponse)
async def generate_roadmap(
    request: RoadmapRequest,
    current_user: User = Depends(get_current_user),
):
    """Generate a learning roadmap."""
    roadmap = await content_generation_service.generate_roadmap(
        subject=request.topic,  # RoadmapRequest uses 'topic' but service expects 'subject'
        duration_days=request.duration_days,
        skill_level=request.skill_level
    )
    return GenerationResponse(content=roadmap)


@router.post("/quiz", response_model=GenerationResponse)
async def generate_quiz(
    request: QuizRequest,
    current_user: User = Depends(get_current_user),
):
    """Generate a quiz."""
    quiz = await content_generation_service.generate_quiz(
        subject=request.topic, # QuizRequest uses 'topic' as the main subject/topic context
        topic=request.topic,   # In this simple mapping, we might need to clarify subject vs topic
        num_questions=request.num_questions,
        skill_level=request.skill_level
    )
    return GenerationResponse(content=quiz)


@router.post("/notes", response_model=GenerationResponse)
async def generate_notes(
    request: NotesRequest,
    current_user: User = Depends(get_current_user),
):
    """Generate study notes."""
    notes = await content_generation_service.generate_notes(
        subject=request.subject,
        topic=request.topic,
        detail_level=request.detail_level
    )
    return GenerationResponse(content=notes)


@router.post("/lecture-flow", response_model=GenerationResponse)
async def generate_lecture_flow(
    request: LectureFlowRequest,
    current_user: User = Depends(get_current_user),
):
    """Generate a lecture flow."""
    flow = await content_generation_service.generate_lecture_flow(
        subject=request.subject,
        topic=request.topic,
        duration_minutes=request.duration_minutes
    )
    return GenerationResponse(content=flow)


@router.post("/assignment", response_model=GenerationResponse)
async def generate_assignment(
    request: AssignmentRequest,
    current_user: User = Depends(get_current_user),
):
    """Generate an assignment."""
    assignment = await content_generation_service.generate_assignment(
        subject=request.subject,
        topic=request.topic,
        difficulty=request.difficulty
    )
    return GenerationResponse(content=assignment)


@router.post("/explanation", response_model=GenerationResponse)
async def generate_explanation(
    request: ExplanationRequest,
    current_user: User = Depends(get_current_user),
):
    """Generate an explanation."""
    explanation = await content_generation_service.generate_explanation(
        subject=request.subject,
        concept=request.concept,
        context_str=request.context
    )
    return GenerationResponse(content=explanation)
