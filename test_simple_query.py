#!/usr/bin/env python3
"""
Simple test to verify basic query functionality.
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_multi_collection_dynamic_db import create_dynamic_db_tool


async def test_simple_query():
    """Test a simple query without complex joins."""
    
    print("🧪 Testing Simple Query")
    print("=" * 30)
    
    try:
        tool = create_dynamic_db_tool()
        
        # Test a simple query that should work
        query_dict = await tool._generate_mongodb_query(
            user_prompt="Find all applications with high criticality",
            unified_schema="""# Simple test schema
## Collections

### application_snapshot Collection
**Schema**:
```json
{
  "type": "object",
  "properties": {
    "application": {
      "type": "object",
      "properties": {
        "csiId": {"type": "integer"},
        "criticality": {"type": "string", "enum": ["High", "Medium", "Low"]}
      }
    }
  }
}
```""",
            limit=5,
            include_aggregation=False,
            join_strategy="lookup"
        )
        
        print("✅ Query generation successful")
        print(f"   Query: {query_dict}")
        
        # Execute the query
        print("\n🔄 Executing simple query...")
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
        print(f"❌ Simple query test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_group_by_criticality():
    """Test a simple group by query."""
    
    print("\n🧪 Testing Group By Criticality")
    print("=" * 35)
    
    try:
        tool = create_dynamic_db_tool()
        
        # Test a simple aggregation query
        query_dict = await tool._generate_mongodb_query(
            user_prompt="Group applications by criticality and count them",
            unified_schema="""# Simple test schema
## Collections

### application_snapshot Collection
**Schema**:
```json
{
  "type": "object",
  "properties": {
    "application": {
      "type": "object",
      "properties": {
        "csiId": {"type": "integer"},
        "criticality": {"type": "string", "enum": ["High", "Medium", "Low"]}
      }
    }
  }
}
```""",
            limit=10,
            include_aggregation=True,
            join_strategy="lookup"
        )
        
        print("✅ Group by query generation successful")
        print(f"   Query: {query_dict}")
        
        # Execute the query
        print("\n🔄 Executing group by query...")
        results = await tool._execute_query(query_dict)
        
        print(f"✅ Group by query execution successful")
        print(f"   Results returned: {len(results)}")
        
        # Show results
        if results:
            print("\n📊 Group By Results:")
            for result in results:
                print(f"   {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Group by query test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run simple query tests."""
    print("🚀 Simple Query Tests")
    print("=" * 25)
    
    # Test simple query
    success1 = await test_simple_query()
    
    # Test group by query
    success2 = await test_group_by_criticality()
    
    if success1 and success2:
        print("\n🎉 All simple tests passed!")
    else:
        print("\n❌ Some tests failed!")
        return False
    
    return True


if __name__ == "__main__":
    asyncio.run(main()) 