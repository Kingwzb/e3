#!/usr/bin/env python3
"""
Test script to verify Vertex AI embeddings functionality.
Make sure to set up your environment variables before running this script.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings
from app.core.llm import LLMClientFactory, LLMClientConfig
from app.tools.vector_store import VectorStore, initialize_sample_documents
from app.utils.logging import logger

async def test_vertex_embeddings():
    """Test Vertex AI embeddings functionality."""
    print("🔧 Testing Vertex AI Embeddings Integration")
    print("=" * 50)
    
    # Check environment configuration
    print(f"📋 Configuration:")
    print(f"   LLM Provider: {settings.llm_provider}")
    print(f"   Embeddings Model: {settings.embeddings_model}")
    print(f"   Vertex AI Project: {settings.vertexai_project_id}")
    print(f"   Vertex AI Location: {settings.vertexai_location}")
    print()
    
    if settings.llm_provider != "vertexai":
        print("❌ Error: LLM_PROVIDER must be set to 'vertexai' in your .env file")
        return False
    
    if not settings.vertexai_project_id:
        print("❌ Error: VERTEXAI_PROJECT_ID must be set in your .env file")
        return False
    
    try:
        # Test 1: Initialize LLM Client
        print("🧪 Test 1: Initialize Vertex AI client...")
        config = LLMClientConfig(
            provider="vertexai",
            model=settings.vertexai_model,
            deployment_type=getattr(settings, 'vertexai_deployment_type', 'cloud'),
            project_id=settings.vertexai_project_id,
            location=settings.vertexai_location,
            credentials_path=settings.google_application_credentials
        )
        client = LLMClientFactory.create_client(config)
        print("✅ Vertex AI client initialized successfully")
        
        # Test 2: Generate embeddings directly
        print("\n🧪 Test 2: Generate embeddings directly...")
        test_texts = [
            "This is a test sentence for embedding generation.",
            "Vertex AI provides powerful embedding models.",
            "Corporate firewalls block external model downloads."
        ]
        
        embeddings = await client.generate_embeddings(test_texts)
        print(f"✅ Generated embeddings for {len(test_texts)} texts")
        print(f"   Embedding dimension: {len(embeddings[0]) if embeddings else 'Unknown'}")
        
        # Test 3: Initialize Vector Store
        print("\n🧪 Test 3: Initialize Vector Store...")
        vector_store = VectorStore()
        print("✅ Vector store initialized successfully")
        print(f"   Index dimension: {vector_store.dimension}")
        print(f"   Model name: {vector_store.embeddings_model_name}")
        
        # Test 4: Add documents to Vector Store
        print("\n🧪 Test 4: Add sample documents...")
        vector_store = initialize_sample_documents()
        stats = vector_store.get_stats()
        print(f"✅ Vector store populated with {stats['total_documents']} documents")
        
        # Test 5: Search functionality
        print("\n🧪 Test 5: Test search functionality...")
        search_query = "What is machine learning?"
        results = vector_store.search(search_query, k=3, min_score=0.1)
        
        print(f"✅ Search completed for query: '{search_query}'")
        print(f"   Found {len(results.sources)} relevant documents")
        print(f"   Confidence score: {results.confidence_score:.3f}")
        
        if results.sources:
            print("   Top result:")
            top_result = results.sources[0]
            print(f"     Content: {top_result['content'][:100]}...")
            print(f"     Score: {top_result['score']:.3f}")
        
        print("\n🎉 All tests passed! Vertex AI embeddings are working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        logger.error(f"Vertex AI embeddings test failed: {str(e)}")
        return False

def main():
    """Main function to run the tests."""
    print("🚀 Starting Vertex AI Embeddings Test")
    print("Make sure you have:")
    print("1. Set LLM_PROVIDER=vertexai in your .env file")
    print("2. Configured Vertex AI credentials")
    print("3. Set VERTEXAI_PROJECT_ID and VERTEXAI_LOCATION")
    print()
    
    success = asyncio.run(test_vertex_embeddings())
    
    if success:
        print("\n🎯 Summary: All tests passed successfully!")
        print("Your application is now configured to use Vertex AI embeddings")
        print("instead of the blocked all-MiniLM-L6-v2 model.")
    else:
        print("\n💥 Summary: Tests failed!")
        print("Please check your configuration and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main() 