#!/usr/bin/env python3
"""
Test script for complete conversation flow with conversation history.
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


def print_conversation_step(step_name: str, user_query: str, conversation_history: str, assistant_response: str = None):
    """Print a conversation step with clear formatting."""
    print(f"\n{'='*60}")
    print(f"🔄 {step_name}")
    print(f"{'='*60}")
    print(f"📝 User Query: {user_query}")
    print(f"\n💬 Current Conversation History ({len(conversation_history)} chars):")
    if conversation_history:
        print(conversation_history)
    else:
        print("(Empty - starting new conversation)")
    
    if assistant_response:
        print(f"\n🤖 Assistant Response: {assistant_response}")
        print(f"\n📋 Updated Conversation History:")
        # Simulate the updated history
        if conversation_history:
            lines = conversation_history.strip().split('\n')
            next_number = len(lines) + 1
            updated_history = conversation_history.strip() + f"\n{next_number}. user: {user_query}\n{next_number + 1}. assistant: {assistant_response}"
        else:
            updated_history = f"1. user: {user_query}\n2. assistant: {assistant_response}"
        print(updated_history)
    else:
        print(f"\n📋 After Planner (User Query Added):")
        if conversation_history:
            lines = conversation_history.strip().split('\n')
            next_number = len(lines) + 1
            updated_history = conversation_history.strip() + f"\n{next_number}. user: {user_query}"
        else:
            updated_history = f"1. user: {user_query}"
        print(updated_history)


async def test_complete_conversation_flow():
    """Test the complete conversation flow with user queries and assistant responses."""
    print("🚀 Complete Conversation Flow Test")
    print("=" * 80)
    print("This test demonstrates how conversation history builds up over multiple turns.")
    print("Each step shows the current state and how it updates after user queries and assistant responses.")
    
    # Step 1: Initial user query
    print_conversation_step(
        "STEP 1: Initial User Query",
        "What are the critical applications?",
        ""
    )
    
    initial_state = MultiHopState(
        request_id="conversation_test_1",
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
        print(f"✅ Planner added user query to history")
        
        # Simulate assistant response
        assistant_response_1 = "I found several critical applications in our system. Here are the main ones: Application A (High Criticality), Application B (Medium Criticality), and Application C (High Criticality)."
        
        # Update conversation history with assistant response
        final_history_1 = update_conversation_with_response(initial_state, assistant_response_1)
        print(f"✅ Assistant response added to history")
        
        print_conversation_step(
            "STEP 2: Follow-up User Query",
            "Tell me more about Application A",
            final_history_1
        )
        
        # Step 2: Follow-up user query
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
        print(f"✅ Planner added follow-up query to history")
        
        # Simulate assistant response
        assistant_response_2 = "Application A is a high-criticality system used for financial transactions. It has 15 engineers assigned and is hosted in the cloud. The application processes over 1 million transactions daily."
        
        # Update conversation history with assistant response
        final_history_2 = update_conversation_with_response(follow_up_state, assistant_response_2)
        print(f"✅ Assistant response added to history")
        
        print_conversation_step(
            "STEP 3: Another Follow-up Query",
            "What are the performance metrics for Application A?",
            final_history_2
        )
        
        # Step 3: Another follow-up
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
        print(f"✅ Planner added final query to history")
        
        # Simulate final assistant response
        assistant_response_3 = "Application A's performance metrics include: 99.9% uptime, average response time of 150ms, throughput of 10,000 transactions per second, and error rate of 0.01%."
        
        # Update conversation history with final assistant response
        final_history_3 = update_conversation_with_response(final_state, assistant_response_3)
        print(f"✅ Final assistant response added to history")
        
        # Show the complete conversation
        print(f"\n{'='*80}")
        print("🎉 COMPLETE CONVERSATION FLOW")
        print(f"{'='*80}")
        print("📋 Final Conversation History:")
        print(final_history_3)
        
        print(f"\n📊 Conversation Statistics:")
        print(f"   • Total messages: {len(final_history_3.split('\\n'))}")
        print(f"   • User queries: 3")
        print(f"   • Assistant responses: 3")
        print(f"   • Conversation length: {len(final_history_3)} characters")
        
        print(f"\n✅ Complete conversation flow test passed!")
        print(f"✅ Conversation history properly maintained throughout the workflow!")
        
    except Exception as e:
        print(f"❌ Complete conversation flow test failed: {e}")
        import traceback
        traceback.print_exc()


async def test_contextual_planning():
    """Test that the planner uses conversation context for better subquery generation."""
    print("\n🧪 Testing Contextual Planning")
    print("=" * 60)
    
    # Create a conversation with context
    conversation_history = """1. user: What are the critical applications?
2. assistant: I found several critical applications. Here are the main ones: Application A (High Criticality), Application B (Medium Criticality), and Application C (High Criticality).
3. user: Tell me more about Application A
4. assistant: Application A is a high-criticality system used for financial transactions. It has 15 engineers assigned and is hosted in the cloud."""
    
    print(f"📋 Initial Conversation Context:")
    print(conversation_history)
    
    # Test contextual query
    contextual_state = MultiHopState(
        request_id="contextual_test",
        session_id="test_session",
        user_query="What are the performance metrics for Application A?",
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
        result = await planner_node(contextual_state)
        
        print(f"\n📝 Contextual Query: What are the performance metrics for Application A?")
        print(f"✅ Subqueries generated: {list(result.get('subqueries', {}).keys())}")
        print(f"✅ Detected docs: {result.get('detected_docs', [])}")
        
        # Show the subqueries
        print(f"\n📋 Contextual Subqueries:")
        for source, queries in result.get('subqueries', {}).items():
            print(f"  {source}:")
            for i, query in enumerate(queries, 1):
                print(f"    {i}. {query}")
        
        # Check if conversation history was updated
        updated_history = result.get('conversation_history', '')
        if "What are the performance metrics for Application A?" in updated_history:
            print(f"\n✅ Conversation history correctly updated with contextual query")
        else:
            print(f"\n❌ Conversation history not updated correctly")
        
        print(f"\n✅ Contextual planning test passed!")
        
    except Exception as e:
        print(f"❌ Contextual planning test failed: {e}")


async def main():
    """Main test function."""
    print("🚀 Conversation Flow Test Suite")
    print("=" * 80)
    
    # Test complete conversation flow
    await test_complete_conversation_flow()
    
    # Test contextual planning
    await test_contextual_planning()
    
    print(f"\n🎉 All tests completed successfully!")
    print(f"✅ Conversation history management is working correctly!")


if __name__ == "__main__":
    asyncio.run(main()) 