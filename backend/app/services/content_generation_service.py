"""
Service for generating educational content using LLM and RAG.
"""
from typing import Dict, Any, List, Optional
import json
import re

from app.services.llm_service import llm_service
from app.services.rag_service import rag_service
from app.core.logging import get_logger

logger = get_logger(__name__)


class ContentGenerationService:
    """Service for generating educational content."""
    
    async def identify_subject(self, text: str) -> str:
        """
        Identify the main subject from text or document content.
        """
        prompt = f"""
        Analyze the following text and identify the main educational subject or topic (e.g., Python Programming, Machine Learning, Data Structures, History of Rome).
        
        Text sample:
        {text[:1000]}...
        
        Return ONLY the subject name, nothing else.
        """
        
        response = await llm_service.generate(prompt, raw_prompt=True)
        return response.strip()
    
    def __init__(self):
        self._syllabus_cache = {}

    async def generate_syllabus(
        self, 
        subject: str, 
        skill_level: str = "beginner",
        target_audience: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a course syllabus."""
        
        cache_key = f"{subject}_{skill_level}_{target_audience}"
        if cache_key in self._syllabus_cache:
            logger.info("⚡ Using cached syllabus", subject=subject, skill_level=skill_level)
            return self._syllabus_cache[cache_key]
        
        logger.info(
            "🎯 Starting syllabus generation",
            subject=subject,
            skill_level=skill_level,
            material_type="syllabus"
        )
        
        # Try to get context from RAG
        # Improved query to target Table of Contents and course structure
        query = f"{subject} table of contents course structure chapters modules overview"
        # Increase top_k to capture content from multiple PDFs if available
        logger.info("🔍 Querying RAG for context", query=query, top_k=10)
        
        context_docs = rag_service.retrieve(query, top_k=10)
        
        # If no context found, try to process the course PDFs automatically
        if not context_docs:
            logger.info("⚠️ No context found. Attempting to process course PDFs...", course=subject)
            try:
                # Import here to avoid circular imports
                from app.services.course_discovery_service import course_discovery_service
                await course_discovery_service.process_course_pdfs(course_name=subject)
                
                # Retry retrieval
                logger.info("🔄 Retrying RAG retrieval after processing...")
                context_docs = rag_service.retrieve(query, top_k=10)
            except Exception as e:
                logger.warning("Failed to auto-process PDFs", error=str(e))
        
        if context_docs:
            # Group docs by source to see which PDFs we are using
            sources = {}
            for doc in context_docs:
                src = doc["metadata"].get("source", "unknown")
                if src not in sources:
                    sources[src] = []
                sources[src].append(doc["text"])
            
            # Construct context emphasizing multiple sources
            context_parts = []
            for src, texts in sources.items():
                context_parts.append(f"--- Source: {src} ---\n" + "\n".join(texts))
            
            context = "\n\n".join(context_parts)
            
            logger.info(
                "✅ RAG CONTEXT FOUND - Using PDF knowledge",
                chunks_retrieved=len(context_docs),
                total_context_length=len(context),
                sources=list(sources.keys()),
                mode="RAG + LLM"
            )
        else:
            context = None
            logger.warning(
                "⚠️ NO RAG CONTEXT - Using LLM knowledge only",
                subject=subject,
                mode="LLM_ONLY",
                reason="No matching documents in vector store"
            )
        
        prompt = f"""
        Generate a comprehensive **3-month duration** course syllabus for {subject}. 
        The course should progress from **Beginner to Intermediate** level.
        {f"Target Audience: {target_audience}" if target_audience else ""}
        
        IMPORTANT: 
        1. **STRICTLY BASED ON PROVIDED CONTEXT:** Generate the syllabus **ONLY** using the information present in the provided source documents.
        2. **Comprehensive Coverage:** Cover **ALL important topics** found in the documents. Do not summarize too briefly.
        3. **Structure:** Organize the content into **8-12 detailed modules** to reflect a 3-month learning journey.
        4. **Mandatory Final Modules:**
           - You MUST include a module at the end titled **"Course Assessment"** which lists key questions, exam topics, or quiz concepts derived from the text.
           - You MUST include a module at the end titled **"Practical Projects"** which lists hands-on project ideas or assignments based on the course content.
        
        The syllabus should be structured into modules, and each module should have a list of topics.
        
        Format the output as a valid JSON object with the following structure:
        {{
            "title": "Course Title",
            "description": "Course description",
            "modules": [
                {{
                    "title": "Module 1 Title",
                    "description": "Module description",
                    "topics": ["Topic 1", "Topic 2", "Topic 3"]
                }},
                ...
                {{
                    "title": "Course Assessment",
                    "description": "Key questions and evaluation topics",
                    "topics": ["Question 1?", "Question 2?", "Exam Topic 1"]
                }},
                {{
                    "title": "Practical Projects",
                    "description": "Hands-on application projects",
                    "topics": ["Project Idea 1", "Project Idea 2"]
                }}
            ]
        }}
        
        Ensure the JSON is valid and strictly follows this structure. Do not include markdown formatting like ```json.
        """
        
        logger.info("🤖 Generating with LLM", has_context=bool(context))
        response = await llm_service.generate(prompt, context=context)
        
        logger.info(
            "✅ Syllabus generation complete",
            subject=subject,
            response_length=len(response),
            used_rag=bool(context)
        )
        
        result = self._parse_json_response(response)
        
        # Fallback if parsing fails or returns empty
        if not result or "error" in result:
            logger.warning("⚠️ JSON parsing failed, using fallback structure", subject=subject)
            result = {
                "title": f"{subject} Course",
                "description": f"A comprehensive guide to {subject} for {skill_level}s.",
                "modules": [
                    {
                        "title": "Introduction",
                        "description": "Getting started with the basics.",
                        "topics": ["Overview", "Key Concepts", "Setup"]
                    },
                    {
                        "title": "Core Fundamentals",
                        "description": "Deep dive into core topics.",
                        "topics": ["Topic 1", "Topic 2", "Topic 3"]
                    }
                ]
            }
            
        self._syllabus_cache[cache_key] = result
        return result

    async def generate_roadmap(
        self,
        subject: str,
        duration_days: int = 30,
        skill_level: str = "beginner"
    ) -> Dict[str, Any]:
        """Generate a learning roadmap."""
        
        logger.info(
            "🎯 Starting roadmap generation",
            subject=subject,
            duration_days=duration_days,
            skill_level=skill_level,
            material_type="roadmap"
        )
        
        query = f"{subject} table of contents chapters sequence prerequisites learning path"
        logger.info("🔍 Querying RAG for context", query=query, top_k=3)
        
        context_docs = rag_service.retrieve(query, top_k=3)
        
        if context_docs:
            context = "\n\n".join([doc["text"] for doc in context_docs])
            logger.info(
                "✅ RAG CONTEXT FOUND - Using PDF knowledge",
                chunks_retrieved=len(context_docs),
                sources=[doc["metadata"].get("source", "unknown") for doc in context_docs],
                mode="RAG + LLM"
            )
        else:
            context = None
            logger.warning("⚠️ NO RAG CONTEXT - Using LLM knowledge only", mode="LLM_ONLY")
        
        prompt = f"""
        Generate a {duration_days}-day learning roadmap for {subject} for a {skill_level} learner.
        
        Format the output as a valid JSON object with the following structure:
        {{
            "title": "Learning Roadmap",
            "days": [
                {{
                    "day": 1,
                    "topic": "Topic for the day",
                    "activities": ["Read chapter 1", "Practice exercises"],
                    "estimated_hours": 2
                }}
            ]
        }}
        
        Ensure the JSON is valid. Do not include markdown formatting.
        """
        
        logger.info("🤖 Generating with LLM", has_context=bool(context))
        response = await llm_service.generate(prompt, context=context)
        logger.info("✅ Roadmap generation complete", used_rag=bool(context))
        
        return self._parse_json_response(response)

    async def generate_quiz(
        self,
        subject: str,
        topic: str,
        num_questions: int = 5,
        skill_level: str = "beginner"
    ) -> Dict[str, Any]:
        """Generate a quiz."""
        
        logger.info(
            "🎯 Starting quiz generation",
            subject=subject,
            topic=topic,
            num_questions=num_questions,
            material_type="quiz"
        )
        
        query = f"{subject} {topic} questions quiz"
        logger.info("🔍 Querying RAG for context", query=query, top_k=3)
        
        context_docs = rag_service.retrieve(query, top_k=3)
        
        if context_docs:
            context = "\n\n".join([doc["text"] for doc in context_docs])
            logger.info(
                "✅ RAG CONTEXT FOUND - Using PDF knowledge",
                chunks_retrieved=len(context_docs),
                sources=[doc["metadata"].get("source", "unknown") for doc in context_docs],
                mode="RAG + LLM"
            )
        else:
            context = None
            logger.warning("⚠️ NO RAG CONTEXT - Using LLM knowledge only", mode="LLM_ONLY")
        
        prompt = f"""
        Generate a quiz with {num_questions} multiple-choice questions on "{topic}" in {subject} for a {skill_level} level.
        
        Format the output as a valid JSON object with the following structure:
        {{
            "title": "Quiz Title",
            "questions": [
                {{
                    "id": 1,
                    "question": "Question text",
                    "options": {{
                        "A": "Option A",
                        "B": "Option B",
                        "C": "Option C",
                        "D": "Option D"
                    }},
                    "correct_answer": "A",
                    "explanation": "Explanation for why A is correct"
                }}
            ]
        }}
        
        Ensure the JSON is valid. Do not include markdown formatting.
        """
        
        logger.info("🤖 Generating with LLM", has_context=bool(context))
        response = await llm_service.generate(prompt, context=context)
        logger.info("✅ Quiz generation complete", used_rag=bool(context))
        
        return self._parse_json_response(response)

    async def generate_notes(
        self,
        subject: str,
        topic: str,
        detail_level: str = "comprehensive"
    ) -> str:
        """Generate study notes."""
        
        logger.info(
            "🎯 Starting notes generation",
            subject=subject,
            topic=topic,
            detail_level=detail_level,
            material_type="notes"
        )
        
        query = f"{subject} {topic} explanation concepts"
        logger.info("🔍 Querying RAG for context", query=query, top_k=5)
        
        context_docs = rag_service.retrieve(query, top_k=5)
        
        if context_docs:
            context = "\n\n".join([doc["text"] for doc in context_docs])
            logger.info(
                "✅ RAG CONTEXT FOUND - Using PDF knowledge",
                chunks_retrieved=len(context_docs),
                sources=[doc["metadata"].get("source", "unknown") for doc in context_docs],
                mode="RAG + LLM"
            )
        else:
            context = None
            logger.warning("⚠️ NO RAG CONTEXT - Using LLM knowledge only", mode="LLM_ONLY")
        
        prompt = f"""
        Generate {detail_level} study notes for the topic "{topic}" in {subject}.
        
        Include:
        1. Key Concepts
        2. Detailed Explanations
        3. Examples (code or real-world)
        4. Summary/Key Takeaways
        
        Format using Markdown.
        """
        
        logger.info("🤖 Generating with LLM", has_context=bool(context))
        response = await llm_service.generate(prompt, context=context)
        logger.info("✅ Notes generation complete", used_rag=bool(context))
        
        return response

    async def generate_lecture_flow(
        self,
        subject: str,
        topic: str,
        duration_minutes: int = 60
    ) -> str:
        """Generate a lecture flow/script."""
        
        logger.info(
            "🎯 Starting lecture flow generation",
            subject=subject,
            topic=topic,
            duration_minutes=duration_minutes,
            material_type="lecture_flow"
        )
        
        query = f"{subject} {topic} teaching guide"
        logger.info("🔍 Querying RAG for context", query=query, top_k=3)
        
        context_docs = rag_service.retrieve(query, top_k=3)
        
        if context_docs:
            context = "\n\n".join([doc["text"] for doc in context_docs])
            logger.info(
                "✅ RAG CONTEXT FOUND - Using PDF knowledge",
                chunks_retrieved=len(context_docs),
                sources=[doc["metadata"].get("source", "unknown") for doc in context_docs],
                mode="RAG + LLM"
            )
        else:
            context = None
            logger.warning("⚠️ NO RAG CONTEXT - Using LLM knowledge only", mode="LLM_ONLY")
        
        prompt = f"""
        Create a lecture flow for a {duration_minutes}-minute session on "{topic}" in {subject}.
        
        Structure:
        1. Introduction & Hook (5-10%)
        2. Core Concepts (Teaching phase)
        3. Examples/Demonstrations
        4. Interactive Activity/Practice
        5. Conclusion & Q&A
        
        Provide time allocations for each section.
        Format using Markdown.
        """
        
        logger.info("🤖 Generating with LLM", has_context=bool(context))
        response = await llm_service.generate(prompt, context=context)
        logger.info("✅ Lecture flow generation complete", used_rag=bool(context))
        
        return response

    async def generate_assignment(
        self,
        subject: str,
        topic: str,
        difficulty: str = "intermediate"
    ) -> Dict[str, Any]:
        """Generate a practical assignment."""
        
        logger.info(
            "🎯 Starting assignment generation",
            subject=subject,
            topic=topic,
            difficulty=difficulty,
            material_type="assignment"
        )
        
        query = f"{subject} {topic} exercises project"
        logger.info("🔍 Querying RAG for context", query=query, top_k=3)
        
        context_docs = rag_service.retrieve(query, top_k=3)
        
        if context_docs:
            context = "\n\n".join([doc["text"] for doc in context_docs])
            logger.info(
                "✅ RAG CONTEXT FOUND - Using PDF knowledge",
                chunks_retrieved=len(context_docs),
                sources=[doc["metadata"].get("source", "unknown") for doc in context_docs],
                mode="RAG + LLM"
            )
        else:
            context = None
            logger.warning("⚠️ NO RAG CONTEXT - Using LLM knowledge only", mode="LLM_ONLY")
        
        prompt = f"""
        Create a practical assignment for "{topic}" in {subject} at {difficulty} level.
        
        Format the output as a valid JSON object with the following structure:
        {{
            "title": "Assignment Title",
            "description": "Overview of the task",
            "instructions": ["Step 1", "Step 2"],
            "requirements": ["Requirement 1", "Requirement 2"],
            "evaluation_criteria": ["Criterion 1", "Criterion 2"],
            "estimated_time": "2 hours"
        }}
        
        Ensure the JSON is valid. Do not include markdown formatting.
        """
        
        logger.info("🤖 Generating with LLM", has_context=bool(context))
        response = await llm_service.generate(prompt, context=context)
        logger.info("✅ Assignment generation complete", used_rag=bool(context))
        
        return self._parse_json_response(response)

    async def generate_explanation(
        self,
        subject: str,
        concept: str,
        context_str: Optional[str] = None
    ) -> str:
        """Generate a clear explanation for a concept."""
        
        logger.info(
            "🎯 Starting explanation generation",
            subject=subject,
            concept=concept,
            material_type="explanation"
        )
        
        rag_context = None
        if not context_str:
            query = f"{subject} {concept} definition explanation"
            logger.info("🔍 Querying RAG for context", query=query, top_k=3)
            
            context_docs = rag_service.retrieve(query, top_k=3)
            
            if context_docs:
                rag_context = "\n\n".join([doc["text"] for doc in context_docs])
                logger.info(
                    "✅ RAG CONTEXT FOUND - Using PDF knowledge",
                    chunks_retrieved=len(context_docs),
                    sources=[doc["metadata"].get("source", "unknown") for doc in context_docs],
                    mode="RAG + LLM"
                )
            else:
                logger.warning("⚠️ NO RAG CONTEXT - Using LLM knowledge only", mode="LLM_ONLY")
        else:
            logger.info("📝 Using provided context", mode="CUSTOM_CONTEXT")
        
        final_context = context_str if context_str else rag_context
        
        prompt = f"""
        Explain the concept "{concept}" in the context of {subject} clearly and simply.
        Use analogies if helpful. Provide a concrete example.
        """
        
        logger.info("🤖 Generating with LLM", has_context=bool(final_context))
        response = await llm_service.generate(prompt, context=final_context)
        logger.info("✅ Explanation generation complete", used_rag=bool(final_context))
        
        return response

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from LLM response, handling potential markdown formatting and extra text."""
        try:
            # Find the first '{' and last '}'
            start_idx = response.find('{')
            end_idx = response.rfind('}')
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx+1]
                return json.loads(json_str)
            
            # Fallback: try removing markdown if no braces found (unlikely for JSON)
            clean_response = re.sub(r'```json\s*|\s*```', '', response).strip()
            return json.loads(clean_response)
            
        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON response", error=str(e), response=response)
            # Return a basic error structure or raise
            return {"error": "Failed to generate structured content", "raw_response": response}

# Global instance
content_generation_service = ContentGenerationService()
