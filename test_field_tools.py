#!/usr/bin/env python3
"""
Test script for the new field path and field values tools.
"""

import asyncio
import sys
import os
import json

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.tools.ee_productivities_tools import create_ee_productivities_tools
from app.utils.logging import logger


async def test_field_tools():
    """Test the new field path and field values tools."""
    print("🚀 Testing EE-Productivities Field Tools")
    print("=" * 60)
    
    try:
        # Create tools
        tools = create_ee_productivities_tools()
        tool_map = {tool.name: tool for tool in tools}
        
        # Test 1: Get field paths for all collections
        print("\n📋 Test 1: Getting field paths for all collections")
        print("-" * 50)
        
        field_paths_tool = tool_map["get_field_paths"]
        result = await field_paths_tool._arun()
        
        if isinstance(result, dict):
            for collection, paths in result.items():
                if isinstance(paths, list):
                    print(f"\n📁 Collection: {collection}")
                    print(f"   Field paths ({len(paths)}):")
                    for path in paths[:10]:  # Show first 10 paths
                        print(f"     • {path}")
                    if len(paths) > 10:
                        print(f"     ... and {len(paths) - 10} more")
                else:
                    print(f"\n❌ Collection {collection}: {paths}")
        else:
            print(f"❌ Error: {result}")
        
        # Test 2: Get field paths for specific collection
        print("\n📋 Test 2: Getting field paths for application_snapshot")
        print("-" * 50)
        
        result = await field_paths_tool._arun(collection_name="application_snapshot")
        if isinstance(result, dict) and "field_paths" in result:
            paths = result["field_paths"]
            print(f"📁 Collection: {result['collection']}")
            print(f"   Field paths ({len(paths)}):")
            for path in paths:
                print(f"     • {path}")
        else:
            print(f"❌ Error: {result}")
        
        # Test 3: Get field values for specific fields
        print("\n📋 Test 3: Getting field values for specific fields")
        print("-" * 50)
        
        field_values_tool = tool_map["get_field_values"]
        
        # Test application_snapshot fields
        test_fields = [
            ("application_snapshot", "status"),
            ("application_snapshot", "sector"),
            ("application_snapshot", "application.criticality"),
            ("employee_ratio", "soeId"),
            ("statistic", "nativeIDType")
        ]
        
        for collection, field_path in test_fields:
            print(f"\n🔍 Collection: {collection}, Field: {field_path}")
            result = await field_values_tool._arun(
                collection_name=collection,
                field_path=field_path,
                limit=10
            )
            
            if isinstance(result, dict) and "unique_values" in result:
                values = result["unique_values"]
                print(f"   Unique values ({len(values)}):")
                for value in values[:5]:  # Show first 5 values
                    print(f"     • {value}")
                if len(values) > 5:
                    print(f"     ... and {len(values) - 5} more")
            else:
                print(f"   ❌ Error: {result}")
        
        print("\n✅ All field tool tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main test function."""
    await test_field_tools()


if __name__ == "__main__":
    asyncio.run(main()) 