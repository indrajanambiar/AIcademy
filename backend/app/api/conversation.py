"""
Conversation API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.conversation import Conversation
from app.models.course import UserCourse
from app.schemas.schemas import ChatMessage, ChatResponse, ConversationHistory
from app.agents.orchestrator import orchestrator
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    message: ChatMessage,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Send a message and get a response from the AI coach.
    """
    logger.info(
        "Chat request received",
        user_id=current_user.id,
        message_length=len(message.message),
    )
    
    # Build user profile context
    user_profile = {
        "username": current_user.username,
        "preferences": current_user.preferences or {},
    }
    
    # Get current course if any
    active_course = db.query(UserCourse).filter(
        UserCourse.user_id == current_user.id,
        UserCourse.status == "in_progress"
    ).first()
    
    # Build context
    context = message.context or {}
    
    # Retrieve last active topic if not in context
    if "current_topic" not in context:
        last_topic_conv = db.query(Conversation).filter(
            Conversation.user_id == current_user.id,
            Conversation.topic.isnot(None)
        ).order_by(Conversation.timestamp.desc()).first()
        
        if last_topic_conv:
            context["current_topic"] = last_topic_conv.topic
            
            # Retrieve onboarding step
            if last_topic_conv.meta_data:
                meta = last_topic_conv.meta_data
                # Handle stringified JSON if necessary
                if isinstance(meta, str):
                    import json
                    try:
                        meta = json.loads(meta)
                    except:
                        meta = {}
                
                if isinstance(meta, dict):
                    context["onboarding_step"] = meta.get("onboarding_step")
                    context["skill_level"] = meta.get("skill_level")
                    context["target_skill_level"] = meta.get("target_skill_level")
                    context["quiz_questions"] = meta.get("quiz_questions")

    if active_course:
        context["course_id"] = active_course.course_id
        context["skill_level"] = active_course.skill_level
        # Add more context from active course
    
    # Process message through orchestrator
    response = await orchestrator.process_message(
        message=message.message,
        user_id=current_user.id,
        user_profile=user_profile,
        context=context,
        db=db,
    )
    
    # Save conversation to database
    conversation = Conversation(
        user_id=current_user.id,
        message=message.message,
        bot_reply=response["reply"],
        intent=response["intent"],
        confidence=response.get("confidence"),
        used_rag=response.get("used_rag", False),
        course_id=context.get("course_id"),
        topic=response.get("topic"),
        meta_data=response.get("metadata", {}),
    )
    
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    
    logger.info(
        "Chat response sent",
        user_id=current_user.id,
        conversation_id=conversation.id,
        intent=response["intent"],
    )
    
    # Return response
    return ChatResponse(
        reply=response["reply"],
        intent=response["intent"],
        confidence=response.get("confidence", 0),
        used_rag=response.get("used_rag", False),
        metadata=response.get("metadata", {}),
        conversation_id=conversation.id,
    )


@router.get("/history", response_model=List[ConversationHistory])
async def get_conversation_history(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get conversation history for the current user."""
    conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(
        Conversation.timestamp.desc()
    ).limit(limit).offset(offset).all()
    
    return conversations


@router.delete("/history/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a specific conversation."""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id,
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    
    db.delete(conversation)
    db.commit()
    
    return {"message": "Conversation deleted successfully"}


@router.post("/feedback/{conversation_id}")
async def provide_feedback(
    conversation_id: str,
    rating: int,
    feedback: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Provide feedback on a conversation."""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id,
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    
    if rating < 1 or rating > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating must be between 1 and 5",
        )
    
    conversation.user_rating = float(rating)
    conversation.user_feedback = feedback
    
    db.commit()
    
    logger.info(
        "Feedback received",
        conversation_id=conversation_id,
        rating=rating,
    )
    
    return {"message": "Feedback saved successfully"}
