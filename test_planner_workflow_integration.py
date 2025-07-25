#!/usr/bin/env python3
"""
Test the planner node integration in the workflow factory.
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.workflows.workflow_factory import create_workflow, WorkflowConfig
from app.models.state import WorkflowState


async def test_planner_workflow_integration():
    """Test the planner node integration in the workflow."""
    
    print("🧪 Testing Planner Node Workflow Integration")
    print("=" * 50)
    
    # Test different workflow configurations
    test_configs = [
        {
            "name": "Full Workflow (RAG + Metrics)",
            "config": WorkflowConfig(
                enable_rag=True,
                enable_metrics=True,
                enable_conversation_history=True,
                enable_conversation_save=True,
                parallel_processing=True,
                conversation_history_limit=5,
                workflow_name="test_full_workflow"
            ),
            "expected_nodes": ["retrieve_history", "planner", "rag_extraction", "metrics_extraction", "response_generation", "save_conversation"]
        },
        {
            "name": "Metrics Only Workflow",
            "config": WorkflowConfig(
                enable_rag=False,
                enable_metrics=True,
                enable_conversation_history=True,
                enable_conversation_save=True,
                conversation_history_limit=5,
                workflow_name="test_metrics_only_workflow"
            ),
            "expected_nodes": ["retrieve_history", "planner", "metrics_extraction", "response_generation", "save_conversation"]
        },
        {
            "name": "RAG Only Workflow",
            "config": WorkflowConfig(
                enable_rag=True,
                enable_metrics=False,
                enable_conversation_history=True,
                enable_conversation_save=True,
                conversation_history_limit=5,
                workflow_name="test_rag_only_workflow"
            ),
            "expected_nodes": ["retrieve_history", "planner", "rag_extraction", "response_generation", "save_conversation"]
        },
        {
            "name": "No Extraction Workflow",
            "config": WorkflowConfig(
                enable_rag=False,
                enable_metrics=False,
                enable_conversation_history=True,
                enable_conversation_save=True,
                conversation_history_limit=5,
                workflow_name="test_no_extraction_workflow"
            ),
            "expected_nodes": ["retrieve_history", "planner", "response_generation", "save_conversation"]
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_configs, 1):
        print(f"\n🔍 Test {i}: {test_case['name']}")
        print(f"   Config: RAG={test_case['config'].enable_rag}, Metrics={test_case['config'].enable_metrics}")
        
        try:
            # Create workflow
            workflow = create_workflow(test_case['config'])
            
            # Check if workflow was created successfully
            if workflow is None:
                print(f"   ❌ Test {i} FAILED: Workflow creation returned None")
                results.append({"test_case": test_case, "success": False, "error": "Workflow creation returned None"})
                continue
            
            # Get workflow nodes
            workflow_nodes = list(workflow.nodes.keys())
            expected_nodes = test_case['expected_nodes']
            
            print(f"   📋 Workflow nodes: {workflow_nodes}")
            print(f"   🎯 Expected nodes: {expected_nodes}")
            
            # Check if all expected nodes are present
            missing_nodes = [node for node in expected_nodes if node not in workflow_nodes]
            extra_nodes = [node for node in workflow_nodes if node not in expected_nodes]
            
            if missing_nodes:
                print(f"   ❌ Missing nodes: {missing_nodes}")
            if extra_nodes:
                print(f"   ⚠️ Extra nodes: {extra_nodes}")
            
            success = len(missing_nodes) == 0
            
            if success:
                print(f"   ✅ Test {i} PASSED")
            else:
                print(f"   ❌ Test {i} FAILED")
            
            results.append({
                "test_case": test_case,
                "success": success,
                "workflow_nodes": workflow_nodes,
                "expected_nodes": expected_nodes,
                "missing_nodes": missing_nodes,
                "extra_nodes": extra_nodes
            })
            
        except Exception as e:
            print(f"   ❌ Test {i} ERROR: {e}")
            results.append({"test_case": test_case, "success": False, "error": str(e)})
    
    # Summary
    print(f"\n📊 Test Summary")
    print("=" * 30)
    passed = sum(1 for r in results if r["success"])
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("🎉 All planner workflow integration tests passed!")
        return True
    else:
        print("⚠️ Some tests failed!")
        return False


async def test_workflow_execution():
    """Test actual workflow execution with planner node."""
    
    print("\n🧪 Testing Workflow Execution with Planner Node")
    print("=" * 55)
    
    # Create a test workflow
    config = WorkflowConfig(
        enable_rag=True,
        enable_metrics=True,
        enable_conversation_history=True,
        enable_conversation_save=False,  # Skip save for testing
        conversation_history_limit=3,
        workflow_name="test_execution_workflow"
    )
    
    try:
        # Create workflow
        workflow = create_workflow(config)
        
        # Create test state
        state = WorkflowState(
            conversation_id="test-execution-123",
            current_message="Show me applications with high criticality",
            messages=[],
            metrics_limit=10,
            metrics_context_limit=2
        )
        
        print(f"🔍 Testing workflow execution with message: {state['current_message']}")
        
        # Compile workflow
        compiled_workflow = workflow.compile()
        
        # Execute workflow
        result = await compiled_workflow.ainvoke(state)
        
        print(f"✅ Workflow execution completed")
        print(f"   Final state keys: {list(result.keys())}")
        print(f"   Has planning data: {bool(result.get('planning_data'))}")
        print(f"   Has metrics data: {bool(result.get('metrics_data'))}")
        print(f"   Has RAG context: {bool(result.get('rag_context'))}")
        print(f"   Has final response: {bool(result.get('final_response'))}")
        
        # Check if planner worked correctly
        planning_data = result.get("planning_data", {})
        if planning_data:
            print(f"   📋 Planning result:")
            print(f"      Needs query: {planning_data.get('needs_database_query', False)}")
            print(f"      Confidence: {planning_data.get('confidence', 0.0)}")
            print(f"      Reasoning: {planning_data.get('reasoning', 'No reasoning')[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Workflow execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all planner workflow integration tests."""
    print("🚀 Planner Workflow Integration Tests")
    print("=" * 50)
    
    # Test workflow creation and node structure
    success1 = await test_planner_workflow_integration()
    
    # Test actual workflow execution
    success2 = await test_workflow_execution()
    
    if success1 and success2:
        print("\n🎉 All planner workflow integration tests passed!")
        print("✅ The planner node is successfully integrated into the workflow")
    else:
        print("\n❌ Some tests failed!")
        return False
    
    return True


if __name__ == "__main__":
    asyncio.run(main()) 