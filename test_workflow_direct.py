#!/usr/bin/env python3
"""
Direct workflow test to identify issues with RAG + Metrics integration.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_workflow_components():
    """Test each workflow component directly."""
    try:
        print("🧪 Testing Workflow Components Directly")
        print("=" * 50)
        
        # Test imports
        from app.workflows.nodes.rag_node import rag_extraction_node
        from app.workflows.nodes.metrics_node import metrics_extraction_node
        from app.workflows.nodes.response_node import response_generation_node
        from app.models.state import WorkflowState
        
        print("✅ All workflow node imports successful")
        
        # Create test state
        test_state = {
            "conversation_id": "test_workflow_789",
            "current_message": "Show me user engagement metrics and explain what they mean",
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi! How can I help you today?"}
            ],
            "rag_context": None,
            "metrics_data": None,
            "final_response": None,
            "error": None,
            "conversation_history_limit": 10,
            "metrics_context_limit": 5,
            "metrics_environment": "development"
        }
        
        print("✅ Test state created")
        
        # Step 1: Test RAG node
        print("\n🔍 Testing RAG Node...")
        try:
            rag_result = await rag_extraction_node(test_state)
            test_state.update(rag_result)
            print(f"✅ RAG node completed: {len(test_state.get('rag_context', ''))} chars context")
        except Exception as e:
            print(f"❌ RAG node failed: {e}")
            return False
        
        # Step 2: Test Metrics node
        print("\n🔍 Testing Metrics Node...")
        try:
            metrics_result = await metrics_extraction_node(test_state)
            test_state.update(metrics_result)
            if test_state.get('metrics_data'):
                print(f"✅ Metrics node completed: {len(test_state['metrics_data'])} tool results")
            else:
                print("ℹ️  Metrics node completed (no data needed)")
        except Exception as e:
            print(f"❌ Metrics node failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Step 3: Test Response node
        print("\n🔍 Testing Response Node...")
        try:
            response_result = await response_generation_node(test_state)
            test_state.update(response_result)
            if test_state.get('final_response'):
                print(f"✅ Response node completed: {len(test_state['final_response'])} chars response")
                print(f"\n📋 Sample Response:")
                print("-" * 30)
                print(test_state['final_response'][:300] + "..." if len(test_state['final_response']) > 300 else test_state['final_response'])
            else:
                print("❌ Response node failed to generate response")
                return False
        except Exception as e:
            print(f"❌ Response node failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        print("\n🎉 All workflow components working!")
        return True
        
    except Exception as e:
        print(f"❌ Workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_combined_output():
    """Test that the output properly combines RAG and metrics data."""
    try:
        print("\n" + "=" * 50)
        print("🔍 Testing Combined RAG + Metrics Output")
        print("=" * 50)
        
        from app.workflows.nodes.rag_node import rag_extraction_node
        from app.workflows.nodes.metrics_node import metrics_extraction_node
        from app.workflows.nodes.response_node import response_generation_node
        
        # Create state with a query that should trigger both RAG and metrics
        test_state = {
            "conversation_id": "test_combined_999",
            "current_message": "Analyze our daily active users and session duration metrics. What do these engagement metrics tell us according to our documentation?",
            "messages": [],
            "rag_context": None,
            "metrics_data": None,
            "final_response": None,
            "error": None,
            "metrics_environment": "production"
        }
        
        # Execute workflow steps
        print("Step 1: RAG extraction...")
        rag_result = await rag_extraction_node(test_state)
        test_state.update(rag_result)
        
        print("Step 2: Metrics extraction...")
        metrics_result = await metrics_extraction_node(test_state)
        test_state.update(metrics_result)
        
        print("Step 3: Response generation...")
        response_result = await response_generation_node(test_state)
        test_state.update(response_result)
        
        # Analyze the final response
        final_response = test_state.get('final_response', '')
        rag_context = test_state.get('rag_context', '')
        metrics_data = test_state.get('metrics_data', {})
        
        print(f"\n📊 Analysis Results:")
        print(f"✅ RAG context retrieved: {len(rag_context)} characters")
        print(f"✅ Metrics data extracted: {len(metrics_data)} tool results" if metrics_data else "ℹ️  No metrics data extracted")
        print(f"✅ Final response generated: {len(final_response)} characters")
        
        # Check if response contains both types of information
        response_lower = final_response.lower()
        has_metrics_keywords = any(keyword in response_lower for keyword in ['metric', 'data', 'users', 'engagement', 'performance'])
        has_doc_keywords = any(keyword in response_lower for keyword in ['documentation', 'system', 'platform', 'according to'])
        
        print(f"\n🔍 Content Analysis:")
        print(f"✅ Contains metrics-related content: {has_metrics_keywords}")
        print(f"✅ Contains documentation-based content: {has_doc_keywords}")
        print(f"✅ Successfully combines both sources: {has_metrics_keywords and has_doc_keywords}")
        
        print(f"\n📋 Full Response:")
        print("-" * 50)
        print(final_response)
        print("-" * 50)
        
        return has_metrics_keywords and has_doc_keywords
        
    except Exception as e:
        print(f"❌ Combined output test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests."""
    print("🚀 Direct Workflow Testing")
    print("=" * 50)
    
    # Test 1: Individual components
    component_test = await test_workflow_components()
    
    # Test 2: Combined output
    combined_test = await test_combined_output()
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    print(f"Workflow Components: {'✅ PASS' if component_test else '❌ FAIL'}")
    print(f"Combined RAG + Metrics: {'✅ PASS' if combined_test else '❌ FAIL'}")
    
    if component_test and combined_test:
        print("\n🎉 ALL TESTS PASSED!")
        print("The workflow successfully combines RAG and metrics data!")
    else:
        print("\n⚠️  Some tests failed. Check the error messages above.")

if __name__ == "__main__":
    asyncio.run(main()) 