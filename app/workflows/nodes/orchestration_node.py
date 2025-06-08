"""Orchestration and conditional logic for LangGraph workflow."""

from app.models.state import WorkflowState
from app.utils.logging import logger


def should_continue_to_response(state: WorkflowState) -> str:
    """
    Conditional function to determine workflow routing.
    
    This function decides whether to:
    - Continue to response generation if everything is working
    - Skip to save if there are errors that prevent response generation
    
    Args:
        state: Current workflow state
        
    Returns:
        String indicating the next node to execute
    """
    try:
        # Check if there are any critical errors that prevent response generation
        error = state.get("error")
        
        if error:
            logger.warning(f"Error detected in workflow: {error}")
            # Even with errors, we might still have some response to save
            return "save"
        
        # Check if we have the minimum required data for response generation
        current_message = state.get("current_message", "")
        if not current_message.strip():
            logger.warning("No current message found in state")
            return "save"
        
        # All checks passed, proceed to response generation
        return "response"
        
    except Exception as e:
        logger.error(f"Error in conditional routing: {str(e)}")
        # Default to save if there's an error in the conditional logic itself
        return "save"


def should_continue_to_parallel_processing(state: WorkflowState) -> bool:
    """
    Conditional function to determine if parallel processing should continue.
    
    This can be used to implement more sophisticated routing logic
    based on the message content or conversation state.
    
    Args:
        state: Current workflow state
        
    Returns:
        Boolean indicating whether to proceed with parallel processing
    """
    try:
        current_message = state.get("current_message", "")
        
        # Basic validation
        if not current_message.strip():
            logger.warning("Empty message, skipping parallel processing")
            return False
        
        # Could add more sophisticated logic here:
        # - Check message length
        # - Analyze message content
        # - Check user permissions
        # - Rate limiting logic
        
        return True
        
    except Exception as e:
        logger.error(f"Error in parallel processing conditional: {str(e)}")
        return False


def get_workflow_metadata(state: WorkflowState) -> dict:
    """
    Extract metadata about the current workflow state.
    
    This is useful for monitoring and debugging workflow execution.
    
    Args:
        state: Current workflow state
        
    Returns:
        Dictionary with workflow metadata
    """
    try:
        return {
            "conversation_id": state.get("conversation_id", "unknown"),
            "has_rag_context": bool(state.get("rag_context")),
            "has_metrics_data": bool(state.get("metrics_data")),
            "conversation_length": len(state.get("messages", [])),
            "has_error": bool(state.get("error")),
            "has_final_response": bool(state.get("final_response")),
            "message_length": len(state.get("current_message", "")),
        }
    except Exception as e:
        logger.error(f"Error extracting workflow metadata: {str(e)}")
        return {"error": str(e)} 