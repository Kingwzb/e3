"""Database connection and session management."""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, DateTime, Text, Float
from datetime import datetime
from typing import AsyncGenerator

from app.core.config import settings


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class MetricsData(Base):
    """Sample metrics table for demonstration."""
    __tablename__ = "metrics_data"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    category = Column(String(50), nullable=True, index=True)
    meta_data = Column(Text, nullable=True)


class ConversationHistory(Base):
    """Table to store conversation history."""
    __tablename__ = "conversation_history"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String(100), nullable=False, index=True)
    message_type = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)


# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True
)

# Create session maker
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_tables():
    """Create all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all) 