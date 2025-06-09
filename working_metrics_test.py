#!/usr/bin/env python3
"""
Working test for metrics node functionality using actual system modules.
"""

import asyncio
import sys
from pathlib import Path
import json

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
            
            # Test querying by category
            result = await session.execute(text("""
                SELECT category, COUNT(*) as count 
                FROM metrics_data 
                GROUP BY category
                ORDER BY category
            """))
            categories = result.fetchall()
            print(f"✅ Categories available: {[row[0] for row in categories]}")
            
            return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

async def test_langchain_db_tools():
    """Test LangChain database tools."""
    try:
        from app.tools.langchain_db_tools import create_langchain_db_tools, create_tool_config_for_environment
        from app.core.database import get_db
        
        print("✅ LangChain DB tools imports successful")
        
        # Create tools
        config = create_tool_config_for_environment("development")
        print(f"✅ Created tool config: {config.allowed_categories}")
        
        async for db_session in get_db():
            tools = create_langchain_db_tools(db_session, config)
            print(f"✅ Created {len(tools)} LangChain tools: {[tool.name for tool in tools]}")
            
            # Test a tool
            metrics_tool = tools[0]  # get_metrics_by_category
            result = await metrics_tool._arun(category="engagement", days_back=7)
            print(f"✅ Tool test successful: {result[:100]}...")
            
            break
        
        return True
    except Exception as e:
        print(f"❌ LangChain DB tools test failed: {e}")
        return False

async def test_vector_store():
    """Test vector store functionality."""
    try:
        from app.tools.vector_store import VectorStore
        
        print("✅ Vector store imports successful")
        
        vs = VectorStore()
        
        # Test the correct method name 'search'
        result = vs.search("metrics performance data", k=3)
        print(f"✅ Vector store search successful - Found context: {len(result.context)} chars")
        print(f"✅ Sources: {len(result.sources)}")
        print(f"✅ Confidence: {result.confidence_score}")
        
        return True
    except Exception as e:
        print(f"❌ Vector store test failed: {e}")
        return False

async def test_llm_client():
    """Test LLM client functionality."""
    try:
        from app.core.llm import llm_client
        
        print("✅ LLM client imports successful")
        
        # Simple test message
        messages = [{"role": "user", "content": "Hello, can you respond with 'Test successful'?"}]
        response = await llm_client.generate_response(messages=messages, max_tokens=50)
        
        print(f"✅ LLM API test successful: {response['content']}")
        return True
    except Exception as e:
        print(f"❌ LLM client test failed: {e}")
        return False

async def test_metrics_node_workflow():
    """Test the complete metrics node workflow."""
    try:
        from app.workflows.nodes.metrics_node import metrics_extraction_node
        from app.models.state import WorkflowState
        
        print("✅ Metrics node imports successful")
        
        # Create a test state
        test_state = WorkflowState(
            conversation_id="test_conv_123",
            current_message="Show me the latest user engagement metrics and performance data",
            messages=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi! How can I help you with metrics today?"},
            ],
            metrics_environment="development",
            metrics_context_limit=3
        )
        
        print("✅ Test state created")
        
        # Run the metrics node
        print("🔄 Running metrics extraction node...")
        result = await metrics_extraction_node(test_state)
        
        print(f"✅ Metrics node completed successfully")
        print(f"✅ Result keys: {list(result.keys())}")
        
        if result.get("metrics_data"):
            print(f"✅ Metrics data extracted: {len(result['metrics_data'])} tools executed")
            for tool_name, tool_result in result["metrics_data"].items():
                print(f"  - {tool_name}: {'Success' if 'error' not in tool_result else 'Error'}")
        else:
            print("ℹ️  No metrics data required for this query")
        
        return True
    except Exception as e:
        print(f"❌ Metrics node workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_complete_metrics_pipeline():
    """Test a complete end-to-end metrics pipeline."""
    try:
        print("🔄 Testing complete metrics pipeline...")
        
        # Step 1: Test database extraction
        from app.tools.langchain_db_tools import create_langchain_db_tools, create_tool_config_for_environment
        from app.core.database import get_db
        
        config = create_tool_config_for_environment("production")
        
        async for db_session in get_db():
            tools = create_langchain_db_tools(db_session, config)
            
            # Extract engagement metrics
            engagement_tool = next(t for t in tools if t.name == "get_metrics_by_category")
            engagement_data = await engagement_tool._arun(category="engagement", days_back=5)
            
            # Extract performance metrics  
            performance_data = await engagement_tool._arun(category="performance", days_back=5)
            
            print(f"✅ Extracted engagement data: {len(engagement_data)} chars")
            print(f"✅ Extracted performance data: {len(performance_data)} chars")
            break
        
        # Step 2: Test vector store retrieval
        from app.tools.vector_store import VectorStore
        vs = VectorStore()
        doc_result = vs.search("user engagement metrics analysis", k=3)
        
        print(f"✅ Retrieved documentation context: {len(doc_result.context)} chars")
        
        # Step 3: Test LLM integration
        from app.core.llm import llm_client
        
        analysis_prompt = f"""
        Based on the following metrics data and documentation:
        
        ENGAGEMENT METRICS:
        {engagement_data[:500]}...
        
        PERFORMANCE METRICS:
        {performance_data[:500]}...
        
        DOCUMENTATION CONTEXT:
        {doc_result.context[:500]}...
        
        Provide a brief analysis of the current system status and user engagement trends.
        """
        
        messages = [
            {"role": "system", "content": "You are a productivity insights analyst."},
            {"role": "user", "content": analysis_prompt}
        ]
        
        analysis = await llm_client.generate_response(messages=messages, max_tokens=300)
        
        print(f"✅ Generated analysis: {len(analysis['content'])} chars")
        print("\n📊 SAMPLE ANALYSIS:")
        print("-" * 40)
        print(analysis['content'][:300] + "..." if len(analysis['content']) > 300 else analysis['content'])
        
        return True
        
    except Exception as e:
        print(f"❌ Complete pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests."""
    print("🧪 RUNNING WORKING METRICS TESTS")
    print("=" * 50)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("LangChain DB Tools", test_langchain_db_tools),
        ("Vector Store", test_vector_store),
        ("LLM Client", test_llm_client),
        ("Metrics Node Workflow", test_metrics_node_workflow),
        ("Complete Pipeline", test_complete_metrics_pipeline),
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n🔍 Testing: {test_name}")
        print("-" * 30)
        results[test_name] = await test_func()
        print()
    
    print("=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("\n🎉 ALL TESTS PASSED!")
        print("The metrics node logic is working correctly with:")
        print("  • Database extraction using LangChain tools")
        print("  • Vector store documentation retrieval")
        print("  • LLM analysis and insights generation")
        print("  • Complete end-to-end workflow")
    else:
        print(f"\n⚠️  {len(tests) - passed} components need attention.")

if __name__ == "__main__":
    asyncio.run(main()) 