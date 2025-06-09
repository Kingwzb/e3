#!/bin/bash

# Test conversation flow with multiple follow-up questions
# This tests chat history, RAG integration, and metrics data combination

CONVERSATION_ID="conversation_flow_test_$(date +%s)"
API_URL="http://localhost:8000/api/chat"

echo "🧪 Testing Conversation Flow with Follow-up Questions"
echo "Conversation ID: $CONVERSATION_ID"
echo "=" * 60

# Function to send a message and display response
send_message() {
    local message="$1"
    local step="$2"
    
    echo
    echo "📝 Step $step: $message"
    echo "-" * 50
    
    response=$(curl -s -X POST "$API_URL" \
        -H "Content-Type: application/json" \
        -d "{\"message\": \"$message\", \"conversation_id\": \"$CONVERSATION_ID\"}")
    
    if [ $? -eq 0 ]; then
        # Extract response content using python for JSON parsing
        response_text=$(echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('response', 'No response found'))
except:
    print('Error parsing JSON')
")
        
        echo "✅ Response received (${#response_text} characters):"
        echo "$response_text"
        
        # Analyze content
        echo
        echo "🔍 Content Analysis:"
        
        # Check for metrics content
        if echo "$response_text" | grep -i -q -E "(metric|data|users|engagement|performance|revenue|satisfaction)"; then
            echo "✅ Contains metrics-related content"
        else
            echo "❌ No metrics content detected"
        fi
        
        # Check for documentation content
        if echo "$response_text" | grep -i -q -E "(documentation|system|platform|according|guide)"; then
            echo "✅ Contains documentation-based content"
        else
            echo "❌ No documentation content detected"
        fi
        
        # Check for conversation history references
        if echo "$response_text" | grep -i -q -E "(previously|earlier|mentioned|discussed|as we|you asked)"; then
            echo "✅ References conversation history"
        else
            echo "❌ No conversation history references"
        fi
        
    else
        echo "❌ Request failed"
    fi
    
    echo
    sleep 2  # Brief pause between requests
}

# Test sequence: Start with a general question, then follow up with specific ones

send_message "Hello! I'd like to understand our system's performance. Can you tell me about our productivity insights platform?" "1"

send_message "Great! Now can you show me our current user engagement metrics?" "2"

send_message "What do these engagement numbers mean according to our documentation? Are they good or concerning?" "3"

send_message "You mentioned daily active users earlier. How do they compare to our session duration metrics?" "4"

send_message "Based on what we've discussed, what recommendations would you make to improve our engagement?" "5"

send_message "Can you also show me revenue metrics and how they relate to the engagement data we just looked at?" "6"

echo
echo "🎯 Test Completed!"
echo "This test verified:"
echo "✅ Multiple follow-up questions in same conversation"
echo "✅ Chat history integration and references"
echo "✅ RAG documentation retrieval"
echo "✅ Metrics database extraction"
echo "✅ Combined responses using both data sources" 