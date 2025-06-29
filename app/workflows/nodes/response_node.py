"""Response generation node for LangGraph workflow."""

import json
from typing import Dict, Any, List

from app.models.state import WorkflowState
from app.core.llm import llm_client
from app.utils.logging import logger


async def response_generation_node(state: WorkflowState) -> WorkflowState:
    """
    Node that generates the final response using LLM with all available context.
    
    This node:
    1. Combines conversation history, RAG context, and metrics data
    2. Constructs appropriate system and user messages for the LLM
    3. Generates a contextual response
    4. Updates the state with the final response
    """
    try:
        logger.info(f"Generating response for conversation: {state['conversation_id']}")
        
        current_message = state["current_message"]
        conversation_history = state.get("messages", [])
        rag_context = state.get("rag_context", "")
        metrics_data = state.get("metrics_data", {})
        
        # Build the system message
        system_message = """You are an AI assistant that provides helpful responses based on conversation history, knowledge base context, and metrics data.

When responding:
1. Use the provided knowledge base context to give accurate information
2. Incorporate relevant metrics data when available
3. Maintain conversation continuity by referencing previous messages when relevant
4. Be concise but informative
5. If you don't have sufficient information, acknowledge the limitation

Your response should be natural and conversational while being informative and helpful."""
        
        # Prepare messages for LLM
        messages = [{"role": "system", "content": system_message}]
        
        # Add conversation history (limit to last 8 messages to avoid token limits)
        for msg in conversation_history[-8:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Add context and data as system messages if available
        if rag_context and rag_context.strip():
            context_message = f"Knowledge Base Context:\n{rag_context}"
            messages.append({"role": "system", "content": context_message})
        
        if metrics_data:
            # Format metrics data for the LLM
            metrics_summary = "Available Metrics Data:\n"
            for tool_name, tool_result in metrics_data.items():
                if "result" in tool_result:
                    # The result is a string from LangChain tools, not a dict
                    metrics_summary += f"\n{tool_name} Results:\n{tool_result['result']}\n"
                elif "error" in tool_result:
                    metrics_summary += f"\n{tool_name}: Error - {tool_result['error']}\n"
                else:
                    # Fallback: show the whole tool_result
                    metrics_summary += f"\n{tool_name}:\n{json.dumps(tool_result, indent=2)}\n"
            
            messages.append({"role": "system", "content": metrics_summary})
        
        # Add current user message
        messages.append({"role": "user", "content": current_message})
        
        # Generate response
        llm_response = await llm_client.generate_response(
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        final_response = llm_response.get("content", "I apologize, but I couldn't generate a response.")
        state["final_response"] = final_response
        
        logger.info("Response generation completed successfully")
        return state
        
    except Exception as e:
        logger.error(f"Error in response generation node: {str(e)}")
        state["error"] = f"Response generation failed: {str(e)}"
        state["final_response"] = "I apologize, but I encountered an error while processing your request."
        return state 