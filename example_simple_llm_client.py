#!/usr/bin/env python3
"""
Example of using the dynamic DB tool with a simple LLM client.
"""

import asyncio
import json
from app.tools.dynamic_db_tool import create_dynamic_db_tool


class SimpleLLMClient:
    """Simple LLM client that takes a prompt and returns JSON."""
    
    async def generate_response(self, prompt: str) -> str:
        """Generate a MongoDB query based on the prompt."""
        print(f"🤖 LLM received prompt: {prompt[:100]}...")
        
        # Simple logic to generate different queries based on prompt content
        if "criticality" in prompt.lower():
            query = {
                "primary_collection": "application_snapshot",
                "filter": {"application.criticality": "High"},
                "projection": {"_id": 0, "application.criticality": 1, "application.csiId": 1},
                "sort": {"application.csiId": 1},
                "limit": 5,
                "aggregation": [],
                "joins": []
            }
        elif "group" in prompt.lower() or "count" in prompt.lower():
            query = {
                "primary_collection": "application_snapshot",
                "filter": {},
                "projection": {},
                "sort": {},
                "limit": 10,
                "aggregation": [
                    {
                        "$group": {
                            "_id": "$application.criticality",
                            "count": {"$sum": 1}
                        }
                    },
                    {
                        "$sort": {"count": -1}
                    }
                ],
                "joins": []
            }
        else:
            # Default query
            query = {
                "primary_collection": "application_snapshot",
                "filter": {},
                "projection": {"_id": 0},
                "sort": {},
                "limit": 5,
                "aggregation": [],
                "joins": []
            }
        
        return json.dumps(query, indent=2)


class MockMongoAdapter:
    """Mock MongoDB adapter for testing."""
    
    def __init__(self):
        self.collection_name = "application_snapshot"
    
    async def initialize(self):
        print("📊 Mock MongoDB adapter initialized")
    
    async def switch_collection(self, collection_name: str):
        self.collection_name = collection_name
        print(f"📊 Switched to collection: {collection_name}")
    
    async def execute_native_query(self, query):
        print(f"📊 Executing query: {query.operation} on {query.collection_table}")
        
        # Return mock data
        if query.operation == "find":
            return [
                {"application": {"criticality": "High", "csiId": 123}},
                {"application": {"criticality": "Medium", "csiId": 456}},
                {"application": {"criticality": "Low", "csiId": 789}}
            ]
        elif query.operation == "aggregate":
            return [
                {"_id": "High", "count": 15},
                {"_id": "Medium", "count": 25},
                {"_id": "Low", "count": 10}
            ]
        else:
            return []


async def main():
    """Example usage of the dynamic DB tool with simple LLM client."""
    
    print("🚀 Dynamic DB Tool with Simple LLM Client Example")
    print("=" * 55)
    
    # Create the tool with custom components
    tool = create_dynamic_db_tool(
        adapter=MockMongoAdapter(),
        llm_client=SimpleLLMClient()
    )
    
    # Define a simple schema
    schema = """
    ### application_snapshot Collection
    **Schema**:
    ```json
    {
      "properties": {
        "application": {
          "properties": {
            "csiId": {"type": "integer"},
            "criticality": {"type": "string", "enum": ["High", "Medium", "Low"]}
          }
        }
      }
    }
    ```
    """
    
    # Test different queries
    test_queries = [
        "Find applications with high criticality",
        "Group applications by criticality and count them",
        "Show me all applications"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🧪 Test {i}: {query}")
        print("-" * 40)
        
        try:
            result = await tool._arun(
                user_prompt=query,
                unified_schema=schema,
                limit=5
            )
            
            print("✅ Query executed successfully")
            print(f"📊 Result: {result[:200]}...")
            
        except Exception as e:
            print(f"❌ Query failed: {e}")
    
    print("\n🎉 Example completed!")


if __name__ == "__main__":
    asyncio.run(main()) 