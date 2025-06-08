"""Main chat workflow orchestrating RAG and metrics agents using LangGraph."""

from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END

from app.models.state import WorkflowState
from app.workflows.nodes import (
    conversation_retrieval_node,
    conversation_save_node,
    response_generation_node,
    should_continue_to_response,
    rag_extraction_node,
    metrics_extraction_node
)
from app.workflows.nodes.orchestration_node import get_workflow_metadata
from app.workflows.workflow_factory import create_workflow, WorkflowConfig
from app.utils.logging import logger


# All node implementations have been moved to separate files in app/workflows/nodes/


def create_chat_workflow(config: Optional[WorkflowConfig] = None) -> StateGraph:
    """
    Create the LangGraph workflow for chat processing using the workflow factory.
    
    Args:
        config: Optional workflow configuration. If None, uses default configuration.
    
    Returns:
        StateGraph workflow (not compiled)
    """
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
            conversation_id: Conversation identifier
            
        Returns:
            Dict containing the response and metadata
        """
        try:
            logger.info(f"Starting workflow for conversation: {conversation_id}")
            
            # Initialize state
            initial_state = WorkflowState(
                conversation_id=conversation_id,
                current_message=message,
                messages=[],
                rag_context=None,
                metrics_data=None,
                final_response=None,
                error=None,
                conversation_history_limit=self.workflow_config.conversation_history_limit,
                metrics_context_limit=self.workflow_config.metrics_context_limit,
                metrics_environment=self.workflow_config.metrics_environment,
                metrics_tools_config=self.workflow_config.metrics_tools_config
            )
            
            # Execute workflow
            final_state = await self.compiled_workflow.ainvoke(initial_state)
            
            # Extract results
            response = final_state.get("final_response", "I apologize, but I couldn't process your request.")
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