"""Application configuration management."""

import os
from typing import Optional, Literal
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings."""
    
    # LLM Provider Configuration
    llm_provider: Literal["openai", "vertexai"] = Field(default="openai", env="LLM_PROVIDER")
    
    # OpenAI Configuration
    openai_api_key: str = Field(default="sk-test", env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", env="OPENAI_MODEL")
    
    # Google Vertex AI Configuration
    vertexai_project_id: str = Field(default="", env="VERTEXAI_PROJECT_ID")
    vertexai_location: str = Field(default="us-central1", env="VERTEXAI_LOCATION")
    vertexai_model: str = Field(default="gemini-2.0-flash-lite-001", env="VERTEXAI_MODEL")
    google_application_credentials: Optional[str] = Field(default=None, env="GOOGLE_APPLICATION_CREDENTIALS")
    
    # Vertex AI Deployment Configuration
    vertexai_deployment_type: Literal["cloud", "on_premise", "corporate"] = Field(default="cloud", env="VERTEXAI_DEPLOYMENT_TYPE")
    vertexai_endpoint_url: Optional[str] = Field(default=None, env="VERTEXAI_ENDPOINT_URL")
    vertexai_api_key: Optional[str] = Field(default=None, env="VERTEXAI_API_KEY")
    vertexai_auth_method: str = Field(default="default", env="VERTEXAI_AUTH_METHOD")
    
    # On-Premise Authentication Configuration
    vertexai_token_function: Optional[str] = Field(default=None, env="VERTEXAI_TOKEN_FUNCTION")
    vertexai_token_function_module: Optional[str] = Field(default=None, env="VERTEXAI_TOKEN_FUNCTION_MODULE")
    vertexai_credentials_function: Optional[str] = Field(default=None, env="VERTEXAI_CREDENTIALS_FUNCTION")
    vertexai_credentials_function_module: Optional[str] = Field(default=None, env="VERTEXAI_CREDENTIALS_FUNCTION_MODULE")
    
    # Database Configuration
    db_host: str = Field(default="localhost", env="DB_HOST")
    db_port: int = Field(default=5432, env="DB_PORT")
    db_name: str = Field(default="", env="DB_NAME")
    db_user: str = Field(default="", env="DB_USER")
    db_password: str = Field(default="", env="DB_PASSWORD")
    
    # Vector Database Configuration
    faiss_index_path: str = Field(default="./data/faiss_index", env="FAISS_INDEX_PATH")
    embeddings_model: str = Field(default="text-embedding-005", env="EMBEDDINGS_MODEL")
    
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
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings() 