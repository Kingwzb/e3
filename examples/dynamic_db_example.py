#!/usr/bin/env python3
"""
Example script demonstrating the dynamic database tool.
This script shows how to use the dynamic database tool with schema documents
to generate and execute MongoDB queries on the fly.
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.tools.dynamic_db_tool import create_dynamic_db_tool


# Import unified schema from separate file
from schemas.unified_schema import UNIFIED_SCHEMA


async def example_single_collection_queries():
    """Example queries for single collections."""
    print("\n🔍 Example: Single Collection Queries")
    print("=" * 50)
    
    tool = create_dynamic_db_tool()
    
    # Example 1: Find high criticality applications
    print("\n1. Finding high criticality applications...")
    result1 = await tool._arun(
        user_prompt="Find all applications with high criticality level",
        unified_schema=UNIFIED_SCHEMA,
        limit=10
    )
    
    # Parse and display results
    try:
        import json
        result_data = json.loads(result1)
        total_count = result_data.get('results', {}).get('total_count', 0)
        print(f"✅ Query executed successfully - {total_count} results found")
        
        # Show sample data
        data = result_data.get('results', {}).get('data', [])
        if data:
            print("📊 Sample Results:")
            for i, item in enumerate(data[:3]):
                app = item.get('application', {})
                print(f"   {i+1}. CSI ID: {app.get('csiId', 'N/A')}, Criticality: {app.get('criticality', 'N/A')}")
        else:
            print("   ⚠️  No results returned (might be expected if no matching data)")
    except Exception as e:
        print(f"❌ Error parsing results: {e}")
        print(f"Raw result: {result1[:500]}...")
    
    # Example 2: Count applications by criticality
    print("\n2. Counting applications by criticality...")
    result2 = await tool._arun(
        user_prompt="Count the number of applications for each criticality level",
        unified_schema=UNIFIED_SCHEMA,
        limit=10,
        include_aggregation=True
    )
    
    # Parse and display aggregation results
    try:
        result_data = json.loads(result2)
        total_count = result_data.get('results', {}).get('total_count', 0)
        print(f"✅ Aggregation executed successfully - {total_count} groups found")
        
        data = result_data.get('results', {}).get('data', [])
        if data:
            print("📊 Aggregation Results:")
            for item in data:
                print(f"   Criticality: {item.get('_id', 'N/A')}, Count: {item.get('count', 'N/A')}")
        else:
            print("   ⚠️  No aggregation results returned")
    except Exception as e:
        print(f"❌ Error parsing aggregation results: {e}")
        print(f"Raw result: {result2[:500]}...")
    
    # Example 3: Find applications by level3 organization
    print("\n3. Finding applications by organization...")
    result3 = await tool._arun(
        user_prompt="Find applications in the IT department (level3)",
        unified_schema=UNIFIED_SCHEMA,
        limit=5
    )
    
    # Parse and display results
    try:
        result_data = json.loads(result3)
        total_count = result_data.get('results', {}).get('total_count', 0)
        print(f"✅ Organization query executed successfully - {total_count} results found")
        
        data = result_data.get('results', {}).get('data', [])
        if data:
            print("📊 Sample Results:")
            for i, item in enumerate(data[:3]):
                app = item.get('application', {})
                print(f"   {i+1}. CSI ID: {app.get('csiId', 'N/A')}, Level3: {app.get('level3', 'N/A')}")
        else:
            print("   ⚠️  No results returned")
    except Exception as e:
        print(f"❌ Error parsing organization results: {e}")
        print(f"Raw result: {result3[:500]}...")


async def example_multi_collection_joins():
    """Example queries involving multiple collections with joins."""
    print("\n🔍 Example: Multi-Collection Join Queries")
    print("=" * 50)
    
    tool = create_dynamic_db_tool()
    
    # Example 1: Join applications with employee ratios
    print("\n1. Joining applications with employee ratios...")
    result1 = await tool._arun(
        user_prompt="Find high criticality applications and their associated employee ratio data",
        unified_schema=UNIFIED_SCHEMA,
        limit=10,
        include_aggregation=True
    )
    
    # Parse and display join results
    try:
        import json
        result_data = json.loads(result1)
        total_count = result_data.get('results', {}).get('total_count', 0)
        collections_involved = result_data.get('summary', {}).get('collections_involved', [])
        print(f"✅ Join query executed successfully - {total_count} results found")
        print(f"   Collections involved: {collections_involved}")
        
        data = result_data.get('results', {}).get('data', [])
        if data:
            print("📊 Sample Join Results:")
            for i, item in enumerate(data[:3]):
                app = item.get('application', {})
                emp_data = item.get('employee_data', [])
                print(f"   {i+1}. CSI ID: {app.get('csiId', 'N/A')}, Criticality: {app.get('criticality', 'N/A')}")
                print(f"      Employee Records: {len(emp_data)}")
                if emp_data:
                    print(f"      Sample Employee Count: {emp_data[0].get('employeeCount', 'N/A')}")
        else:
            print("   ⚠️  No join results returned")
    except Exception as e:
        print(f"❌ Error parsing join results: {e}")
        print(f"Raw result: {result1[:500]}...")
    
    # Example 2: Complex join with management segments
    print("\n2. Complex join with management segments...")
    result2 = await tool._arun(
        user_prompt="Find applications by criticality level and join with their management segment information",
        unified_schema=UNIFIED_SCHEMA,
        limit=10,
        include_aggregation=True
    )
    
    # Parse and display complex join results
    try:
        result_data = json.loads(result2)
        total_count = result_data.get('results', {}).get('total_count', 0)
        collections_involved = result_data.get('summary', {}).get('collections_involved', [])
        print(f"✅ Complex join executed successfully - {total_count} results found")
        print(f"   Collections involved: {collections_involved}")
        
        data = result_data.get('results', {}).get('data', [])
        if data:
            print("📊 Sample Complex Join Results:")
            for i, item in enumerate(data[:3]):
                app = item.get('application', {})
                seg_data = item.get('segment_data', [])
                print(f"   {i+1}. CSI ID: {app.get('csiId', 'N/A')}, Criticality: {app.get('criticality', 'N/A')}")
                print(f"      Segment Records: {len(seg_data)}")
                if seg_data:
                    print(f"      Sample Segment: {seg_data[0].get('name', 'N/A')}")
        else:
            print("   ⚠️  No complex join results returned")
    except Exception as e:
        print(f"❌ Error parsing complex join results: {e}")
        print(f"Raw result: {result2[:500]}...")
    
    # Example 3: Multi-collection aggregation
    print("\n3. Multi-collection aggregation...")
    result3 = await tool._arun(
        user_prompt="Count applications by sector and include average employee count for each sector",
        unified_schema=UNIFIED_SCHEMA,
        limit=10,
        include_aggregation=True
    )
    
    # Parse and display aggregation results
    try:
        result_data = json.loads(result3)
        total_count = result_data.get('results', {}).get('total_count', 0)
        collections_involved = result_data.get('summary', {}).get('collections_involved', [])
        print(f"✅ Multi-collection aggregation executed successfully - {total_count} groups found")
        print(f"   Collections involved: {collections_involved}")
        
        data = result_data.get('results', {}).get('data', [])
        if data:
            print("📊 Aggregation Results:")
            for item in data:
                sector = item.get('_id', 'N/A')
                count = item.get('count', 'N/A')
                avg_employee_count = item.get('avgEmployeeCount', 'N/A')
                print(f"   Sector: {sector}, Count: {count}, Avg Employee Count: {avg_employee_count}")
        else:
            print("   ⚠️  No aggregation results returned")
    except Exception as e:
        print(f"❌ Error parsing aggregation results: {e}")
        print(f"Raw result: {result3[:500]}...")


async def example_complex_analytics():
    """Example of complex analytical queries across multiple collections."""
    print("\n🔍 Example: Complex Analytics Queries")
    print("=" * 50)
    
    tool = create_dynamic_db_tool()
    
    # Example 1: Cross-collection analysis
    print("\n1. Cross-collection analysis...")
    result1 = await tool._arun(
        user_prompt="Analyze the relationship between application criticality and employee ratios, group by sector",
        unified_schema=UNIFIED_SCHEMA,
        limit=15,
        include_aggregation=True
    )
    print(f"Result: {result1[:500]}...")
    
    # Example 2: Time-based analysis
    print("\n2. Time-based analysis...")
    result2 = await tool._arun(
        user_prompt="Find applications with their employee ratio trends over the last year",
        unified_schema=UNIFIED_SCHEMA,
        limit=10,
        include_aggregation=True
    )
    print(f"Result: {result2[:500]}...")
    
    # Example 3: Performance metrics
    print("\n3. Performance metrics analysis...")
    result3 = await tool._arun(
        user_prompt="Calculate average engineer ratio by application criticality and management segment",
        unified_schema=UNIFIED_SCHEMA,
        limit=10,
        include_aggregation=True
    )
    print(f"Result: {result3[:500]}...")


async def example_filtering_and_sorting():
    """Example of complex filtering and sorting across collections."""
    print("\n🔍 Example: Advanced Filtering and Sorting")
    print("=" * 50)
    
    tool = create_dynamic_db_tool()
    
    # Example 1: Filtered joins
    print("\n1. Filtered joins...")
    result1 = await tool._arun(
        user_prompt="Find active applications with high criticality that have employee ratios above 0.7",
        unified_schema=UNIFIED_SCHEMA,
        limit=10,
        include_aggregation=True
    )
    print(f"Result: {result1[:500]}...")
    
    # Example 2: Sorted multi-collection results
    print("\n2. Sorted multi-collection results...")
    result2 = await tool._arun(
        user_prompt="Find applications sorted by criticality level and then by employee count in descending order",
        unified_schema=UNIFIED_SCHEMA,
        limit=10,
        include_aggregation=True
    )
    print(f"Result: {result2[:500]}...")
    
    # Example 3: Conditional joins
    print("\n3. Conditional joins...")
    result3 = await tool._arun(
        user_prompt="Find applications that have both employee ratio data and management segment data, filter by active status",
        unified_schema=UNIFIED_SCHEMA,
        limit=10,
        include_aggregation=True
    )
    print(f"Result: {result3[:500]}...")


async def main():
    """Run all examples."""
    print("🚀 Dynamic Database Tool Examples")
    print("=" * 60)
    
    try:
        # Run examples
        await example_single_collection_queries()
        await example_multi_collection_joins()
        await example_complex_analytics()
        await example_filtering_and_sorting()
        
        print("\n✅ All examples completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 