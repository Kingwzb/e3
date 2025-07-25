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


def should_route_to_metrics(state: WorkflowState) -> str:
    """
    Conditional function to determine routing after planner node.
    
    This function routes to metrics extraction, RAG, or both based on
    the planner node's decision.
    
    Args:
        state: Current workflow state with planning data
        
    Returns:
        String indicating the next node to execute ("metrics_extraction", "rag_extraction", or "both")
    """
    try:
        # Check if planner has determined we need metrics extraction
        trigger_metrics = state.get("trigger_metrics", False)
        trigger_rag = state.get("trigger_rag", True)  # Default to True for RAG
        planning_data = state.get("planning_data", {})
        
        # Also check planning_data for triggers (fallback)
        if not trigger_metrics:
            trigger_metrics = planning_data.get("trigger_metrics", False)
        if not trigger_rag:
            trigger_rag = planning_data.get("trigger_rag", True)
        
        # Additional fallback: check needs_metrics and needs_rag
        if not trigger_metrics:
            trigger_metrics = state.get("needs_metrics", False)
        if not trigger_rag:
            trigger_rag = state.get("needs_rag", True)
        
        # Final fallback: check planning_data.needs_database_query
        if not trigger_metrics and planning_data.get("needs_database_query", False):
            trigger_metrics = True
        
        # Final fallback: if we have planning data with needs_database_query=True, force trigger_metrics=True
        logger.info(f"Routing - Checking final fallback: state={state} needs_database_query={planning_data.get('needs_database_query', False)}, confidence={planning_data.get('confidence', 0.0)}")
        if planning_data.get("needs_database_query", False) and planning_data.get("confidence", 0.0) > 0.5:
            trigger_metrics = True
            logger.info(f"Routing - Forcing trigger_metrics=True based on planning data")
        else:
            logger.info(f"Routing - Final fallback condition not met")
        
        # Additional fallback: check direct state values
        direct_needs_query = state.get("needs_database_query", False)
        direct_confidence = state.get("confidence", 0.0)
        logger.info(f"Routing - Checking direct values: needs_database_query={direct_needs_query}, confidence={direct_confidence}")
        if direct_needs_query and direct_confidence > 0.5:
            trigger_metrics = True
            logger.info(f"Routing - Forcing trigger_metrics=True based on direct state values")
        
        # Final aggressive fallback: if we have any indication of database query need, trigger metrics
        # This is a last resort to ensure database queries are handled
        if not trigger_metrics:
            # Check if the message contains database-related keywords
            current_message = state.get("current_message", "").lower()
            db_keywords = ["database", "db", "query", "soeid", "employee", "list", "get", "find", "show"]
            has_db_keywords = any(keyword in current_message for keyword in db_keywords)
            
            if has_db_keywords:
                trigger_metrics = True
                logger.info(f"Routing - Forcing trigger_metrics=True based on message keywords: {current_message}")
        
        # Debug logging
        logger.info(f"Routing decision - trigger_metrics: {trigger_metrics}, trigger_rag: {trigger_rag}")
        logger.info(f"Planning data triggers - trigger_metrics: {planning_data.get('trigger_metrics', False)}, trigger_rag: {planning_data.get('trigger_rag', True)}")
        logger.info(f"Needs fallback - needs_metrics: {state.get('needs_metrics', False)}, needs_rag: {state.get('needs_rag', True)}")
        logger.info(f"Database query needed: {planning_data.get('needs_database_query', False)}")
        logger.info(f"Planning data content: {planning_data}")
        
        # Determine routing based on what's needed
        if trigger_metrics and trigger_rag:
            logger.info("Planner determined both metrics and RAG extraction are needed")
            return "both"
        elif trigger_metrics:
            logger.info("Planner determined only metrics extraction is needed")
            return "metrics_extraction"
        elif trigger_rag:
            logger.info("Planner determined only RAG extraction is needed")
            return "rag_extraction"
        else:
            logger.info("Planner determined no extraction is needed")
            return "response_generation"
            
    except Exception as e:
        logger.error(f"Error in planner routing: {str(e)}")
        # Default to RAG if there's an error
        return "rag_extraction" 