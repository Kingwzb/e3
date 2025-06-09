"""Tests for individual agent nodes."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.agents.rag_agent import rag_extraction_node
from app.agents.metrics_agent import metrics_extraction_node
from app.models.state import WorkflowState


@pytest.mark.asyncio
async def test_rag_extraction_node():
    """Test RAG extraction node."""
    # Create test state
    state = WorkflowState(
        conversation_id="test_conv",
        current_message="What are the user engagement metrics?",
        messages=[],
        rag_context=None,
        metrics_data=None,
        final_response=None,
        error=None
    )
    
    # Run RAG extraction
    result_state = await rag_extraction_node(state)
    
    # Verify results
    assert result_state["conversation_id"] == "test_conv"
    assert result_state["rag_context"] is not None
    assert result_state["error"] is None


@pytest.mark.asyncio
async def test_rag_extraction_node_with_error():
    """Test RAG extraction node error handling."""
    # Create test state with empty message
    state = WorkflowState(
        conversation_id="test_conv",
        current_message="",
        messages=[],
        rag_context=None,
        metrics_data=None,
        final_response=None,
        error=None
    )
    
    # Run RAG extraction
    result_state = await rag_extraction_node(state)
    
    # Should handle gracefully even with empty message
    assert result_state["conversation_id"] == "test_conv"
    assert result_state["rag_context"] is not None  # Should have fallback context


@pytest.mark.asyncio 
async def test_metrics_extraction_node():
    """Test metrics extraction node."""
    # Create test state
    state = WorkflowState(
        conversation_id="test_conv",
        current_message="Show me the revenue metrics for last week",
        messages=[
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi! How can I help you?"}
        ],
        rag_context=None,
        metrics_data=None,
        final_response=None,
        error=None
    )
    
    # Note: This test will require proper database setup or mocking
    # For now, we'll test that it runs without crashing
    result_state = await metrics_extraction_node(state)
    
    # Verify results
    assert result_state["conversation_id"] == "test_conv"
    # metrics_data might be None if no metrics tools are called
    # This is acceptable behavior


@pytest.mark.asyncio
async def test_metrics_extraction_node_no_metrics_needed():
    """Test metrics extraction node when no metrics are needed."""
    # Create test state with non-metrics question
    state = WorkflowState(
        conversation_id="test_conv",
        current_message="Hello, how are you?",
        messages=[],
        rag_context=None,
        metrics_data=None,
        final_response=None,
        error=None
    )
    
    # Run metrics extraction
    result_state = await metrics_extraction_node(state)
    
    # Should complete without extracting metrics
    assert result_state["conversation_id"] == "test_conv"
    assert result_state["error"] is None


def test_rag_agent_tools():
    """Test RAG agent tools configuration."""
    from app.agents.rag_agent import create_rag_agent_tools
    
    tools = create_rag_agent_tools()
    
    assert "vector_store" in tools
    assert "search_params" in tools
    assert "default_k" in tools["search_params"]
    assert "default_min_score" in tools["search_params"]


def test_metrics_agent_tools():
    """Test metrics agent tools configuration."""
    from app.agents.metrics_agent import create_metrics_agent_tools
    
    tools = create_metrics_agent_tools()
    
    assert "database_tools" in tools
    assert "extraction_params" in tools
    assert isinstance(tools["database_tools"], list)
    assert len(tools["database_tools"]) > 0 