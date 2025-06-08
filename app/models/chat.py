"""Chat request and response models."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str = Field(..., description="User message")
    conversation_id: str = Field(..., description="Conversation identifier")


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str = Field(..., description="AI response")
    conversation_id: str = Field(..., description="Conversation identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Message(BaseModel):
    """Individual message model."""
    role: str = Field(..., description="Message role (user, assistant, system)")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConversationContext(BaseModel):
    """Conversation context model."""
    conversation_id: str
    messages: List[Message] = Field(default_factory=list)
    rag_context: Optional[str] = None
    metrics_data: Optional[Dict[str, Any]] = None 