"""API endpoint tests."""

import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Async test client fixture."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


def test_root_endpoint(client):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_chat_health_endpoint(client):
    """Test the chat health endpoint."""
    response = client.get("/api/chat/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_chat_endpoint_valid_request(async_client):
    """Test chat endpoint with valid request."""
    request_data = {
        "message": "What are the latest user engagement metrics?",
        "conversation_id": "test_conv_001"
    }
    
    response = await async_client.post("/api/chat", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "response" in data
    assert "conversation_id" in data
    assert "timestamp" in data
    assert data["conversation_id"] == "test_conv_001"


@pytest.mark.asyncio
async def test_chat_endpoint_empty_message():
    """Test chat endpoint with empty message."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        request_data = {
            "message": "",
            "conversation_id": "test_conv_002"
        }
        
        response = await ac.post("/api/chat", json=request_data)
        assert response.status_code == 400


@pytest.mark.asyncio
async def test_chat_endpoint_empty_conversation_id():
    """Test chat endpoint with empty conversation ID."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        request_data = {
            "message": "Hello",
            "conversation_id": ""
        }
        
        response = await ac.post("/api/chat", json=request_data)
        assert response.status_code == 400


@pytest.mark.asyncio
async def test_chat_endpoint_missing_fields():
    """Test chat endpoint with missing required fields."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Missing message
        response = await ac.post("/api/chat", json={"conversation_id": "test"})
        assert response.status_code == 422
        
        # Missing conversation_id
        response = await ac.post("/api/chat", json={"message": "Hello"})
        assert response.status_code == 422


def test_chat_stats_endpoint(client):
    """Test the chat stats endpoint."""
    response = client.get("/api/chat/stats")
    assert response.status_code == 200
    
    data = response.json()
    assert "vector_store" in data
    assert "workflow" in data


@pytest.mark.asyncio
async def test_conversation_continuity():
    """Test that conversation history is maintained."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        conversation_id = "test_conv_continuity"
        
        # First message
        response1 = await ac.post("/api/chat", json={
            "message": "Hello, I want to know about metrics",
            "conversation_id": conversation_id
        })
        assert response1.status_code == 200
        
        # Follow-up message
        response2 = await ac.post("/api/chat", json={
            "message": "Can you give me more details?",
            "conversation_id": conversation_id
        })
        assert response2.status_code == 200
        
        # Both should have the same conversation_id
        assert response1.json()["conversation_id"] == conversation_id
        assert response2.json()["conversation_id"] == conversation_id 