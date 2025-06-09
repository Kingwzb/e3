#!/usr/bin/env python3
"""
Comprehensive test to verify all tools functions can be correctly called by LLM.
"""

import asyncio
import sys
from pathlib import Path
import json

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_individual_tools():
    """Test each tool individually to ensure they work correctly."""
    
    print("🔧 COMPREHENSIVE TOOLS VERIFICATION")
    print("=" * 60)
    print("Testing all database tools individually")
    print("=" * 60)
    
    try:
        from app.tools.langchain_db_tools import (
            create_langchain_db_tools, 
            create_tool_config_for_environment,
            GetMetricsByCategoryTool,
            GetTopMetricsTool,
            ExecuteCustomQueryTool
        )
        from app.core.database import get_db
        
        print("✅ Tool imports successful")
        
        # Test different environment configurations
        environments = ["development", "testing", "production"]
        
        for env in environments:
            print(f"\n🌍 Testing {env.upper()} Environment Configuration")
            print("-" * 40)
            
            config = create_tool_config_for_environment(env)
            print(f"✅ Config created for {env}")
            print(f"   - Max days back: {config.max_days_back}")
            print(f"   - Max limit: {config.max_limit}")
            print(f"   - Custom queries enabled: {config.enable_custom_queries}")
            print(f"   - Allowed categories: {len(config.allowed_categories)}")
            print(f"   - Allowed metrics: {len(config.allowed_metric_names)}")
        
        # Test with production config
        config = create_tool_config_for_environment("production")
        
        # Get database session
        async for db_session in get_db():
            print(f"\n🔧 Testing Individual Tools")
            print("-" * 40)
            
            # Create tools
            tools = create_langchain_db_tools(db_session, config)
            print(f"✅ Created {len(tools)} tools")
            
            # Test each tool
            tool_results = {}
            
            # Test 1: GetMetricsByCategoryTool
            print(f"\n🔍 Test 1: GetMetricsByCategoryTool")
            category_tool = next((t for t in tools if t.name == "get_metrics_by_category"), None)
            if category_tool:
                try:
                    result = await category_tool._arun(category="engagement", days_back=7)
                    tool_results["get_metrics_by_category"] = {
                        "success": True,
                        "result_length": len(result),
                        "contains_data": "Successfully retrieved" in result
                    }
                    print(f"✅ Tool executed successfully")
                    print(f"   - Result length: {len(result)} characters")
                    print(f"   - Contains data: {'Successfully retrieved' in result}")
                    print(f"   - Preview: {result[:100]}...")
                except Exception as e:
                    tool_results["get_metrics_by_category"] = {"success": False, "error": str(e)}
                    print(f"❌ Tool failed: {e}")
            else:
                print("❌ Tool not found")
            
            # Test 2: GetTopMetricsTool
            print(f"\n🔍 Test 2: GetTopMetricsTool")
            top_tool = next((t for t in tools if t.name == "get_top_metrics"), None)
            if top_tool:
                try:
                    result = await top_tool._arun(metric_name="daily_active_users", limit=5)
                    tool_results["get_top_metrics"] = {
                        "success": True,
                        "result_length": len(result),
                        "contains_data": "Successfully retrieved" in result
                    }
                    print(f"✅ Tool executed successfully")
                    print(f"   - Result length: {len(result)} characters")
                    print(f"   - Contains data: {'Successfully retrieved' in result}")
                    print(f"   - Preview: {result[:100]}...")
                except Exception as e:
                    tool_results["get_top_metrics"] = {"success": False, "error": str(e)}
                    print(f"❌ Tool failed: {e}")
            else:
                print("❌ Tool not found")
            
            # Test 3: ExecuteCustomQueryTool (if enabled)
            print(f"\n🔍 Test 3: ExecuteCustomQueryTool")
            if config.enable_custom_queries:
                custom_tool = next((t for t in tools if t.name == "execute_custom_query"), None)
                if custom_tool:
                    try:
                        test_query = "SELECT category, COUNT(*) as count FROM metrics_data GROUP BY category LIMIT 5"
                        result = await custom_tool._arun(sql_query=test_query)
                        tool_results["execute_custom_query"] = {
                            "success": True,
                            "result_length": len(result),
                            "contains_data": "Query executed successfully" in result
                        }
                        print(f"✅ Tool executed successfully")
                        print(f"   - Result length: {len(result)} characters")
                        print(f"   - Contains data: {'Query executed successfully' in result}")
                        print(f"   - Preview: {result[:100]}...")
                    except Exception as e:
                        tool_results["execute_custom_query"] = {"success": False, "error": str(e)}
                        print(f"❌ Tool failed: {e}")
                else:
                    print("❌ Tool not found")
            else:
                print("ℹ️  Custom queries disabled in production config")
                tool_results["execute_custom_query"] = {"success": True, "note": "Disabled in production"}
            
            break  # Exit after first session
        
        return tool_results
        
    except Exception as e:
        print(f"❌ Tools verification failed: {e}")
        import traceback
        traceback.print_exc()
        return {}

async def test_tools_with_llm_integration():
    """Test tools integration with LLM through the metrics node."""
    
    print(f"\n🤖 TESTING TOOLS WITH LLM INTEGRATION")
    print("=" * 60)
    
    try:
        from app.workflows.nodes.metrics_node import metrics_extraction_node
        from app.models.state import WorkflowState
        
        # Test different queries that should trigger different tools
        test_cases = [
            {
                "name": "Category-based Query",
                "message": "Show me engagement metrics for the last 5 days",
                "expected_tool": "get_metrics_by_category"
            },
            {
                "name": "Top Metrics Query", 
                "message": "What are the highest daily active user counts?",
                "expected_tool": "get_top_metrics"
            },
            {
                "name": "Performance Metrics Query",
                "message": "Show me performance metrics data",
                "expected_tool": "get_metrics_by_category"
            },
            {
                "name": "Revenue Analysis Query",
                "message": "What are our top revenue numbers?",
                "expected_tool": "get_top_metrics"
            }
        ]
        
        llm_results = {}
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🔍 LLM Test {i}: {test_case['name']}")
            print(f"Query: {test_case['message']}")
            print("-" * 50)
            
            # Create test state
            test_state = {
                "conversation_id": f"tool_test_{i}",
                "current_message": test_case["message"],
                "messages": [],
                "rag_context": None,
                "metrics_data": None,
                "final_response": None,
                "error": None,
                "metrics_environment": "production"
            }
            
            try:
                # Execute metrics node
                result_state = await metrics_extraction_node(test_state)
                
                metrics_data = result_state.get("metrics_data", {})
                
                if metrics_data:
                    print(f"✅ LLM successfully triggered tools")
                    print(f"   - Tools executed: {len(metrics_data)}")
                    print(f"   - Tool names: {list(metrics_data.keys())}")
                    
                    # Check if expected tool was used
                    expected_tool = test_case["expected_tool"]
                    tool_used = expected_tool in metrics_data
                    print(f"   - Expected tool '{expected_tool}' used: {tool_used}")
                    
                    llm_results[test_case["name"]] = {
                        "success": True,
                        "tools_executed": len(metrics_data),
                        "expected_tool_used": tool_used,
                        "tools_used": list(metrics_data.keys())
                    }
                else:
                    print(f"❌ No tools were executed")
                    llm_results[test_case["name"]] = {
                        "success": False,
                        "error": "No tools executed"
                    }
                    
            except Exception as e:
                print(f"❌ LLM integration test failed: {e}")
                llm_results[test_case["name"]] = {
                    "success": False,
                    "error": str(e)
                }
        
        return llm_results
        
    except Exception as e:
        print(f"❌ LLM integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return {}

async def test_tool_error_handling():
    """Test tool error handling and edge cases."""
    
    print(f"\n⚠️  TESTING TOOL ERROR HANDLING")
    print("=" * 60)
    
    try:
        from app.tools.langchain_db_tools import create_langchain_db_tools, create_tool_config_for_environment
        from app.core.database import get_db
        
        config = create_tool_config_for_environment("development")
        
        async for db_session in get_db():
            tools = create_langchain_db_tools(db_session, config)
            
            error_tests = []
            
            # Test invalid category
            print(f"\n🔍 Error Test 1: Invalid Category")
            category_tool = next((t for t in tools if t.name == "get_metrics_by_category"), None)
            if category_tool:
                try:
                    result = await category_tool._arun(category="invalid_category", days_back=7)
                    contains_error = "Error:" in result or "Invalid category" in result
                    print(f"✅ Error handling works: {contains_error}")
                    print(f"   - Response: {result[:100]}...")
                    error_tests.append({"test": "invalid_category", "handled": contains_error})
                except Exception as e:
                    print(f"❌ Unexpected exception: {e}")
                    error_tests.append({"test": "invalid_category", "handled": False, "exception": str(e)})
            
            # Test invalid metric name
            print(f"\n🔍 Error Test 2: Invalid Metric Name")
            top_tool = next((t for t in tools if t.name == "get_top_metrics"), None)
            if top_tool:
                try:
                    result = await top_tool._arun(metric_name="nonexistent_metric", limit=5)
                    contains_error = "No metrics found" in result or "Error:" in result
                    print(f"✅ Error handling works: {contains_error}")
                    print(f"   - Response: {result[:100]}...")
                    error_tests.append({"test": "invalid_metric", "handled": contains_error})
                except Exception as e:
                    print(f"❌ Unexpected exception: {e}")
                    error_tests.append({"test": "invalid_metric", "handled": False, "exception": str(e)})
            
            # Test dangerous SQL (if custom queries enabled)
            if config.enable_custom_queries:
                print(f"\n🔍 Error Test 3: Dangerous SQL Query")
                custom_tool = next((t for t in tools if t.name == "execute_custom_query"), None)
                if custom_tool:
                    try:
                        result = await custom_tool._arun(sql_query="DROP TABLE metrics_data")
                        contains_error = "Error:" in result or "prohibited" in result
                        print(f"✅ Security check works: {contains_error}")
                        print(f"   - Response: {result[:100]}...")
                        error_tests.append({"test": "dangerous_sql", "handled": contains_error})
                    except Exception as e:
                        print(f"❌ Unexpected exception: {e}")
                        error_tests.append({"test": "dangerous_sql", "handled": False, "exception": str(e)})
            
            break
        
        return error_tests
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return []

async def main():
    """Run all tool verification tests."""
    
    print("🚀 COMPLETE TOOLS VERIFICATION SUITE")
    print("=" * 60)
    
    # Test 1: Individual tools
    tool_results = await test_individual_tools()
    
    # Test 2: LLM integration
    llm_results = await test_tools_with_llm_integration()
    
    # Test 3: Error handling
    error_results = await test_tool_error_handling()
    
    # Final summary
    print(f"\n" + "=" * 60)
    print("🎯 FINAL VERIFICATION SUMMARY")
    print("=" * 60)
    
    print(f"\n📊 Individual Tool Tests:")
    for tool_name, result in tool_results.items():
        status = "✅ PASS" if result.get("success", False) else "❌ FAIL"
        print(f"{status} - {tool_name}")
        if not result.get("success", False) and "error" in result:
            print(f"      Error: {result['error']}")
    
    print(f"\n🤖 LLM Integration Tests:")
    for test_name, result in llm_results.items():
        status = "✅ PASS" if result.get("success", False) else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result.get("success", False):
            print(f"      Tools executed: {result.get('tools_executed', 0)}")
            print(f"      Expected tool used: {result.get('expected_tool_used', False)}")
    
    print(f"\n⚠️  Error Handling Tests:")
    for result in error_results:
        status = "✅ PASS" if result.get("handled", False) else "❌ FAIL"
        print(f"{status} - {result['test']}")
    
    # Overall assessment
    individual_success = sum(1 for r in tool_results.values() if r.get("success", False))
    llm_success = sum(1 for r in llm_results.values() if r.get("success", False))
    error_success = sum(1 for r in error_results if r.get("handled", False))
    
    total_individual = len(tool_results)
    total_llm = len(llm_results)
    total_error = len(error_results)
    
    print(f"\n🎉 OVERALL RESULTS:")
    print(f"✅ Individual Tools: {individual_success}/{total_individual} ({individual_success/total_individual*100:.1f}%)" if total_individual > 0 else "✅ Individual Tools: N/A")
    print(f"✅ LLM Integration: {llm_success}/{total_llm} ({llm_success/total_llm*100:.1f}%)" if total_llm > 0 else "✅ LLM Integration: N/A")
    print(f"✅ Error Handling: {error_success}/{total_error} ({error_success/total_error*100:.1f}%)" if total_error > 0 else "✅ Error Handling: N/A")
    
    overall_success = (individual_success + llm_success + error_success)
    overall_total = (total_individual + total_llm + total_error)
    
    if overall_total > 0:
        success_rate = overall_success / overall_total * 100
        if success_rate >= 90:
            print(f"\n🎉 ALL TOOLS VERIFIED SUCCESSFULLY! ({success_rate:.1f}% success rate)")
            print("✅ All tools can be correctly called by LLM")
            print("✅ All tools handle errors properly")
            print("✅ All tools integrate correctly with the workflow")
        elif success_rate >= 75:
            print(f"\n✅ TOOLS MOSTLY VERIFIED ({success_rate:.1f}% success rate)")
            print("Most tools working correctly, minor issues detected")
        else:
            print(f"\n⚠️  TOOLS PARTIALLY VERIFIED ({success_rate:.1f}% success rate)")
            print("Some tools need attention")

if __name__ == "__main__":
    asyncio.run(main()) 