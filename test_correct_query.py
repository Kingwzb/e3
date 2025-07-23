#!/usr/bin/env python3
"""
Test to verify correct query generation with actual schema.
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_multi_collection_dynamic_db import create_dynamic_db_tool


async def test_correct_group_by_query():
    """Test that the query generation creates correct field references."""
    
    print("🧪 Testing Correct Group By Query")
    print("=" * 35)
    
    try:
        tool = create_dynamic_db_tool()
        
        # Test with the actual schema
        from schemas.unified_schema import UNIFIED_SCHEMA
        
        query_dict = await tool._generate_mongodb_query(
            user_prompt="Group applications by criticality and count them",
            unified_schema=UNIFIED_SCHEMA,
            limit=10,
            include_aggregation=True,
            join_strategy="lookup"
        )
        
        print("✅ Query generation successful")
        print(f"   Primary collection: {query_dict.get('primary_collection')}")
        
        # Check the aggregation pipeline
        aggregation = query_dict.get("aggregation", [])
        print(f"   Aggregation stages: {len(aggregation)}")
        
        # Look for the group stage
        group_stage = None
        for stage in aggregation:
            if "$group" in stage:
                group_stage = stage["$group"]
                break
        
        if group_stage:
            print(f"   Group stage: {group_stage}")
            
            # Check if it uses correct field names
            if "_id" in group_stage and "$application.criticality" in str(group_stage["_id"]):
                print("✅ Correct field reference: $application.criticality")
            else:
                print("❌ Incorrect field reference in group stage")
                print(f"   Expected: $application.criticality")
                print(f"   Found: {group_stage.get('_id')}")
            
            # Check for invalid $size references
            has_invalid_size = False
            for field_name, field_expr in group_stage.items():
                if isinstance(field_expr, dict) and "$size" in field_expr:
                    size_field = field_expr["$size"]
                    if "employeeRatioSnapshot" in size_field:
                        print(f"❌ Invalid $size reference: {size_field}")
                        has_invalid_size = True
            
            if not has_invalid_size:
                print("✅ No invalid $size references found")
        
        # Check if it avoids joins
        joins = query_dict.get("joins", [])
        if not joins:
            print("✅ Correctly avoids joins (no relationships in schema)")
        else:
            print("❌ Still includes joins when it shouldn't")
        
        # Try to execute the query
        print("\n🔄 Executing corrected query...")
        results = await tool._execute_query(query_dict)
        
        print(f"✅ Query execution successful")
        print(f"   Results returned: {len(results)}")
        
        # Show results
        if results:
            print("\n📊 Results:")
            for result in results:
                print(f"   {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Correct query test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_simple_count_query():
    """Test a simple count query without complex aggregations."""
    
    print("\n🧪 Testing Simple Count Query")
    print("=" * 35)
    
    try:
        tool = create_dynamic_db_tool()
        
        # Test with the actual schema
        from schemas.unified_schema import UNIFIED_SCHEMA
        
        query_dict = await tool._generate_mongodb_query(
            user_prompt="Count applications by criticality level",
            unified_schema=UNIFIED_SCHEMA,
            limit=10,
            include_aggregation=True,
            join_strategy="lookup"
        )
        
        print("✅ Query generation successful")
        print(f"   Primary collection: {query_dict.get('primary_collection')}")
        
        # Check the aggregation pipeline
        aggregation = query_dict.get("aggregation", [])
        print(f"   Aggregation stages: {len(aggregation)}")
        
        # Execute the query
        print("\n🔄 Executing count query...")
        results = await tool._execute_query(query_dict)
        
        print(f"✅ Query execution successful")
        print(f"   Results returned: {len(results)}")
        
        # Show results
        if results:
            print("\n📊 Count Results:")
            for result in results:
                print(f"   {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Count query test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run the correct query tests."""
    print("🚀 Correct Query Tests")
    print("=" * 25)
    
    # Test group by query
    success1 = await test_correct_group_by_query()
    
    # Test count query
    success2 = await test_simple_count_query()
    
    if success1 and success2:
        print("\n🎉 All correct query tests passed!")
        print("✅ The dynamic DB tool now generates correct field references")
    else:
        print("\n❌ Some tests failed!")
        return False
    
    return True


if __name__ == "__main__":
    asyncio.run(main()) 