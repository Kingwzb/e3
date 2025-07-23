#!/usr/bin/env python3
"""
Test script for the dynamic database tool.
This script tests the basic functionality of the dynamic database tool.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.tools.dynamic_db_tool import create_dynamic_db_tool
from app.utils.logging import logger


# Test schema document
TEST_SCHEMA = """
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "_id": {
      "type": "object",
      "properties": {
        "$oid": {
          "type": "string",
          "description": "Unique identifier for the document in MongoDB."
        }
      },
      "required": ["$oid"]
    },
    "name": {
      "type": "string",
      "description": "Name of the item."
    },
    "status": {
      "type": "string",
      "enum": ["active", "inactive", "pending"],
      "description": "Status of the item."
    },
    "value": {
      "type": "number",
      "description": "Numeric value of the item."
    },
    "createdAt": {
      "type": "string",
      "format": "date-time",
      "description": "Creation timestamp."
    }
  }
}
"""


async def test_tool_creation():
    """Test that the tool can be created successfully."""
    print("🔍 Testing tool creation...")
    
    try:
        tool = create_dynamic_db_tool()
        print("✅ Tool created successfully")
        print(f"   Tool name: {tool.name}")
        print(f"   Tool description: {tool.description}")
        return True
    except Exception as e:
        print(f"❌ Tool creation failed: {e}")
        return False


async def test_llm_client():
    """Test that the LLM client can be initialized."""
    print("\n🔍 Testing LLM client initialization...")
    
    try:
        tool = create_dynamic_db_tool()
        llm_client = await tool._get_llm_client()
        provider_info = llm_client.get_provider_info()
        print("✅ LLM client initialized successfully")
        print(f"   Provider: {provider_info.get('provider', 'Unknown')}")
        print(f"   Model: {provider_info.get('model', 'Unknown')}")
        return True
    except Exception as e:
        print(f"❌ LLM client initialization failed: {e}")
        return False


async def test_query_generation():
    """Test that the tool can generate queries."""
    print("\n🔍 Testing query generation...")
    
    try:
        tool = create_dynamic_db_tool()
        
        # Test query generation
        query_dict = await tool._generate_mongodb_query(
            user_prompt="Find all active items with value greater than 100",
            schema_document=TEST_SCHEMA,
            collection_name="test_collection",
            limit=10,
            include_aggregation=False
        )
        
        print("✅ Query generation successful")
        print(f"   Generated query: {query_dict}")
        
        # Verify query structure
        required_keys = ["filter", "projection", "sort", "limit"]
        for key in required_keys:
            if key not in query_dict:
                print(f"❌ Missing required key: {key}")
                return False
        
        print("✅ Query structure is valid")
        return True
        
    except Exception as e:
        print(f"❌ Query generation failed: {e}")
        return False


async def test_prompt_creation():
    """Test that prompts are created correctly."""
    print("\n🔍 Testing prompt creation...")
    
    try:
        tool = create_dynamic_db_tool()
        
        prompt = tool._create_query_generation_prompt(
            user_prompt="Find active items",
            schema_document=TEST_SCHEMA,
            collection_name="test_collection",
            limit=5,
            include_aggregation=False
        )
        
        print("✅ Prompt creation successful")
        print(f"   Prompt length: {len(prompt)} characters")
        
        # Check that prompt contains required elements
        required_elements = [
            "COLLECTION NAME: test_collection",
            "USER REQUEST: Find active items",
            "SCHEMA DOCUMENT:",
            "Generate only the JSON query object"
        ]
        
        for element in required_elements:
            if element not in prompt:
                print(f"❌ Missing required element: {element}")
                return False
        
        print("✅ Prompt contains all required elements")
        return True
        
    except Exception as e:
        print(f"❌ Prompt creation failed: {e}")
        return False


async def test_result_formatting():
    """Test that results are formatted correctly."""
    print("\n🔍 Testing result formatting...")
    
    try:
        tool = create_dynamic_db_tool()
        
        # Mock query dict
        query_dict = {
            "filter": {"status": "active"},
            "projection": {},
            "sort": {},
            "limit": 10,
            "collection_name": "test_collection"
        }
        
        # Mock results
        mock_results = [
            {
                "_id": {"$oid": "507f1f77bcf86cd799439011"},
                "name": "Test Item 1",
                "status": "active",
                "value": 150
            },
            {
                "_id": {"$oid": "507f1f77bcf86cd799439012"},
                "name": "Test Item 2",
                "status": "active",
                "value": 200
            }
        ]
        
        formatted_response = tool._format_results(mock_results, query_dict)
        
        print("✅ Result formatting successful")
        
        # Verify response structure
        required_keys = ["query_info", "results", "summary"]
        for key in required_keys:
            if key not in formatted_response:
                print(f"❌ Missing required key in response: {key}")
                return False
        
        print("✅ Response structure is valid")
        print(f"   Total count: {formatted_response['results']['total_count']}")
        print(f"   Data items: {len(formatted_response['results']['data'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Result formatting failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("🚀 Dynamic Database Tool Tests")
    print("=" * 50)
    
    tests = [
        test_tool_creation,
        test_llm_client,
        test_prompt_creation,
        test_query_generation,
        test_result_formatting
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
        print("🎉 All tests passed! The dynamic database tool is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the configuration and dependencies.")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 