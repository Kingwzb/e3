#!/usr/bin/env python3
"""
Test Vertex AI setup before running the main standalone tool test.
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.llm import LLMClientConfig, VertexAIClient
from app.core.config import settings


async def test_vertex_ai_setup():
    """Test that Vertex AI is properly configured."""
    
    print("🔍 Testing Vertex AI Setup")
    print("=" * 30)
    
    # Check configuration
    print(f"Project ID: {settings.vertexai_project_id}")
    print(f"Location: {settings.vertexai_location}")
    print(f"Model: {settings.vertexai_model}")
    print(f"Credentials: {settings.google_application_credentials}")
    
    if not settings.vertexai_project_id:
        print("❌ Vertex AI project ID not configured")
        return False
    
    try:
        # Create Vertex AI client
        config = LLMClientConfig(
            provider="vertexai",
            model=settings.vertexai_model,
            deployment_type="cloud",
            project_id=settings.vertexai_project_id,
            location=settings.vertexai_location,
            credentials_path=settings.google_application_credentials
        )
        
        vertex_client = VertexAIClient(config)
        
        # Test simple generation
        messages = [{"role": "user", "content": "Hello! Please respond with 'Vertex AI test successful'."}]
        
        response = await vertex_client.generate_response(
            messages=messages,
            temperature=0.1,
            max_tokens=50
        )
        
        content = response.get("content", "")
        print(f"✅ Vertex AI Response: {content}")
        
        if "Vertex AI test successful" in content:
            print("✅ Vertex AI setup is working correctly!")
            return True
        else:
            print("⚠️ Vertex AI responded but not as expected")
            return True  # Still consider it working
            
    except Exception as e:
        print(f"❌ Vertex AI setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Test Vertex AI setup."""
    success = await test_vertex_ai_setup()
    
    if success:
        print("\n🎉 Vertex AI setup is ready for testing!")
    else:
        print("\n❌ Vertex AI setup needs to be configured.")
    
    return success


if __name__ == "__main__":
    asyncio.run(main()) 