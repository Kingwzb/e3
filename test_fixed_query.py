#!/usr/bin/env python3
"""
Test the fixed query generation with updated constraints.
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_multi_collection_dynamic_db import create_dynamic_db_tool


async def test_fixed_group_by_query():
    """Test the fixed group by query generation."""
    
    print("🧪 Testing Fixed Group By Query")
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
        print(f"   Has aggregation: {bool(query_dict.get('aggregation'))}")
        print(f"   Has joins: {bool(query_dict.get('joins'))}")
        
        # Check if it's a simple single-collection query (which is correct)
        if not query_dict.get("joins") and query_dict.get("aggregation"):
            print("✅ Query correctly avoids joins (no relationships in schema)")
            
            # Execute the query
            print("\n🔄 Executing fixed query...")
            results = await tool._execute_query(query_dict)
            
            print(f"✅ Query execution successful")
            print(f"   Results returned: {len(results)}")
            
            # Show results
            if results:
                print("\n📊 Results:")
                for result in results:
                    print(f"   {result}")
            
            return True
        else:
            print("❌ Query still includes joins when it shouldn't")
            print(f"   Query: {query_dict}")
            return False
        
    except Exception as e:
        print(f"❌ Fixed query test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_simple_filter_query():
    """Test a simple filter query."""
    
    print("\n🧪 Testing Simple Filter Query")
    print("=" * 35)
    
    try:
        tool = create_dynamic_db_tool()
        
        # Test with the actual schema
        from schemas.unified_schema import UNIFIED_SCHEMA
        
        query_dict = await tool._generate_mongodb_query(
            user_prompt="Find applications with high criticality",
            unified_schema=UNIFIED_SCHEMA,
            limit=5,
            include_aggregation=False,
            join_strategy="lookup"
        )
        
        print("✅ Query generation successful")
        print(f"   Primary collection: {query_dict.get('primary_collection')}")
        print(f"   Filter: {query_dict.get('filter')}")
        print(f"   Has joins: {bool(query_dict.get('joins'))}")
        
        # Execute the query
        print("\n🔄 Executing simple filter query...")
        results = await tool._execute_query(query_dict)
        
        print(f"✅ Query execution successful")
        print(f"   Results returned: {len(results)}")
        
        # Show sample results
        if results:
            print("\n📊 Sample Results:")
            for i, result in enumerate(results[:3]):
                print(f"   Result {i+1}: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Simple filter query test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run the fixed query tests."""
    print("🚀 Fixed Query Tests")
    print("=" * 25)
    
    # Test simple filter query
    success1 = await test_simple_filter_query()
    
    # Test group by query
    success2 = await test_fixed_group_by_query()
    
    if success1 and success2:
        print("\n🎉 All fixed tests passed!")
        print("✅ The dynamic DB tool now correctly handles queries without relationships")
    else:
        print("\n❌ Some tests failed!")
        return False
    
    return True


if __name__ == "__main__":
    asyncio.run(main()) 