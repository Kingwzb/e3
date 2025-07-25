"""Planner node for LangGraph workflow that determines intent and routes to appropriate nodes."""

import json
import re
from typing import Dict, Any, List

from app.models.state import MultiHopState
from app.core.llm import llm_client
from app.utils.logging import logger


def _load_unified_schema() -> str:
    """Load the unified schema document."""
    try:
        schema_path = "schemas/unified_schema.txt"
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_content = f.read()
        logger.info(f"Loaded unified schema from {schema_path}")
        return schema_content
    except Exception as e:
        logger.error(f"Failed to load unified schema: {e}")
        raise


def _create_planning_prompt(user_query: str, conversation_history: str, unified_schema: str) -> str:
    """Create a prompt for the LLM to analyze the user query and determine subqueries."""
    
    # Format conversation history for context
    history_context = ""
    if conversation_history and conversation_history.strip():
        history_context = f"\nCONVERSATION HISTORY:\n{conversation_history}\n"
    
    prompt = f"""
You are an intelligent query planner that analyzes user queries and breaks them down into subqueries for different data sources.

CURRENT USER QUERY: {user_query}
{history_context}
UNIFIED SCHEMA:
{unified_schema}

Your task is to:
1. Analyze the user query and conversation history to understand what information is needed
2. Consider the context from previous messages to provide more relevant subqueries
3. Identify which documents/databases are relevant based on the full conversation context
4. Generate specific subqueries for each relevant source
5. Detect relevant RAG documents that should be searched

IMPORTANT: Consider the conversation history when planning:
- If the user is asking follow-up questions, reference previous context
- If they're refining their request, build upon earlier queries
- If they're asking for clarification, consider what was discussed before
- Use the conversation context to make subqueries more specific and relevant

Return your analysis as a JSON object with the following structure:
{{
    "subqueries": {{
        "Database": [
            "specific question about database data",
            "another database question if needed"
        ],
        "Document1": [
            "specific question about this document",
            "another question about this document"
        ],
        "Document2": [
            "specific question about this document"
        ]
    }},
    "detected_docs": [
        "document1_name",
        "document2_name"
    ],
    "reasoning": "explanation of why these subqueries were chosen, considering conversation history",
    "confidence": 0.9
}}

IMPORTANT RULES:
- Only include sources that are actually relevant to the user query and conversation context
- Generate specific, focused subqueries that can be answered by each source
- For database queries, be specific about what data to retrieve
- For document queries, ask specific questions about the document content
- If no database query is needed, omit the "Database" key
- If no document queries are needed, omit document keys
- detected_docs should list the names of RAG documents that should be searched
- Consider conversation history to make queries more contextual and relevant

Examples:
- For "give me unique soeId list from database": Include Database subquery
- For "explain the employee structure": Include relevant document subqueries
- For "what are the critical applications": Include both Database and document subqueries
- For follow-up questions like "show me more details": Reference previous context

Return only the JSON object, no additional text.
"""
    return prompt


def _update_conversation_history(current_history: str, user_query: str, assistant_response: str = None) -> str:
    """Update conversation history by appending the current user query and optionally the assistant response."""
    if not current_history or not current_history.strip():
        # If no history exists, start with the current query
        if assistant_response:
            return f"1. user: {user_query}\n2. assistant: {assistant_response}"
        else:
            return f"1. user: {user_query}"
    
    # Count existing messages to get the next number
    lines = current_history.strip().split('\n')
    next_number = len(lines) + 1
    
    # Append the new user query
    updated_history = current_history.strip() + f"\n{next_number}. user: {user_query}"
    
    # If assistant response is provided, append it too
    if assistant_response:
        updated_history += f"\n{next_number + 1}. assistant: {assistant_response}"
    
    return updated_history


async def planner_node(state: MultiHopState) -> Dict[str, Any]:
    """
    LangGraph node that analyzes user queries and determines subqueries for multi-hop reasoning.
    
    This node:
    1. Analyzes the user query and conversation history to understand intent
    2. Identifies relevant data sources (documents and databases)
    3. Generates specific subqueries for each source
    4. Detects relevant RAG documents to search
    5. Updates conversation history with the current user query
    6. Returns structured subqueries and detected documents
    """
    try:
        user_query = state["user_query"]
        conversation_history = state.get("conversation_history", "")
        
        logger.info(f"Planner node processing query: {user_query}")
        logger.info(f"Planner node using conversation history: {len(conversation_history)} characters")
        
        # Load unified schema for database understanding
        unified_schema = _load_unified_schema()
        
        # Create planning prompt with conversation history
        planning_prompt = _create_planning_prompt(user_query, conversation_history, unified_schema)
        
        # Get LLM response for planning
        try:
            response = await llm_client.generate_response(
                messages=[{"role": "user", "content": planning_prompt}],
                temperature=0.1,
                max_tokens=1000
            )
            
            # Parse the planning response - handle markdown code blocks
            try:
                response_content = response.get("content", "")
                
                # First try to parse the entire response as JSON
                try:
                    planning_result = json.loads(response_content)
                except json.JSONDecodeError:
                    # If that fails, try to extract JSON from markdown code blocks
                    import re
                    
                    # Look for JSON code blocks (```json ... ```)
                    json_block_match = re.search(r'```json\s*\n(.*?)\n```', response_content, re.DOTALL)
                    if json_block_match:
                        json_content = json_block_match.group(1).strip()
                        try:
                            planning_result = json.loads(json_content)
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse JSON from code block: {e}")
                            logger.error(f"JSON content: {json_content[:200]}...")
                            raise
                    else:
                        # Look for any JSON object in the response
                        json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
                        if json_match:
                            json_content = json_match.group(0)
                            try:
                                planning_result = json.loads(json_content)
                            except json.JSONDecodeError as e:
                                logger.error(f"Failed to parse extracted JSON: {e}")
                                logger.error(f"Extracted content: {json_content[:200]}...")
                                raise
                        else:
                            logger.error(f"No JSON found in response: {response_content[:200]}...")
                            raise ValueError("No valid JSON found in LLM response")
                
                # Extract planning information
                subqueries = planning_result.get("subqueries", {})
                detected_docs = planning_result.get("detected_docs", [])
                reasoning = planning_result.get("reasoning", "No reasoning provided")
                confidence = planning_result.get("confidence", 0.0)
                
                logger.info(f"Planning analysis completed: subqueries={len(subqueries)}, detected_docs={len(detected_docs)}")
                logger.info(f"Planning determined: subqueries={list(subqueries.keys())}, detected_docs={detected_docs} (confidence: {confidence})")
                logger.info(f"Planning reasoning: {reasoning[:100]}...")
                
                # Update conversation history with the current user query only
                # (Assistant response will be added by the final response node)
                updated_conversation_history = _update_conversation_history(conversation_history, user_query)
                logger.info(f"Updated conversation history: {len(updated_conversation_history)} characters")
                
                result = {
                    "subqueries": subqueries,
                    "detected_docs": detected_docs,
                    "formatted_user_query": user_query,
                    "db_schema": unified_schema,
                    "subquery_responses": {},
                    "retrieved_docs": {},
                    "final_answer": {},
                    "conversation_history": updated_conversation_history
                }
                
                logger.info(f"Planner node returning: {result}")
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse planning response: {e}")
                logger.error(f"Raw response: {response.get('content', '')}")
                
                # Fallback to keyword-based detection
                fallback_subqueries = _fallback_subquery_generation(user_query, conversation_history)
                
                # Update conversation history
                updated_conversation_history = _update_conversation_history(conversation_history, user_query)
                
                result = {
                    "subqueries": fallback_subqueries,
                    "detected_docs": ["general_documentation"],
                    "formatted_user_query": user_query,
                    "db_schema": unified_schema,
                    "subquery_responses": {},
                    "retrieved_docs": {},
                    "final_answer": {},
                    "conversation_history": updated_conversation_history
                }
                
                logger.info(f"Planner node fallback returning: {result}")
                return result
                
        except Exception as llm_error:
            logger.error(f"Error in LLM planning: {llm_error}")
            
            # Fallback to keyword-based detection
            fallback_subqueries = _fallback_subquery_generation(user_query, conversation_history)
            
            # Update conversation history
            updated_conversation_history = _update_conversation_history(conversation_history, user_query)
            
            result = {
                "subqueries": fallback_subqueries,
                "detected_docs": ["general_documentation"],
                "formatted_user_query": user_query,
                "db_schema": unified_schema,
                "subquery_responses": {},
                "retrieved_docs": {},
                "final_answer": {},
                "conversation_history": updated_conversation_history
            }
            
            logger.info(f"Planner node LLM error fallback returning: {result}")
            return result
        
    except Exception as e:
        logger.error(f"Error in planner node: {str(e)}")
        
        # Update conversation history even in error case
        conversation_history = state.get("conversation_history", "")
        updated_conversation_history = _update_conversation_history(conversation_history, state.get("user_query", ""))
        
        result = {
            "subqueries": {"Database": ["general database query"]},
            "detected_docs": ["general_documentation"],
            "formatted_user_query": state.get("user_query", ""),
            "db_schema": _load_unified_schema(),
            "subquery_responses": {},
            "retrieved_docs": {},
            "final_answer": {},
            "conversation_history": updated_conversation_history
        }
        return result


def _fallback_subquery_generation(user_query: str, conversation_history: str) -> Dict[str, List[str]]:
    """Fallback method to generate subqueries based on keywords when LLM fails."""
    query_lower = user_query.lower()
    subqueries = {}
    
    # Check for database-related keywords
    db_keywords = ["database", "db", "soeid", "employee", "list", "get", "find", "show", "query"]
    if any(keyword in query_lower for keyword in db_keywords):
        subqueries["Database"] = [f"Retrieve data for: {user_query}"]
    
    # Check for document-related keywords
    doc_keywords = ["explain", "what", "how", "documentation", "guide", "help"]
    if any(keyword in query_lower for keyword in doc_keywords):
        subqueries["General_Documentation"] = [f"Find information about: {user_query}"]
    
    # Check conversation history for context
    if conversation_history and conversation_history.strip():
        history_lower = conversation_history.lower()
        # Look for follow-up indicators in conversation history
        if any(word in history_lower for word in ['more', 'details', 'specific', 'show', 'tell']):
            # This might be a follow-up question
            subqueries["General_Documentation"] = [f"Find additional details about: {user_query}"]
    
    # If no specific keywords found, default to both
    if not subqueries:
        subqueries = {
            "Database": [f"Retrieve data for: {user_query}"],
            "General_Documentation": [f"Find information about: {user_query}"]
        }
    
    return subqueries


def update_conversation_with_response(state: MultiHopState, final_response: str) -> str:
    """
    Update conversation history with the final assistant response.
    
    This function should be called by the final response node to add the assistant's response
    to the conversation history.
    
    Args:
        state: The current MultiHopState
        final_response: The final response from the assistant
        
    Returns:
        Updated conversation history string
    """
    current_history = state.get("conversation_history", "")
    user_query = state.get("user_query", "")
    
    # Update history with both user query and assistant response
    updated_history = _update_conversation_history(current_history, user_query, final_response)
    
    logger.info(f"Updated conversation history with final response: {len(updated_history)} characters")
    return updated_history


def create_planner_node_tools() -> Dict[str, Any]:
    """Create tools for the planner node."""
    return {
        "planner_node": planner_node
    } 