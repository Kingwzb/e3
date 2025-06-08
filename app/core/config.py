"""Application configuration management."""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings."""
    
    # OpenAI Configuration
    openai_api_key: str = Field(default="sk-test", env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", env="OPENAI_MODEL")
    
    # Database Configuration
    db_host: str = Field(default="localhost", env="DB_HOST")
    db_port: int = Field(default=5432, env="DB_PORT")
    db_name: str = Field(default="", env="DB_NAME")
    db_user: str = Field(default="", env="DB_USER")
    db_password: str = Field(default="", env="DB_PASSWORD")
    
    # Vector Database Configuration
    faiss_index_path: str = Field(default="./data/faiss_index", env="FAISS_INDEX_PATH")
    embeddings_model: str = Field(default="all-MiniLM-L6-v2", env="EMBEDDINGS_MODEL")
    
    # Application Configuration
    app_host: str = Field(default="0.0.0.0", env="APP_HOST")
    app_port: int = Field(default=8000, env="APP_PORT")
    debug: bool = Field(default=True, env="DEBUG")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    @property
    def database_url(self) -> str:
        """Get the database URL."""
        # Force SQLite for development (change this for production)
        use_sqlite = os.getenv("USE_SQLITE", "true").lower() == "true"
        if use_sqlite:
            return "sqlite+aiosqlite:///./ai_chat.db"
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings() 