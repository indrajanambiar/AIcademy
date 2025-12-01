"""
Service for discovering courses from PDF folders and generating comprehensive learning materials.
"""
from typing import Dict, Any, List, Optional
import os
from pathlib import Path
import PyPDF2
from app.services.rag_service import rag_service
from app.services.content_generation_service import content_generation_service
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class CourseDiscoveryService:
    """Service for discovering and processing courses from PDF folders."""
    
    def __init__(self):
        self.pdfs_base_path = Path(settings.BASE_DIR) / "pdfs"
        logger.info("Course Discovery Service initialized", pdfs_path=str(self.pdfs_base_path))
    
    def discover_courses(self) -> List[Dict[str, Any]]:
        """
        Scan the pdfs folder to discover available courses.
        
        Returns:
            List of discovered courses with metadata
        """
        courses = []
        
        if not self.pdfs_base_path.exists():
            logger.warning("PDFs folder not found", path=str(self.pdfs_base_path))
            return courses
        
        # Scan subdirectories (each represents a course)
        for course_dir in self.pdfs_base_path.iterdir():
            if course_dir.is_dir():
                pdf_files = list(course_dir.glob("*.pdf"))
                
                if pdf_files:
                    course_info = {
                        "name": course_dir.name,
                        "display_name": self._format_course_name(course_dir.name),
                        "path": str(course_dir),
                        "pdf_count": len(pdf_files),
                        "pdf_files": [f.name for f in pdf_files],
                        "total_size_mb": sum(f.stat().st_size for f in pdf_files) / (1024 * 1024)
                    }
                    courses.append(course_info)
                    logger.info("Course discovered", course=course_info["display_name"], pdfs=len(pdf_files))
        
        return sorted(courses, key=lambda x: x["display_name"])
    
    def _format_course_name(self, folder_name: str) -> str:
        """Format folder name to a readable course name."""
        # Replace underscores and capitalize
        formatted = folder_name.replace("_", " ").replace("-", " ")
        # Capitalize each word
        return " ".join(word.capitalize() for word in formatted.split())
    
    def extract_text_from_pdf(self, pdf_path: Path, max_pages: Optional[int] = None) -> str:
        """
        Extract text from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            max_pages: Maximum number of pages to extract (None for all)
            
        Returns:
            Extracted text content
        """
        text_parts = []
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                pages_to_read = min(max_pages, total_pages) if max_pages else total_pages
                
                logger.info(
                    "Extracting PDF text",
                    file=pdf_path.name,
                    total_pages=total_pages,
                    reading_pages=pages_to_read
                )
                
                for page_num in range(pages_to_read):
                    try:
                        page = pdf_reader.pages[page_num]
                        text = page.extract_text()
                        if text.strip():
                            text_parts.append(text)
                    except Exception as e:
                        logger.warning(f"Failed to extract page {page_num}", error=str(e))
                        continue
                
            return "\n\n".join(text_parts)
        
        except Exception as e:
            logger.error("PDF extraction failed", file=str(pdf_path), error=str(e))
            return ""
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        Split text into overlapping chunks for better RAG retrieval.
        
        Args:
            text: Text to chunk
            chunk_size: Size of each chunk
            overlap: Overlap between chunks
            
        Returns:
            List of text chunks
        """
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
                
                if break_point > chunk_size // 2:
                    chunk = text[start:start + break_point + 1]
                    end = start + break_point + 1
            
            chunks.append(chunk.strip())
            start = end - overlap
        
        return [c for c in chunks if c]
    
    async def process_course_pdfs(
        self,
        course_name: str,
        max_pdfs: Optional[int] = None,
        max_pages_per_pdf: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Process all PDFs for a course and add to RAG.
        
        Args:
            course_name: Name of the course folder
            max_pdfs: Maximum number of PDFs to process (None for all)
            max_pages_per_pdf: Maximum pages per PDF (None for all)
            
        Returns:
            Processing statistics
        """
        course_path = self.pdfs_base_path / course_name
        
        if not course_path.exists():
            raise ValueError(f"Course folder not found: {course_name}")
        
        pdf_files = list(course_path.glob("*.pdf"))
        if max_pdfs:
            pdf_files = pdf_files[:max_pdfs]
        
        total_chunks = 0
        processed_files = 0
        failed_files = []
        
        logger.info(
            "Processing course PDFs",
            course=course_name,
            total_pdfs=len(pdf_files)
        )
        
        for pdf_file in pdf_files:
            try:
                # Extract text
                text = self.extract_text_from_pdf(pdf_file, max_pages_per_pdf)
                
                if not text.strip():
                    logger.warning("No text extracted", file=pdf_file.name)
                    failed_files.append(pdf_file.name)
                    continue
                
                # Chunk the text
                chunks = self.chunk_text(text)
                
                # Prepare metadata
                metadatas = [
                    {
                        "course": course_name,
                        "source": pdf_file.name,
                        "chunk_index": i,
                        "type": "course_material"
                    }
                    for i in range(len(chunks))
                ]
                
                # Add to RAG
                rag_service.add_documents(
                    texts=chunks,
                    metadatas=metadatas
                )
                
                total_chunks += len(chunks)
                processed_files += 1
                
                logger.info(
                    "PDF processed",
                    file=pdf_file.name,
                    chunks=len(chunks)
                )
                
            except Exception as e:
                logger.error("Failed to process PDF", file=pdf_file.name, error=str(e))
                failed_files.append(pdf_file.name)
        
        return {
            "course": course_name,
            "processed_files": processed_files,
            "total_files": len(pdf_files),
            "total_chunks": total_chunks,
            "failed_files": failed_files
        }
    
    async def generate_all_materials(
        self,
        course_name: str,
        skill_level: str = "beginner",
        duration_days: int = 30
    ) -> Dict[str, Any]:
        """
        Generate all learning materials for a course.
        
        Args:
            course_name: Name of the course
            skill_level: Skill level (beginner, intermediate, advanced)
            duration_days: Duration for roadmap
            
        Returns:
            Dictionary containing all generated materials
        """
        logger.info(
            "Generating all materials",
            course=course_name,
            skill_level=skill_level
        )
        
        materials = {}
        
        try:
            # Generate Syllabus
            logger.info("Generating syllabus", course=course_name)
            materials["syllabus"] = await content_generation_service.generate_syllabus(
                subject=course_name,
                skill_level=skill_level
            )
            
            # Generate Roadmap
            logger.info("Generating roadmap", course=course_name)
            materials["roadmap"] = await content_generation_service.generate_roadmap(
                subject=course_name,
                duration_days=duration_days,
                skill_level=skill_level
            )
            
            # Generate sample quiz (general course quiz)
            logger.info("Generating quiz", course=course_name)
            materials["quiz"] = await content_generation_service.generate_quiz(
                subject=course_name,
                topic=f"{course_name} fundamentals",
                num_questions=10,
                skill_level=skill_level
            )
            
            # Generate notes for the course overview
            logger.info("Generating notes", course=course_name)
            materials["notes"] = await content_generation_service.generate_notes(
                subject=course_name,
                topic="Course Overview and Key Concepts",
                detail_level="comprehensive"
            )
            
            # Generate lecture flow
            logger.info("Generating lecture flow", course=course_name)
            materials["lecture_flow"] = await content_generation_service.generate_lecture_flow(
                subject=course_name,
                topic="Introduction and Fundamentals",
                duration_minutes=60
            )
            
            # Generate assignment
            logger.info("Generating assignment", course=course_name)
            materials["assignment"] = await content_generation_service.generate_assignment(
                subject=course_name,
                topic="Practical Application",
                difficulty=skill_level
            )
            
            logger.info("All materials generated successfully", course=course_name)
            
        except Exception as e:
            logger.error("Failed to generate materials", course=course_name, error=str(e))
            materials["error"] = str(e)
        
        return materials
    
    async def get_course_explanation(
        self,
        course_name: str,
        concept: str
    ) -> str:
        """
        Get an explanation for a specific concept in a course.
        
        Args:
            course_name: Name of the course
            concept: Concept to explain
            
        Returns:
            Explanation text
        """
        return await content_generation_service.generate_explanation(
            subject=course_name,
            concept=concept
        )


# Global instance
course_discovery_service = CourseDiscoveryService()
