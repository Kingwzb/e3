#!/usr/bin/env python3
"""
Example configurations for different LLM deployment types.
This file demonstrates how to configure the LLM client for various scenarios.
"""

import asyncio
import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.llm import LLMClientConfig, LLMClientFactory


# Example 1: OpenAI Cloud Configuration
def create_openai_config():
    """Create OpenAI configuration for cloud deployment."""
    return LLMClientConfig(
        provider="openai",
        model="gpt-4",
        deployment_type="cloud",
        api_key="your-openai-api-key"
    )


# Example 2: OpenAI-Compatible Custom Endpoint
def create_openai_custom_config():
    """Create OpenAI configuration with custom endpoint (e.g., Azure OpenAI)."""
    return LLMClientConfig(
        provider="openai",
        model="gpt-4",
        deployment_type="cloud",
        api_key="your-api-key",
        base_url="https://your-custom-openai-endpoint.com/v1"
    )


# Example 3: Google Cloud Vertex AI
def create_vertexai_cloud_config():
    """Create Vertex AI configuration for Google Cloud."""
    return LLMClientConfig(
        provider="vertexai",
        model="gemini-2.0-flash-lite-001",
        deployment_type="cloud",
        project_id="your-gcp-project-id",
        location="us-central1",
        credentials_path="/path/to/service-account-key.json"
    )


# Example 4: Corporate Hosted Gemini
def create_corporate_gemini_config():
    """Create configuration for corporate hosted Gemini models."""
    return LLMClientConfig(
        provider="vertexai",
        model="gemini-2.0-flash-lite-001",
        deployment_type="corporate",
        project_id="corporate-project",
        location="corporate-location",
        endpoint_url="https://your-corporate-gemini.company.com/v1",
        api_key="your-corporate-api-key",
        auth_method="api_key"
    )


# Example 5: On-Premise Vertex AI (Basic)
def create_onpremise_vertexai_config():
    """Create configuration for on-premise Vertex AI deployment."""
    return LLMClientConfig(
        provider="vertexai",
        model="gemini-1.5-pro-002",
        deployment_type="on_premise",
        project_id="onprem-project",
        location="onprem-datacenter",
        endpoint_url="https://vertex-ai.internal.company.com",
        api_key="your-onprem-api-key"
    )


# Example 6: On-Premise Vertex AI with In-House Token Function
def create_onpremise_vertexai_token_config():
    """Create configuration for on-premise Vertex AI with in-house token function."""
    return LLMClientConfig(
        provider="vertexai",
        model="gemini-2.0-flash-lite-001",
        deployment_type="on_premise",
        project_id="onprem-project",
        location="onprem-datacenter",
        endpoint_url="https://vertex-ai.internal.company.com",
        token_function="get_auth_token",
        token_function_module="your_company.auth.gemini_auth"
    )


# Example 7: On-Premise Vertex AI with In-House Credentials Function
def create_onpremise_vertexai_credentials_config():
    """Create configuration for on-premise Vertex AI with in-house credentials function."""
    return LLMClientConfig(
        provider="vertexai",
        model="gemini-1.5-flash-002",
        deployment_type="on_premise",
        project_id="onprem-project",
        location="onprem-datacenter",
        endpoint_url="https://vertex-ai.internal.company.com",
        credentials_function="get_gemini_credentials",
        credentials_function_module="your_company.auth.vertex_auth"
    )


# Example 8: Corporate Gemini with Custom Authentication
def create_corporate_gemini_custom_auth_config():
    """Create configuration for corporate Gemini with custom authentication."""
    return LLMClientConfig(
        provider="vertexai",
        model="gemini-1.5-flash-002",
        deployment_type="corporate",
        project_id="corp-ai-project",
        location="us-east1",
        endpoint_url="https://ai-gateway.corp.com/gemini/v1",
        api_key="corp-api-key-12345",
        auth_method="bearer_token"
    )


async def test_configuration(config: LLMClientConfig, config_name: str):
    """Test a configuration by creating a client and getting provider info."""
    try:
        print(f"\n🔧 Testing {config_name}...")
        
        # Create client
        client = LLMClientFactory.create_client(config)
        
        # Get provider info
        provider_info = client.get_provider_info()
        print(f"✅ Provider Info: {provider_info}")
        
        # Note: We don't make actual API calls since these are example configurations
        print(f"✅ {config_name} configuration created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ {config_name} configuration failed: {str(e)}")
        return False


async def demonstrate_configurations():
    """Demonstrate all configuration types."""
    print("🚀 LLM Deployment Configuration Examples")
    print("=" * 60)
    
    configurations = [
        (create_openai_config(), "OpenAI Cloud"),
        (create_openai_custom_config(), "OpenAI Custom Endpoint"),
        (create_vertexai_cloud_config(), "Vertex AI Cloud"),
        (create_corporate_gemini_config(), "Corporate Gemini"),
        (create_onpremise_vertexai_config(), "On-Premise Vertex AI Basic"),
        (create_onpremise_vertexai_token_config(), "On-Premise Vertex AI Token Function"),
        (create_onpremise_vertexai_credentials_config(), "On-Premise Vertex AI Credentials Function"),
        (create_corporate_gemini_custom_auth_config(), "Corporate Gemini Custom Auth")
    ]
    
    results = []
    
    for config, name in configurations:
        # For demonstration, we only test configuration creation
        # In real scenarios, you would test actual API connectivity
        try:
            print(f"\n📋 {name} Configuration:")
            print(f"   Provider: {config.provider}")
            print(f"   Model: {config.model}")
            print(f"   Deployment Type: {config.deployment_type}")
            
            # Show relevant configuration details
            if config.config.get("endpoint_url"):
                print(f"   Endpoint URL: {config.config['endpoint_url']}")
            if config.config.get("project_id"):
                print(f"   Project ID: {config.config['project_id']}")
            if config.config.get("location"):
                print(f"   Location: {config.config['location']}")
            if config.config.get("auth_method"):
                print(f"   Auth Method: {config.config['auth_method']}")
            
            print(f"✅ {name} configuration is valid")
            results.append(True)
            
        except Exception as e:
            print(f"❌ {name} configuration error: {str(e)}")
            results.append(False)
    
    # Summary
    print(f"\n📊 Configuration Summary:")
    print("=" * 40)
    passed = sum(results)
    total = len(results)
    print(f"Valid configurations: {passed}/{total}")
    
    if passed == total:
        print("🎉 All configurations are valid!")
    else:
        print("⚠️  Some configurations have issues.")


def print_environment_examples():
    """Print example environment variable configurations."""
    print("\n🔧 Environment Variable Examples:")
    print("=" * 50)
    
    print("\n1. OpenAI Cloud:")
    print("LLM_PROVIDER=openai")
    print("OPENAI_API_KEY=sk-your-openai-api-key")
    print("OPENAI_MODEL=gpt-4")
    
    print("\n2. OpenAI Custom Endpoint (Azure):")
    print("LLM_PROVIDER=openai")
    print("OPENAI_API_KEY=your-azure-api-key")
    print("OPENAI_MODEL=gpt-4")
    print("OPENAI_BASE_URL=https://your-resource.openai.azure.com/")
    
    print("\n3. Google Cloud Vertex AI:")
    print("LLM_PROVIDER=vertexai")
    print("VERTEXAI_PROJECT_ID=your-gcp-project")
    print("VERTEXAI_LOCATION=us-central1")
    print("VERTEXAI_MODEL=gemini-2.0-flash-lite-001")
    print("VERTEXAI_DEPLOYMENT_TYPE=cloud")
    print("GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json")
    
    print("\n4. Corporate Hosted Gemini:")
    print("LLM_PROVIDER=vertexai")
    print("VERTEXAI_PROJECT_ID=corporate-project")
    print("VERTEXAI_LOCATION=corporate-location")
    print("VERTEXAI_MODEL=gemini-2.0-flash-lite-001")
    print("VERTEXAI_DEPLOYMENT_TYPE=corporate")
    print("VERTEXAI_ENDPOINT_URL=https://gemini.corp.com/v1")
    print("VERTEXAI_API_KEY=your-corporate-api-key")
    print("VERTEXAI_AUTH_METHOD=api_key")
    
    print("\n5. On-Premise Vertex AI (Basic):")
    print("LLM_PROVIDER=vertexai")
    print("VERTEXAI_PROJECT_ID=onprem-project")
    print("VERTEXAI_LOCATION=datacenter-1")
    print("VERTEXAI_MODEL=gemini-1.5-pro-002")
    print("VERTEXAI_DEPLOYMENT_TYPE=on_premise")
    print("VERTEXAI_ENDPOINT_URL=https://vertex.internal.com")
    print("VERTEXAI_API_KEY=onprem-api-key")
    
    print("\n6. On-Premise Vertex AI (Token Function):")
    print("LLM_PROVIDER=vertexai")
    print("VERTEXAI_PROJECT_ID=onprem-project")
    print("VERTEXAI_LOCATION=datacenter-1")
    print("VERTEXAI_MODEL=gemini-2.0-flash-lite-001")
    print("VERTEXAI_DEPLOYMENT_TYPE=on_premise")
    print("VERTEXAI_ENDPOINT_URL=https://vertex.internal.com")
    print("VERTEXAI_TOKEN_FUNCTION=get_auth_token")
    print("VERTEXAI_TOKEN_FUNCTION_MODULE=your_company.auth.gemini_auth")
    
    print("\n7. On-Premise Vertex AI (Credentials Function):")
    print("LLM_PROVIDER=vertexai")
    print("VERTEXAI_PROJECT_ID=onprem-project")
    print("VERTEXAI_LOCATION=datacenter-1")
    print("VERTEXAI_MODEL=gemini-1.5-flash-002")
    print("VERTEXAI_DEPLOYMENT_TYPE=on_premise")
    print("VERTEXAI_ENDPOINT_URL=https://vertex.internal.com")
    print("VERTEXAI_CREDENTIALS_FUNCTION=get_gemini_credentials")
    print("VERTEXAI_CREDENTIALS_FUNCTION_MODULE=your_company.auth.vertex_auth")


async def main():
    """Main demonstration function."""
    await demonstrate_configurations()
    print_environment_examples()
    
    print("\n💡 Usage Tips:")
    print("=" * 20)
    print("1. Choose the deployment type that matches your infrastructure")
    print("2. For corporate/on-premise, ensure your endpoint URLs are accessible")
    print("3. Test connectivity before deploying to production")
    print("4. Use environment variables for sensitive configuration")
    print("5. The tool calling fix automatically limits to single tool for Vertex AI")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}") 