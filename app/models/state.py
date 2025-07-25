"""LangGraph state models for workflow management."""

from typing import List, Dict, Any, Optional, TypedDict, Union
from pydantic import BaseModel, Field

from app.models.chat import Message


class WorkflowState(TypedDict):
    """LangGraph workflow state."""
    conversation_id: str
    current_message: str
    messages: List[Dict[str, str]]  # Conversation history
    rag_context: Optional[str]
    metrics_data: Optional[Dict[str, Any]]
    final_response: Optional[str]
    error: Optional[str]
    
    # Planning and routing fields (set by planner node)
    trigger_metrics: Optional[bool]
    trigger_rag: Optional[bool]
    needs_metrics: Optional[bool]
    needs_rag: Optional[bool]
    needs_database_query: Optional[bool]
    confidence: Optional[float]
    planning_data: Optional[Dict[str, Any]]
    
    # Configuration parameters (optional)
    conversation_history_limit: Optional[int]  # Number of previous messages to retrieve
    metrics_context_limit: Optional[int]  # Number of messages to use for metrics context
    metrics_environment: Optional[str]  # Environment for metrics tools (development, testing, production)
    metrics_tools_config: Optional[Dict[str, Any]]  # Custom configuration for metrics tools


class MultiHopState(TypedDict):
    """Multi-hop reasoning workflow state."""
    request_id: str
    session_id: str
    user_query: str
    formatted_user_query: str
    conversation_history: str  # Conversation history as formatted string
    subqueries: Dict[str, List[str]]  # Document/DB -> List of queries
    retrieved_docs: Dict[str, Dict[str, List]]  # Document/DB -> Retrieved content
    db_schema: str
    subquery_responses: Dict[str, Dict]  # Query -> Response
    final_answer: Dict[str, Any]
    detected_docs: List[str]  # List of detected relevant RAG documents


class RAGResult(BaseModel):
    """RAG extraction result."""
    context: str = Field(..., description="Retrieved context from vector database")
    sources: List[Union[str, Dict[str, Any]]] = Field(default_factory=list, description="Source documents with metadata")
    confidence_score: float = Field(default=0.0, description="Confidence score")


class MetricsResult(BaseModel):
    """Metrics extraction result."""
    data: Dict[str, Any] = Field(..., description="Extracted metrics data")
    query_used: str = Field(..., description="SQL query that was executed")
    execution_time: float = Field(..., description="Query execution time in seconds") 