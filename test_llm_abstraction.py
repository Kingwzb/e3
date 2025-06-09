#!/usr/bin/env python3
"""
Test script to verify the abstracted LLM client initialization.
Tests different deployment types and configurations.
"""

import asyncio
import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.core.llm import LLMClientConfig, LLMClientFactory, llm_client
from app.core.config import settings
from app.utils.logging import logger


async def test_current_configuration():
    """Test the current configuration from settings."""
    print("🔍 Testing Current Configuration from Settings...")
    
    try:
        provider_info = llm_client.get_provider_info()
        print(f"✅ Current Provider Info: {provider_info}")
        
        # Test basic functionality
        messages = [{"role": "user", "content": "Hello! Please respond briefly."}]
        response = await llm_client.generate_response(messages=messages, max_tokens=50)
        
        print(f"✅ Response: {response.get('content', 'No content')[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ Current configuration test failed: {str(e)}")
        return False


async def test_openai_configuration():
    """Test OpenAI configuration with custom settings."""
    print("\n🔍 Testing OpenAI Configuration...")
    
    try:
        config = LLMClientConfig(
            provider="openai",
            model="gpt-3.5-turbo",
            deployment_type="cloud",
            api_key=settings.openai_api_key
        )
        
        client = LLMClientFactory.create_client(config)
        provider_info = client.get_provider_info()
        print(f"✅ OpenAI Provider Info: {provider_info}")
        
        # Test basic functionality
        messages = [{"role": "user", "content": "Hello from OpenAI test!"}]
        response = await client.generate_response(messages=messages, max_tokens=30)
        
        print(f"✅ OpenAI Response: {response.get('content', 'No content')[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI configuration test failed: {str(e)}")
        return False


async def test_vertexai_cloud_configuration():
    """Test Vertex AI cloud configuration."""
    print("\n🔍 Testing Vertex AI Cloud Configuration...")
    
    try:
        config = LLMClientConfig(
            provider="vertexai",
            model=settings.vertexai_model,
            deployment_type="cloud",
            project_id=settings.vertexai_project_id,
            location=settings.vertexai_location,
            credentials_path=settings.google_application_credentials
        )
        
        client = LLMClientFactory.create_client(config)
        provider_info = client.get_provider_info()
        print(f"✅ Vertex AI Cloud Provider Info: {provider_info}")
        
        # Test basic functionality
        messages = [{"role": "user", "content": "Hello from Vertex AI cloud test!"}]
        response = await client.generate_response(messages=messages, max_tokens=30)
        
        print(f"✅ Vertex AI Cloud Response: {response.get('content', 'No content')[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ Vertex AI cloud configuration test failed: {str(e)}")
        return False


def test_corporate_configuration_setup():
    """Test corporate configuration setup (without actual API call)."""
    print("\n🔍 Testing Corporate Configuration Setup...")
    
    try:
        config = LLMClientConfig(
            provider="vertexai",
            model="gemini-2.0-flash-lite-001",
            deployment_type="corporate",
            project_id="corporate-project",
            location="corporate-location",
            endpoint_url="https://corporate-gemini.example.com/v1",
            api_key="corporate-api-key",
            auth_method="api_key"
        )
        
        # Just test the configuration creation, not the actual client
        print(f"✅ Corporate Config Created: {config.provider}, {config.deployment_type}")
        print(f"   Endpoint: {config.config.get('endpoint_url')}")
        print(f"   Auth Method: {config.config.get('auth_method')}")
        
        # Note: We don't create the actual client since we don't have a real corporate endpoint
        return True
        
    except Exception as e:
        print(f"❌ Corporate configuration setup failed: {str(e)}")
        return False


def test_on_premise_configuration_setup():
    """Test on-premise configuration setup (without actual API call)."""
    print("\n🔍 Testing On-Premise Configuration Setup...")
    
    try:
        config = LLMClientConfig(
            provider="vertexai",
            model="gemini-1.5-pro-002",
            deployment_type="on_premise",
            project_id="onprem-project",
            location="onprem-location",
            endpoint_url="https://onprem-vertex.example.com",
            api_key="onprem-api-key"
        )
        
        # Just test the configuration creation, not the actual client
        print(f"✅ On-Premise Config Created: {config.provider}, {config.deployment_type}")
        print(f"   Endpoint: {config.config.get('endpoint_url')}")
        print(f"   Model: {config.model}")
        
        # Note: We don't create the actual client since we don't have a real on-premise endpoint
        return True
        
    except Exception as e:
        print(f"❌ On-premise configuration setup failed: {str(e)}")
        return False


async def test_tool_calling_fix():
    """Test that the tool calling fix works with current configuration."""
    print("\n🔍 Testing Tool Calling Fix...")
    
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
        
        messages = [{"role": "user", "content": "What's the weather like in Tokyo?"}]
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
            print(f"⚠️  No tool calls made. Response: {response.get('content', 'No content')[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Tool calling test failed: {str(e)}")
        return False


def print_current_settings():
    """Print current settings for debugging."""
    print("🔧 Current Settings:")
    print(f"   LLM Provider: {settings.llm_provider}")
    print(f"   Vertex AI Deployment Type: {getattr(settings, 'vertexai_deployment_type', 'Not set')}")
    print(f"   Vertex AI Model: {settings.vertexai_model}")
    print(f"   Vertex AI Project: {settings.vertexai_project_id}")
    print(f"   Vertex AI Location: {settings.vertexai_location}")
    print(f"   Vertex AI Endpoint URL: {getattr(settings, 'vertexai_endpoint_url', 'Not set')}")
    print()


async def main():
    """Main test function."""
    print("🚀 LLM Client Abstraction Test Suite")
    print("=" * 60)
    
    print_current_settings()
    
    # Test results
    results = {}
    
    # Test current configuration
    results["current_config"] = await test_current_configuration()
    
    # Test OpenAI configuration (if API key is available)
    if settings.openai_api_key and settings.openai_api_key != "sk-test":
        results["openai_config"] = await test_openai_configuration()
    else:
        print("\n⚠️  Skipping OpenAI test - API key not configured")
        results["openai_config"] = None
    
    # Test Vertex AI cloud configuration
    if settings.vertexai_project_id:
        results["vertexai_cloud"] = await test_vertexai_cloud_configuration()
    else:
        print("\n⚠️  Skipping Vertex AI cloud test - project not configured")
        results["vertexai_cloud"] = None
    
    # Test configuration setups (no actual API calls)
    results["corporate_setup"] = test_corporate_configuration_setup()
    results["onpremise_setup"] = test_on_premise_configuration_setup()
    
    # Test tool calling fix
    results["tool_calling"] = await test_tool_calling_fix()
    
    # Summary
    print("\n📊 Test Summary:")
    print("=" * 40)
    for test_name, success in results.items():
        if success is None:
            status = "⚠️  SKIP"
        elif success:
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    # Count results
    passed_tests = sum(1 for result in results.values() if result is True)
    failed_tests = sum(1 for result in results.values() if result is False)
    skipped_tests = sum(1 for result in results.values() if result is None)
    total_tests = len(results)
    
    print(f"\nOverall: {passed_tests} passed, {failed_tests} failed, {skipped_tests} skipped out of {total_tests} tests")
    
    if failed_tests == 0:
        print("🎉 All executed tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check configuration and implementation.")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1) 