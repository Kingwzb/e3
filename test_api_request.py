#!/usr/bin/env python3
"""
Test API request to verify RAG + Metrics integration.
"""

import asyncio
import aiohttp
import json

async def test_api_endpoint():
    """Test the chat API endpoint with a query that should trigger both RAG and metrics."""
    
    url = "http://localhost:8000/api/chat"
    
    test_requests = [
        {
            "message": "Show me engagement metrics",
            "conversation_id": "test_metrics_001"
        },
        {
            "message": "What do our user engagement metrics tell us according to the documentation?",
            "conversation_id": "test_rag_metrics_002"
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        for i, request_data in enumerate(test_requests, 1):
            print(f"\n🔍 Test {i}: {request_data['message']}")
            print("-" * 50)
            
            try:
                async with session.post(url, json=request_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        response_text = result.get("response", "")
                        print(f"✅ Status: {response.status}")
                        print(f"✅ Response length: {len(response_text)} characters")
                        
                        # Check if response contains both types of information
                        response_lower = response_text.lower()
                        has_metrics = any(keyword in response_lower for keyword in ['metric', 'data', 'users', 'engagement'])
                        has_docs = any(keyword in response_lower for keyword in ['documentation', 'system', 'according'])
                        
                        print(f"✅ Contains metrics content: {has_metrics}")
                        print(f"✅ Contains documentation content: {has_docs}")
                        print(f"✅ Successfully combines both: {has_metrics and has_docs}")
                        
                        print(f"\n📋 Response Preview:")
                        print(response_text[:300] + "..." if len(response_text) > 300 else response_text)
                    else:
                        print(f"❌ Error: HTTP {response.status}")
                        error_text = await response.text()
                        print(f"Error details: {error_text}")
                        
            except Exception as e:
                print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_api_endpoint()) 