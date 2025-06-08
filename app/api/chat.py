"""Chat endpoint implementation."""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from app.models.chat import ChatRequest, ChatResponse
from app.workflows.chat_workflow import chat_workflow_manager
from app.core.database import get_db
from app.utils.logging import logger

# Create router
router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
) -> ChatResponse:
    """
    Main chat endpoint that processes user messages through the LangGraph workflow.
    
    This endpoint:
    1. Validates the request
    2. Processes the message through the chat workflow
    3. Returns the AI response
    4. Handles errors gracefully
    """
    try:
        logger.info(f"Received chat request for conversation: {request.conversation_id}")
        
        # Validate input
        if not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        if not request.conversation_id.strip():
            raise HTTPException(status_code=400, detail="Conversation ID cannot be empty")
        
        # Process through workflow
        result = await chat_workflow_manager.process_message(
            message=request.message,
            conversation_id=request.conversation_id
        )
        
        # Check if workflow was successful
        if not result["success"]:
            logger.error(f"Workflow failed: {result.get('metadata', {}).get('error', 'Unknown error')}")
            # Still return a response, but log the error
        
        # Create response
        response = ChatResponse(
            response=result["response"],
            conversation_id=result["conversation_id"]
        )
        
        logger.info(f"Chat request completed for conversation: {request.conversation_id}")
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An internal error occurred while processing your request."
        )


@router.get("/chat/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint for the chat service.
    """
    return {
        "status": "healthy",
        "service": "chat_endpoint"
    }


@router.get("/chat/stats")
async def get_chat_stats() -> Dict[str, Any]:
    """
    Get statistics about the chat service.
    """
    try:
        from app.tools.vector_store import vector_store
        
        # Get vector store stats
        vector_stats = vector_store.get_stats()
        
        return {
            "vector_store": vector_stats,
            "workflow": {
                "status": "active",
                "nodes": ["retrieve_history", "rag_extraction", "metrics_extraction", "response_generation", "save_conversation"]
            }
        }
    except Exception as e:
        logger.error(f"Error getting chat stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics") 