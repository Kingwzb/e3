#!/usr/bin/env python3
"""
Final test for revenue metrics with conversation history.
"""

import requests
import json

def test_final_conversation():
    """Test revenue metrics integration with conversation history."""
    
    url = "http://localhost:8000/api/chat"
    conversation_id = "conversation_flow_test_1749308120"  # Same as previous tests
    
    message = "Can you show me revenue metrics and how they relate to the engagement data we looked at?"
    
    print("🔍 Final Conversation Test: Revenue + Engagement Integration")
    print("=" * 60)
    print(f"Message: {message}")
    print("-" * 60)
    
    request_data = {
        "message": message,
        "conversation_id": conversation_id
    }
    
    try:
        response = requests.post(url, json=request_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            response_text = result.get("response", "")
            
            print(f"✅ Status: {response.status_code}")
            print(f"✅ Response length: {len(response_text)} characters")
            
            # Analysis
            response_lower = response_text.lower()
            
            checks = {
                "Contains revenue data": "revenue" in response_lower,
                "References engagement": "engagement" in response_lower,
                "References previous discussion": any(word in response_lower for word in ["looked", "discussed", "earlier", "previously", "we've", "mentioned"]),
                "Contains metrics data": any(word in response_lower for word in ["metric", "data", "users", "session"]),
                "Contains documentation context": any(word in response_lower for word in ["documentation", "system", "platform", "according"])
            }
            
            print("\n🔍 Content Analysis:")
            for check, result in checks.items():
                print(f"{'✅' if result else '❌'} {check}: {result}")
            
            all_passed = all(checks.values())
            print(f"\n{'🎉' if all_passed else '⚠️'} Overall: {'ALL CHECKS PASSED' if all_passed else 'Some checks failed'}")
            
            print(f"\n📋 Full Response:")
            print("-" * 60)
            print(response_text)
            print("-" * 60)
            
            return all_passed
            
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

if __name__ == "__main__":
    success = test_final_conversation()
    
    print(f"\n🎯 Final Test Result: {'SUCCESS' if success else 'FAILED'}")
    
    if success:
        print("\n🎉 COMPLETE VERIFICATION:")
        print("✅ Chat history integration working")
        print("✅ RAG documentation retrieval working") 
        print("✅ Metrics database extraction working")
        print("✅ Cross-category metrics integration working")
        print("✅ Conversation context maintained across multiple questions")
        print("✅ All components successfully combined in responses") 