"""
LLM service for interacting with language models (Ollama or OpenAI).
"""
from typing import Optional, Dict, Any, List
from langchain_community.llms import Ollama
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMService:
    """Service for interacting with language models."""
    
    def __init__(self):
        """Initialize the LLM based on configuration."""
        self.provider = settings.LLM_PROVIDER
        self.model_name = settings.LLM_MODEL
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.LLM_MAX_TOKENS
        
        # Initialize the appropriate LLM
        if self.provider == "ollama":
            self.llm = Ollama(
                model=self.model_name,
                base_url=settings.OLLAMA_BASE_URL,
                temperature=self.temperature,
            )
            logger.info("Initialized Ollama LLM", model=self.model_name)
        elif self.provider == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError("OpenAI API key not configured")
            self.llm = ChatOpenAI(
                model=self.model_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                openai_api_key=settings.OPENAI_API_KEY,
            )
            logger.info("Initialized OpenAI LLM", model=self.model_name)
        elif self.provider == "gemini":
            if not settings.GOOGLE_API_KEY:
                raise ValueError("Google API key not configured")
            self.llm = ChatGoogleGenerativeAI(
                model=self.model_name,
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
                google_api_key=settings.GOOGLE_API_KEY,
            )
            logger.info("Initialized Gemini LLM", model=self.model_name)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
    
    async def generate(
        self,
        prompt: str,
        context: Optional[str] = None,
        system_message: Optional[str] = None,
        raw_prompt: bool = False,
    ) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The user's prompt/question
            context: Optional context from RAG
            system_message: Optional system message to guide behavior
            raw_prompt: If True, bypasses the standard QA prompt formatting
            
        Returns:
            LLM generated response
        """
        try:
            # Build the full prompt
            if raw_prompt:
                # For raw prompts, just prepend system message if exists
                if system_message:
                    full_prompt = f"{system_message}\n\n{prompt}"
                else:
                    full_prompt = prompt
            else:
                full_prompt = self._build_prompt(prompt, context, system_message)
            
            # Generate response
            response = await self.llm.ainvoke(full_prompt)
            
            # Extract text from response
            if isinstance(response, str):
                return response
            elif hasattr(response, "content"):
                return response.content
            else:
                return str(response)
                
        except Exception as e:
            logger.error("LLM generation failed", error=str(e))
            raise
    
    def _build_prompt(
        self,
        prompt: str,
        context: Optional[str] = None,
        system_message: Optional[str] = None,
    ) -> str:
        """Build the complete prompt with context and system message."""
        parts = []
        
        # Add system message
        if system_message:
            parts.append(f"SYSTEM: {system_message}\n")
        
        # Add context from RAG
        if context:
            parts.append(f"CONTEXT:\n{context}\n")
            parts.append("Use the above context to answer the question. If the context doesn't contain relevant information, say so clearly.\n")
        
        # Add the user's question
        parts.append(f"QUESTION: {prompt}\n")
        parts.append("ANSWER:")
        
        return "\n".join(parts)
    
    async def evaluate_confidence(
        self,
        question: str,
        answer: str,
    ) -> Dict[str, Any]:
        """
        Evaluate the confidence and completeness of an answer.
        
        Args:
            question: The original question
            answer: The generated answer
            
        Returns:
            Dictionary with confidence score and analysis
        """
        evaluation_prompt = f"""
You are a critical evaluator. Analyze the following question and answer pair.

QUESTION: {question}

ANSWER: {answer}

Evaluate this answer and provide:
1. Confidence score (0-100): How confident are you that this answer is correct and complete?
2. Completeness: Is the answer thorough and complete?
3. Accuracy indicators: Any signs of uncertainty or potential inaccuracies?

Respond in this exact format:
CONFIDENCE: [0-100]
COMPLETENESS: [complete/partial/incomplete]
ISSUES: [list any concerns or uncertainties]
IS_GUESS: [true/false]
"""
        
        try:
            evaluation = await self.llm.ainvoke(evaluation_prompt)
            
            # Parse the evaluation
            result = self._parse_evaluation(str(evaluation))
            
            logger.info(
                "Confidence evaluation completed",
                question=question[:50],
                confidence=result["confidence"]
            )
            
            return result
            
        except Exception as e:
            logger.error("Confidence evaluation failed", error=str(e))
            # Return low confidence if evaluation fails
            return {
                "confidence": 30,
                "completeness": "unknown",
                "issues": ["Evaluation failed"],
                "is_guess": True,
            }
    
    def _parse_evaluation(self, evaluation_text: str) -> Dict[str, Any]:
        """Parse the evaluation response into structured data."""
        result = {
            "confidence": 50,  # Default medium confidence
            "completeness": "unknown",
            "issues": [],
            "is_guess": True,
        }
        
        lines = evaluation_text.split("\n")
        for line in lines:
            line = line.strip()
            
            if line.startswith("CONFIDENCE:"):
                try:
                    score = int(line.split(":")[1].strip())
                    result["confidence"] = max(0, min(100, score))
                except ValueError:
                    pass
            
            elif line.startswith("COMPLETENESS:"):
                completeness = line.split(":")[1].strip().lower()
                result["completeness"] = completeness
            
            elif line.startswith("ISSUES:"):
                issues = line.split(":", 1)[1].strip()
                if issues and issues.lower() != "none":
                    result["issues"].append(issues)
            
            elif line.startswith("IS_GUESS:"):
                is_guess = line.split(":")[1].strip().lower()
                result["is_guess"] = is_guess == "true"
        
        return result


# Global instance
llm_service = LLMService()
