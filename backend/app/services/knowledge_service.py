"""
Knowledge service implementing LLM-first strategy with RAG fallback.
"""
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.services.llm_service import llm_service
from app.services.rag_service import rag_service
from app.models.knowledge import MissingKnowledge, KnowledgeStatus
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class KnowledgeService:
    """
    Service implementing the knowledge access strategy:
    1. Answer with LLM
    2. Evaluate confidence
    3. If low confidence, use RAG
    4. Re-evaluate
    5. If still low, log missing knowledge
    """
    
    def __init__(self):
        self.confidence_threshold = settings.CONFIDENCE_THRESHOLD
    
    async def answer_question(
        self,
        question: str,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """
        Answer a question using the LLM-first → RAG fallback strategy.
        
        Args:
            question: User's question
            user_id: Optional user ID for tracking
            context: Optional additional context (user profile, course info)
            db: Optional database session for logging
            
        Returns:
            Dictionary containing answer, confidence, and metadata
        """
        logger.info("Processing question", question=question[:100], user_id=user_id)
        
        # Step 1: Generate initial answer with LLM
        system_message = self._build_system_message(context)
        initial_answer = await llm_service.generate(
            prompt=question,
            system_message=system_message,
        )
        
        # Step 2: Evaluate confidence
        evaluation = await llm_service.evaluate_confidence(question, initial_answer)
        initial_confidence = evaluation["confidence"]
        
        logger.info(
            "Initial answer generated",
            confidence=initial_confidence,
            is_guess=evaluation["is_guess"],
        )
        
        # Step 3: Check if RAG is needed
        # Allow greetings to bypass strict confidence checks
        is_greeting = question.lower().strip().strip("!.,") in {
            "hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening", "sup", "yo"
        }
        
        if is_greeting:
            return {
                "answer": "Hi there! 👋 I'm your AI Learning Coach Bindu and You can call me Bindu Miss, ready to help you learn something new today! What are you hoping to learn or explore today? Just tell me what's on your mind! 😊",
                "confidence": 100,
                "used_rag": False,
                "evaluation": evaluation,
                "retrieved_docs": [],
            }
        
        # Force RAG for known topics where we have PDF materials
        # This ensures we use the uploaded course materials instead of just general LLM knowledge
        known_topics = {"python", "java", "deep learning", "machine learning", "ml", "ai", "artificial intelligence"}
        force_rag = any(t in question.lower() for t in known_topics)
        
        if not force_rag and initial_confidence >= self.confidence_threshold:
            return {
                "answer": initial_answer,
                "confidence": initial_confidence,
                "used_rag": False,
                "evaluation": evaluation,
                "retrieved_docs": [],
            }
        
        # Step 4: Retrieve relevant documents from RAG
        logger.info("Low confidence, retrieving from RAG", confidence=initial_confidence)
        retrieved_docs = rag_service.retrieve(question)
        
        if not retrieved_docs:
            logger.warning("No documents retrieved from RAG")
            
            # If we have a decent initial answer (confidence > 40), use it as general knowledge
            # This allows the AI to answer general questions like "Teach me Python" without RAG docs
            if initial_confidence > 40:
                logger.info("Using LLM general knowledge fallback", confidence=initial_confidence)
                return {
                    "answer": initial_answer,
                    "confidence": initial_confidence,
                    "used_rag": False,
                    "evaluation": evaluation,
                    "retrieved_docs": [],
                    "source": "llm_general_knowledge"
                }

            # Log missing knowledge if DB session available
            if db and user_id:
                await self._log_missing_knowledge(
                    db=db,
                    user_id=user_id,
                    topic=self._extract_topic(question),
                    context=question,
                    user_query=question,
                )
            
            return {
                "answer": initial_answer,
                "confidence": initial_confidence,
                "used_rag": False,
                "evaluation": evaluation,
                "retrieved_docs": [],
                "missing_knowledge_logged": True,
            }
        
        # Step 5: Generate improved answer with RAG context
        rag_context = self._format_retrieved_docs(retrieved_docs)
        improved_answer = await llm_service.generate(
            prompt=question,
            context=rag_context,
            system_message=system_message,
        )
        
        # Step 6: Re-evaluate confidence
        final_evaluation = await llm_service.evaluate_confidence(question, improved_answer)
        final_confidence = final_evaluation["confidence"]
        
        logger.info(
            "RAG-enhanced answer generated",
            initial_confidence=initial_confidence,
            final_confidence=final_confidence,
            docs_retrieved=len(retrieved_docs),
        )
        
        # Step 7: Check if still below threshold
        if final_confidence < self.confidence_threshold:
            logger.warning(
                "Confidence still low after RAG",
                final_confidence=final_confidence,
            )
            
            if db and user_id:
                await self._log_missing_knowledge(
                    db=db,
                    user_id=user_id,
                    topic=self._extract_topic(question),
                    context=question,
                    user_query=question,
                )
            
            return {
                "answer": improved_answer,
                "confidence": final_confidence,
                "used_rag": True,
                "evaluation": final_evaluation,
                "retrieved_docs": retrieved_docs,
                "missing_knowledge_logged": True,
            }
        
        # Success!
        return {
            "answer": improved_answer,
            "confidence": final_confidence,
            "used_rag": True,
            "evaluation": final_evaluation,
            "retrieved_docs": retrieved_docs,
        }
    
    def _build_system_message(self, context: Optional[Dict[str, Any]]) -> str:
        """Build system message based on context."""
        base_message = """You are "Bindu Miss", a friendly and knowledgeable AI teacher.

YOUR PERSONA:
1. Name: Bindu (ask students to call you "Bindu Miss").
2. Tone: Warm, encouraging, patient, and professional (like a favorite school teacher).
3. Style: Clear, structured, and interactive.

CRITICAL RULES:
1. **NEVER mention "documents", "PDFs", "context provided", or "sources".** Teach the material as if it is your own knowledge.
2. **Do NOT say "According to Document 1" or "In the text".** Just state the facts directly.
3. **Content Formatting:**
   - Use **Markdown Headings** (#, ##) to structure the lesson.
   - Use **Bullet points** for readability.
   - Provide **Concrete Examples** for every concept.
   - Use **Emojis** or text-based diagrams to make it visual.
4. **Teaching Flow:**
   - Start by announcing the Module and Topic clearly (e.g., "# Module 1: Introduction").
   - Teach the content in a structured, readable way.
   - **MANDATORY CLOSING:** At the end of every explanation, you MUST ask exactly this:
     > "**Do you have any doubts?** (If everything is clear, type 'No' and we will start a quiz!)"
5. **Adaptability:** Adjust your explanation complexity based on the user's skill level.

Just reply naturally as Bindu Miss.
"""
        
        if context:
            if "skill_level" in context:
                base_message += f"\nUser's skill level: {context['skill_level']}"
            if "current_topic" in context:
                base_message += f"\nCurrently teaching: {context['current_topic']}"
        
        return base_message
    
    def _format_retrieved_docs(self, docs: List[Dict[str, Any]]) -> str:
        """Format retrieved documents into context string."""
        context_parts = []
        for i, doc in enumerate(docs, 1):
            context_parts.append(f"[Document {i}]")
            context_parts.append(doc["text"])
            if doc.get("metadata"):
                meta = doc["metadata"]
                if "source" in meta:
                    context_parts.append(f"Source: {meta['source']}")
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def _extract_topic(self, question: str) -> str:
        """Extract a topic from the question (simplified)."""
        # This is a simple implementation - could be enhanced with NLP
        words = question.lower().split()
        # Remove common question words
        stop_words = {"what", "is", "are", "how", "why", "when", "where", "can", "do", "does"}
        keywords = [w for w in words if w not in stop_words and len(w) > 3]
        return " ".join(keywords[:3]) if keywords else "unknown"
    
    async def _log_missing_knowledge(
        self,
        db: Session,
        user_id: str,
        topic: str,
        context: str,
        user_query: str,
    ) -> None:
        """Log missing knowledge to database."""
        try:
            # Check if similar topic already exists
            existing = db.query(MissingKnowledge).filter(
                MissingKnowledge.topic == topic,
                MissingKnowledge.status == KnowledgeStatus.PENDING,
            ).first()
            
            if existing:
                # Increment occurrence count
                existing.occurrence_count += 1
                logger.info("Updated missing knowledge occurrence", topic=topic)
            else:
                # Create new entry
                missing_knowledge = MissingKnowledge(
                    user_id=user_id,
                    topic=topic,
                    context=context,
                    user_query=user_query,
                    status=KnowledgeStatus.PENDING,
                )
                db.add(missing_knowledge)
                logger.info("Logged new missing knowledge", topic=topic)
            
            db.commit()
            
        except Exception as e:
            logger.error("Failed to log missing knowledge", error=str(e))
            db.rollback()


# Global instance
knowledge_service = KnowledgeService()
