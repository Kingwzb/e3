#!/usr/bin/env python3
"""
Test script for ee-productivities LLM tools integration.
This script demonstrates how the LLM tools can be used to query the MongoDB database
and answer natural language questions about the data.
"""

import asyncio
import sys
import os
import json
from typing import Dict, Any, List

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.tools.ee_productivities_tools import create_ee_productivities_tools
from app.utils.logging import logger


class EEProductivitiesLLMTester:
    """Test class for ee-productivities LLM tools integration."""
    
    def __init__(self):
        self.tools = create_ee_productivities_tools()
        self.tool_map = {tool.name: tool for tool in self.tools}
    
    async def test_database_schema(self):
        """Test getting database schema information."""
        print("\n" + "="*60)
        print("Testing Database Schema Tool")
        print("="*60)
        
        try:
            schema_tool = self.tool_map["get_database_schema"]
            
            # Test getting all schemas
            print("📊 Getting all database schemas...")
            result = await schema_tool._arun()
            schemas = json.loads(result) if isinstance(result, str) else result
            
            print(f"✅ Found {len(schemas)} collections:")
            for collection_name, schema_info in schemas.items():
                if isinstance(schema_info, dict) and "document_count" in schema_info:
                    print(f"   📁 {collection_name}: {schema_info['document_count']} documents")
                else:
                    print(f"   📁 {collection_name}: Schema info available")
            
            # Test getting specific collection schema
            print("\n📋 Getting application_snapshot schema...")
            result = await schema_tool._arun(collection_name="application_snapshot")
            schema = json.loads(result) if isinstance(result, str) else result
            
            if isinstance(schema, dict):
                print(f"   📄 Document count: {schema.get('document_count', 'Unknown')}")
                print(f"   💾 Storage size: {schema.get('storage_size', 'Unknown')} bytes")
                print(f"   🔍 Indexes: {len(schema.get('indexes', []))}")
            
            print("✅ Database schema test completed successfully!")
            
        except Exception as e:
            print(f"❌ Database schema test failed: {e}")
            import traceback
            traceback.print_exc()
    
    async def test_application_snapshots(self):
        """Test application snapshots queries."""
        print("\n" + "="*60)
        print("Testing Application Snapshots Tool")
        print("="*60)
        
        try:
            app_tool = self.tool_map["query_application_snapshots"]
            
            # Test 1: Get all active applications
            print("🔍 Querying active applications...")
            result = await app_tool._arun(status="Active", limit=5)
            data = json.loads(result)
            
            print(f"✅ Found {data['total_count']} active applications")
            if data['summary']:
                print(f"   📊 Status distribution: {data['summary']['status_distribution']}")
                print(f"   🏢 Sector distribution: {data['summary']['sector_distribution']}")
                print(f"   ⚠️  Criticality distribution: {data['summary']['criticality_distribution']}")
            
            # Test 2: Get high criticality applications
            print("\n🔍 Querying high criticality applications...")
            result = await app_tool._arun(criticality="High", limit=3)
            data = json.loads(result)
            
            print(f"✅ Found {data['total_count']} high criticality applications")
            
            # Test 3: Get applications by sector
            print("\n🔍 Querying Technology sector applications...")
            result = await app_tool._arun(sector="Technology", limit=3)
            data = json.loads(result)
            
            print(f"✅ Found {data['total_count']} Technology sector applications")
            
            # Test 4: Get applications by development model
            print("\n🔍 Querying Agile development applications...")
            result = await app_tool._arun(developmentModel="Agile", limit=3)
            data = json.loads(result)
            
            print(f"✅ Found {data['total_count']} Agile development applications")
            
            print("✅ Application snapshots test completed successfully!")
            
        except Exception as e:
            print(f"❌ Application snapshots test failed: {e}")
            import traceback
            traceback.print_exc()
    
    async def test_employee_ratios(self):
        """Test employee ratios queries."""
        print("\n" + "="*60)
        print("Testing Employee Ratios Tool")
        print("="*60)
        
        try:
            ratio_tool = self.tool_map["query_employee_ratios"]
            
            # Test 1: Get all employee ratios
            print("👥 Querying employee ratios...")
            result = await ratio_tool._arun(limit=3)
            data = json.loads(result)
            
            print(f"✅ Found {data['total_count']} employee ratio records")
            if data['summary']:
                print(f"   📊 Total employee snapshots: {data['summary']['total_employees']}")
                print(f"   🛠️  Total tools adoption snapshots: {data['summary']['total_tools_adoption']}")
            
            # Test 2: Get employee ratios for specific year
            print("\n👥 Querying employee ratios for 2023...")
            result = await ratio_tool._arun(year=2023, limit=2)
            data = json.loads(result)
            
            print(f"✅ Found {data['total_count']} employee ratio records for 2023")
            
            print("✅ Employee ratios test completed successfully!")
            
        except Exception as e:
            print(f"❌ Employee ratios test failed: {e}")
            import traceback
            traceback.print_exc()
    
    async def test_employee_trees(self):
        """Test employee trees queries."""
        print("\n" + "="*60)
        print("Testing Employee Trees Tool")
        print("="*60)
        
        try:
            tree_tool = self.tool_map["query_employee_trees"]
            
            # Test 1: Get top-level employee trees
            print("🌳 Querying top-level employee trees...")
            result = await tree_tool._arun(hierarchy=1, limit=3)
            data = json.loads(result)
            
            print(f"✅ Found {data['total_count']} top-level employee trees")
            if data['summary']:
                print(f"   👥 Total employees: {data['summary']['total_employees']}")
                print(f"   🔧 Total engineers: {data['summary']['total_engineers']}")
                print(f"   📊 Hierarchy distribution: {data['summary']['hierarchy_distribution']}")
            
            # Test 2: Get employee trees for specific year
            print("\n🌳 Querying employee trees for 2023...")
            result = await tree_tool._arun(year=2023, limit=2)
            data = json.loads(result)
            
            print(f"✅ Found {data['total_count']} employee trees for 2023")
            
            print("✅ Employee trees test completed successfully!")
            
        except Exception as e:
            print(f"❌ Employee trees test failed: {e}")
            import traceback
            traceback.print_exc()
    
    async def test_enablers(self):
        """Test enablers queries."""
        print("\n" + "="*60)
        print("Testing Enablers Tool")
        print("="*60)
        
        try:
            enabler_tool = self.tool_map["query_enablers"]
            
            # Test 1: Get all enablers
            print("🔧 Querying enablers...")
            result = await enabler_tool._arun(limit=3)
            data = json.loads(result)
            
            print(f"✅ Found {data['total_count']} enabler records")
            if data['summary']:
                print(f"   📊 Total aggregations: {data['summary']['total_aggregations']}")
                print(f"   🔧 Total enablers: {data['summary']['total_enablers']}")
            
            # Test 2: Get enablers for specific year
            print("\n🔧 Querying enablers for 2023...")
            result = await enabler_tool._arun(year=2023, limit=2)
            data = json.loads(result)
            
            print(f"✅ Found {data['total_count']} enabler records for 2023")
            
            print("✅ Enablers test completed successfully!")
            
        except Exception as e:
            print(f"❌ Enablers test failed: {e}")
            import traceback
            traceback.print_exc()
    
    async def test_management_segments(self):
        """Test management segments queries."""
        print("\n" + "="*60)
        print("Testing Management Segments Tool")
        print("="*60)
        
        try:
            segment_tool = self.tool_map["query_management_segments"]
            
            # Test 1: Get all management segments
            print("🏢 Querying management segments...")
            result = await segment_tool._arun(limit=3)
            data = json.loads(result)
            
            print(f"✅ Found {data['total_count']} management segment records")
            if data['summary']:
                print(f"   📊 Hierarchy distribution: {data['summary']['hierarchy_distribution']}")
                print(f"   🔄 Version distribution: {data['summary']['version_distribution']}")
            
            # Test 2: Get segments for specific year
            print("\n🏢 Querying management segments for 2023...")
            result = await segment_tool._arun(year=2023, limit=2)
            data = json.loads(result)
            
            print(f"✅ Found {data['total_count']} management segment records for 2023")
            
            print("✅ Management segments test completed successfully!")
            
        except Exception as e:
            print(f"❌ Management segments test failed: {e}")
            import traceback
            traceback.print_exc()
    
    async def test_statistics(self):
        """Test statistics queries."""
        print("\n" + "="*60)
        print("Testing Statistics Tool")
        print("="*60)
        
        try:
            stat_tool = self.tool_map["query_statistics"]
            
            # Test 1: Get all statistics
            print("📊 Querying statistics...")
            result = await stat_tool._arun(limit=3)
            data = json.loads(result)
            
            print(f"✅ Found {data['total_count']} statistic records")
            if data['summary']:
                print(f"   📈 Total snapshots: {data['summary']['total_snapshots']}")
                print(f"   🏷️  Type distribution: {data['summary']['type_distribution']}")
            
            # Test 2: Get statistics for specific year
            print("\n📊 Querying statistics for 2023...")
            result = await stat_tool._arun(year=2023, limit=2)
            data = json.loads(result)
            
            print(f"✅ Found {data['total_count']} statistic records for 2023")
            
            print("✅ Statistics test completed successfully!")
            
        except Exception as e:
            print(f"❌ Statistics test failed: {e}")
            import traceback
            traceback.print_exc()
    
    async def test_natural_language_scenarios(self):
        """Test natural language scenarios that would be used by LLM."""
        print("\n" + "="*60)
        print("Testing Natural Language Scenarios")
        print("="*60)
        
        scenarios = [
            {
                "question": "How many active applications do we have?",
                "tool": "query_application_snapshots",
                "params": {"status": "Active", "limit": 10}
            },
            {
                "question": "What are the high criticality applications?",
                "tool": "query_application_snapshots",
                "params": {"criticality": "High", "limit": 5}
            },
            {
                "question": "Show me Technology sector applications",
                "tool": "query_application_snapshots",
                "params": {"sector": "Technology", "limit": 5}
            },
            {
                "question": "What are our employee ratios?",
                "tool": "query_employee_ratios",
                "params": {"limit": 3}
            },
            {
                "question": "Show me the organizational hierarchy",
                "tool": "query_employee_trees",
                "params": {"hierarchy": 1, "limit": 3}
            },
            {
                "question": "What enablers do we have?",
                "tool": "query_enablers",
                "params": {"limit": 3}
            },
            {
                "question": "Show me management segments",
                "tool": "query_management_segments",
                "params": {"limit": 3}
            },
            {
                "question": "What statistics are available?",
                "tool": "query_statistics",
                "params": {"limit": 3}
            }
        ]
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n{i}. Question: {scenario['question']}")
            print(f"   Tool: {scenario['tool']}")
            print(f"   Parameters: {scenario['params']}")
            
            try:
                tool = self.tool_map[scenario['tool']]
                result = await tool._arun(**scenario['params'])
                data = json.loads(result)
                
                print(f"   ✅ Result: {data['total_count']} records found")
                
                # Show some sample data
                if 'applications' in data and data['applications']:
                    app = data['applications'][0]
                    print(f"   📋 Sample: {app.get('name', 'Unknown')} - {app.get('status', 'Unknown')}")
                elif 'employee_ratios' in data and data['employee_ratios']:
                    ratio = data['employee_ratios'][0]
                    print(f"   📋 Sample: SOE ID {ratio.get('soeId', 'Unknown')}")
                elif 'employee_trees' in data and data['employee_trees']:
                    tree = data['employee_trees'][0]
                    print(f"   📋 Sample: SOE ID {tree.get('soeId', 'Unknown')} - {tree.get('totalNum', 0)} employees")
                elif 'enablers' in data and data['enablers']:
                    enabler = data['enablers'][0]
                    print(f"   📋 Sample: CSI ID {enabler.get('csiId', 'Unknown')}")
                elif 'segments' in data and data['segments']:
                    segment = data['segments'][0]
                    print(f"   📋 Sample: {segment.get('name', 'Unknown')} - Hierarchy {segment.get('hierarchy', 0)}")
                elif 'statistics' in data and data['statistics']:
                    stat = data['statistics'][0]
                    print(f"   📋 Sample: {stat.get('nativeID', 'Unknown')} - {stat.get('nativeIDType', 'Unknown')}")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        print("\n✅ Natural language scenarios test completed!")
    
    async def run_all_tests(self):
        """Run all tests."""
        print("🚀 Starting EE-Productivities LLM Tools Integration Tests")
        
        await self.test_database_schema()
        await self.test_application_snapshots()
        await self.test_employee_ratios()
        await self.test_employee_trees()
        await self.test_enablers()
        await self.test_management_segments()
        await self.test_statistics()
        await self.test_natural_language_scenarios()
        
        print("\n🎉 All tests completed successfully!")


async def main():
    """Main test function."""
    tester = EEProductivitiesLLMTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main()) 