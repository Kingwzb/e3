"""Application configuration management."""

import os
import json
from typing import Optional, Literal, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application settings."""
    
    # LLM Provider Configuration
    llm_provider: Literal["openai", "vertexai"] = Field(default="openai", env="LLM_PROVIDER")
    
    # LLM Metadata Configuration (JSON format)
    llm_metadata: Optional[str] = Field(default=None, env="LLM_METADATA")
    
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
    
    # On-Premise Transport Configuration
    vertexai_api_transport: Optional[str] = Field(default=None, env="VERTEXAI_API_TRANSPORT")
    
    # SSL Configuration for On-Premise Deployments
    vertexai_ssl_verify: bool = Field(default=True, env="VERTEXAI_SSL_VERIFY")
    vertexai_ssl_cert_path: Optional[str] = Field(default=None, env="VERTEXAI_SSL_CERT_PATH")
    vertexai_ssl_key_path: Optional[str] = Field(default=None, env="VERTEXAI_SSL_KEY_PATH")
    vertexai_ssl_ca_cert_path: Optional[str] = Field(default=None, env="VERTEXAI_SSL_CA_CERT_PATH")
    
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
    
    @validator('llm_metadata')
    def validate_llm_metadata(cls, v):
        """Validate and parse LLM metadata JSON."""
        if v is None:
            return None
        try:
            parsed = json.loads(v)
            if not isinstance(parsed, dict):
                raise ValueError("LLM metadata must be a JSON object")
            return parsed
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in LLM_METADATA: {e}")
    
    @property
    def parsed_llm_metadata(self) -> Dict[str, Any]:
        """Get parsed LLM metadata as a dictionary."""
        if self.llm_metadata is None:
            return {}
        return self.llm_metadata if isinstance(self.llm_metadata, dict) else {}
    
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