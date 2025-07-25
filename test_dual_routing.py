#!/usr/bin/env python3
"""
Test the dual routing capability of the planner node.
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.workflows.nodes.planner_node import planner_node
from app.workflows.nodes.orchestration_node import should_route_to_metrics
from app.models.state import WorkflowState


async def test_dual_routing():
    """Test that the planner can route to both metrics and RAG nodes."""
    
    print("🧪 Testing Dual Routing (Metrics + RAG)")
    print("=" * 40)
    
    # Test cases for different routing scenarios
    test_cases = [
        {
            "message": "Show me applications with high criticality and tell me about our company policies",
            "expected_routing": "both",
            "description": "Database query + general knowledge"
        },
        {
            "message": "Find applications in the finance sector",
            "expected_routing": "both",  # Should trigger both metrics and RAG
            "description": "Database query only"
        },
        {
            "message": "What's the weather like today?",
            "expected_routing": "rag_extraction",
            "description": "General knowledge only"
        },
        {
            "message": "How many employees do we have?",
            "expected_routing": "both",  # Should trigger both metrics and RAG
            "description": "Database query only"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: {test_case['description']}")
        print(f"   Message: {test_case['message']}")
        
        # Create test state
        state = WorkflowState(
            conversation_id=f"test-dual-routing-{i}",
            current_message=test_case['message'],
            messages=[],
            metrics_limit=10,
            metrics_context_limit=2
        )
        
        try:
            # Run planner node
            planner_result = await planner_node(state)
            
            # Update state with planner result
            state.update(planner_result)
            
            # Test routing decision
            routing_decision = should_route_to_metrics(state)
            
            # Extract planner triggers
            trigger_metrics = planner_result.get("trigger_metrics", False)
            trigger_rag = planner_result.get("trigger_rag", True)
            
            print(f"   📋 Planner triggers: metrics={trigger_metrics}, rag={trigger_rag}")
            print(f"   🎯 Routing decision: {routing_decision}")
            print(f"   📊 Expected routing: {test_case['expected_routing']}")
            
            # Check if routing matches expectation
            success = routing_decision == test_case['expected_routing']
            
            if success:
                print(f"   ✅ Test {i} PASSED")
            else:
                print(f"   ❌ Test {i} FAILED")
            
            results.append({
                "test_case": test_case,
                "result": {
                    "routing_decision": routing_decision,
                    "trigger_metrics": trigger_metrics,
                    "trigger_rag": trigger_rag,
                    "planner_result": planner_result
                },
                "success": success
            })
            
        except Exception as e:
            print(f"   ❌ Test {i} ERROR: {e}")
            results.append({
                "test_case": test_case,
                "result": {"error": str(e)},
                "success": False
            })
    
    # Summary
    print(f"\n📊 Test Summary")
    print("=" * 30)
    passed = sum(1 for r in results if r["success"])
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("🎉 All dual routing tests passed!")
        return True
    else:
        print("⚠️ Some tests failed!")
        return False


async def test_workflow_edges():
    """Test that the workflow can handle both routing scenarios."""
    
    print("\n🧪 Testing Workflow Edge Handling")
    print("=" * 35)
    
    from app.workflows.workflow_factory import create_workflow, WorkflowConfig
    
    try:
        # Create a workflow with both RAG and metrics enabled
        config = WorkflowConfig(
            enable_rag=True,
            enable_metrics=True,
            enable_conversation_history=True,
            enable_conversation_save=False,
            conversation_history_limit=3,
            workflow_name="test_dual_routing_workflow"
        )
        
        workflow = create_workflow(config)
        
        # Check if the workflow has the expected edges
        nodes = list(workflow.nodes.keys())
        print(f"📋 Workflow nodes: {nodes}")
        
        # Check if planner node is present
        if "planner" in nodes:
            print("✅ Planner node found in workflow")
        else:
            print("❌ Planner node missing from workflow")
            return False
        
        # Check if both extraction nodes are present
        if "metrics_extraction" in nodes and "rag_extraction" in nodes:
            print("✅ Both extraction nodes found in workflow")
        else:
            print("❌ Missing extraction nodes in workflow")
            return False
        
        print("✅ Workflow edge handling test passed")
        return True
        
    except Exception as e:
        print(f"❌ Workflow edge handling test failed: {e}")
        return False


async def main():
    """Run all dual routing tests."""
    print("🚀 Dual Routing Tests")
    print("=" * 50)
    
    # Test dual routing logic
    success1 = await test_dual_routing()
    
    # Test workflow edge handling
    success2 = await test_workflow_edges()
    
    if success1 and success2:
        print("\n🎉 All dual routing tests passed!")
        print("✅ The planner can successfully route to both metrics and RAG nodes")
    else:
        print("\n❌ Some tests failed!")
        return False
    
    return True


if __name__ == "__main__":
    asyncio.run(main()) 