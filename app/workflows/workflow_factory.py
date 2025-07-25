"""Workflow factory for creating different types of LangGraph workflows."""

from typing import Dict, Any, Optional, List
from langgraph.graph import StateGraph, END

from app.models.state import WorkflowState
from app.workflows.nodes import (
    conversation_retrieval_node,
    conversation_save_node,
    response_generation_node,
    should_continue_to_response,
    should_route_to_metrics,
    rag_extraction_node,
    metrics_extraction_node,
    planner_node
)
from app.utils.logging import logger


class WorkflowConfig:
    """Configuration for workflow creation."""
    
    def __init__(
        self,
        enable_rag: bool = True,
        enable_metrics: bool = True,
        enable_conversation_history: bool = True,
        enable_conversation_save: bool = True,
        parallel_processing: bool = True,
        conversation_history_limit: int = 10,
        metrics_context_limit: Optional[int] = None,
        metrics_environment: str = "production",
        metrics_tools_config: Optional[Dict[str, Any]] = None,
        workflow_name: str = "default_chat_workflow"
    ):
        self.enable_rag = enable_rag
        self.enable_metrics = enable_metrics
        self.enable_conversation_history = enable_conversation_history
        self.enable_conversation_save = enable_conversation_save
        self.parallel_processing = parallel_processing
        self.conversation_history_limit = conversation_history_limit
        self.metrics_context_limit = metrics_context_limit
        self.metrics_environment = metrics_environment
        self.metrics_tools_config = metrics_tools_config
        self.workflow_name = workflow_name


def create_workflow(config: Optional[WorkflowConfig] = None) -> StateGraph:
    """
    Create a LangGraph workflow based on configuration.
    
    Args:
        config: Workflow configuration. If None, uses default configuration.
        
    Returns:
        Compiled StateGraph workflow
    """
    if config is None:
        config = WorkflowConfig()
    
    logger.info(f"Creating workflow: {config.workflow_name}")
    
    # Create state graph
    workflow = StateGraph(WorkflowState)
    
    # Always add response generation node
    workflow.add_node("response_generation", response_generation_node)
    
    # Conditionally add nodes based on configuration
    if config.enable_conversation_history:
        workflow.add_node("retrieve_history", conversation_retrieval_node)
        workflow.set_entry_point("retrieve_history")
    else:
        # If no conversation history, start with planner node
        workflow.set_entry_point("planner")
    
    # Always add planner node for intelligent routing
    workflow.add_node("planner", planner_node)
    
    if config.enable_rag:
        workflow.add_node("rag_extraction", rag_extraction_node)
    
    if config.enable_metrics:
        workflow.add_node("metrics_extraction", metrics_extraction_node)
    
    if config.enable_conversation_save:
        workflow.add_node("save_conversation", conversation_save_node)
    
    # Define workflow connections
    _add_workflow_edges(workflow, config)
    
    logger.info(f"Workflow {config.workflow_name} created successfully")
    return workflow


def _add_workflow_edges(workflow: StateGraph, config: WorkflowConfig) -> None:
    """Add edges to the workflow based on configuration."""
    
    if config.enable_conversation_history:
        # Start from conversation retrieval, then go to planner
        workflow.add_edge("retrieve_history", "planner")
    else:
        # If no conversation history, planner is the entry point
        pass
    
    # Planner routes to metrics, RAG, or both based on its decision
    if config.enable_rag and config.enable_metrics:
        # Both enabled - use conditional routing from planner
        workflow.add_conditional_edges(
            "planner",
            should_route_to_metrics,
            {
                "metrics_extraction": "metrics_extraction",
                "rag_extraction": "rag_extraction",
                "both": "metrics_extraction"  # Start with metrics, then RAG
            }
        )
        
        # Add edge from metrics to RAG for "both" case
        workflow.add_edge("metrics_extraction", "rag_extraction")
        
        # Only RAG goes to response generation (since it's the last in sequence)
        workflow.add_edge("rag_extraction", "response_generation")
        
    elif config.enable_metrics and not config.enable_rag:
        # Only metrics enabled
        workflow.add_edge("planner", "metrics_extraction")
        workflow.add_edge("metrics_extraction", "response_generation")
        
    elif config.enable_rag and not config.enable_metrics:
        # Only RAG enabled
        workflow.add_edge("planner", "rag_extraction")
        workflow.add_edge("rag_extraction", "response_generation")
        
    else:
        # Neither enabled - go directly to response generation
        workflow.add_edge("planner", "response_generation")
    
    # Handle response generation to save/end
    if config.enable_conversation_save:
        workflow.add_conditional_edges(
            "response_generation",
            should_continue_to_response,
            {
                "response": "save_conversation",
                "save": "save_conversation"
            }
        )
        workflow.add_edge("save_conversation", END)
    else:
        workflow.add_edge("response_generation", END)


def create_minimal_workflow() -> StateGraph:
    """Create a minimal workflow for testing (response generation only)."""
    config = WorkflowConfig(
        enable_rag=False,
        enable_metrics=False,
        enable_conversation_history=False,
        enable_conversation_save=False,
        conversation_history_limit=0,  # No history needed for minimal workflow
        metrics_environment="testing",
        workflow_name="minimal_workflow"
    )
    return create_workflow(config)


def create_rag_only_workflow() -> StateGraph:
    """Create a workflow that only uses RAG (no metrics)."""
    config = WorkflowConfig(
        enable_rag=True,
        enable_metrics=False,
        enable_conversation_history=True,
        enable_conversation_save=True,
        conversation_history_limit=5,  # Lighter history for RAG-focused workflow
        workflow_name="rag_only_workflow"
    )
    return create_workflow(config)


def create_metrics_only_workflow() -> StateGraph:
    """Create a workflow that only uses metrics (no RAG)."""
    config = WorkflowConfig(
        enable_rag=False,
        enable_metrics=True,
        enable_conversation_history=True,
        enable_conversation_save=True,
        conversation_history_limit=15,  # More history for metrics context
        metrics_context_limit=10,  # Use more context for metrics analysis
        metrics_environment="production",
        workflow_name="metrics_only_workflow"
    )
    return create_workflow(config)


def create_sequential_workflow() -> StateGraph:
    """Create a workflow with sequential processing (no parallelism)."""
    config = WorkflowConfig(
        enable_rag=True,
        enable_metrics=True,
        enable_conversation_history=True,
        enable_conversation_save=True,
        parallel_processing=False,
        conversation_history_limit=8,  # Moderate history for debugging
        workflow_name="sequential_workflow"
    )
    return create_workflow(config)


def create_long_context_workflow() -> StateGraph:
    """Create a workflow with extended conversation history for complex conversations."""
    config = WorkflowConfig(
        enable_rag=True,
        enable_metrics=True,
        enable_conversation_history=True,
        enable_conversation_save=True,
        parallel_processing=True,
        conversation_history_limit=25,  # Extended history for complex conversations
        metrics_context_limit=12,  # More metrics context for complex analysis
        workflow_name="long_context_workflow"
    )
    return create_workflow(config)


def create_short_context_workflow() -> StateGraph:
    """Create a workflow with minimal conversation history for quick responses."""
    config = WorkflowConfig(
        enable_rag=True,
        enable_metrics=True,
        enable_conversation_history=True,
        enable_conversation_save=True,
        parallel_processing=True,
        conversation_history_limit=3,  # Minimal history for quick responses
        workflow_name="short_context_workflow"
    )
    return create_workflow(config)


def create_development_workflow() -> StateGraph:
    """Create a development workflow with enhanced metrics tools."""
    config = WorkflowConfig(
        enable_rag=True,
        enable_metrics=True,
        enable_conversation_history=True,
        enable_conversation_save=True,
        parallel_processing=True,
        conversation_history_limit=15,
        metrics_context_limit=8,
        metrics_environment="development",
        metrics_tools_config={
            "max_days_back": 30,
            "max_limit": 25,
            "enable_custom_queries": True,
            "allowed_categories": ["engagement", "revenue", "performance", "satisfaction", "testing"],
            "allowed_metric_names": [
                "daily_active_users", "session_duration", "page_views",
                "monthly_revenue", "conversion_rate", "customer_lifetime_value",
                "response_time", "uptime_percentage", "error_rate",
                "nps_score", "support_rating", "churn_rate",
                "test_metric_1", "test_metric_2"  # Additional test metrics
            ]
        },
        workflow_name="development_workflow"
    )
    return create_workflow(config)


def get_available_workflows() -> Dict[str, callable]:
    """Get a dictionary of available workflow factory functions."""
    return {
        "default": lambda: create_workflow(),
        "minimal": create_minimal_workflow,
        "rag_only": create_rag_only_workflow,
        "metrics_only": create_metrics_only_workflow,
        "sequential": create_sequential_workflow,
        "long_context": create_long_context_workflow,
        "short_context": create_short_context_workflow,
        "development": create_development_workflow
    } 