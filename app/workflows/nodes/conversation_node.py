"""Conversation management nodes for LangGraph workflow."""

from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.state import MultiHopState
from app.core.database import get_db
from app.tools.conversation_tools import ConversationTools
from app.utils.logging import logger


def _format_conversation_history(messages: List[Dict[str, str]]) -> str:
    """Format conversation messages into a string format for MultiHopState."""
    formatted = []
    for i, msg in enumerate(messages, 1):
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')
        formatted.append(f"{i}. {role}: {content}")
    return "\n".join(formatted)


async def conversation_retrieval_node(state: MultiHopState) -> MultiHopState:
    """
    Node that retrieves conversation history from database.
    
    This node:
    1. Fetches previous conversation messages for the given session_id
    2. Converts them to the expected format for the workflow
    3. Updates the state with conversation history
    
    Configuration:
    - Uses state.get("conversation_history_limit", 10) to determine how many messages to retrieve
    """
    try:
        logger.info(f"Retrieving conversation history for: {state['session_id']}")
        
        # Get configurable history limit from state, default to 10
        history_limit = state.get("conversation_history_limit", 10)
        logger.debug(f"Using conversation history limit: {history_limit}")
        
        # Get database session and retrieve conversation history
        async for db_session in get_db():
            conversation_tools = ConversationTools(db_session)
            history = await conversation_tools.get_conversation_history(
                state["session_id"], 
                limit=history_limit
            )
            
            # Convert to the expected format
            messages = []
            for msg in history:
                messages.append({
                    "role": msg["message_type"],
                    "content": msg["content"]
                })
            
            # Format conversation history as string for MultiHopState
            conversation_history = _format_conversation_history(messages)
            state["conversation_history"] = conversation_history
            
            logger.info(f"Retrieved {len(messages)} conversation messages")
            break
        
        return state
        
    except Exception as e:
        logger.error(f"Error retrieving conversation history: {str(e)}")
        state["conversation_history"] = ""
        return state


async def conversation_save_node(state: MultiHopState) -> MultiHopState:
    """
    Node that saves the current conversation exchange to database.
    
    This node:
    1. Saves the user's current message
    2. Saves the assistant's generated response
    3. Handles errors gracefully without failing the workflow
    """
    try:
        logger.info(f"Saving conversation for: {state['session_id']}")
        
        user_query = state["user_query"]
        final_response = state.get("final_answer", {}).get("response", "")
        
        # Save both user message and assistant response
        async for db_session in get_db():
            conversation_tools = ConversationTools(db_session)
            
            # Save user message
            await conversation_tools.save_conversation_message(
                state["session_id"],
                "user",
                user_query
            )
            
            # Save assistant response
            if final_response:
                await conversation_tools.save_conversation_message(
                    state["session_id"],
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