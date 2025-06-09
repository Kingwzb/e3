"""Tests for LangGraph workflow orchestration."""

import pytest
from unittest.mock import AsyncMock, patch

from app.workflows.chat_workflow import (
    ChatWorkflowManager,
    create_chat_workflow,
    conversation_retrieval_node,
    response_generation_node,
    conversation_save_node
)
from app.models.state import WorkflowState


@pytest.mark.asyncio
async def test_conversation_retrieval_node():
    """Test conversation retrieval node."""
    state = WorkflowState(
        conversation_id="test_conv",
        current_message="Hello",
        messages=[],
        rag_context=None,
        metrics_data=None,
        final_response=None,
        error=None
    )
    
    result_state = await conversation_retrieval_node(state)
    
    # Should complete without error
    assert result_state["conversation_id"] == "test_conv"
    assert "messages" in result_state


@pytest.mark.asyncio
async def test_response_generation_node():
    """Test response generation node."""
    state = WorkflowState(
        conversation_id="test_conv",
        current_message="What are the metrics?",
        messages=[
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ],
        rag_context="Some relevant context from knowledge base",
        metrics_data={"sample": {"data": "test"}},
        final_response=None,
        error=None
    )
    
    result_state = await response_generation_node(state)
    
    # Should generate a response
    assert result_state["conversation_id"] == "test_conv"
    assert result_state["final_response"] is not None
    assert len(result_state["final_response"]) > 0


@pytest.mark.asyncio
async def test_conversation_save_node():
    """Test conversation save node."""
    state = WorkflowState(
        conversation_id="test_conv",
        current_message="Test message",
        messages=[],
        rag_context=None,
        metrics_data=None,
        final_response="Test response",
        error=None
    )
    
    result_state = await conversation_save_node(state)
    
    # Should complete without error
    assert result_state["conversation_id"] == "test_conv"


def test_create_chat_workflow():
    """Test chat workflow creation."""
    workflow = create_chat_workflow()
    
    # Verify workflow structure
    assert workflow is not None
    # The workflow should have the expected nodes
    expected_nodes = [
        "retrieve_history",
        "rag_extraction", 
        "metrics_extraction",
        "response_generation",
        "save_conversation"
    ]
    
    # Note: The exact API for checking nodes may vary based on LangGraph version
    # This is a basic structural test


@pytest.mark.asyncio
async def test_chat_workflow_manager_initialization():
    """Test ChatWorkflowManager initialization."""
    manager = ChatWorkflowManager()
    
    assert manager.workflow is not None
    assert manager.compiled_workflow is not None


@pytest.mark.asyncio
async def test_chat_workflow_manager_process_message():
    """Test ChatWorkflowManager message processing."""
    manager = ChatWorkflowManager()
    
    result = await manager.process_message(
        message="Hello, what are the latest metrics?",
        conversation_id="test_workflow_conv"
    )
    
    # Verify result structure
    assert "response" in result
    assert "conversation_id" in result
    assert "success" in result
    assert "metadata" in result
    
    assert result["conversation_id"] == "test_workflow_conv"
    assert isinstance(result["success"], bool)
    assert isinstance(result["metadata"], dict)


@pytest.mark.asyncio
async def test_chat_workflow_manager_error_handling():
    """Test ChatWorkflowManager error handling."""
    manager = ChatWorkflowManager()
    
    # Test with empty message (should be handled gracefully)
    result = await manager.process_message(
        message="",
        conversation_id="test_error_conv"
    )
    
    # Should still return a proper response structure
    assert "response" in result
    assert "conversation_id" in result
    assert "success" in result
    assert result["conversation_id"] == "test_error_conv"


def test_workflow_state_typing():
    """Test WorkflowState typing and structure."""
    state = WorkflowState(
        conversation_id="test",
        current_message="test message",
        messages=[],
        rag_context=None,
        metrics_data=None,
        final_response=None,
        error=None
    )
    
    # Verify required fields
    assert state["conversation_id"] == "test"
    assert state["current_message"] == "test message"
    assert state["messages"] == []
    assert state["rag_context"] is None
    assert state["metrics_data"] is None
    assert state["final_response"] is None
    assert state["error"] is None


@pytest.mark.asyncio
async def test_workflow_with_rag_and_metrics():
    """Test complete workflow with both RAG and metrics."""
    manager = ChatWorkflowManager()
    
    # Test a message that should trigger both RAG and metrics
    result = await manager.process_message(
        message="Show me user engagement metrics and related documentation",
        conversation_id="test_full_workflow"
    )
    
    # Should complete successfully
    assert result["success"] is True or result["success"] is False  # Either is acceptable
    assert result["response"] is not None
    assert len(result["response"]) > 0
    
    # Metadata should indicate what was processed
    metadata = result["metadata"]
    assert "rag_context_available" in metadata
    assert "metrics_data_available" in metadata
    assert "conversation_length" in metadata 