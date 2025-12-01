"""
Assessment Agent - Handles user onboarding and skill assessment.
"""
import re
from typing import Dict, Any
from app.agents.state import AgentState
from app.services.llm_service import llm_service
from app.core.logging import get_logger
from app.agents.quiz_agent import quiz_agent
from app.agents.planning_agent import planning_agent
from app.services.adaptive_assessment_service import adaptive_assessment_service

logger = get_logger(__name__)

class AssessmentAgent:
    """Agent responsible for onboarding and assessment flow."""
    
    async def __call__(self, state: AgentState) -> AgentState:
        logger.info("Assessment agent activated")
        
        message = state["user_message"].lower().strip()
        
        # Check if this is a greeting (fresh start)
        greetings = ["hi", "hello", "hey", "start", "begin"]
        is_greeting = message in greetings
        
        if is_greeting:
            logger.info("🔄 Greeting detected - resetting conversation state")
            # Reset metadata for fresh start
            state["metadata"] = {
                "onboarding_step": None
            }
            state["current_topic"] = "general"
        
        # Retrieve step from metadata (persisted state)
        step = state.get("metadata", {}).get("onboarding_step")
        topic = state.get("current_topic", "general")
        
        logger.info(f"Current onboarding step: {step}, topic: {topic}, is_greeting: {is_greeting}")
        
        if not step:
            # Step 0: Ask for topic if not set
            if not topic or topic == "general":
                logger.info("📚 Topic not specified, asking user")
                state["bot_response"] = (
                    "Great! I'm here to help you learn. 😊\n\n"
                    "**What topic would you like to learn?**\n"
                    "(e.g., Python, Machine Learning, Data Science, Java, etc.)"
                )
                state["metadata"]["onboarding_step"] = "diagnostic_quiz_direct"
            else:
                # Topic is already set, go straight to quiz generation
                logger.info(f"📚 Topic already set: {topic} - generating quiz directly")
                
                state["current_topic"] = topic
                state["metadata"]["current_topic"] = topic
                
                # Set step and fall through to quiz generation
                step = "diagnostic_quiz_direct"
                # Don't return, continue to quiz generation below
        
        if step == "diagnostic_quiz_direct":
            # Extract topic from message only if not already set
            if not topic or topic == "general":
                extracted_topic = message.strip()
                if len(extracted_topic) > 50:  # Too long
                    extracted_topic = "general"
                
                state["current_topic"] = extracted_topic
                state["metadata"]["current_topic"] = extracted_topic
                topic = extracted_topic
            
            logger.info(
                "🎯 Starting diagnostic quiz generation",
                topic=topic,
                note="Skipping self-assessment questions"
            )
            
            state["bot_response"] = (
                f"Perfect! Let's assess your **{topic.title()}** skills.\n\n"
                "I'll ask you 5 questions ranging from Beginner to Advanced. "
                "Based on your answers, I'll determine your actual skill level and create a personalized study plan.\n\n"
                "Ready? Here we go!"
            )
            
            try:
                logger.info("📝 Calling adaptive_assessment_service.generate_diagnostic_quiz", subject=topic)
                
                # Generate adaptive quiz using the new service
                quiz = await adaptive_assessment_service.generate_diagnostic_quiz(
                    subject=topic
                )
                
                logger.info(
                    "✅ Quiz generated successfully",
                    questions_count=len(quiz.get("questions", [])),
                    has_metadata=bool(quiz.get("metadata"))
                )
                
                # Store full quiz object for evaluation later
                state["metadata"]["quiz_data"] = quiz
                
                # Check if RAG was used
                used_rag = quiz.get("metadata", {}).get("used_rag", False)
                chunks_retrieved = quiz.get("metadata", {}).get("chunks_retrieved", 0)
                sources = quiz.get("metadata", {}).get("sources", [])
                
                logger.info(
                    "🔍 RAG Status",
                    used_rag=used_rag,
                    chunks_retrieved=chunks_retrieved,
                    sources=sources
                )
                
                if not used_rag:
                    logger.warning("⚠️ RAG not used - no PDF content found for this topic")
                    state["bot_response"] += "\n\n⚠️ **Note:** Using general questions. For topic-specific questions, add PDFs to the course folder."
                else:
                    logger.info(f"✅ RAG active - using {chunks_retrieved} chunks from PDFs")
                    state["bot_response"] += "\n\n✅ **Questions based on your course materials.**"
                
                # Format questions for chat
                questions_text = ""
                for q in quiz.get("questions", []):
                    questions_text += f"\n\n**Question {q['id']}** ({q['difficulty'].title()}):\n{q['question']}\n"
                    for key, value in q['options'].items():
                        questions_text += f"{key}) {value}\n"
                
                logger.info(f"📋 Formatted {len(quiz.get('questions', []))} questions for display")
                
                state["bot_response"] += questions_text
                state["bot_response"] += "\n\nReply with your answers (e.g., '1A 2B 3C 4D 5A') to get your results!"
                
                state["metadata"]["onboarding_step"] = "evaluate_and_plan"
                logger.info("✅ Diagnostic quiz step completed, moving to evaluate_and_plan")
            
            except Exception as e:
                logger.error(f"❌ Failed to generate quiz: {str(e)}", exc_info=True)
                state["bot_response"] += f"\n\n❌ **Error:** Failed to generate the quiz. ({str(e)})\nPlease try again or choose a different topic."
                state["metadata"]["onboarding_step"] = None  # Reset
            
        elif step == "evaluate_and_plan":
            # Step 4: Evaluate Quiz and Generate Roadmap
            logger.info("📊 Starting quiz evaluation and study plan generation")
            
            # Check if this is a direct roadmap request (from quiz results button)
            roadmap_pattern = r"generate a roadmap for (\w+) level"
            roadmap_match = re.search(roadmap_pattern, message, re.IGNORECASE)
            
            if roadmap_match:
                # Direct roadmap request - skip evaluation
                requested_level = roadmap_match.group(1).capitalize()
                logger.info(f"🎯 Direct roadmap request detected for level: {requested_level}")
                
                # Ensure topic is set
                if not topic or topic == "general":
                    topic = state.get("metadata", {}).get("current_topic", "Python")
                    logger.info(f"📚 Using topic from metadata: {topic}")
                
                state["bot_response"] = (
                    f"**Generating {requested_level} Level Roadmap** 📚\n\n"
                    f"Creating a personalized study plan for **{topic}** tailored for {requested_level} learners...\n\n"
                )
                
                # Generate roadmap directly
                logger.info(
                    "📚 Calling adaptive_assessment_service.generate_personalized_study_plan",
                    subject=topic,
                    skill_level=requested_level,
                    duration_days=30
                )
                
                plan = await adaptive_assessment_service.generate_personalized_study_plan(
                    subject=topic,
                    skill_level=requested_level,
                    evaluation_results={
                        "total_correct": 0,
                        "total_questions": 0,
                        "skill_level": requested_level,
                        "strengths": [f"{requested_level} level concepts"],
                        "areas_for_improvement": []
                    },
                    duration_days=30
                )
                
                # Check RAG status
                used_rag = plan.get("metadata", {}).get("used_rag", False)
                chunks_retrieved = plan.get("metadata", {}).get("chunks_retrieved", 0)
                sources = plan.get("metadata", {}).get("sources", [])
                
                logger.info(
                    "🔍 Study Plan RAG Status",
                    used_rag=used_rag,
                    chunks_retrieved=chunks_retrieved,
                    sources=sources
                )
                
                if used_rag:
                    unique_sources = list(set(sources))
                    logger.info(f"✅ RAG active for study plan - using {chunks_retrieved} chunks from {len(unique_sources)} sources")
                    state["bot_response"] += f"✅ **RAG Active:** Plan tailored using content from: {', '.join(unique_sources)}\n\n"
                
                # Format plan
                plan_text = self._format_study_plan(plan)
                state["bot_response"] += f"**Personalized Study Plan: {topic}**\n{plan_text}\n\n"
                state["bot_response"] += "**Shall we start with Day 1?**"
                
                state["metadata"]["roadmap"] = plan
                state["metadata"]["onboarding_step"] = "completed"
                
                logger.info("✅ Direct roadmap generation completed successfully")
                
                return state
            
            # Original evaluation flow (from quiz answers)
            quiz_data = state.get("metadata", {}).get("quiz_data", {})
            questions = quiz_data.get("questions", [])
            
            logger.info(f"📝 Retrieved {len(questions)} questions from quiz data")
            
            # Parse answers
            user_answers_map = self._parse_answers(message)
            logger.info(f"🔤 Parsed user answers", answer_count=len(user_answers_map), answers=user_answers_map)
            
            # Convert map to list for service [1:'A', 2:'B'] -> ['A', 'B', ...]
            user_answers_list = []
            for i in range(1, len(questions) + 1):
                user_answers_list.append(user_answers_map.get(i, ""))
            
            logger.info("🔄 Converted answers to list format", answers_list=user_answers_list)
            
            # Evaluate using service
            logger.info("📊 Calling adaptive_assessment_service.evaluate_skill_level")
            evaluation = adaptive_assessment_service.evaluate_skill_level(
                quiz_questions=questions,
                user_answers=user_answers_list
            )
            
            score = evaluation['total_correct']
            total = evaluation['total_questions']
            assessed_level = evaluation['skill_level']
            
            logger.info(
                "✅ Evaluation completed",
                score=f"{score}/{total}",
                assessed_level=assessed_level,
                percentage=evaluation.get('score_percentage'),
                strengths=evaluation.get('strengths'),
                weaknesses=evaluation.get('areas_for_improvement')
            )
            
            stars = "⭐" * score
            
            state["bot_response"] = (
                f"**Quiz Results:**\n"
                f"You got {score}/{total} correct! {stars}\n\n"
                f"**Assessed Level:** {assessed_level.upper()}\n"
                f"{evaluation['level_description']}\n\n"
                f"**Strengths:** {', '.join(evaluation['strengths'])}\n"
                f"**Focus Areas:** {', '.join(evaluation['areas_for_improvement'])}\n\n"
                "Generating your personalized study plan based on these results..."
            )
            
            # Generate Personalized Plan
            logger.info(
                "📚 Calling adaptive_assessment_service.generate_personalized_study_plan",
                subject=topic,
                skill_level=assessed_level,
                duration_days=30
            )
            
            plan = await adaptive_assessment_service.generate_personalized_study_plan(
                subject=topic,
                skill_level=assessed_level,
                evaluation_results=evaluation,
                duration_days=30
            )
            
            logger.info(
                "✅ Study plan generated",
                title=plan.get('title'),
                focus_areas_count=len(plan.get('focus_areas', [])),
                daily_plan_days=len(plan.get('daily_plan', []))
            )
            
            # Check if RAG was used
            used_rag = plan.get("metadata", {}).get("used_rag", False)
            chunks_retrieved = plan.get("metadata", {}).get("chunks_retrieved", 0)
            sources = plan.get("metadata", {}).get("sources", [])
            
            logger.info(
                "🔍 Study Plan RAG Status",
                used_rag=used_rag,
                chunks_retrieved=chunks_retrieved,
                sources=sources
            )
            
            if not used_rag:
                logger.warning("⚠️ RAG not used for study plan - no PDF content found")
                state["bot_response"] += "\n\n⚠️ **Note:** I couldn't find processed PDF materials for this topic, so I generated a general study plan. For a more tailored experience, please go to the **Course Discovery** page and process your course PDFs."
            else:
                unique_sources = list(set(sources))
                logger.info(f"✅ RAG active for study plan - using {chunks_retrieved} chunks from {len(unique_sources)} sources")
                state["bot_response"] += f"\n\n✅ **RAG Active:** Plan tailored using content from: {', '.join(unique_sources[:3])}"
            
            # Format Plan for Chat
            plan_text = f"\n\n**Personalized Study Plan: {plan.get('title', topic)}**\n"
            plan_text += f"Focus: {', '.join(plan.get('focus_areas', []))}\n\n"
            
            for day in plan.get('daily_plan', [])[:5]: # Show first 5 days to avoid huge message
                plan_text += f"**Day {day['day']}: {day['topic']}**\n"
                plan_text += f"- {day['focus']}\n"
                plan_text += f"- Activities: {', '.join(day.get('activities', []))}\n\n"
            
            if len(plan.get('daily_plan', [])) > 5:
                plan_text += "*...and more! View the full plan in the dashboard.*"

            state["bot_response"] += plan_text
            state["bot_response"] += "\n\n**Shall we start with Day 1?**"
            
            logger.info("✅ Assessment and planning flow completed successfully")
            state["metadata"]["onboarding_step"] = "completed"
            
        else:
            # Fallback
            state["bot_response"] = "Let's start learning!"
            state["metadata"]["onboarding_step"] = "completed"
            
        state["completed"] = True
        return state

    def _parse_answers(self, message: str) -> Dict[int, str]:
        """Parse user answers like '1A 2B' or 'A B C'."""
        answers = {}
        message = message.upper()
        
        # Try to find patterns like "1A", "1. A", "1: A"
        import re
        matches = re.findall(r'(\d+)[\.\:\)\s]*([A-D])', message)
        if matches:
            for num, ans in matches:
                answers[int(num)] = ans
            return answers
            
        # If no numbers, assume sequential letters
        # Split by non-letter chars
        tokens = re.findall(r'[A-D]', message)
        for i, ans in enumerate(tokens, 1):
            answers[i] = ans
            
        return answers

    def _extract_level(self, message: str) -> str:
        if "begin" in message: return "Beginner"
        if "interm" in message: return "Intermediate"
        if "advan" in message: return "Advanced"
        if "expert" in message: return "Expert"
        return "Beginner"

assessment_agent = AssessmentAgent()
