"""
Adaptive Assessment Service - Evaluates user skill level through diagnostic quizzes.
"""
from typing import Dict, Any, List, Optional
from app.services.llm_service import llm_service
from app.services.rag_service import rag_service
from app.core.logging import get_logger
import json
import re

logger = get_logger(__name__)


class AdaptiveAssessmentService:
    """Service for adaptive skill assessment and personalized recommendations."""
    
    async def generate_diagnostic_quiz(
        self,
        subject: str,
        topic: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a diagnostic quiz with mixed difficulty levels.
        
        Args:
            subject: Subject to assess (e.g., "Python", "Machine Learning")
            topic: Optional specific topic within the subject
            
        Returns:
            Quiz with 5 questions (2 beginner, 2 intermediate, 1 advanced)
        """
        logger.info(
            "🎯 Generating diagnostic quiz",
            subject=subject,
            topic=topic,
            quiz_type="adaptive_diagnostic"
        )
        
        # Try to get context from RAG
        query = f"{subject} {topic or ''} fundamentals concepts questions"
        logger.info("🔍 Querying RAG for context", query=query, top_k=5)
        
        context_docs = rag_service.retrieve(query, top_k=5)
        
        # AUTO-PROCESSING: If no context found, check if PDFs exist and process them
        if not context_docs:
            logger.warning(f"⚠️ No RAG context found for '{subject}' - checking for unprocessed PDFs")
            
            # Try to auto-process PDFs for this subject
            try:
                from app.services.course_discovery_service import course_discovery_service
                from pathlib import Path
                
                # Check if course folder exists
                course_path = course_discovery_service.pdfs_base_path / subject.lower()
                
                if course_path.exists() and course_path.is_dir():
                    pdf_files = list(course_path.glob("*.pdf"))
                    
                    if pdf_files:
                        logger.info(
                            f"🔄 Auto-processing {len(pdf_files)} PDFs for '{subject}'",
                            course=subject.lower(),
                            pdf_count=len(pdf_files)
                        )
                        
                        # Process the course PDFs
                        result = await course_discovery_service.process_course_pdfs(subject.lower())
                        
                        logger.info(
                            f"✅ Auto-processed PDFs successfully",
                            processed=result['processed_files'],
                            total=result['total_files'],
                            chunks=result['total_chunks']
                        )
                        
                        # Retry RAG retrieval after processing
                        context_docs = rag_service.retrieve(query, top_k=5)
                        logger.info(f"🔄 Re-queried RAG, found {len(context_docs)} chunks")
                    else:
                        logger.info(f"📁 Course folder exists but no PDFs found for '{subject}'")
                else:
                    logger.info(f"📁 No course folder found for '{subject}' at {course_path}")
                    
            except Exception as e:
                logger.error(f"❌ Auto-processing failed: {e}", exc_info=True)
                # Continue without context - will use LLM only
        
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
        
        # Construct prompt based on whether context exists
        if context:
            context_instruction = """
            IMPORTANT: Use the provided CONTEXT from the course materials to generate the questions.
            The questions should test knowledge specifically found in or related to the context.
            """
        else:
            context_instruction = "Generate standard diagnostic questions for this subject."

        topic_context = f" ({topic})" if topic else ""

        prompt = f"""
        Generate a diagnostic quiz for {subject}{topic_context} to assess the user's skill level.
        {context_instruction}
        
        The quiz must have EXACTLY 5 questions with the following distribution:
        - Questions 1-2: BEGINNER level (basic concepts, definitions)
        - Questions 3-4: INTERMEDIATE level (application, problem-solving)
        - Question 5: ADVANCED level (complex scenarios, optimization)
        
        Format the output as a valid JSON object with this EXACT structure:
        {{
            "title": "Diagnostic Quiz: {subject}",
            "description": "This quiz will help us assess your current skill level",
            "total_questions": 5,
            "questions": [
                {{
                    "id": 1,
                    "difficulty": "beginner",
                    "question": "Question text here",
                    "options": {{
                        "A": "Option A",
                        "B": "Option B",
                        "C": "Option C",
                        "D": "Option D"
                    }},
                    "correct_answer": "A",
                    "explanation": "Why A is correct"
                }}
            ]
        }}
        
        Make questions practical and relevant. Ensure the JSON is valid.
        """
        
        logger.info("🤖 Generating diagnostic quiz with LLM", has_context=bool(context))
        response = await llm_service.generate(prompt, context=context)
        
        quiz = self._parse_json_response(response)
        
        # FALLBACK: If quiz generation failed (empty response from Gemini quota), use mock data
        if not quiz.get("questions") or len(quiz.get("questions", [])) == 0:
            logger.warning("⚠️ LLM returned empty quiz (likely quota issue) - using fallback mock data")
            quiz = {
                "title": f"Diagnostic Quiz: {subject}",
                "description": "Assessment quiz (generated with fallback data due to API limits)",
                "total_questions": 5,
                "questions": [
                    {
                        "id": 1,
                        "difficulty": "beginner",
                        "question": f"What is {subject}?",
                        "options": {
                            "A": f"A programming language",
                            "B": f"A database",
                            "C": f"An operating system",
                            "D": f"A framework"
                        },
                        "correct_answer": "A",
                        "explanation": "Correct answer for beginner level"
                    },
                    {
                        "id": 2,
                        "difficulty": "beginner",
                        "question": f"What is a key feature of {subject}?",
                        "options": {
                            "A": "Easy to learn",
                            "B": "Hard to use",
                            "C": "Obsolete",
                            "D": "Windows only"
                        },
                        "correct_answer": "A",
                        "explanation": "Correct"
                    },
                    {
                        "id": 3,
                        "difficulty": "intermediate",
                        "question": f"How do you handle errors in {subject}?",
                        "options": {
                            "A": "Try-except blocks",
                            "B": "Ignore them",
                            "C": "Restart computer",
                            "D": "Delete code"
                        },
                        "correct_answer": "A",
                        "explanation": "Correct"
                    },
                    {
                        "id": 4,
                        "difficulty": "intermediate",
                        "question": f"What is an advanced concept in {subject}?",
                        "options": {
                            "A": "Decorators",
                            "B": "Variables",
                            "C": "Comments",
                            "D": "Print statements"
                        },
                        "correct_answer": "A",
                        "explanation": "Correct"
                    },
                    {
                        "id": 5,
                        "difficulty": "advanced",
                        "question": f"What is a performance optimization technique in {subject}?",
                        "options": {
                            "A": "Caching and memoization",
                            "B": "Using more variables",
                            "C": "Adding comments",
                            "D": "Restarting often"
                        },
                        "correct_answer": "A",
                        "explanation": "Correct"
                    }
                ]
            }
        
        # Add metadata about generation
        quiz["metadata"] = {
            "used_rag": bool(context),
            "chunks_retrieved": len(context_docs) if context_docs else 0,
            "sources": [doc["metadata"].get("source", "unknown") for doc in context_docs] if context_docs else []
        }
        
        logger.info(
            "✅ Diagnostic quiz generated",
            subject=subject,
            questions_count=len(quiz.get("questions", [])),
            used_rag=bool(context)
        )
        
        return quiz
    
    def evaluate_skill_level(
        self,
        quiz_questions: List[Dict[str, Any]],
        user_answers: List[str]
    ) -> Dict[str, Any]:
        """
        Evaluate user's skill level based on their quiz answers.
        
        Scoring logic:
        - Only beginner questions correct (1-2): BEGINNER
        - Beginner + intermediate correct (1-4): INTERMEDIATE
        - All questions correct (1-5): ADVANCED
        
        Args:
            quiz_questions: List of quiz questions with difficulty levels
            user_answers: List of user's answers (e.g., ["A", "B", "C", "D", "A"])
            
        Returns:
            Evaluation results with skill level and recommendations
        """
        logger.info(
            "📊 Evaluating skill level",
            total_questions=len(quiz_questions),
            answers_provided=len(user_answers)
        )
        
        # Score by difficulty level
        scores = {
            "beginner": {"correct": 0, "total": 0},
            "intermediate": {"correct": 0, "total": 0},
            "advanced": {"correct": 0, "total": 0}
        }
        
        detailed_results = []
        
        for i, question in enumerate(quiz_questions):
            if i >= len(user_answers):
                break
                
            difficulty = question.get("difficulty", "beginner").lower()
            correct_answer = question.get("correct_answer", "").upper()
            user_answer = user_answers[i].upper()
            
            is_correct = user_answer == correct_answer
            
            scores[difficulty]["total"] += 1
            if is_correct:
                scores[difficulty]["correct"] += 1
            
            detailed_results.append({
                "question_id": question.get("id", i + 1),
                "difficulty": difficulty,
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "is_correct": is_correct,
                "question": question.get("question", ""),
                "explanation": question.get("explanation", "")
            })
        
        # Determine skill level
        beginner_score = scores["beginner"]["correct"]
        intermediate_score = scores["intermediate"]["correct"]
        advanced_score = scores["advanced"]["correct"]
        
        total_correct = beginner_score + intermediate_score + advanced_score
        total_questions = sum(s["total"] for s in scores.values())
        
        # Skill level logic
        if advanced_score > 0 and intermediate_score >= 1 and beginner_score >= 1:
            skill_level = "advanced"
            level_description = "You have strong knowledge and can handle complex topics"
        elif intermediate_score >= 1 and beginner_score >= 1:
            skill_level = "intermediate"
            level_description = "You understand the fundamentals and can apply concepts"
        else:
            skill_level = "beginner"
            level_description = "You're starting your journey - let's build a strong foundation"
        
        logger.info(
            "✅ Skill level evaluated",
            skill_level=skill_level,
            total_correct=total_correct,
            total_questions=total_questions,
            beginner_correct=beginner_score,
            intermediate_correct=intermediate_score,
            advanced_correct=advanced_score
        )
        
        return {
            "skill_level": skill_level,
            "level_description": level_description,
            "total_correct": total_correct,
            "total_questions": total_questions,
            "score_percentage": round((total_correct / total_questions) * 100, 1) if total_questions > 0 else 0,
            "scores_by_difficulty": scores,
            "detailed_results": detailed_results,
            "strengths": self._identify_strengths(scores),
            "areas_for_improvement": self._identify_weaknesses(scores)
        }
    
    async def generate_personalized_study_plan(
        self,
        subject: str,
        skill_level: str,
        evaluation_results: Dict[str, Any],
        duration_days: int = 30
    ) -> Dict[str, Any]:
        """
        Generate a personalized study plan based on assessed skill level.
        
        Args:
            subject: Subject to study
            skill_level: Assessed skill level (beginner/intermediate/advanced)
            evaluation_results: Results from skill evaluation
            duration_days: Duration of the study plan
            
        Returns:
            Personalized study plan
        """
        logger.info(
            "🎯 Generating personalized study plan",
            subject=subject,
            skill_level=skill_level,
            duration_days=duration_days
        )
        
        # Get context from RAG
        query = f"{subject} {skill_level} learning path curriculum"
        logger.info("🔍 Querying RAG for context", query=query, top_k=5)
        
        context_docs = rag_service.retrieve(query, top_k=5)
        
        if context_docs:
            context = "\n\n".join([doc["text"] for doc in context_docs])
            logger.info("✅ RAG CONTEXT FOUND", chunks_retrieved=len(context_docs), mode="RAG + LLM")
        else:
            context = None
            logger.warning("⚠️ NO RAG CONTEXT", mode="LLM_ONLY")
        
        # Extract strengths and weaknesses
        strengths = evaluation_results.get("strengths", [])
        weaknesses = evaluation_results.get("areas_for_improvement", [])
        
        strengths_text = ", ".join(strengths) if strengths else "foundational concepts"
        weaknesses_text = ", ".join(weaknesses) if weaknesses else "advanced topics"
        
        # Construct prompt based on whether context exists
        if context:
            context_instruction = """
            IMPORTANT: Use the provided CONTEXT from the course materials to structure the study plan.
            Ensure the topics and activities align with the actual content available in the course PDFs.
            """
        else:
            context_instruction = "Generate a standard study plan for this subject."

        prompt = f"""
        Create a personalized {duration_days}-day study plan for {subject} for a {skill_level} level learner.
        {context_instruction}
        
        Based on their diagnostic quiz:
        - Current skill level: {skill_level}
        - Strengths: {strengths_text}
        - Areas to improve: {weaknesses_text}
        - Score: {evaluation_results.get('score_percentage', 0)}%
        
        The plan should:
        1. Build on their existing strengths
        2. Address their weak areas
        3. Progress from their current level to the next
        4. Include practical exercises and projects
        5. Be realistic and achievable
        
        Format as valid JSON:
        {{
            "title": "Personalized Study Plan",
            "skill_level": "{skill_level}",
            "duration_days": {duration_days},
            "focus_areas": ["area1", "area2"],
            "learning_objectives": ["objective1", "objective2"],
            "daily_plan": [
                {{
                    "day": 1,
                    "topic": "Topic name",
                    "focus": "What to focus on",
                    "activities": ["Activity 1", "Activity 2"],
                    "estimated_hours": 2,
                    "difficulty": "beginner/intermediate/advanced"
                }}
            ],
            "milestones": [
                {{
                    "day": 7,
                    "milestone": "Complete basics",
                    "assessment": "Quiz on fundamentals"
                }}
            ],
            "recommended_resources": ["Resource 1", "Resource 2"]
        }}
        """
        
        logger.info("🤖 Generating personalized plan with LLM", has_context=bool(context))
        response = await llm_service.generate(prompt, context=context)
        
        plan = self._parse_json_response(response)
        
        # Add metadata about generation
        plan["metadata"] = {
            "used_rag": bool(context),
            "chunks_retrieved": len(context_docs) if context_docs else 0,
            "sources": [doc["metadata"].get("source", "unknown") for doc in context_docs] if context_docs else []
        }
        
        logger.info(
            "✅ Personalized study plan generated",
            skill_level=skill_level,
            days=duration_days,
            used_rag=bool(context)
        )
        
        return plan
    
    def _identify_strengths(self, scores: Dict[str, Dict[str, int]]) -> List[str]:
        """Identify user's strengths based on scores."""
        strengths = []
        
        for difficulty, score_data in scores.items():
            if score_data["total"] > 0:
                percentage = (score_data["correct"] / score_data["total"]) * 100
                if percentage >= 75:
                    strengths.append(f"{difficulty} level concepts")
        
        return strengths if strengths else ["basic understanding"]
    
    def _identify_weaknesses(self, scores: Dict[str, Dict[str, int]]) -> List[str]:
        """Identify areas for improvement based on scores."""
        weaknesses = []
        
        for difficulty, score_data in scores.items():
            if score_data["total"] > 0:
                percentage = (score_data["correct"] / score_data["total"]) * 100
                if percentage < 50:
                    weaknesses.append(f"{difficulty} level topics")
        
        return weaknesses if weaknesses else ["advanced concepts"]
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from LLM response."""
        try:
            clean_response = re.sub(r'```json\s*|\s*```', '', response).strip()
            return json.loads(clean_response)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON response", error=str(e), response=response[:200])
            return {"error": "Failed to generate structured content", "raw_response": response}


# Global instance
adaptive_assessment_service = AdaptiveAssessmentService()
