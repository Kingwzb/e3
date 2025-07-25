"""Orchestration and conditional logic for LangGraph workflow."""

from app.models.state import MultiHopState
from app.utils.logging import logger


def should_continue_to_response(state: MultiHopState) -> str:
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
        user_query = state.get("user_query", "")
        if not user_query.strip():
            logger.warning("No user query found in state")
            return "save"
        
        # All checks passed, proceed to response generation
        return "response"
        
    except Exception as e:
        logger.error(f"Error in conditional routing: {str(e)}")
        # Default to save if there's an error in the conditional logic itself
        return "save"


def should_continue_to_parallel_processing(state: MultiHopState) -> bool:
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


def get_workflow_metadata(state: MultiHopState) -> dict:
    """
    Extract metadata about the current workflow state.
    
    Args:
        state: Current workflow state
        
    Returns:
        Dict containing workflow metadata
    """
    return {
        "request_id": state.get("request_id"),
        "session_id": state.get("session_id"),
        "user_query": state.get("user_query"),
        "subqueries": state.get("subqueries"),
        "detected_docs": state.get("detected_docs"),
        "final_answer_status": "generated" if state.get("final_answer") else "pending"
    }


def should_route_to_metrics(state: MultiHopState) -> str:
    """
    Conditional function to determine routing based on planner node decision.
    
    This function analyzes the planning data from the planner node and determines
    whether to route to metrics extraction, RAG extraction, or both.
    
    Args:
        state: Current workflow state with planning data
        
    Returns:
        String indicating the next node to execute:
        - "metrics_extraction": Only database queries needed
        - "rag_extraction": Only RAG context needed
        - "both": Both database queries and RAG context needed
        - "response_generation": No extraction needed
    """
    try:
        logger.info(f"Routing - Checking planner decision for session: {state['session_id']}")
        
        # Check for subqueries (MultiHopState format)
        subqueries = state.get("subqueries", {})
        detected_docs = state.get("detected_docs", [])
        
        # Determine what's needed based on subqueries
        # Check for database-related subquery keys
        db_related_keys = ["Database", "employee_ratio", "application_snapshot", "statistic", "enabler_csi_snapshots", "employee_tree_archived", "management_segment_tree"]
        needs_database = any(key in subqueries for key in db_related_keys) or any(db_term in key.lower() for key in subqueries.keys() for db_term in ["employee_ratio", "application_snapshot", "statistic", "enabler_csi_snapshots", "employee_tree_archived", "management_segment_tree"])
        needs_rag = len(detected_docs) > 0 or any(key != "Database" and not any(db_term in key.lower() for db_term in ["employee_ratio", "application_snapshot", "statistic", "enabler_csi_snapshots", "employee_tree_archived", "management_segment_tree"]) for key in subqueries.keys())
        
        logger.info(f"Routing - Subqueries analysis: needs_database={needs_database}, needs_rag={needs_rag}")
        logger.info(f"Routing - Subqueries keys: {list(subqueries.keys())}")
        logger.info(f"Routing - Detected docs: {detected_docs}")
        
        # Fallback checks for backward compatibility
        planning_data = state.get("planning_data", {})
        trigger_metrics = planning_data.get("trigger_metrics", False)
        trigger_rag = planning_data.get("trigger_rag", True)  # Default to True for RAG
        
        logger.info(f"Routing - Fallback planning data: trigger_metrics={trigger_metrics}, trigger_rag={trigger_rag}")
        
        # Use subqueries as primary decision, fallback to planning_data
        if needs_database and needs_rag:
            logger.info("Planner determined both metrics and RAG extraction are needed")
            return "both"
        elif needs_database:
            logger.info("Planner determined only metrics extraction is needed")
            return "metrics_extraction"
        elif needs_rag:
            logger.info("Planner determined only RAG extraction is needed")
            return "rag_extraction"
        elif trigger_metrics and trigger_rag:
            logger.info("Fallback: Planning data indicates both metrics and RAG needed")
            return "both"
        elif trigger_metrics:
            logger.info("Fallback: Planning data indicates only metrics needed")
            return "metrics_extraction"
        elif trigger_rag:
            logger.info("Fallback: Planning data indicates only RAG needed")
            return "rag_extraction"
        else:
            logger.info("Planner determined no extraction is needed")
            return "response_generation"
            
    except Exception as e:
        logger.error(f"Error in planner routing: {str(e)}")
        # Default to RAG if there's an error
        return "rag_extraction" 