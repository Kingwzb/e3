#!/usr/bin/env python3
"""
Test script to verify LLM provider functionality.
This script tests both OpenAI and Vertex AI providers if configured.
"""

import asyncio
import os
import sys
from typing import Dict, Any

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.core.config import settings
from app.core.llm import OpenAIClient, VertexAIClient, llm_client
from app.utils.logging import logger


async def test_openai_client():
    """Test OpenAI client functionality."""
    print("\n🔍 Testing OpenAI Client...")
    
    if not settings.openai_api_key or settings.openai_api_key == "sk-test":
        print("❌ OpenAI API key not configured. Skipping OpenAI test.")
        return False
    
    try:
        client = OpenAIClient(
            api_key=settings.openai_api_key,
            model=settings.openai_model
        )
        
        messages = [
            {"role": "user", "content": "Hello! Please respond with 'OpenAI test successful' to confirm connectivity."}
        ]
        
        response = await client.generate_response(
            messages=messages,
            temperature=0.1,
            max_tokens=50
        )
        
        print(f"✅ OpenAI Response: {response.get('content', 'No content')}")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI test failed: {str(e)}")
        return False


async def test_vertexai_client():
    """Test Vertex AI client functionality."""
    print("\n🔍 Testing Vertex AI Client...")
    
    if not settings.vertexai_project_id:
        print("❌ Vertex AI project ID not configured. Skipping Vertex AI test.")
        return False
    
    try:
        client = VertexAIClient(
            project_id=settings.vertexai_project_id,
            location=settings.vertexai_location,
            model=settings.vertexai_model,
            credentials_path=settings.google_application_credentials
        )
        
        messages = [
            {"role": "user", "content": "Hello! Please respond with 'Vertex AI test successful' to confirm connectivity."}
        ]
        
        response = await client.generate_response(
            messages=messages,
            temperature=0.1,
            max_tokens=50
        )
        
        print(f"✅ Vertex AI Response: {response.get('content', 'No content')}")
        return True
        
    except Exception as e:
        print(f"❌ Vertex AI test failed: {str(e)}")
        return False


async def test_unified_client():
    """Test the unified LLM client."""
    print(f"\n🔍 Testing Unified Client (Provider: {settings.llm_provider})...")
    
    try:
        provider_info = llm_client.get_provider_info()
        print(f"📋 Provider Info: {provider_info}")
        
        messages = [
            {"role": "user", "content": "Hello! Please respond with 'Unified client test successful' to confirm connectivity."}
        ]
        
        response = await llm_client.generate_response(
            messages=messages,
            temperature=0.1,
            max_tokens=50
        )
        
        print(f"✅ Unified Client Response: {response.get('content', 'No content')}")
        return True
        
    except Exception as e:
        print(f"❌ Unified client test failed: {str(e)}")
        return False


async def test_tool_calling():
    """Test tool calling functionality with the current provider."""
    print(f"\n🔍 Testing Tool Calling (Provider: {settings.llm_provider})...")
    
    try:
        # Define a simple test tool
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get the current weather for a location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "The city and state, e.g. San Francisco, CA"
                            }
                        },
                        "required": ["location"]
                    }
                }
            }
        ]
        
        messages = [
            {"role": "user", "content": "What's the weather like in New York?"}
        ]
        
        response = await llm_client.generate_response(
            messages=messages,
            tools=tools,
            temperature=0.1,
            max_tokens=100
        )
        
        if response.get("tool_calls"):
            print(f"✅ Tool calling successful: {len(response['tool_calls'])} tool calls")
            for tool_call in response["tool_calls"]:
                print(f"   - Function: {tool_call['function']['name']}")
                print(f"   - Arguments: {tool_call['function']['arguments']}")
        else:
            print(f"⚠️  No tool calls made. Response: {response.get('content', 'No content')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Tool calling test failed: {str(e)}")
        return False


def print_configuration():
    """Print current configuration."""
    print("🔧 Current Configuration:")
    print(f"   LLM Provider: {settings.llm_provider}")
    
    if settings.llm_provider == "openai":
        print(f"   OpenAI Model: {settings.openai_model}")
        print(f"   OpenAI API Key: {'✅ Configured' if settings.openai_api_key and settings.openai_api_key != 'sk-test' else '❌ Not configured'}")
    
    elif settings.llm_provider == "vertexai":
        print(f"   Vertex AI Model: {settings.vertexai_model}")
        print(f"   Vertex AI Project: {settings.vertexai_project_id}")
        print(f"   Vertex AI Location: {settings.vertexai_location}")
        print(f"   Credentials: {'✅ Configured' if settings.google_application_credentials else '❌ Not configured'}")


async def main():
    """Main test function."""
    print("🚀 LLM Provider Test Suite")
    print("=" * 50)
    
    print_configuration()
    
    # Test results
    results = {}
    
    # Test individual clients
    results["openai"] = await test_openai_client()
    results["vertexai"] = await test_vertexai_client()
    
    # Test unified client
    results["unified"] = await test_unified_client()
    
    # Test tool calling
    results["tools"] = await test_tool_calling()
    
    # Summary
    print("\n📊 Test Summary:")
    print("=" * 30)
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name.capitalize()}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check configuration and credentials.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main()) 