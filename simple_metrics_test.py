#!/usr/bin/env python3
"""
Simple test for metrics node functionality.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_database_connection():
    """Test basic database connection."""
    try:
        from app.core.database import AsyncSessionLocal
        from sqlalchemy import text
        
        print("✅ Database imports successful")
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT COUNT(*) FROM metrics_data"))
            count = result.scalar()
            print(f"✅ Database connection successful - Found {count} metrics records")
            return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

async def test_db_extract_functions():
    """Test database extraction functions."""
    try:
        from app.tools.db_extract import extract_metrics_summary
        
        print("✅ DB extract imports successful")
        
        summary = await extract_metrics_summary()
        print(f"✅ Metrics summary extracted: {summary}")
        return True
    except Exception as e:
        print(f"❌ DB extract test failed: {e}")
        return False

async def test_vector_store():
    """Test vector store functionality."""
    try:
        from app.tools.vector_store import VectorStore
        
        print("✅ Vector store imports successful")
        
        vs = VectorStore()
        docs = vs.similarity_search("metrics", k=2)
        print(f"✅ Vector store search successful - Found {len(docs)} documents")
        return True
    except Exception as e:
        print(f"❌ Vector store test failed: {e}")
        return False

async def test_openai_client():
    """Test OpenAI client functionality."""
    try:
        from app.api.openai_client import OpenAIClient
        
        print("✅ OpenAI client imports successful")
        
        client = OpenAIClient()
        
        # Simple test message
        messages = [{"role": "user", "content": "Hello, can you respond with 'Test successful'?"}]
        response = await client.chat_completion(messages=messages, max_tokens=50)
        
        print(f"✅ OpenAI API test successful: {response.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"❌ OpenAI client test failed: {e}")
        return False

async def main():
    """Run all simple tests."""
    print("🧪 RUNNING SIMPLE METRICS TESTS")
    print("=" * 40)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("DB Extract Functions", test_db_extract_functions),
        ("Vector Store", test_vector_store),
        ("OpenAI Client", test_openai_client),
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n🔍 Testing: {test_name}")
        print("-" * 20)
        results[test_name] = await test_func()
    
    print("\n" + "=" * 40)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 40)
    
    passed = 0
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("\n🎉 All components are working! Ready for metrics node testing.")
    else:
        print(f"\n⚠️  {len(tests) - passed} components need attention before full testing.")

if __name__ == "__main__":
    asyncio.run(main()) 