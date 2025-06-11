#!/usr/bin/env python3
"""
Debug script to test api_transport configuration reading from environment variables.
This will help identify why api_transport is not being set in on-premise mode.
"""

import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings
from app.core.llm import LLMClientFactory, LLMClientConfig
from app.utils.logging import logger

def test_api_transport_config():
    """Test api_transport configuration reading and setup."""
    print("🔧 Testing API Transport Configuration")
    print("=" * 50)
    
    # Check environment variables directly
    print("📋 Environment Variables:")
    env_vars = [
        "VERTEXAI_API_TRANSPORT",
        "VERTEXAI_DEPLOYMENT_TYPE", 
        "VERTEXAI_ENDPOINT_URL",
        "LLM_PROVIDER"
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        print(f"   {var}={repr(value)} (type: {type(value)})")
    print()
    
    # Check settings object
    print("📋 Settings Object:")
    print(f"   settings.vertexai_api_transport={repr(settings.vertexai_api_transport)}")
    print(f"   settings.vertexai_deployment_type={repr(settings.vertexai_deployment_type)}")
    print(f"   settings.vertexai_endpoint_url={repr(settings.vertexai_endpoint_url)}")
    print(f"   settings.llm_provider={repr(settings.llm_provider)}")
    print()
    
    # Check using getattr (same as in the code)
    print("📋 Using getattr (same as code):")
    api_transport_getattr = getattr(settings, 'vertexai_api_transport', None)
    print(f"   getattr(settings, 'vertexai_api_transport', None)={repr(api_transport_getattr)}")
    print(f"   Type: {type(api_transport_getattr)}")
    print(f"   Bool: {bool(api_transport_getattr)}")
    print()
    
    # Test creating config
    print("📋 Creating LLM Config:")
    try:
        # Create config manually to test
        config = LLMClientConfig(
            provider="vertexai",
            model=settings.vertexai_model,
            deployment_type=getattr(settings, 'vertexai_deployment_type', 'cloud'),
            project_id=settings.vertexai_project_id,
            location=settings.vertexai_location,
            credentials_path=settings.google_application_credentials,
            endpoint_url=getattr(settings, 'vertexai_endpoint_url', None),
            api_transport=getattr(settings, 'vertexai_api_transport', None)
        )
        
        print(f"   Config created successfully")
        print(f"   config.config['api_transport']={repr(config.config.get('api_transport'))}")
        print(f"   config.config keys={list(config.config.keys())}")
        print()
        
        # Test with manually set environment variable
        print("📋 Testing with manually set environment variable:")
        os.environ["VERTEXAI_API_TRANSPORT"] = "grpc"
        print(f"   Set VERTEXAI_API_TRANSPORT=grpc in environment")
        
        # Reload settings to pick up the new env var
        from app.core.config import Settings
        new_settings = Settings()
        print(f"   new_settings.vertexai_api_transport={repr(new_settings.vertexai_api_transport)}")
        
        # Create new config with manually set value
        manual_config = LLMClientConfig(
            provider="vertexai",
            model=new_settings.vertexai_model,
            deployment_type="on_premise",
            project_id=new_settings.vertexai_project_id,
            location=new_settings.vertexai_location,
            credentials_path=new_settings.google_application_credentials,
            endpoint_url="https://test-endpoint.example.com/v1",
            api_transport=new_settings.vertexai_api_transport
        )
        
        print(f"   manual_config.config['api_transport']={repr(manual_config.config.get('api_transport'))}")
        print()
        
        # Test REST transport specifically
        print("📋 Testing REST transport explicitly:")
        os.environ["VERTEXAI_API_TRANSPORT"] = "rest"
        print(f"   Set VERTEXAI_API_TRANSPORT=rest in environment")
        
        rest_settings = Settings()
        print(f"   rest_settings.vertexai_api_transport={repr(rest_settings.vertexai_api_transport)}")
        
        rest_config = LLMClientConfig(
            provider="vertexai",
            model=rest_settings.vertexai_model,
            deployment_type="on_premise",
            project_id=rest_settings.vertexai_project_id,
            location=rest_settings.vertexai_location,
            credentials_path=rest_settings.google_application_credentials,
            endpoint_url="https://test-endpoint.example.com/v1",
            api_transport=rest_settings.vertexai_api_transport
        )
        
        print(f"   rest_config.config['api_transport']={repr(rest_config.config.get('api_transport'))}")
        print("   Note: REST transport should now be passed explicitly to vertexai.init()")
        print()
        
        # Test LLM client creation with debug logging
        print("📋 Creating LLM Client (check logs for debug info):")
        print("Look for 'VERTEXAI_CONFIG_DEBUG' and 'VERTEXAI_INIT_DEBUG' messages:")
        print("-" * 40)
        
        try:
            client = LLMClientFactory.create_client(manual_config)
            print("✅ LLM Client created successfully")
        except Exception as e:
            print(f"⚠️  LLM Client creation failed (may be expected): {str(e)}")
        
        # Test REST client
        try:
            rest_client = LLMClientFactory.create_client(rest_config)
            print("✅ REST LLM Client created successfully")
        except Exception as e:
            print(f"⚠️  REST LLM Client creation failed (may be expected): {str(e)}")
        
    except Exception as e:
        print(f"❌ Config creation failed: {str(e)}")
        return False
    
    return True

def main():
    """Main function to run the api_transport debug tests."""
    print("🚀 Starting API Transport Debug Test")
    print("This test will help identify why api_transport is not being set.")
    print()
    
    success = test_api_transport_config()
    
    if success:
        print("\n🎯 Debug test completed!")
        print("Check the output above to see where the api_transport value is lost.")
        print()
        print("💡 Common issues and solutions:")
        print("   1. **Environment variable not set**: Add VERTEXAI_API_TRANSPORT=grpc (or rest) to your .env file")
        print("   2. **Wrong .env file location**: Ensure .env is in the project root directory")
        print("   3. **Extra quotes/spaces**: Use VERTEXAI_API_TRANSPORT=grpc (not 'grpc' or \"grpc\")")
        print("   4. **Case sensitivity**: Use exact case: VERTEXAI_API_TRANSPORT (not vertexai_api_transport)")
        print("   5. **Environment not loaded**: Restart your application after changing .env")
        print("   6. **Override by other config**: Check if other config files override the setting")
        print()
        print("🔍 To fix the issue:")
        print("   1. Add this line to your .env file:")
        print("      - For gRPC: VERTEXAI_API_TRANSPORT=grpc")
        print("      - For REST: VERTEXAI_API_TRANSPORT=rest")
        print("   2. Ensure VERTEXAI_DEPLOYMENT_TYPE=on_premise")
        print("   3. Restart your application")
        print("   4. Run this debug script again to verify")
        print("   5. Both 'rest' and 'grpc' are now passed explicitly to vertexai.init()")
        
    else:
        print("\n💥 Debug test failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 