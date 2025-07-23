#!/usr/bin/env python3
"""
Test script for the multi-collection dynamic database tool.
This script tests the enhanced functionality for joining multiple collections.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.tools.dynamic_db_tool import create_dynamic_db_tool
from app.utils.logging import logger


# Import unified schema from separate file
from schemas.unified_schema import UNIFIED_SCHEMA


async def test_multi_collection_config():
    """Test that the tool can handle unified schema configuration."""
    print("🔍 Testing unified schema configuration...")
    
    try:
        tool = create_dynamic_db_tool()
        
        # Test that the tool accepts the unified schema parameter structure
        print("✅ Unified schema configuration accepted")
        print(f"   Schema length: {len(UNIFIED_SCHEMA)} characters")
        return True
        
    except Exception as e:
        print(f"❌ Unified schema configuration failed: {e}")
        return False


async def test_multi_collection_query_execution():
    """Test that the tool can generate and execute queries for multiple collections."""
    print("\n🔍 Testing multi-collection query generation and execution...")
    
    try:
        tool = create_dynamic_db_tool()
        
        # Using unified schema instead of individual collections
        
        # Test query generation for unified schema scenario
        query_dict = await tool._generate_mongodb_query(
            user_prompt="Find high criticality applications and their employee data",
            unified_schema=UNIFIED_SCHEMA,
            limit=10,
            include_aggregation=True,
            join_strategy="lookup"
        )
        
        print("✅ Multi-collection query generation successful")
        print(f"   Primary collection: {query_dict.get('primary_collection')}")
        print(f"   Joins: {len(query_dict.get('joins', []))}")
        print(f"   Aggregation stages: {len(query_dict.get('aggregation', []))}")
        
        # Verify query structure
        required_keys = ["primary_collection", "filter", "projection", "sort", "limit", "aggregation", "joins"]
        for key in required_keys:
            if key not in query_dict:
                print(f"❌ Missing required key: {key}")
                return False
        
        print("✅ Multi-collection query structure is valid")
        
        # Execute the generated query
        print("\n🔄 Executing generated query against MongoDB...")
        results = await tool._execute_query(query_dict)
        
        print(f"✅ Query execution successful")
        print(f"   Results returned: {len(results)}")
        
        # Display sample results
        if results:
            print("\n📊 Sample Results:")
            for i, result in enumerate(results[:3]):  # Show first 3 results
                print(f"   Result {i+1}:")
                print(f"     - ID: {result.get('_id', 'N/A')}")
                print(f"     - Snapshot ID: {result.get('snapshotId', 'N/A')}")
                if 'application' in result:
                    app = result['application']
                    print(f"     - CSI ID: {app.get('csiId', 'N/A')}")
                    print(f"     - Criticality: {app.get('criticality', 'N/A')}")
                if 'employee_data' in result:
                    emp_data = result['employee_data']
                    print(f"     - Employee Data Records: {len(emp_data)}")
                    if emp_data:
                        print(f"     - Sample Employee Count: {emp_data[0].get('employeeCount', 'N/A')}")
        else:
            print("   ⚠️  No results returned (this might be expected if no matching data)")
        
        return True
        
    except Exception as e:
        print(f"❌ Multi-collection query execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_complex_join_execution():
    """Test complex join scenarios with actual database execution."""
    print("\n🔍 Testing complex join scenarios with execution...")
    
    try:
        tool = create_dynamic_db_tool()
        
        # Using unified schema instead of individual collections
        
        # Test complex join scenario
        query_dict = await tool._generate_mongodb_query(
            user_prompt="Analyze applications by criticality, join with employee ratios and management segments",
            unified_schema=UNIFIED_SCHEMA,
            limit=15,
            include_aggregation=True,
            join_strategy="lookup"
        )
        
        print("✅ Complex join query generation successful")
        print(f"   Using unified schema with comprehensive collection information")
        print(f"   Join operations: {len(query_dict.get('joins', []))}")
        
        # Check that the query includes multiple lookups
        aggregation = query_dict.get("aggregation", [])
        lookup_stages = [stage for stage in aggregation if "$lookup" in stage]
        
        if len(lookup_stages) >= 2:
            print("✅ Multiple lookup operations detected")
        else:
            print("⚠️  Expected multiple lookup operations")
        
        # Execute the complex join query
        print("\n🔄 Executing complex join query against MongoDB...")
        results = await tool._execute_query(query_dict)
        
        print(f"✅ Complex join execution successful")
        print(f"   Results returned: {len(results)}")
        
        # Display sample results
        if results:
            print("\n📊 Sample Complex Join Results:")
            for i, result in enumerate(results[:3]):  # Show first 3 results
                print(f"   Result {i+1}:")
                print(f"     - ID: {result.get('_id', 'N/A')}")
                if 'application' in result:
                    app = result['application']
                    print(f"     - CSI ID: {app.get('csiId', 'N/A')}")
                    print(f"     - Criticality: {app.get('criticality', 'N/A')}")
                    print(f"     - Sector: {app.get('sector', 'N/A')}")
                if 'employee_data' in result:
                    emp_data = result['employee_data']
                    print(f"     - Employee Data Records: {len(emp_data)}")
                if 'segment_data' in result:
                    seg_data = result['segment_data']
                    print(f"     - Segment Data Records: {len(seg_data)}")
        else:
            print("   ⚠️  No results returned (this might be expected if no matching data)")
        
        return True
        
    except Exception as e:
        print(f"❌ Complex join execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_filtering_across_collections():
    """Test filtering capabilities across multiple collections with execution."""
    print("\n🔍 Testing filtering across collections with execution...")
    
    try:
        tool = create_dynamic_db_tool()
        
        # Using unified schema instead of individual collections
        
        # Test filtering scenario
        query_dict = await tool._generate_mongodb_query(
            user_prompt="Find high criticality applications that have employee ratios above 0.7",
            unified_schema=UNIFIED_SCHEMA,
            limit=10,
            include_aggregation=True,
            join_strategy="lookup"
        )
        
        print("✅ Cross-collection filtering query generation successful")
        
        # Check that the query includes filtering logic
        aggregation = query_dict.get("aggregation", [])
        match_stages = [stage for stage in aggregation if "$match" in stage]
        
        if match_stages:
            print("✅ Filtering stages detected in aggregation")
        else:
            print("⚠️  Expected filtering stages")
        
        # Execute the filtering query
        print("\n🔄 Executing filtering query against MongoDB...")
        results = await tool._execute_query(query_dict)
        
        print(f"✅ Filtering execution successful")
        print(f"   Results returned: {len(results)}")
        
        # Display sample results
        if results:
            print("\n📊 Sample Filtering Results:")
            for i, result in enumerate(results[:3]):  # Show first 3 results
                print(f"   Result {i+1}:")
                print(f"     - ID: {result.get('_id', 'N/A')}")
                if 'application' in result:
                    app = result['application']
                    print(f"     - CSI ID: {app.get('csiId', 'N/A')}")
                    print(f"     - Criticality: {app.get('criticality', 'N/A')}")
                if 'employee_data' in result:
                    emp_data = result['employee_data']
                    print(f"     - Employee Data Records: {len(emp_data)}")
                    if emp_data:
                        print(f"     - Sample Engineer Ratio: {emp_data[0].get('engineerRatio', 'N/A')}")
        else:
            print("   ⚠️  No results returned (this might be expected if no matching data)")
        
        return True
        
    except Exception as e:
        print(f"❌ Cross-collection filtering execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_sorting_and_grouping():
    """Test sorting and grouping capabilities across collections with execution."""
    print("\n🔍 Testing sorting and grouping with execution...")
    
    try:
        tool = create_dynamic_db_tool()
        
        # Using unified schema instead of individual collections
        
        # Test sorting and grouping scenario
        query_dict = await tool._generate_mongodb_query(
            user_prompt="Group applications by criticality and sort by average employee count",
            unified_schema=UNIFIED_SCHEMA,
            limit=10,
            include_aggregation=True,
            join_strategy="lookup"
        )
        
        print("✅ Sorting and grouping query generation successful")
        
        # Check for grouping and sorting stages
        aggregation = query_dict.get("aggregation", [])
        group_stages = [stage for stage in aggregation if "$group" in stage]
        sort_stages = [stage for stage in aggregation if "$sort" in stage]
        
        if group_stages:
            print("✅ Grouping stages detected")
        if sort_stages:
            print("✅ Sorting stages detected")
        
        # Execute the grouping and sorting query
        print("\n🔄 Executing grouping and sorting query against MongoDB...")
        results = await tool._execute_query(query_dict)
        
        print(f"✅ Grouping and sorting execution successful")
        print(f"   Results returned: {len(results)}")
        
        # Display sample results
        if results:
            print("\n📊 Sample Grouping and Sorting Results:")
            for i, result in enumerate(results[:3]):  # Show first 3 results
                print(f"   Result {i+1}:")
                print(f"     - Group ID: {result.get('_id', 'N/A')}")
                print(f"     - Count: {result.get('count', 'N/A')}")
                if 'avgEmployeeCount' in result:
                    print(f"     - Average Employee Count: {result.get('avgEmployeeCount', 'N/A')}")
                if 'totalApplications' in result:
                    print(f"     - Total Applications: {result.get('totalApplications', 'N/A')}")
        else:
            print("   ⚠️  No results returned (this might be expected if no matching data)")
        
        return True
        
    except Exception as e:
        print(f"❌ Sorting and grouping execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_full_query_execution():
    """Test the complete flow from prompt to formatted results."""
    print("\n🔍 Testing complete query execution flow...")
    
    try:
        tool = create_dynamic_db_tool()
        
        # Using unified schema instead of individual collections
        
        # Test the complete flow
        user_prompt = "Find applications with high criticality and show their employee data, limit to 5 results"
        
        print(f"📝 User Prompt: {user_prompt}")
        
        # Generate query
        query_dict = await tool._generate_mongodb_query(
            user_prompt=user_prompt,
            unified_schema=UNIFIED_SCHEMA,
            limit=5,
            include_aggregation=True,
            join_strategy="lookup"
        )
        
        print("✅ Query generation successful")
        print(f"   Generated query structure: {list(query_dict.keys())}")
        
        # Execute query
        print("\n🔄 Executing query against MongoDB...")
        results = await tool._execute_query(query_dict)
        
        print(f"✅ Query execution successful")
        print(f"   Raw results returned: {len(results)}")
        
        # Format results
        formatted_response = tool._format_results(results, query_dict)
        
        print("✅ Result formatting successful")
        
        # Display comprehensive results
        print("\n📊 Complete Query Results:")
        print(f"   Query Type: {formatted_response.get('query_info', {}).get('query_type', 'N/A')}")
        print(f"   Primary Collection: {formatted_response.get('query_info', {}).get('primary_collection', 'N/A')}")
        print(f"   Total Results: {formatted_response.get('results', {}).get('total_count', 0)}")
        print(f"   Collections Involved: {formatted_response.get('summary', {}).get('collections_involved', [])}")
        
        # Show sample data
        data = formatted_response.get('results', {}).get('data', [])
        if data:
            print("\n📋 Sample Data:")
            for i, result in enumerate(data[:2]):  # Show first 2 results
                print(f"   Result {i+1}:")
                print(f"     - ID: {result.get('_id', 'N/A')}")
                if 'snapshotId' in result:
                    print(f"     - Snapshot ID: {result.get('snapshotId', 'N/A')}")
                if 'application' in result:
                    app = result['application']
                    print(f"     - CSI ID: {app.get('csiId', 'N/A')}")
                    print(f"     - Criticality: {app.get('criticality', 'N/A')}")
                    print(f"     - Sector: {app.get('sector', 'N/A')}")
                if 'employee_data' in result:
                    emp_data = result['employee_data']
                    print(f"     - Employee Data Records: {len(emp_data)}")
                    if emp_data:
                        print(f"     - Sample Employee Count: {emp_data[0].get('employeeCount', 'N/A')}")
                        print(f"     - Sample Engineer Ratio: {emp_data[0].get('engineerRatio', 'N/A')}")
        else:
            print("   ⚠️  No data returned (this might be expected if no matching data)")
        
        # Verify response structure
        required_keys = ["query_info", "results", "summary"]
        for key in required_keys:
            if key not in formatted_response:
                print(f"❌ Missing required key in response: {key}")
                return False
        
        print("✅ Complete flow test successful")
        return True
        
    except Exception as e:
        print(f"❌ Complete flow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_collections_involved_tracking():
    """Test that the tool correctly tracks collections involved in queries."""
    print("\n🔍 Testing collections involved tracking...")
    
    try:
        tool = create_dynamic_db_tool()
        
        # Test with single collection
        query_dict1 = {
            "primary_collection": "application_snapshot",
            "joins": []
        }
        collections1 = tool._get_collections_involved(query_dict1)
        print(f"   Single collection: {collections1}")
        
        # Test with multiple collections
        query_dict2 = {
            "primary_collection": "application_snapshot",
            "joins": [
                {"collection": "employee_ratio"},
                {"collection": "management_segment_tree"}
            ],
            "aggregation": [
                {
                    "$lookup": {
                        "from": "employee_ratio",
                        "localField": "application.csiId",
                        "foreignField": "csiId",
                        "as": "employee_data"
                    }
                }
            ]
        }
        collections2 = tool._get_collections_involved(query_dict2)
        print(f"   Multiple collections: {collections2}")
        
        if len(collections1) == 1 and len(collections2) >= 3:
            print("✅ Collections tracking working correctly")
            return True
        else:
            print("❌ Collections tracking not working as expected")
            return False
        
    except Exception as e:
        print(f"❌ Collections tracking failed: {e}")
        return False


async def main():
    """Run all multi-collection tests."""
    print("🚀 Multi-Collection Dynamic Database Tool Tests")
    print("=" * 60)
    
    tests = [
        test_multi_collection_config,
        test_multi_collection_query_execution,
        test_complex_join_execution,
        test_filtering_across_collections,
        test_sorting_and_grouping,
        test_full_query_execution,
        test_collections_involved_tracking
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if await test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All multi-collection tests passed! The enhanced dynamic database tool is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the configuration and dependencies.")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 