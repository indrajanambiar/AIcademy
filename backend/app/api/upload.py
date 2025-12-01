"""
File upload API for adding knowledge to RAG.
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
import os
from pathlib import Path
import PyPDF2
import docx
from typing import List

from app.core.database import get_db
from app.core.config import settings
from app.api.auth import get_current_user
from app.models.user import User
from app.services.rag_service import rag_service
from app.schemas.schemas import UploadResponse
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file."""
    text = []
    with open(file_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            text.append(page.extract_text())
    return "\n".join(text)


def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX file."""
    doc = docx.Document(file_path)
    text = []
    for paragraph in doc.paragraphs:
        text.append(paragraph.text)
    return "\n".join(text)


def extract_text_from_txt(file_path: str) -> str:
    """Extract text from TXT file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        
        # Try to find a good breaking point (period, newline)
        if end < text_length:
            last_period = chunk.rfind('.')
            last_newline = chunk.rfind('\n')
            break_point = max(last_period, last_newline)
            
            if break_point > chunk_size // 2:  # Only break if it's not too early
                chunk = text[start:start + break_point + 1]
                end = start + break_point + 1
        
        chunks.append(chunk.strip())
        start = end - overlap
    
    return [c for c in chunks if c]  # Filter empty chunks


@router.post("/document", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload a document to add to the knowledge base.
    Supports: PDF, DOCX, TXT, MD
    """
    logger.info(
        "Document upload started",
        filename=file.filename,
        user_id=current_user.id,
    )
    
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file_ext} not allowed. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}",
        )
    
    # Create upload directory if it doesn't exist
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Save file
    file_path = upload_dir / f"{current_user.id}_{file.filename}"
    
    try:
        # Read and save file
        contents = await file.read()
        
        # Check file size
        if len(contents) > settings.max_file_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds maximum of {settings.MAX_FILE_SIZE_MB}MB",
            )
        
        with open(file_path, 'wb') as f:
            f.write(contents)
        
        # Extract text based on file type
        if file_ext == '.pdf':
            text = extract_text_from_pdf(str(file_path))
        elif file_ext == '.docx':
            text = extract_text_from_docx(str(file_path))
        elif file_ext in ['.txt', '.md']:
            text = extract_text_from_txt(str(file_path))
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported file type",
            )
        
        # Chunk the text
        chunks = chunk_text(text)
        
        # Add to RAG
        metadatas = [
            {
                "source": file.filename,
                "user_id": current_user.id,
                "chunk_index": i,
            }
            for i in range(len(chunks))
        ]
        
        rag_service.add_documents(
            texts=chunks,
            metadatas=metadatas,
        )
        
        logger.info(
            "Document uploaded and processed",
            filename=file.filename,
            chunks_count=len(chunks),
            user_id=current_user.id,
        )
        
        return UploadResponse(
            filename=file.filename,
            size=len(contents),
            chunks_added=len(chunks),
            message="Document uploaded and added to knowledge base successfully",
        )
        
    except Exception as e:
        logger.error("Document upload failed", error=str(e), filename=file.filename)
        
        # Clean up file if it was saved
        if file_path.exists():
            file_path.unlink()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}",
        )


@router.get("/stats")
async def get_upload_stats(
    current_user: User = Depends(get_current_user),
):
    """Get statistics about the knowledge base."""
    stats = rag_service.get_collection_stats()
    return stats
