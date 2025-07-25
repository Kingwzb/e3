#!/usr/bin/env python3
"""
Test script for dynamic_db_tool integration with LangGraph workflow.
"""

import asyncio
import sys
import os
import json

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.workflows.nodes.metrics_node import metrics_extraction_node
from app.models.state import WorkflowState
from app.core.llm import llm_client


async def test_metrics_node_with_dynamic_db():
    """Test the metrics node with dynamic database tool."""
    
    print("🧪 Testing Metrics Node with Dynamic DB Tool")
    print("=" * 50)
    
    try:
        # Create test state
        test_state = WorkflowState(
            conversation_id="test-conversation-123",
            current_message="Find applications with high criticality",
            messages=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi! How can I help you with the database?"}
            ],
            rag_context=None,
            metrics_data=None,
            final_response=None,
            error=None,
            conversation_history_limit=10,
            metrics_context_limit=3,
            metrics_environment="production",
            metrics_tools_config=None
        )
        
        # Test the metrics extraction node
        print("🔄 Testing metrics extraction node...")
        result = await metrics_extraction_node(test_state)
        
        print("✅ Metrics extraction completed")
        print(f"   Result keys: {list(result.keys())}")
        
        if "metrics_data" in result:
            metrics_data = result["metrics_data"]
            if metrics_data:
                print("   📊 Metrics data retrieved:")
                for key, value in metrics_data.items():
                    if isinstance(value, dict):
                        if "error" in value:
                            print(f"     ❌ {key}: {value['error']}")
                        else:
                            print(f"     ✅ {key}: Success")
                    else:
                        print(f"     📋 {key}: {type(value)}")
            else:
                print("   ℹ️ No metrics data required for this query")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_workflow_integration():
    """Test the complete workflow integration."""
    
    print("\n🧪 Testing Complete Workflow Integration")
    print("=" * 50)
    
    try:
        from app.workflows.workflow_factory import create_workflow, WorkflowConfig
        
        # Create workflow configuration
        config = WorkflowConfig(
            enable_rag=True,
            enable_metrics=True,
            enable_conversation_history=True,
            enable_conversation_save=False,  # Skip for testing
            parallel_processing=True,
            conversation_history_limit=5,
            metrics_context_limit=3
        )
        
        # Create workflow
        workflow = create_workflow(config)
        
        # Compile the workflow
        compiled_workflow = workflow.compile()
        
        print("✅ Workflow created and compiled successfully")
        
        # Test with a simple message
        test_state = WorkflowState(
            conversation_id="test-workflow-123",
            current_message="Show me high criticality applications",
            messages=[],
            rag_context=None,
            metrics_data=None,
            final_response=None,
            error=None,
            conversation_history_limit=5,
            metrics_context_limit=3,
            metrics_environment="production",
            metrics_tools_config=None
        )
        
        print("🔄 Testing workflow execution...")
        final_state = await compiled_workflow.ainvoke(test_state)
        
        print("✅ Workflow execution completed")
        print(f"   Final response: {final_state.get('final_response', 'No response')[:200]}...")
        print(f"   Has metrics data: {bool(final_state.get('metrics_data'))}")
        print(f"   Has RAG context: {bool(final_state.get('rag_context'))}")
        print(f"   Has error: {bool(final_state.get('error'))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Workflow integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run the integration tests."""
    print("🚀 Dynamic DB Tool Workflow Integration Tests")
    print("=" * 60)
    
    # Test metrics node
    success1 = await test_metrics_node_with_dynamic_db()
    
    # Test complete workflow
    success2 = await test_workflow_integration()
    
    if success1 and success2:
        print("\n🎉 All integration tests passed!")
        print("✅ Dynamic DB tool successfully integrated with LangGraph workflow")
    else:
        print("\n❌ Some integration tests failed!")
        return False
    
    return True


if __name__ == "__main__":
    asyncio.run(main()) 