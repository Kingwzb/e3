"""Conversation database tools."""

from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import ConversationHistory
from app.utils.logging import logger


class ConversationTools:
    """Database tools for conversation management."""
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
    
    async def save_conversation_message(
        self, 
        conversation_id: str, 
        message_type: str, 
        content: str
    ) -> bool:
        """Save a conversation message to the database."""
        try:
            message = ConversationHistory(
                conversation_id=conversation_id,
                message_type=message_type,
                content=content
            )
            self.db_session.add(message)
            await self.db_session.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving conversation message: {str(e)}")
            await self.db_session.rollback()
            return False
    
    async def get_conversation_history(
        self, 
        conversation_id: str, 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get conversation history for a given conversation ID."""
        try:
            query = select(ConversationHistory).where(
                ConversationHistory.conversation_id == conversation_id
            ).order_by(ConversationHistory.timestamp.desc()).limit(limit)
            
            result = await self.db_session.execute(query)
            messages = result.scalars().all()
            
            return [
                {
                    "message_type": msg.message_type,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat()
                }
                for msg in reversed(messages)  # Reverse to get chronological order
            ]
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            return [] 