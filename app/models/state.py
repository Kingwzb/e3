"""LangGraph state models for workflow management."""

from typing import List, Dict, Any, Optional, TypedDict
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
    
    # Configuration parameters (optional)
    conversation_history_limit: Optional[int]  # Number of previous messages to retrieve
    metrics_context_limit: Optional[int]  # Number of messages to use for metrics context
    metrics_environment: Optional[str]  # Environment for metrics tools (development, testing, production)
    metrics_tools_config: Optional[Dict[str, Any]]  # Custom configuration for metrics tools


class RAGResult(BaseModel):
    """RAG extraction result."""
    context: str = Field(..., description="Retrieved context from vector database")
    sources: List[str] = Field(default_factory=list, description="Source documents")
    confidence_score: float = Field(default=0.0, description="Confidence score")


class MetricsResult(BaseModel):
    """Metrics extraction result."""
    data: Dict[str, Any] = Field(..., description="Extracted metrics data")
    query_used: str = Field(..., description="SQL query that was executed")
    execution_time: float = Field(..., description="Query execution time in seconds") 