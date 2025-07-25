#!/usr/bin/env python3
"""
Test the new planner node functionality.
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.workflows.nodes.planner_node import planner_node
from app.models.state import WorkflowState


async def test_planner_node():
    """Test the planner node with various types of messages."""
    
    print("🧪 Testing Planner Node")
    print("=" * 30)
    
    # Test cases
    test_cases = [
        {
            "message": "Show me applications with high criticality",
            "expected_needs_query": True,
            "description": "Database query needed - applications"
        },
        {
            "message": "How many employees are there?",
            "expected_needs_query": True,
            "description": "Database query needed - employee count"
        },
        {
            "message": "What's the weather like today?",
            "expected_needs_query": False,
            "description": "No database query needed - weather"
        },
        {
            "message": "Tell me a joke",
            "expected_needs_query": False,
            "description": "No database query needed - joke"
        },
        {
            "message": "Find applications in the finance sector",
            "expected_needs_query": True,
            "description": "Database query needed - sector filtering"
        },
        {
            "message": "What is the capital of France?",
            "expected_needs_query": False,
            "description": "No database query needed - general knowledge"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: {test_case['description']}")
        print(f"   Message: {test_case['message']}")
        
        # Create test state
        state = WorkflowState(
            conversation_id=f"test-conversation-{i}",
            current_message=test_case['message'],
            messages=[],
            metrics_limit=100,
            metrics_context_limit=3
        )
        
        try:
            # Run planner node
            result = await planner_node(state)
            
            # Extract results
            planning_data = result.get("planning_data", {})
            needs_query = planning_data.get("needs_database_query", False)
            reasoning = planning_data.get("reasoning", "No reasoning")
            confidence = planning_data.get("confidence", 0.0)
            next_node = result.get("next_node", "unknown")
            trigger_metrics = result.get("trigger_metrics", False)
            
            # Check if result matches expectation
            success = needs_query == test_case["expected_needs_query"]
            
            print(f"   ✅ Result: {needs_query} (expected: {test_case['expected_needs_query']})")
            print(f"   📊 Confidence: {confidence:.2f}")
            print(f"   🎯 Next node: {next_node}")
            print(f"   💭 Reasoning: {reasoning[:100]}...")
            
            if success:
                print(f"   ✅ Test {i} PASSED")
            else:
                print(f"   ❌ Test {i} FAILED")
            
            results.append({
                "test_case": test_case,
                "result": result,
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
        print("🎉 All planner node tests passed!")
        return True
    else:
        print("⚠️ Some tests failed!")
        return False


async def test_planner_metrics_integration():
    """Test the integration between planner and metrics nodes."""
    
    print("\n🧪 Testing Planner-Metrics Integration")
    print("=" * 40)
    
    # Test a message that should trigger metrics
    test_message = "Show me applications with high criticality"
    
    print(f"🔍 Testing integration with message: {test_message}")
    
    # Create test state
    state = WorkflowState(
        conversation_id="test-integration-123",
        current_message=test_message,
        messages=[],
        metrics_limit=100,
        metrics_context_limit=3
    )
    
    try:
        # Run planner node
        planner_result = await planner_node(state)
        
        print(f"📋 Planner result:")
        print(f"   Needs query: {planner_result.get('planning_data', {}).get('needs_database_query', False)}")
        print(f"   Next node: {planner_result.get('next_node', 'unknown')}")
        print(f"   Trigger metrics: {planner_result.get('trigger_metrics', False)}")
        
        # Update state with planner result
        state.update(planner_result)
        
        # Test metrics node decision
        from app.workflows.nodes.metrics_node import _should_extract_metrics
        
        should_extract = _should_extract_metrics(state)
        print(f"📊 Metrics node decision: {should_extract}")
        
        # Check both metrics and RAG triggers
        trigger_metrics = planner_result.get("trigger_metrics", False)
        trigger_rag = planner_result.get("trigger_rag", True)
        
        print(f"📋 Planner triggers: metrics={trigger_metrics}, rag={trigger_rag}")
        
        if should_extract == trigger_metrics:
            print("✅ Integration test PASSED - Metrics node correctly triggered")
            return True
        else:
            print("❌ Integration test FAILED - Metrics node not triggered when it should be")
            return False
            
    except Exception as e:
        print(f"❌ Integration test ERROR: {e}")
        return False


async def main():
    """Run all planner node tests."""
    print("🚀 Planner Node Tests")
    print("=" * 50)
    
    # Test planner node functionality
    success1 = await test_planner_node()
    
    # Test planner-metrics integration
    success2 = await test_planner_metrics_integration()
    
    if success1 and success2:
        print("\n🎉 All planner node tests passed!")
        print("✅ The planner node works correctly and integrates with metrics node")
    else:
        print("\n❌ Some tests failed!")
        return False
    
    return True


if __name__ == "__main__":
    asyncio.run(main()) 