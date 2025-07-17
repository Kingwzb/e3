#!/usr/bin/env python3
"""
Test script for field tools integration with LLM conversation workflow.

This script tests:
1. Field tools integration with metrics node
2. LLM conversation workflow with field exploration
3. Dynamic field path discovery
4. Field value exploration
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.workflows.nodes.metrics_node import metrics_extraction_node
from app.models.state import WorkflowState
from app.utils.logging import logger


async def test_field_tools_workflow():
    """Test field tools integration with the LLM conversation workflow."""
    
    print("🧪 TESTING FIELD TOOLS WORKFLOW INTEGRATION")
    print("=" * 60)
    
    # Test cases for field exploration
    test_cases = [
        {
            "name": "Field Path Discovery",
            "message": "What fields are available in the application snapshots collection?",
            "expected_tools": ["get_field_paths"],
            "collection": "application_snapshots"
        },
        {
            "name": "Field Values Exploration",
            "message": "What are the possible values for the status field in applications?",
            "expected_tools": ["get_field_values"],
            "field_path": "status"
        },
        {
            "name": "Schema Exploration",
            "message": "Show me the structure of the employee ratio collection",
            "expected_tools": ["get_field_paths"],
            "collection": "employee_ratio"
        },
        {
            "name": "Value Analysis",
            "message": "What unique values exist for the criticality field?",
            "expected_tools": ["get_field_values"],
            "field_path": "criticality"
        },
        {
            "name": "General Data Query",
            "message": "Show me some application snapshots data",
            "expected_tools": ["query_application_snapshots"],
            "collection": "application_snapshots"
        }
    ]
    
    results = {}
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: {test_case['name']}")
        print(f"Query: {test_case['message']}")
        print("-" * 50)
        
        # Create test state
        test_state = WorkflowState(
            conversation_id=f"field_test_{i}",
            current_message=test_case["message"],
            messages=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi! How can I help you explore the data?"},
            ],
            metrics_environment="development",
            metrics_context_limit=3
        )
        
        try:
            # Execute metrics node
            result = await metrics_extraction_node(test_state)
            
            metrics_data = result.get("metrics_data", {})
            
            if metrics_data:
                print(f"✅ Tools executed successfully")
                print(f"   - Tools used: {list(metrics_data.keys())}")
                
                # Check if expected tools were used
                expected_tools = test_case["expected_tools"]
                tools_used = list(metrics_data.keys())
                
                for expected_tool in expected_tools:
                    if expected_tool in tools_used:
                        print(f"   ✅ Expected tool '{expected_tool}' was used")
                    else:
                        print(f"   ❌ Expected tool '{expected_tool}' was NOT used")
                
                # Show sample results
                for tool_name, tool_result in metrics_data.items():
                    if "result" in tool_result:
                        result_preview = str(tool_result["result"])[:200]
                        print(f"   📊 {tool_name}: {result_preview}...")
                    elif "error" in tool_result:
                        print(f"   ❌ {tool_name}: Error - {tool_result['error']}")
                
                results[test_case["name"]] = {
                    "success": True,
                    "tools_used": tools_used,
                    "expected_tools_found": all(tool in tools_used for tool in expected_tools),
                    "result_count": len(metrics_data)
                }
            else:
                print(f"❌ No tools were executed")
                results[test_case["name"]] = {
                    "success": False,
                    "error": "No tools executed"
                }
                
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            results[test_case["name"]] = {
                "success": False,
                "error": str(e)
            }
    
    # Summary
    print(f"\n📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    successful_tests = 0
    total_tests = len(test_cases)
    
    for test_name, result in results.items():
        if result["success"]:
            successful_tests += 1
            print(f"✅ {test_name}: SUCCESS")
            print(f"   - Tools used: {result['tools_used']}")
            print(f"   - Expected tools found: {result['expected_tools_found']}")
        else:
            print(f"❌ {test_name}: FAILED")
            if "error" in result:
                print(f"   - Error: {result['error']}")
    
    print(f"\n🎯 OVERALL RESULTS")
    print(f"   - Successful tests: {successful_tests}/{total_tests}")
    print(f"   - Success rate: {(successful_tests/total_tests)*100:.1f}%")
    
    return successful_tests == total_tests


async def test_dynamic_field_exploration():
    """Test dynamic field exploration capabilities."""
    
    print(f"\n🔍 TESTING DYNAMIC FIELD EXPLORATION")
    print("=" * 60)
    
    # Test a more complex field exploration scenario
    test_state = WorkflowState(
        conversation_id="dynamic_field_test",
        current_message="Show me what fields are available in the employee ratio collection",
        messages=[
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi! I can help you explore the employee ratio data."},
        ],
        metrics_environment="development",
        metrics_context_limit=3
    )
    
    try:
        result = await metrics_extraction_node(test_state)
        metrics_data = result.get("metrics_data", {})
        
        if metrics_data:
            print(f"✅ Dynamic field exploration successful")
            print(f"   - Tools executed: {list(metrics_data.keys())}")
            
            for tool_name, tool_result in metrics_data.items():
                if "result" in tool_result:
                    result_preview = str(tool_result["result"])[:300]
                    print(f"   📊 {tool_name}: {result_preview}...")
                elif "error" in tool_result:
                    print(f"   ❌ {tool_name}: Error - {tool_result['error']}")
            
            return True
        else:
            print(f"❌ No tools were executed for dynamic exploration")
            return False
            
    except Exception as e:
        print(f"❌ Dynamic field exploration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all field tools workflow tests."""
    
    print("🚀 STARTING FIELD TOOLS WORKFLOW INTEGRATION TESTS")
    print("=" * 60)
    
    # Test 1: Basic field tools integration
    basic_success = await test_field_tools_workflow()
    
    # Test 2: Dynamic field exploration
    dynamic_success = await test_dynamic_field_exploration()
    
    # Final summary
    print(f"\n🎯 FINAL TEST RESULTS")
    print("=" * 60)
    print(f"✅ Basic field tools integration: {'PASSED' if basic_success else 'FAILED'}")
    print(f"✅ Dynamic field exploration: {'PASSED' if dynamic_success else 'FAILED'}")
    
    overall_success = basic_success and dynamic_success
    print(f"\n🎉 OVERALL RESULT: {'ALL TESTS PASSED' if overall_success else 'SOME TESTS FAILED'}")
    
    return overall_success


if __name__ == "__main__":
    asyncio.run(main()) 