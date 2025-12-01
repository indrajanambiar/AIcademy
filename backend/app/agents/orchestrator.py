"""
LangGraph orchestrator for the multi-agent workflow.
"""
from typing import Dict, Any
from datetime import datetime

from langgraph.graph import StateGraph, END
from app.agents.state import AgentState, Intent
from app.agents.intent_agent import intent_agent
from app.agents.teaching_agent import teaching_agent
from app.agents.quiz_agent import quiz_agent
from app.agents.planning_agent import planning_agent
from app.agents.assessment_agent import assessment_agent
from app.core.logging import get_logger

logger = get_logger(__name__)


class AgentOrchestrator:
    """Orchestrates the multi-agent workflow using LangGraph."""
    
    def __init__(self):
        """Initialize the workflow graph."""
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        # Create the graph
        workflow = StateGraph(AgentState)
        
        # Add nodes (agents)
        workflow.add_node("intent_agent", self._intent_node)
        workflow.add_node("teaching_agent", self._teaching_node)
        workflow.add_node("quiz_agent", self._quiz_node)
        workflow.add_node("planning_agent", self._planning_node)
        workflow.add_node("assessment_agent", self._assessment_node)
        
        # Set entry point
        workflow.set_entry_point("intent_agent")
        
        # Add conditional edges based on intent
        workflow.add_conditional_edges(
            "intent_agent",
            self._route_intent,
            {
                "teaching_agent": "teaching_agent",
                "quiz_agent": "quiz_agent",
                "planning_agent": "planning_agent",
                "assessment_agent": "assessment_agent",
            }
        )
        
        # All agents end
        workflow.add_edge("teaching_agent", END)
        workflow.add_edge("quiz_agent", END)
        workflow.add_edge("planning_agent", END)
        workflow.add_edge("assessment_agent", END)
        
        # Compile the graph
        return workflow.compile()
    
    async def _intent_node(self, state: AgentState) -> AgentState:
        """Intent detection node."""
        logger.info("Executing intent agent")
        return await intent_agent(state)
    
    async def _teaching_node(self, state: AgentState) -> AgentState:
        """Teaching node."""
        logger.info("Executing teaching agent")
        return await teaching_agent(state)
    
    async def _quiz_node(self, state: AgentState) -> AgentState:
        """Quiz generation node."""
        logger.info("Executing quiz agent")
        return await quiz_agent(state)
    
    async def _planning_node(self, state: AgentState) -> AgentState:
        """Roadmap planning node."""
        logger.info("Executing planning agent")
        return await planning_agent(state)

    async def _assessment_node(self, state: AgentState) -> AgentState:
        """Assessment node."""
        logger.info("Executing assessment agent")
        return await assessment_agent(state)
    
    def _route_intent(self, state: AgentState) -> str:
        """Route to appropriate agent based on intent."""
        # Check for active onboarding
        onboarding_step = state.get("metadata", {}).get("onboarding_step")
        if onboarding_step and onboarding_step != "completed":
            logger.info("Continuing onboarding flow", step=onboarding_step)
            return "assessment_agent"
            
        # Start onboarding for new LEARN requests with a topic
        if state["intent"] == Intent.LEARN and state.get("current_topic"):
            logger.info("Starting onboarding for new topic")
            # Force reset of onboarding step to ensure AssessmentAgent starts from beginning
            if "metadata" in state:
                state["metadata"]["onboarding_step"] = None
            return "assessment_agent"

        next_agent = state.get("next_agent", "teaching_agent")
        logger.info("Routing to agent", next_agent=next_agent)
        return next_agent
    
    async def process_message(
        self,
        message: str,
        user_id: str = None,
        user_profile: Dict[str, Any] = None,
        context: Dict[str, Any] = None,
        db: Any = None,
    ) -> Dict[str, Any]:
        """
        Process a user message through the agent workflow.
        
        Args:
            message: User's message
            user_id: Optional user ID
            user_profile: Optional user profile data
            context: Optional additional context
            db: Optional database session
            
        Returns:
            Response dictionary with bot reply and metadata
        """
        logger.info(
            "Processing message",
            message=message[:50],
            user_id=user_id,
        )
        
        # Initialize state
        initial_state: AgentState = {
            "user_message": message,
            "user_id": user_id,
            "user_profile": user_profile or {},
            "db": db,
            "bot_response": "",
            "intent": Intent.UNKNOWN,
            "confidence": 0.0,
            "used_rag": False,
            "retrieved_docs": [],
            "evaluation": {},
            "skill_level": "beginner",
            "quiz_questions": [],
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": context or {},
            "completed": False,
        }
        
        # Heuristic: If user says "no" (no doubts), route to quiz agent
        if message.strip().lower() in ["no", "no doubt", "no doubts", "nope", "none", "clear", "all clear"]:
             # We rely on the intent agent or default routing, but we can hint the intent here
             # However, IntentAgent is better suited. Let's leave it to IntentAgent or just let it fall through.
             # Actually, let's force the intent if we are in a "teaching flow" context.
             # Since we don't have explicit "teaching flow" state persistence easily accessible here without DB lookup of previous msg,
             # we will let the IntentAgent handle it or add a specific check in IntentAgent.
             pass
        
        # Add context data
        if context:
            if "skill_level" in context:
                initial_state["skill_level"] = context["skill_level"]
            if "current_topic" in context:
                initial_state["current_topic"] = context["current_topic"]
            if "course_id" in context:
                initial_state["current_course_id"] = context["course_id"]
        
        try:
            # Run the workflow
            final_state = await self.graph.ainvoke(initial_state)
            
            # Extract response
            response = {
                "reply": final_state.get("bot_response", "I'm not sure how to respond to that."),
                "intent": final_state.get("intent", Intent.UNKNOWN),
                "confidence": final_state.get("confidence", 0),
                "used_rag": final_state.get("used_rag", False),
                "topic": final_state.get("current_topic"),
                "metadata": {
                    "timestamp": final_state.get("timestamp"),
                    "evaluation": final_state.get("evaluation", {}),
                    "quiz_questions": final_state.get("quiz_questions", []),
                    "quiz_results": final_state.get("quiz_results"),
                    "roadmap": final_state.get("generated_roadmap"),
                    "onboarding_step": final_state.get("metadata", {}).get("onboarding_step"),
                },
            }
            
            logger.info(
                "Message processed successfully",
                intent=response["intent"],
                confidence=response["confidence"],
            )
            
            return response
            
        except Exception as e:
            logger.error("Workflow execution failed", error=str(e))
            return {
                "reply": "I apologize, but I encountered an error processing your request. Please try again.",
                "intent": Intent.UNKNOWN,
                "confidence": 0,
                "used_rag": False,
                "metadata": {"error": str(e)},
            }


# Global instance
orchestrator = AgentOrchestrator()
