"""LLM provider management endpoints."""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from pydantic import BaseModel

from app.core.llm import llm_client
from app.core.config import settings
from app.utils.logging import logger


# Create router
router = APIRouter(prefix="/api/llm", tags=["llm"])


class LLMProviderInfo(BaseModel):
    """LLM provider information response model."""
    provider: str
    model: str
    project: str = None
    location: str = None
    status: str


class LLMTestRequest(BaseModel):
    """LLM test request model."""
    message: str = "Hello, please respond with 'Test successful' to confirm connectivity."


class LLMTestResponse(BaseModel):
    """LLM test response model."""
    success: bool
    response: str
    provider_info: Dict[str, str]
    error: str = None


@router.get("/provider", response_model=LLMProviderInfo)
async def get_provider_info() -> LLMProviderInfo:
    """
    Get information about the current LLM provider.
    """
    try:
        provider_info = llm_client.get_provider_info()
        
        return LLMProviderInfo(
            provider=provider_info.get("provider", "Unknown"),
            model=provider_info.get("model", "Unknown"),
            project=provider_info.get("project"),
            location=provider_info.get("location"),
            status="active"
        )
    except Exception as e:
        logger.error(f"Error getting provider info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get provider info: {str(e)}")


@router.post("/test", response_model=LLMTestResponse)
async def test_llm_connectivity(request: LLMTestRequest) -> LLMTestResponse:
    """
    Test connectivity to the current LLM provider.
    """
    try:
        logger.info(f"Testing LLM connectivity with provider: {settings.llm_provider}")
        
        # Prepare test message
        messages = [
            {"role": "user", "content": request.message}
        ]
        
        # Test the LLM
        response = await llm_client.generate_response(
            messages=messages,
            temperature=0.1,
            max_tokens=100
        )
        
        provider_info = llm_client.get_provider_info()
        
        return LLMTestResponse(
            success=True,
            response=response.get("content", ""),
            provider_info=provider_info
        )
        
    except Exception as e:
        logger.error(f"LLM connectivity test failed: {str(e)}")
        provider_info = llm_client.get_provider_info()
        
        return LLMTestResponse(
            success=False,
            response="",
            provider_info=provider_info,
            error=str(e)
        )


@router.get("/providers")
async def get_available_providers() -> Dict[str, Any]:
    """
    Get list of available LLM providers and their configuration requirements.
    """
    return {
        "available_providers": [
            {
                "name": "openai",
                "display_name": "OpenAI",
                "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
                "required_config": ["OPENAI_API_KEY", "OPENAI_MODEL"],
                "optional_config": []
            },
            {
                "name": "vertexai",
                "display_name": "Google Vertex AI",
                "models": ["gemini-2.0-flash-lite-001", "gemini-1.5-pro-002", "gemini-1.5-flash-002", "gemini-1.0-pro-001"],
                "required_config": ["VERTEXAI_PROJECT_ID", "VERTEXAI_MODEL"],
                "optional_config": ["VERTEXAI_LOCATION", "GOOGLE_APPLICATION_CREDENTIALS"]
            }
        ],
        "current_provider": settings.llm_provider,
        "configuration_note": "To switch providers, update the LLM_PROVIDER environment variable and restart the application."
    }


@router.get("/config")
async def get_llm_config() -> Dict[str, Any]:
    """
    Get current LLM configuration (without sensitive information).
    """
    config = {
        "provider": settings.llm_provider,
    }
    
    if settings.llm_provider == "openai":
        config.update({
            "model": settings.openai_model,
            "api_key_configured": bool(settings.openai_api_key and settings.openai_api_key != "sk-test")
        })
    elif settings.llm_provider == "vertexai":
        config.update({
            "model": settings.vertexai_model,
            "project_id": settings.vertexai_project_id,
            "location": settings.vertexai_location,
            "deployment_type": settings.vertexai_deployment_type,
            "credentials_configured": bool(settings.google_application_credentials),
            "endpoint_url_configured": bool(settings.vertexai_endpoint_url),
            "api_key_configured": bool(settings.vertexai_api_key)
        })
    
    return config


@router.get("/health")
async def llm_health_check() -> Dict[str, str]:
    """
    Health check endpoint for LLM service.
    """
    try:
        provider_info = llm_client.get_provider_info()
        return {
            "status": "healthy",
            "provider": provider_info.get("provider", "Unknown"),
            "model": provider_info.get("model", "Unknown")
        }
    except Exception as e:
        logger.error(f"LLM health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        } 