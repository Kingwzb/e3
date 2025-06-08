"""Conversation management nodes for LangGraph workflow."""

from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.state import WorkflowState
from app.core.database import get_db
from app.tools.conversation_tools import ConversationTools
from app.utils.logging import logger


async def conversation_retrieval_node(state: WorkflowState) -> WorkflowState:
    """
    Node that retrieves conversation history from database.
    
    This node:
    1. Fetches previous conversation messages for the given conversation_id
    2. Converts them to the expected format for the workflow
    3. Updates the state with conversation history
    
    Configuration:
    - Uses state.get("conversation_history_limit", 10) to determine how many messages to retrieve
    """
    try:
        logger.info(f"Retrieving conversation history for: {state['conversation_id']}")
        
        # Get configurable history limit from state, default to 10
        history_limit = state.get("conversation_history_limit", 10)
        logger.debug(f"Using conversation history limit: {history_limit}")
        
        # Get database session and retrieve conversation history
        async for db_session in get_db():
            conversation_tools = ConversationTools(db_session)
            history = await conversation_tools.get_conversation_history(
                state["conversation_id"], 
                limit=history_limit
            )
            
            # Convert to the expected format
            messages = []
            for msg in history:
                messages.append({
                    "role": msg["message_type"],
                    "content": msg["content"]
                })
            
            state["messages"] = messages
            logger.info(f"Retrieved {len(messages)} conversation messages")
            break
        
        return state
        
    except Exception as e:
        logger.error(f"Error retrieving conversation history: {str(e)}")
        state["messages"] = []
        return state


async def conversation_save_node(state: WorkflowState) -> WorkflowState:
    """
    Node that saves the current conversation exchange to database.
    
    This node:
    1. Saves the user's current message
    2. Saves the assistant's generated response
    3. Handles errors gracefully without failing the workflow
    """
    try:
        logger.info(f"Saving conversation for: {state['conversation_id']}")
        
        current_message = state["current_message"]
        final_response = state.get("final_response", "")
        
        # Save both user message and assistant response
        async for db_session in get_db():
            conversation_tools = ConversationTools(db_session)
            
            # Save user message
            await conversation_tools.save_conversation_message(
                state["conversation_id"],
                "user",
                current_message
            )
            
            # Save assistant response
            if final_response:
                await conversation_tools.save_conversation_message(
                    state["conversation_id"],
                    "assistant",
                    final_response
                )
            
            logger.info("Conversation saved successfully")
            break
        
        return state
        
    except Exception as e:
        logger.error(f"Error saving conversation: {str(e)}")
        # Don't fail the workflow if saving fails
        return state 