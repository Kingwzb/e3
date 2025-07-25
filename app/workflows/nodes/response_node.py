"""Response generation node for LangGraph workflow."""

import json
from typing import Dict, Any, List

from app.models.state import MultiHopState
from app.core.llm import llm_client
from app.utils.logging import logger


async def response_generation_node(state: MultiHopState) -> MultiHopState:
    """
    Node that generates the final response using LLM with all available context.
    
    This node:
    1. Combines conversation history, RAG context, and metrics data
    2. Constructs appropriate system and user messages for the LLM
    3. Generates a contextual response
    4. Updates the state with the final response
    """
    try:
        logger.info(f"Generating response for session: {state['session_id']}")
        
        user_query = state["user_query"]
        conversation_history = state.get("conversation_history", "")
        retrieved_docs = state.get("retrieved_docs", {})
        subquery_responses = state.get("subquery_responses", {})
        
        # Debug the data we're working with
        logger.info(f"DEBUG: Response generation - user_query: {user_query}")
        logger.info(f"DEBUG: Response generation - retrieved_docs type: {type(retrieved_docs)}, keys: {list(retrieved_docs.keys()) if isinstance(retrieved_docs, dict) else 'Not a dict'}")
        logger.info(f"DEBUG: Response generation - subquery_responses type: {type(subquery_responses)}")
        logger.info(f"DEBUG: Response generation - subquery_responses keys: {list(subquery_responses.keys()) if isinstance(subquery_responses, dict) else 'Not a dict'}")
        logger.info(f"DEBUG: Response generation - subquery_responses content: {subquery_responses}")
        
        # Build system message with available context
        messages = []
        
        # Add conversation history as context
        if conversation_history and conversation_history.strip():
            messages.append({
                "role": "system", 
                "content": f"Conversation History:\n{conversation_history}\n\nUse this context to provide more relevant and contextual responses."
            })
        
        # Add RAG context if available
        rag_context = retrieved_docs.get("rag_context", "")
        if rag_context:
            logger.info(f"DEBUG: Response generation - Processing RAG context")
            messages.append({
                "role": "system", 
                "content": f"Relevant Information from Knowledge Base:\n{rag_context}"
            })
        
        # Add database query results if available
        if subquery_responses:
            logger.info(f"DEBUG: Response generation - Processing subquery_responses")
            # Format database results for the LLM
            db_summary = "Database Query Results:\n"
            for query_type, query_result in subquery_responses.items():
                logger.info(f"DEBUG: Response generation - Processing query type: {query_type}")
                logger.info(f"DEBUG: Response generation - Query result type: {type(query_result)}")
                logger.info(f"DEBUG: Response generation - Query result keys: {list(query_result.keys()) if isinstance(query_result, dict) else 'Not a dict'}")
                
                if "result" in query_result:
                    # The result is a string from LangChain tools, not a dict
                    result_content = query_result['result']
                    logger.info(f"DEBUG: Response generation - Adding result content, length: {len(result_content) if result_content else 0}")
                    db_summary += f"\n{query_type} Results:\n{result_content}\n"
                elif "error" in query_result:
                    logger.info(f"DEBUG: Response generation - Adding error content")
                    db_summary += f"\n{query_type}: Error - {query_result['error']}\n"
                else:
                    # Fallback: show the whole query_result
                    logger.info(f"DEBUG: Response generation - Adding fallback content")
                    db_summary += f"\n{query_type}:\n{json.dumps(query_result, indent=2)}\n"
            
            logger.info(f"DEBUG: Response generation - Final db_summary length: {len(db_summary)}")
            messages.append({"role": "system", "content": db_summary})
        else:
            logger.info(f"DEBUG: Response generation - No subquery_responses available")
        
        # Add current user query
        messages.append({"role": "user", "content": user_query})
        
        # Generate response using LLM
        try:
            response = await llm_client.generate_response(
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            final_response = response.get("content", "I apologize, but I couldn't generate a response at this time.")
            
            # Update state with final response
            state["final_answer"] = {
                "response": final_response,
                "context_used": {
                    "conversation_history": bool(conversation_history),
                    "rag_context": bool(rag_context),
                    "database_results": bool(subquery_responses)
                }
            }
            
            logger.info(f"Response generation completed successfully")
            return state
            
        except Exception as llm_error:
            logger.error(f"Error in LLM response generation: {llm_error}")
            error_response = "I apologize, but I encountered an error while generating a response. Please try again."
            state["final_answer"] = {
                "response": error_response,
                "error": str(llm_error),
                "context_used": {
                    "conversation_history": bool(conversation_history),
                    "rag_context": bool(rag_context),
                    "database_results": bool(subquery_responses)
                }
            }
            return state
        
    except Exception as e:
        logger.error(f"Error in response generation node: {str(e)}")
        state["final_answer"] = {
            "response": "I apologize, but I encountered an error while processing your request.",
            "error": str(e)
        }
        return state 