#!/usr/bin/env python3
"""
Test script to demonstrate detailed logging for vertexai.init and get_embeddings calls.
This script will trigger the logging we added to show complete parameter details.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings
from app.core.llm import LLMClientFactory, LLMClientConfig
from app.tools.vector_store import VectorStore
from app.utils.logging import logger

async def test_detailed_logging():
    """Test the detailed logging for vertexai.init and get_embeddings calls."""
    print("🔧 Testing Detailed Logging for Vertex AI Calls")
    print("=" * 60)
    
    # Check environment configuration
    print(f"📋 Configuration:")
    print(f"   LLM Provider: {settings.llm_provider}")
    print(f"   Embeddings Model: {settings.embeddings_model}")
    print(f"   Vertex AI Project: {settings.vertexai_project_id}")
    print(f"   Vertex AI Location: {settings.vertexai_location}")
    print(f"   Deployment Type: {getattr(settings, 'vertexai_deployment_type', 'cloud')}")
    print()
    
    if settings.llm_provider != "vertexai":
        print("❌ Error: LLM_PROVIDER must be set to 'vertexai' in your .env file")
        return False
    
    try:
        print("🧪 Test 1: Initialize Vertex AI client (will trigger VERTEXAI_INIT_CALL logging)...")
        print("Look for 'VERTEXAI_INIT_CALL' in the logs below:")
        print("-" * 40)
        
        # This will trigger vertexai.init logging
        config = LLMClientConfig(
            provider="vertexai",
            model=settings.vertexai_model,
            deployment_type=getattr(settings, 'vertexai_deployment_type', 'cloud'),
            project_id=settings.vertexai_project_id,
            location=settings.vertexai_location,
            credentials_path=settings.google_application_credentials,
            # Add some test metadata
            endpoint_url=getattr(settings, 'vertexai_endpoint_url', None),
            api_transport=getattr(settings, 'vertexai_api_transport', None)
        )
        client = LLMClientFactory.create_client(config)
        print("✅ Vertex AI client initialized successfully")
        print()
        
        # Test with custom endpoint to demonstrate location parameter handling
        if getattr(settings, 'vertexai_deployment_type', 'cloud') in ['on_premise', 'corporate']:
            print("🧪 Test 1b: Testing custom endpoint behavior (location parameter handling)...")
            print("Look for location parameter handling in the logs:")
            print("-" * 40)
            
            # Create a config with custom endpoint to test location parameter behavior
            custom_config = LLMClientConfig(
                provider="vertexai",
                model=settings.vertexai_model,
                deployment_type=getattr(settings, 'vertexai_deployment_type', 'cloud'),
                project_id=settings.vertexai_project_id,
                location=settings.vertexai_location,
                credentials_path=settings.google_application_credentials,
                endpoint_url="https://custom-vertex-endpoint.example.com/v1",  # Custom endpoint
                api_transport=getattr(settings, 'vertexai_api_transport', None)
            )
            
            try:
                custom_client = LLMClientFactory.create_client(custom_config)
                print("✅ Custom endpoint client initialized (location parameter should be skipped)")
            except Exception as e:
                print(f"⚠️  Custom endpoint test failed (expected for demo): {str(e)}")
            print()
        
        print("🧪 Test 2: Generate embeddings directly (will trigger GET_EMBEDDINGS_CALL logging)...")
        print("Look for 'GET_EMBEDDINGS_CALL' in the logs below:")
        print("-" * 40)
        
        # This will trigger get_embeddings logging
        test_texts = [
            "This is a test sentence for embedding generation with detailed logging.",
            "Vertex AI provides powerful embedding models for enterprise use.",
            "The detailed logging shows all parameters passed to each API call."
        ]
        
        # Add some test metadata with more comprehensive values
        test_metadata = {
            "test_session": "detailed_logging_test",
            "timestamp": "2024-01-01T00:00:00Z",
            "user_id": "test_user_12345",
            "request_id": "req_abc123def456",
            "environment": "development",
            "api_version": "v1.2.3",
            "client_info": {
                "name": "test_client",
                "version": "1.0.0",
                "platform": "linux"
            },
            "processing_options": {
                "batch_size": 5,
                "normalize": True,
                "task_type": "RETRIEVAL_DOCUMENT"
            },
            "security_context": {
                "tenant_id": "tenant_789",
                "permissions": ["read", "embed"],
                "classification": "internal"
            }
        }
        
        embeddings = await client.generate_embeddings(test_texts, metadata=test_metadata)
        print(f"✅ Generated embeddings for {len(test_texts)} texts")
        print(f"   Embedding dimension: {len(embeddings[0]) if embeddings else 'Unknown'}")
        print()
        
        print("🧪 Test 3: Test Vector Store operations (will trigger additional embedding requests)...")
        print("Look for 'VECTOR_STORE_EMBEDDINGS_REQUEST' and subsequent 'GET_EMBEDDINGS_CALL' in the logs:")
        print("-" * 40)
        
        # This will trigger vector store embedding requests
        vector_store = VectorStore()
        
        # Add some test documents with comprehensive metadata
        test_documents = [
            {
                "content": "Machine learning is a subset of artificial intelligence that focuses on algorithms.",
                "metadata": {
                    "category": "AI",
                    "source": "test_doc_1",
                    "author": "AI Research Team",
                    "created_date": "2024-01-01",
                    "tags": ["machine-learning", "artificial-intelligence", "algorithms"],
                    "confidence_score": 0.95,
                    "language": "en",
                    "document_type": "educational",
                    "access_level": "public"
                }
            },
            {
                "content": "Deep learning uses neural networks with multiple layers to process data.",
                "metadata": {
                    "category": "AI",
                    "source": "test_doc_2",
                    "author": "Deep Learning Experts",
                    "created_date": "2024-01-02",
                    "tags": ["deep-learning", "neural-networks", "data-processing"],
                    "confidence_score": 0.92,
                    "language": "en",
                    "document_type": "technical",
                    "access_level": "internal"
                }
            },
            {
                "content": "Natural language processing helps computers understand human language.",
                "metadata": {
                    "category": "NLP",
                    "source": "test_doc_3",
                    "author": "NLP Research Group",
                    "created_date": "2024-01-03",
                    "tags": ["nlp", "natural-language-processing", "human-language"],
                    "confidence_score": 0.88,
                    "language": "en",
                    "document_type": "research",
                    "access_level": "restricted"
                }
            }
        ]
        
        vector_store.add_documents(test_documents)
        print("✅ Added test documents to vector store")
        
        # Perform a search (will trigger more embedding requests)
        search_query = "What is machine learning?"
        results = vector_store.search(search_query, k=2, min_score=0.1)
        print(f"✅ Search completed for query: '{search_query}'")
        print(f"   Found {len(results.sources)} relevant documents")
        print()
        
        print("🎉 All tests completed! Check the logs above for detailed parameter logging.")
        print()
        print("📝 Summary of logged calls with complete values:")
        print("   - VERTEXAI_INIT_CALL: Shows all parameters passed to vertexai.init() with complete values")
        print("     * For cloud deployments: Includes project + location")
        print("     * For custom endpoints: Includes project + api_endpoint (location skipped)")
        print("   - GET_EMBEDDINGS_CALL: Shows all parameters passed to get_embeddings() with complete metadata values")
        print("   - VECTOR_STORE_EMBEDDINGS_REQUEST: Shows embedding requests from vector store with full metadata")
        print("   - GENERATE_EMBEDDINGS_INPUT: Shows complete input parameters and metadata values")
        print("   - METADATA_MERGE: Shows how global and call-specific metadata are combined")
        print("   - EMBEDDING_MODEL_CONFIG: Shows model configuration and final metadata values")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        logger.error(f"Detailed logging test failed: {str(e)}")
        return False

def main():
    """Main function to run the detailed logging tests."""
    print("🚀 Starting Enhanced Detailed Logging Test for Vertex AI")
    print("This test will demonstrate the comprehensive logging we added for:")
    print("1. All vertexai.init() calls with complete parameter values (not just keys)")
    print("2. All get_embeddings() calls with complete metadata values (not just keys)")
    print("3. Complete metadata merging and processing details")
    print("4. Full configuration and context information")
    print()
    
    success = asyncio.run(test_detailed_logging())
    
    if success:
        print("\n🎯 Summary: Enhanced detailed logging test completed successfully!")
        print("You should see comprehensive parameter logging with complete values for all Vertex AI API calls above.")
        print("The logs now include:")
        print("  ✅ Complete metadata dictionaries (not just keys)")
        print("  ✅ Full parameter values for all API calls")
        print("  ✅ Configuration details and context information")
        print("  ✅ Batch processing and model configuration details")
    else:
        print("\n💥 Summary: Enhanced detailed logging test failed!")
        print("Please check your configuration and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main() 