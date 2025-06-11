#!/usr/bin/env python3
"""
Debug script for SSL certificate verification issues with on-premise Vertex AI deployments.
This script helps diagnose and resolve common SSL certificate problems.
"""

import os
import sys
import ssl
import socket
import requests
import urllib3
from urllib.parse import urlparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_ssl_connection(endpoint_url):
    """Test direct SSL connection to the endpoint."""
    try:
        parsed_url = urlparse(endpoint_url)
        hostname = parsed_url.hostname
        port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)
        
        logger.info(f"SSL_TEST: Testing direct SSL connection to {hostname}:{port}")
        
        # Create SSL context
        context = ssl.create_default_context()
        
        # Test with verification enabled
        try:
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    logger.info(f"SSL_TEST_SUCCESS: SSL connection successful with verification")
                    logger.info(f"SSL_CERT_INFO: Certificate version: {ssock.version()}")
                    cert = ssock.getpeercert()
                    logger.info(f"SSL_CERT_INFO: Subject: {cert.get('subject')}")
                    logger.info(f"SSL_CERT_INFO: Issuer: {cert.get('issuer')}")
                    logger.info(f"SSL_CERT_INFO: Serial: {cert.get('serialNumber')}")
                    return True
        except ssl.SSLCertVerificationError as e:
            logger.error(f"SSL_TEST_FAILED: Certificate verification failed: {e}")
            return False
        except Exception as e:
            logger.error(f"SSL_TEST_ERROR: SSL connection error: {e}")
            return False
    except Exception as e:
        logger.error(f"SSL_TEST_ERROR: General connection error: {e}")
        return False

def test_requests_with_ssl_options(endpoint_url):
    """Test HTTP requests with different SSL configurations."""
    logger.info(f"REQUESTS_TEST: Testing HTTP requests to {endpoint_url}")
    
    # Test 1: With SSL verification (should fail for self-signed certs)
    try:
        logger.info("REQUESTS_TEST: Testing with SSL verification enabled...")
        response = requests.get(f"{endpoint_url}/health", timeout=10, verify=True)
        logger.info(f"REQUESTS_SUCCESS: SSL verification enabled - Status: {response.status_code}")
    except requests.exceptions.SSLError as e:
        logger.error(f"REQUESTS_SSL_ERROR: SSL verification failed: {e}")
    except Exception as e:
        logger.error(f"REQUESTS_ERROR: Request failed: {e}")
    
    # Test 2: With SSL verification disabled
    try:
        logger.info("REQUESTS_TEST: Testing with SSL verification disabled...")
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        response = requests.get(f"{endpoint_url}/health", timeout=10, verify=False)
        logger.info(f"REQUESTS_SUCCESS: SSL verification disabled - Status: {response.status_code}")
    except Exception as e:
        logger.error(f"REQUESTS_ERROR: Request failed even with SSL disabled: {e}")

def test_vertex_ai_ssl_init():
    """Test Vertex AI initialization with SSL configurations."""
    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel
        
        # Get configuration from environment
        endpoint_url = os.getenv("VERTEXAI_ENDPOINT_URL")
        project_id = os.getenv("VERTEXAI_PROJECT_ID")
        ssl_verify = os.getenv("VERTEXAI_SSL_VERIFY", "true").lower() == "true"
        api_transport = os.getenv("VERTEXAI_API_TRANSPORT", "rest")
        
        if not endpoint_url or not project_id:
            logger.error("VERTEX_TEST_ERROR: Missing required environment variables VERTEXAI_ENDPOINT_URL or VERTEXAI_PROJECT_ID")
            return False
        
        logger.info(f"VERTEX_TEST: Testing Vertex AI initialization")
        logger.info(f"VERTEX_TEST: endpoint_url={endpoint_url}")
        logger.info(f"VERTEX_TEST: project_id={project_id}")
        logger.info(f"VERTEX_TEST: ssl_verify={ssl_verify}")
        logger.info(f"VERTEX_TEST: api_transport={api_transport}")
        
        # Configure SSL environment if verification is disabled
        if not ssl_verify:
            logger.warning("VERTEX_SSL: Disabling SSL verification for test")
            os.environ["PYTHONHTTPSVERIFY"] = "0"
            os.environ["CURL_CA_BUNDLE"] = ""
            os.environ["REQUESTS_CA_BUNDLE"] = ""
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Test initialization
        init_kwargs = {
            "project": project_id,
            "api_endpoint": endpoint_url,
        }
        
        if api_transport:
            init_kwargs["api_transport"] = api_transport
        
        logger.info(f"VERTEX_INIT: Calling vertexai.init with: {init_kwargs}")
        vertexai.init(**init_kwargs)
        
        # Test model creation
        model = GenerativeModel("gemini-pro")
        logger.info("VERTEX_SUCCESS: Vertex AI initialization successful")
        return True
        
    except Exception as e:
        logger.error(f"VERTEX_ERROR: Vertex AI initialization failed: {e}")
        return False

def print_ssl_troubleshooting_guide():
    """Print comprehensive SSL troubleshooting guide."""
    guide = """
    
=== SSL CERTIFICATE TROUBLESHOOTING GUIDE ===

If you're getting SSL certificate verification errors, here are the solutions:

1. QUICK FIX (Development Only - Insecure):
   Add to your .env file:
   VERTEXAI_SSL_VERIFY=false
   
   This disables SSL verification entirely. Only use in development!

2. PROPER SOLUTION (Production):
   
   a) Get the CA certificate from your IT department or:
      openssl s_client -showcerts -connect your-endpoint:443 < /dev/null 2>/dev/null | openssl x509 -outform PEM > ca-cert.pem
   
   b) Add to your .env file:
      VERTEXAI_SSL_CA_CERT_PATH=/path/to/ca-cert.pem
   
   c) Or set system-wide:
      export REQUESTS_CA_BUNDLE=/path/to/ca-cert.pem
      export CURL_CA_BUNDLE=/path/to/ca-cert.pem

3. CORPORATE PROXY/FIREWALL:
   Your network may be intercepting SSL traffic. Contact IT for:
   - Corporate CA bundle
   - Proxy configuration
   - Firewall exceptions

4. COMMON ISSUES:
   - Self-signed certificates (common in development)
   - Corporate certificate authorities not in system trust store
   - Proxy servers with certificate inspection
   - Outdated certificate bundles

5. TESTING:
   Run this script to diagnose: python test_ssl_debug.py

6. ENVIRONMENT VARIABLES:
   VERTEXAI_SSL_VERIFY=false          # Disable verification (insecure)
   VERTEXAI_SSL_CA_CERT_PATH=path     # Custom CA certificate
   REQUESTS_CA_BUNDLE=path            # System-wide CA bundle
   CURL_CA_BUNDLE=path                # System-wide CA bundle
   
=== END TROUBLESHOOTING GUIDE ===
    """
    print(guide)

def main():
    """Main function to run all SSL tests."""
    logger.info("Starting SSL certificate debugging for Vertex AI...")
    
    endpoint_url = os.getenv("VERTEXAI_ENDPOINT_URL")
    if not endpoint_url:
        logger.error("ERROR: VERTEXAI_ENDPOINT_URL environment variable is required")
        print_ssl_troubleshooting_guide()
        return
    
    logger.info(f"Testing endpoint: {endpoint_url}")
    
    # Test 1: Direct SSL connection
    ssl_success = test_ssl_connection(endpoint_url)
    
    # Test 2: HTTP requests with different SSL options
    test_requests_with_ssl_options(endpoint_url)
    
    # Test 3: Vertex AI initialization
    vertex_success = test_vertex_ai_ssl_init()
    
    # Summary
    logger.info("\n=== TEST SUMMARY ===")
    logger.info(f"SSL Connection Test: {'PASS' if ssl_success else 'FAIL'}")
    logger.info(f"Vertex AI Init Test: {'PASS' if vertex_success else 'FAIL'}")
    
    if not ssl_success or not vertex_success:
        print_ssl_troubleshooting_guide()
    else:
        logger.info("All SSL tests passed! Your configuration should work.")

if __name__ == "__main__":
    main() 