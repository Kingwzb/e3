#!/usr/bin/env python3
"""
Simple LLM Demo - Test specific prompts and show clear output.
"""

import asyncio
import sys
import os
import json

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.tools.ee_productivities_tools import create_ee_productivities_tools


async def test_specific_prompts():
    """Test specific prompts and show clear output."""
    print("🚀 Simple LLM Demo - Testing Specific Prompts")
    print("="*60)
    
    # Create tools
    tools = create_ee_productivities_tools()
    tool_map = {tool.name: tool for tool in tools}
    
    # Test prompts
    test_cases = [
        {
            "prompt": "How many active applications do we have?",
            "tool": "query_application_snapshots",
            "params": {"status": "Active", "limit": 5}
        },
        {
            "prompt": "Show me high criticality applications",
            "tool": "query_application_snapshots", 
            "params": {"criticality": "High", "limit": 3}
        },
        {
            "prompt": "What's our database schema?",
            "tool": "get_database_schema",
            "params": {}
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}: {test_case['prompt']}")
        print(f"Tool: {test_case['tool']}")
        print(f"Parameters: {test_case['params']}")
        
        try:
            tool = tool_map[test_case['tool']]
            result = await tool._arun(**test_case['params'])
            
            # Parse and display result
            try:
                data = json.loads(result)
                print(f"✅ Success!")
                print(f"📊 Total records: {data.get('total_count', 'N/A')}")
                
                # Show summary if available
                if 'summary' in data:
                    print(f"📈 Summary: {data['summary']}")
                
                # Show sample data
                if 'applications' in data and data['applications']:
                    app = data['applications'][0]
                    print(f"📋 Sample: {app.get('name', 'Unknown')} - {app.get('status', 'Unknown')}")
                
            except json.JSONDecodeError:
                print(f"📄 Raw result: {result[:200]}...")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print("🎉 Demo completed!")


async def main():
    """Main function."""
    await test_specific_prompts()


if __name__ == "__main__":
    asyncio.run(main()) 