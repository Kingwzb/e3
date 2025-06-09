#!/usr/bin/env python3
"""
Simple API test using requests library.
"""

import requests
import json

def test_api():
    """Test the chat API endpoint."""
    
    url = "http://localhost:8000/api/chat"
    
    # Test 1: Simple engagement metrics query
    print("🔍 Test 1: Simple metrics query")
    print("-" * 40)
    
    request1 = {
        "message": "Show me engagement metrics",
        "conversation_id": "test_simple_metrics"
    }
    
    try:
        response1 = requests.post(url, json=request1, timeout=30)
        if response1.status_code == 200:
            result1 = response1.json()
            response_text1 = result1.get("response", "")
            print(f"✅ Status: {response1.status_code}")
            print(f"✅ Response length: {len(response_text1)} characters")
            print(f"\n📋 Response:")
            print(response_text1[:400] + "..." if len(response_text1) > 400 else response_text1)
        else:
            print(f"❌ Error: HTTP {response1.status_code}")
            print(f"Error: {response1.text}")
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    print("\n" + "="*50)
    
    # Test 2: Combined RAG + metrics query
    print("🔍 Test 2: Combined RAG + metrics query")
    print("-" * 40)
    
    request2 = {
        "message": "What do our user engagement metrics tell us according to the documentation?",
        "conversation_id": "test_combined_query"
    }
    
    try:
        response2 = requests.post(url, json=request2, timeout=30)
        if response2.status_code == 200:
            result2 = response2.json()
            response_text2 = result2.get("response", "")
            print(f"✅ Status: {response2.status_code}")
            print(f"✅ Response length: {len(response_text2)} characters")
            
            # Check content
            response_lower = response_text2.lower()
            has_metrics = any(keyword in response_lower for keyword in ['metric', 'data', 'users', 'engagement'])
            has_docs = any(keyword in response_lower for keyword in ['documentation', 'system', 'according'])
            
            print(f"✅ Contains metrics content: {has_metrics}")
            print(f"✅ Contains documentation content: {has_docs}")
            print(f"✅ Successfully combines both: {has_metrics and has_docs}")
            
            print(f"\n📋 Response:")
            print(response_text2[:400] + "..." if len(response_text2) > 400 else response_text2)
            
            if has_metrics and has_docs:
                print("\n🎉 SUCCESS: API properly combines RAG and metrics data!")
            else:
                print("\n⚠️  Partial success - may need further optimization")
        else:
            print(f"❌ Error: HTTP {response2.status_code}")
            print(f"Error: {response2.text}")
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_api() 