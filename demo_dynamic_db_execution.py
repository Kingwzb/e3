#!/usr/bin/env python3
"""
Demonstration script for the dynamic database tool with actual MongoDB execution.
This script shows real query results from the database.
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.tools.dynamic_db_tool import create_dynamic_db_tool


# Import unified schema from separate file
from schemas.unified_schema import UNIFIED_SCHEMA


async def demo_simple_query():
    """Demonstrate a simple single-collection query."""
    print("\n🚀 Demo 1: Simple Single-Collection Query")
    print("=" * 60)
    
    tool = create_dynamic_db_tool()
    
    user_prompt = "Find the first 5 applications with high criticality"
    
    print(f"📝 User Prompt: {user_prompt}")
    print("🔄 Generating and executing query...")
    
    try:
        result = await tool._arun(
            user_prompt=user_prompt,
            unified_schema=UNIFIED_SCHEMA,
            limit=5
        )
        
        # Parse and display results
        result_data = json.loads(result)
        total_count = result_data.get('results', {}).get('total_count', 0)
        query_type = result_data.get('query_info', {}).get('query_type', 'N/A')
        
        print(f"\n✅ Query executed successfully!")
        print(f"   Query Type: {query_type}")
        print(f"   Total Results: {total_count}")
        
        # Show detailed results
        data = result_data.get('results', {}).get('data', [])
        if data:
            print("\n📊 Query Results:")
            for i, item in enumerate(data):
                app = item.get('application', {})
                print(f"   {i+1}. CSI ID: {app.get('csiId', 'N/A')}")
                print(f"      Criticality: {app.get('criticality', 'N/A')}")
                print(f"      Sector: {app.get('sector', 'N/A')}")
                print(f"      Status: {app.get('status', 'N/A')}")
                print()
        else:
            print("   ⚠️  No results returned (no matching data found)")
            
    except Exception as e:
        print(f"❌ Query execution failed: {e}")
        import traceback
        traceback.print_exc()


async def demo_aggregation_query():
    """Demonstrate an aggregation query."""
    print("\n🚀 Demo 2: Aggregation Query")
    print("=" * 60)
    
    tool = create_dynamic_db_tool()
    
    user_prompt = "Count applications by criticality level and show the count for each"
    
    print(f"📝 User Prompt: {user_prompt}")
    print("🔄 Generating and executing aggregation query...")
    
    try:
        result = await tool._arun(
            user_prompt=user_prompt,
            unified_schema=UNIFIED_SCHEMA,
            limit=10,
            include_aggregation=True
        )
        
        # Parse and display results
        result_data = json.loads(result)
        total_count = result_data.get('results', {}).get('total_count', 0)
        query_type = result_data.get('query_info', {}).get('query_type', 'N/A')
        
        print(f"\n✅ Aggregation executed successfully!")
        print(f"   Query Type: {query_type}")
        print(f"   Total Groups: {total_count}")
        
        # Show aggregation results
        data = result_data.get('results', {}).get('data', [])
        if data:
            print("\n📊 Aggregation Results:")
            for item in data:
                criticality = item.get('_id', 'N/A')
                count = item.get('count', 'N/A')
                print(f"   Criticality: {criticality} -> Count: {count}")
        else:
            print("   ⚠️  No aggregation results returned")
            
    except Exception as e:
        print(f"❌ Aggregation execution failed: {e}")
        import traceback
        traceback.print_exc()


async def demo_multi_collection_join():
    """Demonstrate a multi-collection join query."""
    print("\n🚀 Demo 3: Multi-Collection Join Query")
    print("=" * 60)
    
    tool = create_dynamic_db_tool()
    
    user_prompt = "Find high criticality applications and join with their employee data"
    
    print(f"📝 User Prompt: {user_prompt}")
    print("🔄 Generating and executing join query...")
    
    try:
        result = await tool._arun(
            user_prompt=user_prompt,
            unified_schema=UNIFIED_SCHEMA,
            limit=5,
            include_aggregation=True
        )
        
        # Parse and display results
        result_data = json.loads(result)
        total_count = result_data.get('results', {}).get('total_count', 0)
        collections_involved = result_data.get('summary', {}).get('collections_involved', [])
        
        print(f"\n✅ Join query executed successfully!")
        print(f"   Total Results: {total_count}")
        print(f"   Collections Involved: {collections_involved}")
        
        # Show join results
        data = result_data.get('results', {}).get('data', [])
        if data:
            print("\n📊 Join Results:")
            for i, item in enumerate(data):
                app = item.get('application', {})
                emp_data = item.get('employee_data', [])
                
                print(f"   {i+1}. Application:")
                print(f"      CSI ID: {app.get('csiId', 'N/A')}")
                print(f"      Criticality: {app.get('criticality', 'N/A')}")
                print(f"      Sector: {app.get('sector', 'N/A')}")
                print(f"      Employee Records: {len(emp_data)}")
                
                if emp_data:
                    for j, emp in enumerate(emp_data[:2]):  # Show first 2 employee records
                        print(f"         Employee {j+1}: Count={emp.get('employeeCount', 'N/A')}, Ratio={emp.get('engineerRatio', 'N/A')}")
                print()
        else:
            print("   ⚠️  No join results returned")
            
    except Exception as e:
        print(f"❌ Join query execution failed: {e}")
        import traceback
        traceback.print_exc()


async def demo_complex_analytics():
    """Demonstrate complex analytics with multiple collections."""
    print("\n🚀 Demo 4: Complex Analytics Query")
    print("=" * 60)
    
    tool = create_dynamic_db_tool()
    
    user_prompt = "Analyze applications by criticality and calculate average employee count for each criticality level"
    
    print(f"📝 User Prompt: {user_prompt}")
    print("🔄 Generating and executing complex analytics query...")
    
    try:
        result = await tool._arun(
            user_prompt=user_prompt,
            unified_schema=UNIFIED_SCHEMA,
            limit=10,
            include_aggregation=True
        )
        
        # Parse and display results
        result_data = json.loads(result)
        total_count = result_data.get('results', {}).get('total_count', 0)
        collections_involved = result_data.get('summary', {}).get('collections_involved', [])
        
        print(f"\n✅ Complex analytics executed successfully!")
        print(f"   Total Groups: {total_count}")
        print(f"   Collections Involved: {collections_involved}")
        
        # Show analytics results
        data = result_data.get('results', {}).get('data', [])
        if data:
            print("\n📊 Analytics Results:")
            for item in data:
                criticality = item.get('_id', 'N/A')
                count = item.get('count', 'N/A')
                avg_employee_count = item.get('avgEmployeeCount', 'N/A')
                total_applications = item.get('totalApplications', 'N/A')
                
                print(f"   Criticality: {criticality}")
                print(f"      Application Count: {count}")
                print(f"      Average Employee Count: {avg_employee_count}")
                print(f"      Total Applications: {total_applications}")
                print()
        else:
            print("   ⚠️  No analytics results returned")
            
    except Exception as e:
        print(f"❌ Complex analytics execution failed: {e}")
        import traceback
        traceback.print_exc()


async def demo_filtered_query():
    """Demonstrate a filtered query with specific criteria."""
    print("\n🚀 Demo 5: Filtered Query")
    print("=" * 60)
    
    tool = create_dynamic_db_tool()
    
    user_prompt = "Find active applications with high criticality that have employee ratios above 0.6"
    
    print(f"📝 User Prompt: {user_prompt}")
    print("🔄 Generating and executing filtered query...")
    
    try:
        result = await tool._arun(
            user_prompt=user_prompt,
            unified_schema=UNIFIED_SCHEMA,
            limit=5,
            include_aggregation=True
        )
        
        # Parse and display results
        result_data = json.loads(result)
        total_count = result_data.get('results', {}).get('total_count', 0)
        collections_involved = result_data.get('summary', {}).get('collections_involved', [])
        
        print(f"\n✅ Filtered query executed successfully!")
        print(f"   Total Results: {total_count}")
        print(f"   Collections Involved: {collections_involved}")
        
        # Show filtered results
        data = result_data.get('results', {}).get('data', [])
        if data:
            print("\n📊 Filtered Results:")
            for i, item in enumerate(data):
                app = item.get('application', {})
                emp_data = item.get('employee_data', [])
                
                print(f"   {i+1}. Application:")
                print(f"      CSI ID: {app.get('csiId', 'N/A')}")
                print(f"      Criticality: {app.get('criticality', 'N/A')}")
                print(f"      Status: {app.get('status', 'N/A')}")
                print(f"      Employee Records: {len(emp_data)}")
                
                if emp_data:
                    for j, emp in enumerate(emp_data[:2]):
                        print(f"         Employee {j+1}: Count={emp.get('employeeCount', 'N/A')}, Ratio={emp.get('engineerRatio', 'N/A')}")
                print()
        else:
            print("   ⚠️  No filtered results returned")
            
    except Exception as e:
        print(f"❌ Filtered query execution failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all demos."""
    print("🎯 Dynamic Database Tool - Real Execution Demo")
    print("=" * 80)
    print("This demo shows actual MongoDB queries being generated and executed")
    print("with real results from your database.")
    print()
    
    try:
        # Run all demos
        await demo_simple_query()
        await demo_aggregation_query()
        await demo_multi_collection_join()
        await demo_complex_analytics()
        await demo_filtered_query()
        
        print("\n🎉 All demos completed successfully!")
        print("The dynamic database tool is working with real MongoDB data!")
        
    except Exception as e:
        print(f"\n❌ Demo execution failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 