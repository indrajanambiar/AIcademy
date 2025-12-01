from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from app.services.adaptive_assessment_service import adaptive_assessment_service
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

# Request Models
class DiagnosticQuizRequest(BaseModel):
    subject: str
    topic: Optional[str] = None

class EvaluateQuizRequest(BaseModel):
    subject: str
    quiz_questions: List[Dict[str, Any]]
    user_answers: List[str]

class GeneratePlanRequest(BaseModel):
    subject: str
    skill_level: str
    evaluation_results: Dict[str, Any]
    duration_days: int = 30

# Endpoints
@router.post("/diagnostic-quiz")
async def generate_diagnostic_quiz(request: DiagnosticQuizRequest):
    """Generate a diagnostic quiz to assess skill level."""
    try:
        quiz = await adaptive_assessment_service.generate_diagnostic_quiz(
            subject=request.subject,
            topic=request.topic
        )
        return quiz
    except Exception as e:
        logger.error("Failed to generate diagnostic quiz", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/evaluate")
async def evaluate_quiz(request: EvaluateQuizRequest):
    """Evaluate quiz answers and determine skill level."""
    try:
        evaluation = adaptive_assessment_service.evaluate_skill_level(
            quiz_questions=request.quiz_questions,
            user_answers=request.user_answers
        )
        return evaluation
    except Exception as e:
        logger.error("Failed to evaluate quiz", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/personalized-plan")
async def generate_personalized_plan(request: GeneratePlanRequest):
    """Generate a personalized study plan based on evaluation."""
    try:
        plan = await adaptive_assessment_service.generate_personalized_study_plan(
            subject=request.subject,
            skill_level=request.skill_level,
            evaluation_results=request.evaluation_results,
            duration_days=request.duration_days
        )
        return plan
    except Exception as e:
        logger.error("Failed to generate personalized plan", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
