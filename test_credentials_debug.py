#!/usr/bin/env python3
"""
Debug script to test credentials handling and fix the 'before_request' attribute error.
This will help identify issues with credentials objects in Vertex AI initialization.
"""

import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings
from app.core.llm import LLMClientFactory, LLMClientConfig
from app.utils.logging import logger

def test_credentials_handling():
    """Test credentials handling to identify the 'before_request' error."""
    print("🔧 Testing Credentials Handling for Vertex AI")
    print("=" * 60)
    
    # Test 1: Basic configuration check
    print("📋 Step 1: Check basic configuration...")
    print(f"   LLM Provider: {settings.llm_provider}")
    print(f"   Deployment Type: {getattr(settings, 'vertexai_deployment_type', 'cloud')}")
    print(f"   Project ID: {settings.vertexai_project_id}")
    print(f"   Credentials Path: {settings.google_application_credentials}")
    print()
    
    # Test 2: Test with minimal configuration (no custom credentials)
    print("📋 Step 2: Test with minimal configuration (no custom auth functions)...")
    try:
        minimal_config = LLMClientConfig(
            provider="vertexai",
            model=settings.vertexai_model,
            deployment_type="cloud",  # Use cloud first to avoid custom auth
            project_id=settings.vertexai_project_id,
            location=settings.vertexai_location,
            credentials_path=settings.google_application_credentials
        )
        
        print("   Creating minimal cloud client...")
        minimal_client = LLMClientFactory.create_client(minimal_config)
        print("   ✅ Minimal cloud client created successfully")
    except Exception as e:
        print(f"   ⚠️  Minimal cloud client failed: {str(e)}")
    print()
    
    # Test 3: Test on-premise without custom credentials
    print("📋 Step 3: Test on-premise without custom credentials...")
    try:
        onprem_basic_config = LLMClientConfig(
            provider="vertexai",
            model=settings.vertexai_model,
            deployment_type="on_premise",
            project_id=settings.vertexai_project_id,
            location=settings.vertexai_location,
            credentials_path=settings.google_application_credentials,
            endpoint_url="https://test-endpoint.example.com/v1",
            api_transport="rest"
        )
        
        print("   Creating basic on-premise client (no custom auth functions)...")
        onprem_basic_client = LLMClientFactory.create_client(onprem_basic_config)
        print("   ✅ Basic on-premise client created successfully")
    except Exception as e:
        print(f"   ⚠️  Basic on-premise client failed: {str(e)}")
        if "'str' object has no attribute 'before_request'" in str(e):
            print("   🔍 This is the 'before_request' error we're trying to fix!")
    print()
    
    # Test 4: Test credentials object creation
    print("📋 Step 4: Test credentials object creation...")
    try:
        from google.oauth2 import credentials as oauth2_credentials
        
        # Test creating credentials from token
        test_token = "test_token_string"
        test_creds = oauth2_credentials.Credentials(token=test_token)
        
        print(f"   Created test credentials: {type(test_creds)}")
        print(f"   Has before_request: {hasattr(test_creds, 'before_request')}")
        print(f"   Has refresh: {hasattr(test_creds, 'refresh')}")
        print(f"   Token: {test_creds.token}")
        print("   ✅ Credentials object creation works correctly")
    except Exception as e:
        print(f"   ❌ Credentials object creation failed: {str(e)}")
    print()
    
    # Test 5: Test with mock custom functions
    print("📋 Step 5: Test with mock custom functions...")
    
    def mock_token_function():
        """Mock token function that returns a string token."""
        return "mock_token_12345"
    
    def mock_credentials_function():
        """Mock credentials function that returns proper credentials object."""
        from google.oauth2 import credentials as oauth2_credentials
        return oauth2_credentials.Credentials(token="mock_creds_token_67890")
    
    def bad_credentials_function():
        """Bad function that returns a string instead of credentials object."""
        return "this_should_be_a_credentials_object_not_a_string"
    
    # Test good token function
    try:
        print("   Testing good token function...")
        token_result = mock_token_function()
        print(f"   Token function returned: {type(token_result)} = {repr(token_result)}")
        
        from google.oauth2 import credentials as oauth2_credentials
        if isinstance(token_result, str):
            creds = oauth2_credentials.Credentials(token=token_result)
            print(f"   Created credentials from token: {type(creds)}")
            print(f"   Credentials has before_request: {hasattr(creds, 'before_request')}")
            print("   ✅ Good token function works correctly")
    except Exception as e:
        print(f"   ❌ Good token function failed: {str(e)}")
    
    # Test good credentials function
    try:
        print("   Testing good credentials function...")
        creds_result = mock_credentials_function()
        print(f"   Credentials function returned: {type(creds_result)}")
        print(f"   Has before_request: {hasattr(creds_result, 'before_request')}")
        print(f"   Has refresh: {hasattr(creds_result, 'refresh')}")
        print("   ✅ Good credentials function works correctly")
    except Exception as e:
        print(f"   ❌ Good credentials function failed: {str(e)}")
    
    # Test bad credentials function
    try:
        print("   Testing bad credentials function...")
        bad_result = bad_credentials_function()
        print(f"   Bad function returned: {type(bad_result)} = {repr(bad_result)}")
        print(f"   Has before_request: {hasattr(bad_result, 'before_request')}")
        print("   ❌ This would cause the 'before_request' error!")
    except Exception as e:
        print(f"   ❌ Bad credentials function test failed: {str(e)}")
    
    print()
    
    return True

def main():
    """Main function to run the credentials debug tests."""
    print("🚀 Starting Credentials Debug Test for Vertex AI")
    print("This test will help identify and fix the 'before_request' attribute error.")
    print()
    
    success = test_credentials_handling()
    
    if success:
        print("\n🎯 Credentials debug test completed!")
        print()
        print("💡 Key findings:")
        print("   1. The 'before_request' error occurs when a string is passed as credentials")
        print("   2. Proper credentials objects have 'before_request' or 'refresh' attributes")
        print("   3. Token functions should return strings, credentials functions should return credential objects")
        print("   4. The code now validates credentials objects before using them")
        print()
        print("🔧 If you're still getting the error:")
        print("   1. Check if your custom token/credentials functions return the correct types")
        print("   2. Token functions should return strings")
        print("   3. Credentials functions should return proper credentials objects")
        print("   4. The enhanced error handling will now retry without credentials if validation fails")
    else:
        print("\n💥 Credentials debug test failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 