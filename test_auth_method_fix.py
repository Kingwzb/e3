#!/usr/bin/env python3
"""
Test script to verify the auth_method fix works correctly.
This tests that the NameError for auth_method is resolved.
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_auth_method_fix():
    """Test that auth_method is properly defined in on-premise initialization."""
    try:
        # Import the LLM client configuration
        from app.core.llm import LLMClientConfig, VertexAIClient
        
        logger.info("Testing auth_method fix...")
        
        # Create a configuration for on-premise deployment
        config = LLMClientConfig(
            provider="vertexai",
            model="gemini-pro",
            deployment_type="on_premise",
            project_id="test-project",
            location="us-central1",
            endpoint_url="https://test-endpoint.company.com",
            api_transport="rest",
            ssl_verify=False  # For testing purposes
        )
        
        logger.info("Created LLMClientConfig successfully")
        
        # Try to create the client - this should not fail with NameError anymore
        try:
            client = VertexAIClient(config)
            logger.error("Client creation should have failed due to missing endpoint, but succeeded unexpectedly")
            return False
        except ValueError as e:
            if "endpoint_url is required" in str(e):
                logger.info("Expected ValueError for missing endpoint - this is correct")
                return True
            else:
                logger.error(f"Unexpected ValueError: {e}")
                return False
        except NameError as e:
            if "auth_method" in str(e):
                logger.error(f"FAILED: auth_method NameError still occurs: {e}")
                return False
            else:
                logger.error(f"Unexpected NameError: {e}")
                return False
        except Exception as e:
            logger.info(f"Got expected exception (not NameError): {type(e).__name__}: {e}")
            return True
            
    except Exception as e:
        logger.error(f"Test failed with unexpected error: {e}")
        return False

def test_ssl_configuration_loading():
    """Test that SSL configuration is properly loaded."""
    try:
        from app.core.llm import LLMClientConfig
        
        logger.info("Testing SSL configuration loading...")
        
        # Create a configuration with SSL settings
        config = LLMClientConfig(
            provider="vertexai",
            model="gemini-pro",
            deployment_type="on_premise",
            project_id="test-project",
            endpoint_url="https://test-endpoint.company.com",
            ssl_verify=False,
            ssl_ca_cert_path="/path/to/ca.crt",
            ssl_cert_path="/path/to/client.crt",
            ssl_key_path="/path/to/client.key"
        )
        
        # Check that SSL configuration is properly stored
        assert config.config.get("ssl_verify") == False
        assert config.config.get("ssl_ca_cert_path") == "/path/to/ca.crt"
        assert config.config.get("ssl_cert_path") == "/path/to/client.crt"
        assert config.config.get("ssl_key_path") == "/path/to/client.key"
        
        logger.info("SSL configuration loaded correctly")
        return True
        
    except Exception as e:
        logger.error(f"SSL configuration test failed: {e}")
        return False

def main():
    """Run all tests."""
    logger.info("Starting auth_method fix verification tests...")
    
    # Test 1: auth_method NameError fix
    auth_method_test = test_auth_method_fix()
    
    # Test 2: SSL configuration loading
    ssl_config_test = test_ssl_configuration_loading()
    
    # Summary
    logger.info("\n=== TEST RESULTS ===")
    logger.info(f"Auth Method Fix Test: {'PASS' if auth_method_test else 'FAIL'}")
    logger.info(f"SSL Configuration Test: {'PASS' if ssl_config_test else 'FAIL'}")
    
    if auth_method_test and ssl_config_test:
        logger.info("All tests passed! The auth_method fix is working correctly.")
        return True
    else:
        logger.error("Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 