"""Chat workflow management for the AI chat agent."""

from typing import Dict, Any, Optional
from langgraph.graph import StateGraph

from app.models.state import MultiHopState
from app.workflows.workflow_factory import create_workflow, WorkflowConfig
from app.workflows.nodes.orchestration_node import get_workflow_metadata
from app.utils.logging import logger


def create_chat_workflow(config: Optional[WorkflowConfig] = None) -> StateGraph:
    """
    Create a chat workflow with the specified configuration.
    
    Args:
        config: Workflow configuration. If None, uses default configuration.
        
    Returns:
        Compiled StateGraph workflow
    """
    if config is None:
        config = WorkflowConfig()
    
    return create_workflow(config)


class ChatWorkflowManager:
    """Manager class for chat workflow operations."""
    
    def __init__(self, workflow_config: Optional[WorkflowConfig] = None):
        """
        Initialize the workflow manager.
        
        Args:
            workflow_config: Configuration for workflow creation. If None, uses default.
        """
        self.workflow_config = workflow_config or WorkflowConfig()
        self.workflow = create_chat_workflow(self.workflow_config)
        self.compiled_workflow = self.workflow.compile()
        
        logger.info(f"ChatWorkflowManager initialized with config: {self.workflow_config.workflow_name}")
    
    async def process_message(
        self, 
        message: str, 
        conversation_id: str
    ) -> Dict[str, Any]:
        """
        Process a user message through the complete workflow.
        
        Args:
            message: User's message
            conversation_id: Conversation identifier (used as session_id)
            
        Returns:
            Dict containing the response and metadata
        """
        try:
            logger.info(f"Starting workflow for conversation: {conversation_id}")
            
            # Initialize state with MultiHopState
            initial_state = MultiHopState(
                request_id=f"req_{conversation_id}_{int(__import__('time').time())}",
                session_id=conversation_id,  # Use conversation_id as session_id
                user_query=message,
                formatted_user_query="",
                subqueries={},
                retrieved_docs={},
                db_schema="",
                subquery_responses={},
                final_answer={},
                detected_docs=[],
                conversation_history="",
                conversation_history_limit=self.workflow_config.conversation_history_limit,
                metrics_context_limit=self.workflow_config.metrics_context_limit,
                metrics_environment=self.workflow_config.metrics_environment,
                metrics_tools_config=self.workflow_config.metrics_tools_config
            )
            
            # Execute workflow
            final_state = await self.compiled_workflow.ainvoke(initial_state)
            
            # Extract results
            final_answer = final_state.get("final_answer", {})
            response = final_answer.get("response", "I apologize, but I couldn't process your request.")
            error = final_state.get("error")
            
            # Get comprehensive workflow metadata
            workflow_metadata = get_workflow_metadata(final_state)
            workflow_metadata.update({
                "error": error,
                "workflow_completed": True
            })
            
            result = {
                "response": response,
                "conversation_id": conversation_id,
                "success": error is None,
                "metadata": workflow_metadata
            }
            
            if error:
                logger.error(f"Workflow completed with error: {error}")
            else:
                logger.info(f"Workflow completed successfully for conversation: {conversation_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}")
            return {
                "response": "I apologize, but I encountered an error while processing your request.",
                "conversation_id": conversation_id,
                "success": False,
                "metadata": {
                    "error": str(e),
                    "workflow_completed": False,
                    "has_rag_context": False,
                    "has_metrics_data": False,
                    "conversation_length": 0,
                    "has_error": True,
                    "has_final_response": False,
                    "message_length": len(message)
                }
            }


# Global workflow manager instance
chat_workflow_manager = ChatWorkflowManager() 