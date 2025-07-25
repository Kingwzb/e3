"""FastAPI application entry point."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from app.core.config import settings
from app.core.database import create_tables
from app.api.chat import router as chat_router
from app.api.llm import router as llm_router
from app.utils.logging import logger
from app.tools.vector_store import initialize_sample_documents


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting AI Chat Agent application...")
    
    try:
        # Create database tables
        await create_tables()
        logger.info("Database tables created/verified")
        
        # Initialize vector store with sample data if empty
        initialize_sample_documents()
        logger.info("Vector store initialized")
        
        logger.info("Application startup completed successfully")
        
    except Exception as e:
        logger.error(f"Error during application startup: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Chat Agent application...")


# Create FastAPI app
app = FastAPI(
    title="AI Chat Agent with RAG and Metrics",
    description="A conversational AI system that combines RAG with database metrics extraction using LangGraph",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router)
app.include_router(llm_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to AI Chat Agent",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/chat/health"
    }


@app.get("/health")
async def health_check():
    """Global health check endpoint."""
    return {
        "status": "healthy",
        "application": "AI Chat Agent",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    ) 