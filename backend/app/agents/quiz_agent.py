"""
Quiz Agent - Generates adaptive quizzes and evaluates answers.
"""
from typing import List, Dict, Any
from app.agents.state import AgentState
from app.services.llm_service import llm_service
from app.core.logging import get_logger

logger = get_logger(__name__)


class QuizAgent:
    """Agent responsible for generating and evaluating quizzes."""
    
    async def __call__(self, state: AgentState) -> AgentState:
        """
        Generate a quiz or evaluate quiz responses.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with quiz
        """
        logger.info("Quiz agent activated")
        
        # Check if we are evaluating answers from a previous quiz
        # We assume answers look like "1A 2B" or "1. A, 2. B" etc.
        if state.get("quiz_questions") and self._is_answer_submission(state["user_message"]):
            logger.info("Evaluating quiz answers")
            user_answers = self._parse_answers(state["user_message"])
            results = await self.evaluate_quiz(state["quiz_questions"], user_answers)
            
            # Update progress if in a course
            course_completed = False
            next_topic_name = None
            
            if state.get("current_course_id") and state.get("db"):
                await self._save_quiz_result(state, results)
                course_completed, next_topic_name = await self._update_progress(state, results)
                
                if course_completed:
                    logger.info("Course completed, generating final exam")
                    # Generate final exam
                    final_questions = await self._generate_final_quiz(state)
                    state["quiz_questions"] = final_questions
                    
                    # Append congratulatory message and final exam
                    state["bot_response"] = self._format_results(results, next_topic_name)
                    state["bot_response"] += "\n\n🎉 **CONGRATULATIONS!** You have completed all modules in this course! 🎓\n\n"
                    state["bot_response"] += "To earn your certificate, please complete this **Final Comprehensive Exam** covering all topics.\n\n"
                    state["bot_response"] += self._format_quiz_response(final_questions, "Final Course Exam")
                    
                    # Do not clear completed flag yet as we want to show this
                    state["completed"] = True
                    return state
            
            state["quiz_results"] = results
            state["bot_response"] = self._format_results(results, next_topic_name)
            
            # Clear pending questions so we don't evaluate again
            state["quiz_questions"] = []
            state["completed"] = True
            return state

        # Otherwise, generate a new quiz
        # Extract topic from message or use current topic
        topic = self._extract_topic(state)
        skill_level = state.get("skill_level", "beginner")
        
        # Generate quiz questions
        # Try to get cached content for the current topic to ensure quiz matches what was taught
        content_context = None
        if state.get("current_course_id") and state.get("db"):
            db = state["db"]
            course_id = state["current_course_id"]
            
            from app.models.course import UserCourse, TopicContent
            user_course = db.query(UserCourse).filter(
                UserCourse.user_id == state["user_id"],
                UserCourse.course_id == course_id
            ).first()
            
            if user_course:
                # Get content for the *current* topic (the one just taught)
                cached_content = db.query(TopicContent).filter(
                    TopicContent.course_id == course_id,
                    TopicContent.module_index == (user_course.current_module or 0),
                    TopicContent.topic_index == (user_course.current_topic or 0)
                ).first()
                
                if cached_content:
                    content_context = cached_content.content
                    logger.info("Using cached topic content for quiz generation")

        questions = await self._generate_quiz(topic, skill_level, content_context=content_context)
        
        state["quiz_questions"] = questions
        state["bot_response"] = self._format_quiz_response(questions, topic)
        state["completed"] = True
        state["next_agent"] = None
        
        logger.info("Quiz generated", topic=topic, question_count=len(questions))
        
        return state

    async def _save_quiz_result(self, state: AgentState, results: Dict[str, Any]):
        """Save quiz result to database."""
        db = state.get("db")
        if not db: return
        
        from app.models.quiz import QuizResult
        from app.models.course import UserCourse
        
        user_id = state["user_id"]
        course_id = state["current_course_id"]
        
        user_course = db.query(UserCourse).filter(
            UserCourse.user_id == user_id,
            UserCourse.course_id == course_id
        ).first()
        
        if user_course:
            # Calculate average quiz score
            current_avg = user_course.quiz_average or 0
            # Simple moving average for now, or just update last
            # Ideally we'd query all results, but let's just store this one
            
            quiz_result = QuizResult(
                user_course_id=user_course.id,
                score=results["score"],
                total_questions=results["total_questions"],
                correct_answers=results["correct_answers"],
                details=results,
                topic=state.get("current_topic", "General"),
                week=user_course.current_module + 1 if user_course.current_module is not None else 1
            )
            db.add(quiz_result)
            
            # Update course average
            # Recalculate from all QuizResults
            all_results = db.query(QuizResult).filter(
                QuizResult.user_course_id == user_course.id
            ).all()
            
            if all_results:
                total_score = sum(r.score for r in all_results)
                user_course.quiz_average = total_score / len(all_results)
            else:
                user_course.quiz_average = results["score"] 
            
            db.commit()
            logger.info("Quiz result saved", score=results["score"])

    def _is_answer_submission(self, message: str) -> bool:
        """Check if message looks like quiz answers."""
        import re
        # Matches patterns like "1A", "1. A", "1: A", "1 A"
        return bool(re.search(r'\d+[\.\:\)\s]*[A-D]', message.upper()))

    def _parse_answers(self, message: str) -> Dict[int, str]:
        """Parse user answers from message."""
        import re
        answers = {}
        # Find all matches of number followed by letter
        matches = re.findall(r'(\d+)[\.\:\)\s]*([A-D])', message.upper())
        for num, letter in matches:
            answers[int(num)] = letter
        return answers

    def _format_results(self, results: Dict[str, Any], next_topic_name: str = None) -> str:
        """Format evaluation results."""
        score = results["score"]
        emoji = "🌟" if score >= 80 else "👍" if score >= 60 else "💪"
        
        response = f"{emoji} **Quiz Results**\n\n"
        response += f"You scored **{score:.0f}%** ({results['correct_answers']}/{results['total_questions']} correct).\n\n"
        
        for detail in results["details"]:
            icon = "✅" if detail["is_correct"] else "❌"
            response += f"{icon} **Q{detail['question_number']}:** {detail['question']}\n"
            if not detail["is_correct"]:
                response += f"   Your answer: {detail['user_answer']} | Correct: {detail['correct_answer']}\n"
            response += f"   *Explanation: {detail['explanation']}*\n\n"
            
        if score >= 70:
            response += "Great job! You've mastered this topic. 🚀\n\n"
            if next_topic_name:
                response += f"Shall we continue to the next topic: **{next_topic_name}**? (Reply 'Yes' to proceed, or 'No' to take a break)"
            else:
                response += "Ready for the next one? Reply 'Yes' to continue!"
        else:
            response += "You scored below 70%, so we'll stay on this topic for now to ensure you've mastered it. 🛡️\n\n"
            response += "Review the explanations above, and when you're ready, you can:\n"
            response += "• Type **'Review'** to go over the lesson again.\n"
            response += "• Type **'Retry'** to take another quiz."
            
        return response

    async def _update_progress(self, state: AgentState, results: Dict[str, Any]) -> tuple[bool, str | None]:
        """
        Update user progress in DB.
        
        Returns:
            tuple: (course_completed, next_topic_name)
        """
        if results["score"] < 70:
            return False, None
            
        db = state["db"]
        user_id = state["user_id"]
        course_id = state["current_course_id"]
        
        from app.models.course import UserCourse, Course
        
        user_course = db.query(UserCourse).filter(
            UserCourse.user_id == user_id,
            UserCourse.course_id == course_id
        ).first()
        
        course_completed = False
        next_topic_name = None
        
        if user_course:
            # Increment topic/module
            course = db.query(Course).filter(Course.id == course_id).first()
            if course and course.syllabus_template:
                modules = course.syllabus_template.get("modules", [])
                curr_mod_idx = user_course.current_module or 0
                curr_topic_idx = user_course.current_topic or 0
                
                if curr_mod_idx < len(modules):
                    topics = modules[curr_mod_idx].get("topics", [])
                    
                    # Move to next topic
                    if curr_topic_idx < len(topics) - 1:
                        user_course.current_topic = curr_topic_idx + 1
                        next_topic_name = topics[curr_topic_idx + 1]
                    else:
                        # Move to next module
                        if curr_mod_idx < len(modules) - 1:
                            user_course.current_module = curr_mod_idx + 1
                            user_course.current_topic = 0
                            
                            # Get first topic of next module
                            next_module = modules[curr_mod_idx + 1]
                            next_topics = next_module.get("topics", [])
                            if next_topics:
                                next_topic_name = f"{next_module.get('title', 'Next Module')}: {next_topics[0]}"
                        else:
                            # Course completed
                            if user_course.status != "completed":
                                user_course.status = "completed"
                                user_course.progress = 100.0
                                course_completed = True
                            
                # Update percentage progress (rough estimate)
                total_modules = len(modules)
                if total_modules > 0:
                    user_course.progress = min(100.0, ((curr_mod_idx + (curr_topic_idx / max(1, len(topics)))) / total_modules) * 100)
            
            db.commit()
            logger.info("User progress updated", user_id=user_id, course_id=course_id, completed=course_completed)
            
        return course_completed, next_topic_name

    async def _generate_final_quiz(self, state: AgentState) -> List[Dict[str, Any]]:
        """Generate a comprehensive final exam for the course."""
        course_id = state.get("current_course_id")
        db = state.get("db")
        
        topics_list = []
        if course_id and db:
            from app.models.course import Course
            course = db.query(Course).filter(Course.id == course_id).first()
            if course and course.syllabus_template:
                for module in course.syllabus_template.get("modules", []):
                    topics_list.extend(module.get("topics", []))
        
        # If we can't find specific topics, fall back to course title
        topics_str = ", ".join(topics_list) if topics_list else f"all topics in {course_id}"
        
        # Generate 20 questions
        return await self._generate_quiz(
            topic=f"Final Exam: {topics_str}", 
            skill_level=state.get("skill_level", "intermediate"),
            num_questions=20
        )
    
    def _extract_topic(self, state: AgentState) -> str:
        """Extract topic from state or message."""
        # 1. Check for explicit topic in state (set by orchestrator or context)
        if state.get("current_topic"):
            return state["current_topic"]
            
        # 2. Check for course context
        if state.get("current_course_id"):
            # If we have a course ID but no specific topic, use the course name + "general concepts"
            return f"{state['current_course_id']} general concepts"
        
        # 3. Try to extract from message
        message = state["user_message"].lower()
        
        # Check if user said "no" (meaning "no doubts") which should trigger a quiz
        # This is a bit heuristic, but aligns with the "Any doubts? -> No -> Quiz" flow
        if message.strip() in ["no", "no.", "no doubt", "no doubts", "nope", "none", "clear", "all clear", "it's clear", "its clear"]:
             if state.get("current_topic"):
                 return state["current_topic"]
        
        # Remove quiz-related words
        topic_keywords = message.replace("quiz", "").replace("test", "").replace("me on", "").strip()
        
        # 4. If message was just "quiz me" and we have no context, default to general knowledge
        # But ideally we should ask the user "What topic?" - for now, let's try to infer from recent history if possible
        # or just return a generic topic that will prompt the user
        
        return topic_keywords if topic_keywords else "general knowledge"
    
    async def _generate_quiz(self, topic: str, skill_level: str, num_questions: int = 5, content_context: str = None) -> List[Dict[str, Any]]:
        """Generate quiz questions using LLM."""
        import random
        from datetime import datetime
        
        # Add randomness to the prompt to ensure different questions each time
        seed = f"{random.randint(1, 10000)}-{datetime.now().timestamp()}"
        
        context_instruction = ""
        if content_context:
            context_instruction = f"""
IMPORTANT: Use ONLY the following content to generate the questions. Do not ask about anything not covered here:
---
{content_context}
---
"""
        
        prompt = f"""
Generate {num_questions} multiple-choice quiz questions about "{topic}" for a {skill_level} level learner.
Seed: {seed}

{context_instruction}

IMPORTANT:
1. Questions must be specific and challenging appropriate to the skill level.
2. If the topic involves writing code (e.g., Python, Java, SQL), include code snippets.
3. If the topic is conceptual (e.g., "What is AI?", history, theory), focus on definitions, key concepts, and understanding.
4. Ensure questions are directly relevant to the specific topic "{topic}". Do not ask about unrelated programming languages or concepts not covered in the topic.
5. Avoid generic questions.
6. **NEVER generate questions like "What would you like to learn?" or "How do you feel about this topic?".** Questions must test knowledge.
7. Ensure exactly {num_questions} questions are generated.

Format your response as a valid JSON array of objects. Do not include markdown formatting.
[
  {{
    "question": "Question text here (include code snippets if applicable)",
    "options": {{
      "A": "Option A text",
      "B": "Option B text",
      "C": "Option C text",
      "D": "Option D text"
    }},
    "correct_answer": "A",
    "explanation": "Brief explanation"
  }}
]
"""
        
        try:
            response = await llm_service.generate(prompt, raw_prompt=True)
            
            # Clean up response (remove markdown)
            cleaned_response = response.strip()
            if "```json" in cleaned_response:
                cleaned_response = cleaned_response.split("```json")[1].split("```")[0]
            elif "```" in cleaned_response:
                cleaned_response = cleaned_response.split("```")[1].split("```")[0]
            
            cleaned_response = cleaned_response.strip()
            
            # Find JSON boundaries
            json_start = cleaned_response.find("[")
            json_end = cleaned_response.rfind("]") + 1
            
            if json_start != -1 and json_end > json_start:
                import json
                json_str = cleaned_response[json_start:json_end]
                parsed = json.loads(json_str)
                
                # Handle if LLM wrapped it in a dict like {"questions": [...]}
                if isinstance(parsed, dict) and "questions" in parsed:
                    questions = parsed["questions"]
                elif isinstance(parsed, list):
                    questions = parsed
                else:
                    questions = []
                
                if not questions:
                     return [self._create_fallback_question(topic)]
                     
                return questions
            else:
                return self._parse_quiz_response(response)
            
        except Exception as e:
            logger.error("Quiz generation failed", error=str(e))
            return [self._create_fallback_question(topic)]
    
    def _parse_quiz_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response into structured quiz questions."""
        questions = []
        current_question = {}
        
        for line in response.split("\n"):
            line = line.strip()
            
            if not line or line == "---":
                if current_question and "question" in current_question:
                    questions.append(current_question)
                    current_question = {}
                continue
            
            if line.startswith("QUESTION:"):
                current_question["question"] = line.replace("QUESTION:", "").strip()
                current_question["options"] = {}
            
            elif line.startswith(("A)", "B)", "C)", "D)")):
                letter = line[0]
                text = line[2:].strip()
                if "options" in current_question:
                    current_question["options"][letter] = text
            
            elif line.startswith("CORRECT:"):
                current_question["correct_answer"] = line.replace("CORRECT:", "").strip()
            
            elif line.startswith("EXPLANATION:"):
                current_question["explanation"] = line.replace("EXPLANATION:", "").strip()
        
        # Add last question if exists
        if current_question and "question" in current_question:
            questions.append(current_question)
        
        return questions
    
    def _create_fallback_question(self, topic: str) -> Dict[str, Any]:
        """Create a fallback question when generation fails."""
        # Return a list of 5 generic but valid questions if possible, 
        # but since this function signature returns a single dict, we might need to adjust the caller
        # However, looking at the code, the caller expects a list if it calls this.
        # Wait, the caller puts it in a list: return [self._create_fallback_question(topic)]
        # So we should probably return a single question here, but make it better.
        
        return {
            "question": f"Which of the following is a key concept related to {topic}?",
            "options": {
                "A": "The fundamental principles",
                "B": "Advanced theoretical applications",
                "C": "Practical implementation details",
                "D": "All of the above are relevant"
            },
            "correct_answer": "D",
            "explanation": f"All these aspects are important when studying {topic}.",
        }
    
    def _format_quiz_response(self, questions: List[Dict[str, Any]], topic: str) -> str:
        """Format quiz questions for display."""
        response = f"🎯 **Quiz: {topic.title()}**\n\n"
        response += "Let's test your knowledge! Answer the following questions:\n\n"
        
        # Create a list of questions with IDs and difficulty for the frontend
        frontend_questions = []
        
        for i, q in enumerate(questions, 1):
            # Frontend parser expects: **Question 1** (Difficulty):
            # Then newline, then question text
            response += f"**Question {i}** (Beginner):\n{q['question']}\n"
            for letter, option in q.get("options", {}).items():
                response += f"{letter}) {option}\n"
            response += "\n"
            
            # Prepare structured data
            frontend_questions.append({
                "id": i,
                "difficulty": "Beginner", # Defaulting to Beginner as per original code
                "question": q["question"],
                "options": q.get("options", {}),
                "correct_answer": q.get("correct_answer", "A")
            })
            
        response += "Reply with your answers (e.g., '1A 2B 3C 4D 5A') to get your results!"
        
        # Append hidden JSON block for robust parsing
        import json
        response += "\n\n```json_quiz\n"
        response += json.dumps({"questions": frontend_questions}, indent=2)
        response += "\n```"
        
        return response
    
    async def evaluate_quiz(
        self,
        questions: List[Dict[str, Any]],
        user_answers: Dict[int, str],
    ) -> Dict[str, Any]:
        """
        Evaluate user's quiz answers.
        
        Args:
            questions: List of questions
            user_answers: Dictionary mapping question number to answer letter
            
        Returns:
            Evaluation results
        """
        results = {
            "total_questions": len(questions),
            "correct_answers": 0,
            "score": 0.0,
            "details": [],
        }
        
        for i, question in enumerate(questions, 1):
            user_answer = user_answers.get(i, "").upper()
            correct_answer = question.get("correct_answer", "").upper()
            is_correct = user_answer == correct_answer
            
            if is_correct:
                results["correct_answers"] += 1
            
            results["details"].append({
                "question_number": i,
                "question": question["question"],
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "is_correct": is_correct,
                "explanation": question.get("explanation", ""),
            })
        
        results["score"] = (results["correct_answers"] / results["total_questions"]) * 100
        
        return results


# Global instance
quiz_agent = QuizAgent()
