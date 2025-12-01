"""
Admin API endpoints for system management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.course import Course, UserCourse
from app.models.conversation import Conversation
from app.models.knowledge import MissingKnowledge, KnowledgeStatus
from app.schemas.schemas import MissingKnowledgeResponse, SystemStats
from app.services.rag_service import rag_service
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


async def require_admin(current_user: User = Depends(get_current_user)):
    """Dependency to require admin privileges."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


@router.get("/stats", response_model=SystemStats)
async def get_system_stats(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get system-wide statistics."""
    total_users = db.query(User).count()
    total_courses = db.query(Course).count()
    total_conversations = db.query(Conversation).count()
    pending_knowledge = db.query(MissingKnowledge).filter(
        MissingKnowledge.status == KnowledgeStatus.PENDING
    ).count()
    
    rag_stats = rag_service.get_collection_stats()
    
    return SystemStats(
        total_users=total_users,
        total_courses=total_courses,
        total_conversations=total_conversations,
        pending_knowledge_gaps=pending_knowledge,
        rag_document_count=rag_stats["document_count"],
    )


@router.get("/knowledge/missing", response_model=List[MissingKnowledgeResponse])
async def get_missing_knowledge(
    status_filter: str = None,
    skip: int = 0,
    limit: int = 100,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get list of missing knowledge entries."""
    query = db.query(MissingKnowledge)
    
    if status_filter:
        try:
            status_enum = KnowledgeStatus(status_filter)
            query = query.filter(MissingKnowledge.status == status_enum)
        except ValueError:
            pass
    
    items = query.order_by(
        MissingKnowledge.occurrence_count.desc(),
        MissingKnowledge.logged_at.desc()
    ).offset(skip).limit(limit).all()
    
    return items


@router.post("/knowledge/missing/{item_id}/resolve")
async def resolve_missing_knowledge(
    item_id: str,
    resolution: str,
    admin_notes: str = None,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Mark a missing knowledge item as resolved."""
    item = db.query(MissingKnowledge).filter(MissingKnowledge.id == item_id).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Missing knowledge item not found",
        )
    
    from datetime import datetime
    item.status = KnowledgeStatus.FILLED
    item.resolution = resolution
    item.admin_notes = admin_notes
    item.resolved_at = datetime.utcnow()
    
    db.commit()
    
    logger.info("Missing knowledge resolved", item_id=item_id, admin_id=admin.id)
    
    return {"message": "Missing knowledge item resolved successfully"}


@router.delete("/knowledge/missing/{item_id}")
async def delete_missing_knowledge(
    item_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Delete a missing knowledge item."""
    item = db.query(MissingKnowledge).filter(MissingKnowledge.id == item_id).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Missing knowledge item not found",
        )
    
    db.delete(item)
    db.commit()
    
    return {"message": "Missing knowledge item deleted successfully"}


@router.get("/users")
async def list_users(
    skip: int = 0,
    limit: int = 100,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List all users (admin only)."""
    users = db.query(User).offset(skip).limit(limit).all()
    
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "is_active": u.is_active,
            "is_admin": u.is_admin,
            "created_at": u.created_at,
            "last_login": u.last_login,
        }
        for u in users
    ]
