"""
Teaching Agent - Handles learning and explanation requests.
"""
from typing import Dict, Any
from app.agents.state import AgentState
from app.services.knowledge_service import knowledge_service
from app.core.logging import get_logger

logger = get_logger(__name__)


class TeachingAgent:
    """Agent responsible for teaching and answering questions."""
    
    async def __call__(self, state: AgentState) -> AgentState:
        """
        Answer user's question using knowledge service.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with answer
        """
        question = state["user_message"]
        user_id = state.get("user_id")
        db = state.get("db")
        course_id = state.get("current_course_id")
        
        logger.info("Teaching agent processing", question=question[:50])
        
        # Build context from user profile
        context = self._build_context(state)
        
        # Check if we are in a course context and have DB access
        if course_id and db:
            from app.models.course import Course, UserCourse
            
            # Get course and user progress
            user_course = db.query(UserCourse).filter(
                UserCourse.user_id == user_id,
                UserCourse.course_id == course_id
            ).first()
            
            course = db.query(Course).filter(Course.id == course_id).first()
            
            if user_course and course and course.syllabus_template:
                syllabus = course.syllabus_template
                modules = syllabus.get("modules", [])
                
                # Determine current topic from progress
                curr_mod_idx = user_course.current_module or 0
                curr_topic_idx = user_course.current_topic or 0
                
                # If user just started or asks "what's next", guide them
                # Also handle affirmative responses like "yes", "ready" which imply "continue"
                # If user just started or asks "what's next", guide them
                # Also handle affirmative responses like "yes", "ready" which imply "continue"
                generic_triggers = [
                    "start", "begin", "next", "what to learn", "guide me", "hello", "hi",
                    "yes", "ready", "sure", "ok", "yeah", "continue", "go ahead",
                    "explain concepts", "teach me", "teach"
                ]
                
                is_generic_request = any(k in question.lower() for k in generic_triggers)
                
                # Also check if the user is explicitly asking about the CURRENT topic
                # This ensures "Explain [Current Topic]" hits the cache
                current_topic_name = ""
                if curr_mod_idx < len(modules):
                    module = modules[curr_mod_idx]
                    topics = module.get("topics", [])
                    if curr_topic_idx < len(topics):
                        current_topic_name = topics[curr_topic_idx].lower()
                        
                # Check for negative response (user wants to pause/stop)
                negative_triggers = ["no", "nope", "not now", "wait", "stop", "pause", "later"]
                is_negative_request = any(k == question.lower().strip() or k in question.lower().split() for k in negative_triggers)

                if is_negative_request:
                    state["bot_response"] = "No problem! Take your time. 🧘\n\nWhen you are ready to continue with the next topic, just type **'Yes'** or **'Ready'**!"
                    state["completed"] = True
                    return state

                if current_topic_name and current_topic_name in question.lower():
                    is_generic_request = True
                
                if is_generic_request:
                    if curr_mod_idx < len(modules):
                        module = modules[curr_mod_idx]
                        topics = module.get("topics", [])
                        
                        if curr_topic_idx < len(topics):
                            topic = topics[curr_topic_idx]
                            
                            # Generate explanation for this specific topic
                            logger.info("Auto-guiding user to next topic", topic=topic)
                            
                            # Update state to reflect we are teaching this topic
                            state["current_topic"] = topic
                            
                            # Check for cached content
                            from app.models.course import TopicContent
                            
                            cached_content = db.query(TopicContent).filter(
                                TopicContent.course_id == course_id,
                                TopicContent.module_index == curr_mod_idx,
                                TopicContent.topic_index == curr_topic_idx
                            ).first()
                            
                            if cached_content:
                                logger.info("Using cached content", topic=topic)
                                response_text = f"{cached_content.content}\n\n"
                                state["answer"] = response_text
                                state["bot_response"] = response_text
                                state["confidence"] = 1.0
                                state["used_rag"] = False
                                state["completed"] = True
                                return state
                            
                            # Generate explanation
                            explanation = await knowledge_service.answer_question(
                                question=f"Teach the topic '{topic}' from '{module['title']}' in {course.title}. Use structured markdown with headings, examples, and emojis. Do not mention documents.",
                                user_id=user_id,
                                context=context,
                                db=db
                            )
                            
                            # Save generated content to cache
                            try:
                                new_content = TopicContent(
                                    course_id=course_id,
                                    module_index=curr_mod_idx,
                                    topic_index=curr_topic_idx,
                                    topic_name=topic,
                                    content=explanation['answer']
                                )
                                db.add(new_content)
                                db.commit()
                                logger.info("Saved new topic content to cache", topic=topic)
                            except Exception as e:
                                logger.error("Failed to save topic content", error=str(e))
                                # Continue even if save fails
                            
                            # Add guidance wrapper
                            # We don't need to introduce Bindu Miss again if the user just said "yes" to the intro
                            response_text = (
                                f"{explanation['answer']}\n\n"
                            )
                            
                            state["answer"] = response_text
                            state["bot_response"] = response_text
                            state["confidence"] = 1.0
                            state["used_rag"] = explanation["used_rag"]
                            state["completed"] = True
                            return state
        
        # Default behavior: Answer specific question
        result = await knowledge_service.answer_question(
            question=question,
            user_id=user_id,
            context=context,
            db=db,
        )
        
        # Update state with results
        state["answer"] = result["answer"]
        state["bot_response"] = result["answer"]
        state["confidence"] = result["confidence"]
        state["used_rag"] = result["used_rag"]
        state["retrieved_docs"] = result.get("retrieved_docs", [])
        state["evaluation"] = result.get("evaluation", {})
        
        # Mark as completed
        state["completed"] = True
        state["next_agent"] = None
        
        logger.info(
            "Teaching agent completed",
            confidence=result["confidence"],
            used_rag=result["used_rag"],
        )
        
        return state
    
    def _build_context(self, state: AgentState) -> Dict[str, Any]:
        """Build context from state for personalized teaching."""
        context = {}
        
        if state.get("skill_level"):
            context["skill_level"] = state["skill_level"]
        
        if state.get("current_topic"):
            context["current_topic"] = state["current_topic"]
        
        if state.get("user_profile"):
            profile = state["user_profile"]
            if "preferences" in profile:
                context.update(profile["preferences"])
        
        return context


# Global instance
teaching_agent = TeachingAgent()
