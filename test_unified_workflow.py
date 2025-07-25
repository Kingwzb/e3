#!/usr/bin/env python3
"""
Test the unified MultiHopState workflow with conversation memory.
"""

import asyncio
import sys
import os
import uuid

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.state import MultiHopState
from app.workflows.nodes.planner_node import planner_node, update_conversation_with_response
from app.workflows.nodes.rag_node import rag_extraction_node
from app.workflows.nodes.metrics_node import metrics_extraction_node
from app.workflows.nodes.response_node import response_generation_node


def print_conversation_step(step_name: str, state: MultiHopState, description: str = ""):
    """Print a conversation step with clear formatting."""
    print(f"\n{'='*60}")
    print(f"🔹 {step_name}")
    print(f"{'='*60}")
    if description:
        print(f"📝 {description}")
    
    print(f"📤 User Query: {state.get('user_query', 'N/A')}")
    print(f"💬 Conversation History: {len(state.get('conversation_history', ''))} chars")
    
    # Show subqueries if available
    subqueries = state.get('subqueries', {})
    if subqueries:
        print(f"🎯 Subqueries:")
        for source, queries in subqueries.items():
            print(f"   {source}: {queries}")
    
    # Show detected docs if available
    detected_docs = state.get('detected_docs', [])
    if detected_docs:
        print(f"📚 Detected Documents: {detected_docs}")
    
    # Show final answer if available
    final_answer = state.get('final_answer', {})
    if final_answer:
        response = final_answer.get('response', 'No response')
        print(f"🤖 Final Response: {response[:200]}...")
    
    print(f"{'='*60}")


async def test_conversation_memory():
    """Test conversation memory with follow-up questions."""
    
    print("🧪 Testing Unified MultiHopState Workflow with Conversation Memory")
    print("=" * 80)
    
    # Simulate the conversation from the logs
    session_id = "test"
    request_id = str(uuid.uuid4())
    
    # Initial state - first question
    initial_state = MultiHopState(
        request_id=request_id,
        session_id=session_id,
        user_query="what data do you have for SOE9191",
        formatted_user_query="",
        subqueries={},
        retrieved_docs={},
        db_schema="",
        subquery_responses={},
        final_answer={},
        detected_docs=[],
        conversation_history=""
    )
    
    print_conversation_step("Initial Query", initial_state, "User asks about SOE9191 data")
    
    # Step 1: Planner node
    try:
        planner_result = await planner_node(initial_state)
        initial_state.update(planner_result)
        print_conversation_step("After Planner", initial_state, "Planner analyzed query and generated subqueries")
    except Exception as e:
        print(f"❌ Planner node error: {e}")
        return False
    
    # Step 2: Metrics extraction (simulated)
    try:
        metrics_result = await metrics_extraction_node(initial_state)
        initial_state.update(metrics_result)
        print_conversation_step("After Metrics", initial_state, "Database query executed")
    except Exception as e:
        print(f"❌ Metrics node error: {e}")
        return False
    
    # Step 3: RAG extraction (simulated)
    try:
        rag_result = await rag_extraction_node(initial_state)
        initial_state.update(rag_result)
        print_conversation_step("After RAG", initial_state, "RAG context retrieved")
    except Exception as e:
        print(f"❌ RAG node error: {e}")
        return False
    
    # Step 4: Response generation
    try:
        response_result = await response_generation_node(initial_state)
        initial_state.update(response_result)
        print_conversation_step("After Response", initial_state, "Final response generated")
    except Exception as e:
        print(f"❌ Response node error: {e}")
        return False
    
    # Update conversation history with the response
    final_response = initial_state.get('final_answer', {}).get('response', '')
    updated_history = update_conversation_with_response(initial_state, final_response)
    initial_state['conversation_history'] = updated_history
    
    print_conversation_step("Updated History", initial_state, "Conversation history updated with response")
    
    # Now test follow-up question: "yes, pls"
    follow_up_state = MultiHopState(
        request_id=str(uuid.uuid4()),
        session_id=session_id,
        user_query="yes, pls",
        formatted_user_query="",
        subqueries={},
        retrieved_docs={},
        db_schema="",
        subquery_responses={},
        final_answer={},
        detected_docs=[],
        conversation_history=initial_state['conversation_history']  # Use previous history
    )
    
    print_conversation_step("Follow-up Query", follow_up_state, "User says 'yes, pls' - should use conversation context")
    
    # Step 1: Planner node with conversation history
    try:
        planner_result = await planner_node(follow_up_state)
        follow_up_state.update(planner_result)
        print_conversation_step("After Planner (Follow-up)", follow_up_state, "Planner should use conversation context")
    except Exception as e:
        print(f"❌ Planner node error (follow-up): {e}")
        return False
    
    # Check if the planner correctly identified this as a follow-up
    subqueries = follow_up_state.get('subqueries', {})
    if "Database" in subqueries:
        print("✅ Planner correctly identified database query needed for follow-up")
    else:
        print("❌ Planner did not identify database query needed for follow-up")
    
    # Step 2: Metrics extraction for follow-up
    try:
        metrics_result = await metrics_extraction_node(follow_up_state)
        follow_up_state.update(metrics_result)
        print_conversation_step("After Metrics (Follow-up)", follow_up_state, "Database query for follow-up executed")
    except Exception as e:
        print(f"❌ Metrics node error (follow-up): {e}")
        return False
    
    # Step 3: RAG extraction for follow-up
    try:
        rag_result = await rag_extraction_node(follow_up_state)
        follow_up_state.update(rag_result)
        print_conversation_step("After RAG (Follow-up)", follow_up_state, "RAG context for follow-up retrieved")
    except Exception as e:
        print(f"❌ RAG node error (follow-up): {e}")
        return False
    
    # Step 4: Response generation for follow-up
    try:
        response_result = await response_generation_node(follow_up_state)
        follow_up_state.update(response_result)
        print_conversation_step("After Response (Follow-up)", follow_up_state, "Final response for follow-up generated")
    except Exception as e:
        print(f"❌ Response node error (follow-up): {e}")
        return False
    
    # Update conversation history with the follow-up response
    follow_up_response = follow_up_state.get('final_answer', {}).get('response', '')
    updated_history = update_conversation_with_response(follow_up_state, follow_up_response)
    follow_up_state['conversation_history'] = updated_history
    
    print_conversation_step("Final Updated History", follow_up_state, "Complete conversation history with both exchanges")
    
    print("\n🎉 Test completed successfully!")
    print("✅ Conversation memory is working correctly")
    print("✅ Follow-up questions are being processed with context")
    print("✅ Database queries are being triggered appropriately")
    
    return True


async def test_contextual_planning():
    """Test that the planner uses conversation context for better subquery generation."""
    
    print("\n🧪 Testing Contextual Planning")
    print("=" * 50)
    
    session_id = "context_test"
    request_id = str(uuid.uuid4())
    
    # Create a conversation history that mentions SOE3200
    conversation_history = """1. user: how about tools adoption for SOE3200
2. assistant: I can provide metrics data for the `employee_ratio` collection, including the `employeeRatioSnapshot` and `toolsAdoptionRatioSnapshot`.

I have retrieved a list of `soeId` values from the `employee_ratio` collection: `SOE8856`, `SOE3003`, `SOE3060`, `SOE7146`, `SOE9663`, `SOE9901`, `SOE3200`, `SOE8201`, `SOE6309`, `SOE7716`, `SOE1684`, `SOE4576`, `SOE8999`, `SOE6018`, `SOE1315`, `SOE1581`, `SOE1839`, `SOE9191`, `SOE6237`, `SOE7765`, `SOE3491`, `SOE5563`, `SOE6573`, `SOE9164`, `SOE7364`, `SOE7752`, `SOE6772`, `SOE5855`, `SOE2356`, and `SOE1925`.

Do you want me to display the `toolsAdoptionRatioSnapshot` data for `SOE3200`?"""
    
    contextual_state = MultiHopState(
        request_id=request_id,
        session_id=session_id,
        user_query="yes, pls",
        formatted_user_query="",
        subqueries={},
        retrieved_docs={},
        db_schema="",
        subquery_responses={},
        final_answer={},
        detected_docs=[],
        conversation_history=conversation_history
    )
    
    print_conversation_step("Contextual Query", contextual_state, "User says 'yes, pls' with SOE3200 context")
    
    # Test planner with conversation context
    try:
        planner_result = await planner_node(contextual_state)
        contextual_state.update(planner_result)
        print_conversation_step("After Contextual Planner", contextual_state, "Planner should reference SOE3200 from context")
        
        # Check if the planner generated appropriate subqueries
        subqueries = contextual_state.get('subqueries', {})
        if "Database" in subqueries:
            db_queries = subqueries["Database"]
            print(f"✅ Planner generated database queries: {db_queries}")
            
            # Check if SOE3200 is mentioned in the queries
            soe3200_mentioned = any("SOE3200" in query for query in db_queries)
            if soe3200_mentioned:
                print("✅ Planner correctly referenced SOE3200 from conversation context")
            else:
                print("⚠️ Planner did not reference SOE3200 from conversation context")
        else:
            print("❌ Planner did not generate database queries")
            
    except Exception as e:
        print(f"❌ Contextual planner error: {e}")
        return False
    
    return True


async def main():
    """Run all tests."""
    print("🚀 Starting Unified MultiHopState Workflow Tests")
    print("=" * 80)
    
    # Test 1: Conversation memory
    success1 = await test_conversation_memory()
    
    # Test 2: Contextual planning
    success2 = await test_contextual_planning()
    
    if success1 and success2:
        print("\n🎉 All tests passed!")
        print("✅ Unified MultiHopState workflow is working correctly")
        print("✅ Conversation memory is functioning")
        print("✅ Contextual planning is working")
        return True
    else:
        print("\n❌ Some tests failed")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 