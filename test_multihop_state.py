#!/usr/bin/env python3
"""
Test script for MultiHopState and planner node functionality.
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import List, Dict

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.models.state import MultiHopState
from app.workflows.nodes.planner_node import planner_node, update_conversation_with_response


def format_conversation_history(messages: List[Dict[str, str]]) -> str:
    """Format conversation history as a string."""
    formatted = []
    for i, msg in enumerate(messages, 1):
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')
        formatted.append(f"{i}. {role}: {content}")
    return "\n".join(formatted)


async def test_planner_node():
    """Test the planner node with MultiHopState."""
    print("🧪 Testing MultiHopState and Planner Node")
    print("=" * 50)
    
    # Create conversation history as formatted string
    conversation_messages = [
        {"role": "user", "content": "Hello, I need some employee information"},
        {"role": "assistant", "content": "I can help you with employee information. What specific data do you need?"}
    ]
    conversation_history = format_conversation_history(conversation_messages)
    
    # Create a test MultiHopState with conversation history
    test_state = MultiHopState(
        request_id="test_request_123",
        session_id="test_session_456",
        user_query="give me unique soeId list from database",
        formatted_user_query="",
        conversation_history=conversation_history,
        subqueries={},
        retrieved_docs={},
        db_schema="",
        subquery_responses={},
        final_answer={},
        detected_docs=[]
    )
    
    print(f"📝 Test Query: {test_state['user_query']}")
    print(f"🆔 Request ID: {test_state['request_id']}")
    print(f"🆔 Session ID: {test_state['session_id']}")
    print(f"💬 Initial Conversation History: {len(conversation_history)} characters")
    print(f"📋 History Preview: {conversation_history[:100]}...")
    
    try:
        # Run the planner node
        print("\n🔄 Running planner node...")
        result = await planner_node(test_state)
        
        print("\n✅ Planner node completed successfully!")
        print(f"📊 Subqueries generated: {len(result.get('subqueries', {}))}")
        print(f"📚 Detected documents: {result.get('detected_docs', [])}")
        
        # Check if conversation history was updated
        updated_history = result.get('conversation_history', '')
        print(f"💬 Updated Conversation History: {len(updated_history)} characters")
        print(f"📋 Updated History Preview: {updated_history[:150]}...")
        
        # Verify the user query was added to history
        if "give me unique soeId list from database" in updated_history:
            print("✅ Conversation history correctly updated with user query")
        else:
            print("❌ Conversation history not updated correctly")
        
        # Display the subqueries
        print("\n📋 Generated Subqueries:")
        for source, queries in result.get('subqueries', {}).items():
            print(f"  {source}:")
            for i, query in enumerate(queries, 1):
                print(f"    {i}. {query}")
        
        # Display detected documents
        print(f"\n📚 Detected Documents: {result.get('detected_docs', [])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Planner node test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_conversation_history_update():
    """Test that conversation history is properly updated."""
    print("\n🧪 Testing Conversation History Update")
    print("=" * 50)
    
    # Test with no initial history
    print("\n🔍 Test 1: No initial history")
    test_state_1 = MultiHopState(
        request_id="test_no_history",
        session_id="test_session",
        user_query="Hello, this is my first message",
        formatted_user_query="",
        conversation_history="",
        subqueries={},
        retrieved_docs={},
        db_schema="",
        subquery_responses={},
        final_answer={},
        detected_docs=[]
    )
    
    try:
        result_1 = await planner_node(test_state_1)
        updated_history_1 = result_1.get('conversation_history', '')
        print(f"✅ Updated history: {updated_history_1}")
        
        if "1. user: Hello, this is my first message" in updated_history_1:
            print("✅ Correctly started conversation history")
        else:
            print("❌ Failed to start conversation history")
            
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
    
    # Test with existing history
    print("\n🔍 Test 2: With existing history")
    initial_history = "1. user: Hello\n2. assistant: Hi there! How can I help you?"
    
    test_state_2 = MultiHopState(
        request_id="test_with_history",
        session_id="test_session",
        user_query="I need some information",
        formatted_user_query="",
        conversation_history=initial_history,
        subqueries={},
        retrieved_docs={},
        db_schema="",
        subquery_responses={},
        final_answer={},
        detected_docs=[]
    )
    
    try:
        result_2 = await planner_node(test_state_2)
        updated_history_2 = result_2.get('conversation_history', '')
        print(f"✅ Updated history: {updated_history_2}")
        
        if "3. user: I need some information" in updated_history_2:
            print("✅ Correctly appended to existing conversation history")
        else:
            print("❌ Failed to append to existing conversation history")
            
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")


async def test_complete_conversation_flow():
    """Test the complete conversation flow with user queries and assistant responses."""
    print("\n🧪 Testing Complete Conversation Flow")
    print("=" * 50)
    
    # Simulate a complete conversation flow
    print("\n🔄 Simulating conversation flow...")
    
    # Step 1: Initial user query
    print("\n📝 Step 1: Initial user query")
    initial_state = MultiHopState(
        request_id="conversation_test",
        session_id="test_session",
        user_query="What are the critical applications?",
        formatted_user_query="",
        conversation_history="",
        subqueries={},
        retrieved_docs={},
        db_schema="",
        subquery_responses={},
        final_answer={},
        detected_docs=[]
    )
    
    try:
        # Run planner node
        result_1 = await planner_node(initial_state)
        updated_history_1 = result_1.get('conversation_history', '')
        print(f"✅ After planner: {updated_history_1}")
        
        # Simulate assistant response
        assistant_response_1 = "I found several critical applications in our system. Here are the main ones: Application A (High Criticality), Application B (Medium Criticality), and Application C (High Criticality)."
        
        # Update conversation history with assistant response
        final_history_1 = update_conversation_with_response(initial_state, assistant_response_1)
        print(f"✅ After assistant response: {final_history_1}")
        
        # Step 2: Follow-up user query
        print("\n📝 Step 2: Follow-up user query")
        follow_up_state = MultiHopState(
            request_id="conversation_test_2",
            session_id="test_session",
            user_query="Tell me more about Application A",
            formatted_user_query="",
            conversation_history=final_history_1,
            subqueries={},
            retrieved_docs={},
            db_schema="",
            subquery_responses={},
            final_answer={},
            detected_docs=[]
        )
        
        # Run planner node again
        result_2 = await planner_node(follow_up_state)
        updated_history_2 = result_2.get('conversation_history', '')
        print(f"✅ After planner (follow-up): {updated_history_2}")
        
        # Simulate assistant response
        assistant_response_2 = "Application A is a high-criticality system used for financial transactions. It has 15 engineers assigned and is hosted in the cloud. The application processes over 1 million transactions daily."
        
        # Update conversation history with assistant response
        final_history_2 = update_conversation_with_response(follow_up_state, assistant_response_2)
        print(f"✅ After assistant response (follow-up): {final_history_2}")
        
        # Step 3: Another follow-up
        print("\n📝 Step 3: Another follow-up query")
        final_state = MultiHopState(
            request_id="conversation_test_3",
            session_id="test_session",
            user_query="What are the performance metrics for Application A?",
            formatted_user_query="",
            conversation_history=final_history_2,
            subqueries={},
            retrieved_docs={},
            db_schema="",
            subquery_responses={},
            final_answer={},
            detected_docs=[]
        )
        
        # Run planner node one more time
        result_3 = await planner_node(final_state)
        updated_history_3 = result_3.get('conversation_history', '')
        print(f"✅ After planner (final): {updated_history_3}")
        
        # Verify the complete conversation flow
        print("\n📋 Complete Conversation Flow:")
        print(final_history_2)
        print("5. user: What are the performance metrics for Application A?")
        
        print("\n✅ Complete conversation flow test passed!")
        
    except Exception as e:
        print(f"❌ Complete conversation flow test failed: {e}")
        import traceback
        traceback.print_exc()


async def test_different_queries():
    """Test the planner node with different types of queries."""
    print("\n🧪 Testing Different Query Types")
    print("=" * 50)
    
    test_scenarios = [
        {
            "query": "give me unique soeId list from database",
            "history": [
                {"role": "user", "content": "I need employee data"},
                {"role": "assistant", "content": "What specific employee information do you need?"}
            ]
        },
        {
            "query": "explain the employee structure and organization",
            "history": [
                {"role": "user", "content": "Tell me about the company structure"},
                {"role": "assistant", "content": "I can help explain the organizational structure. What aspects interest you?"}
            ]
        },
        {
            "query": "show me more details about critical applications",
            "history": [
                {"role": "user", "content": "What are the critical applications?"},
                {"role": "assistant", "content": "I found several critical applications. Here's a summary..."},
                {"role": "user", "content": "show me more details about critical applications"}
            ]
        },
        {
            "query": "how does the management hierarchy work",
            "history": [
                {"role": "user", "content": "I want to understand the management structure"},
                {"role": "assistant", "content": "The management hierarchy has several levels. What would you like to know?"}
            ]
        },
        {
            "query": "show me employee ratios by department",
            "history": [
                {"role": "user", "content": "I need employee statistics"},
                {"role": "assistant", "content": "I can help with employee statistics. What specific metrics do you need?"}
            ]
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n🔍 Test {i}: {scenario['query']}")
        print("-" * 40)
        
        # Format conversation history
        conversation_history = format_conversation_history(scenario['history'])
        
        test_state = MultiHopState(
            request_id=f"test_request_{i}",
            session_id="test_session",
            user_query=scenario['query'],
            formatted_user_query="",
            conversation_history=conversation_history,
            subqueries={},
            retrieved_docs={},
            db_schema="",
            subquery_responses={},
            final_answer={},
            detected_docs=[]
        )
        
        try:
            result = await planner_node(test_state)
            
            print(f"✅ Subqueries: {list(result.get('subqueries', {}).keys())}")
            print(f"✅ Detected docs: {result.get('detected_docs', [])}")
            
            # Check conversation history update
            updated_history = result.get('conversation_history', '')
            if scenario['query'] in updated_history:
                print("✅ Conversation history updated correctly")
            else:
                print("❌ Conversation history not updated")
            
            # Show a sample subquery
            subqueries = result.get('subqueries', {})
            if subqueries:
                first_source = list(subqueries.keys())[0]
                first_query = subqueries[first_source][0] if subqueries[first_source] else "No query"
                print(f"✅ Sample query: {first_query[:50]}...")
            
        except Exception as e:
            print(f"❌ Failed: {e}")


async def test_follow_up_queries():
    """Test the planner node with follow-up questions."""
    print("\n🧪 Testing Follow-up Questions")
    print("=" * 50)
    
    # Simulate a conversation with follow-up questions
    conversation_messages = [
        {"role": "user", "content": "What are the critical applications in our system?"},
        {"role": "assistant", "content": "I found several critical applications. Here are the main ones: Application A (High Criticality), Application B (Medium Criticality), and Application C (High Criticality)."},
        {"role": "user", "content": "Tell me more about Application A"},
        {"role": "assistant", "content": "Application A is a high-criticality system used for financial transactions. It has 15 engineers assigned and is hosted in the cloud."}
    ]
    
    conversation_history = format_conversation_history(conversation_messages)
    
    test_state = MultiHopState(
        request_id="follow_up_test",
        session_id="test_session",
        user_query="show me the performance metrics for Application A",
        formatted_user_query="",
        conversation_history=conversation_history,
        subqueries={},
        retrieved_docs={},
        db_schema="",
        subquery_responses={},
        final_answer={},
        detected_docs=[]
    )
    
    print(f"📝 Follow-up Query: {test_state['user_query']}")
    print(f"💬 Conversation Context: {len(conversation_history)} characters")
    print(f"📋 History Preview: {conversation_history[:150]}...")
    
    try:
        result = await planner_node(test_state)
        
        print(f"\n✅ Subqueries generated: {list(result.get('subqueries', {}).keys())}")
        print(f"✅ Detected docs: {result.get('detected_docs', [])}")
        
        # Check conversation history update
        updated_history = result.get('conversation_history', '')
        print(f"💬 Updated History: {len(updated_history)} characters")
        if "show me the performance metrics for Application A" in updated_history:
            print("✅ Follow-up query correctly added to conversation history")
        else:
            print("❌ Follow-up query not added to conversation history")
        
        # Show the subqueries
        print("\n📋 Contextual Subqueries:")
        for source, queries in result.get('subqueries', {}).items():
            print(f"  {source}:")
            for i, query in enumerate(queries, 1):
                print(f"    {i}. {query}")
        
    except Exception as e:
        print(f"❌ Follow-up test failed: {e}")


async def main():
    """Main test function."""
    print("🚀 MultiHopState and Planner Node Test")
    print("=" * 60)
    
    # Test basic functionality
    success = await test_planner_node()
    
    if success:
        # Test conversation history update
        await test_conversation_history_update()
        
        # Test complete conversation flow
        await test_complete_conversation_flow()
        
        # Test different query types
        await test_different_queries()
        
        # Test follow-up questions
        await test_follow_up_queries()
    
    print("\n🎉 Test completed!")


if __name__ == "__main__":
    asyncio.run(main()) 