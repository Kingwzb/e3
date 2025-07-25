"""Planner node for LangGraph workflow that determines if database queries are needed."""

import json
import os
from typing import Dict, Any, List, Optional
from app.models.state import WorkflowState
from app.core.llm import llm_client
from app.utils.logging import logger


def _load_unified_schema() -> str:
    """Load the unified schema from file."""
    try:
        schema_path = "schemas/unified_schema.txt"
        with open(schema_path, "r") as f:
            schema = f.read()
        logger.info(f"Loaded unified schema from {schema_path}")
        return schema
    except FileNotFoundError:
        logger.error(f"Unified schema file not found: {schema_path}")
        raise FileNotFoundError(f"Unified schema file not found: {schema_path}")
    except Exception as e:
        logger.error(f"Failed to load unified schema: {e}")
        raise


def _create_planning_prompt(user_message: str, unified_schema: str) -> str:
    """Create a prompt for the LLM to determine if a database query is needed."""
    return f"""You are a database query planner. Your task is to analyze a user's message and determine if they need to query a MongoDB database.

DATABASE SCHEMA:
{unified_schema}

USER MESSAGE:
{user_message}

ANALYSIS TASK:
1. Read the user's message carefully
2. Review the available database collections and their fields
3. Determine if the user is asking for:
   - Data retrieval from the database
   - Information about applications, employees, ratios, etc.
   - Statistics, counts, or metrics
   - Any information that would require querying the database

AVAILABLE COLLECTIONS:
- application_snapshot: Contains application data with criticality, CSI IDs, etc.
- employee_ratio: Contains employee data with ratios and headcount information
- soe_achievement: Contains achievement data

RESPONSE FORMAT:
Return a JSON object with the following structure:
{{
    "needs_database_query": true/false,
    "reasoning": "Explanation of why a database query is or is not needed",
    "relevant_collections": ["list", "of", "relevant", "collections"],
    "query_type": "find|aggregate|count|analysis",
    "confidence": 0.0-1.0
}}

EXAMPLES:
- "Show me applications with high criticality" → needs_database_query: true
- "What's the weather like?" → needs_database_query: false
- "How many employees are there?" → needs_database_query: true
- "Tell me a joke" → needs_database_query: false
- "Find applications in the finance sector" → needs_database_query: true

Respond with only the JSON object, no additional text."""


async def planner_node(state: WorkflowState) -> Dict[str, Any]:
    """
    LangGraph node that plans whether database queries are needed.
    
    This node:
    1. Analyzes the user's message using LLM
    2. Reviews the database schema
    3. Determines if a database query is needed
    4. Provides reasoning and planning information
    
    Returns:
        Dict with planning information including whether to trigger metrics node
    """
    try:
        logger.info(f"Planner node processing message for conversation: {state['conversation_id']}")
        
        current_message = state["current_message"]
        conversation_history = state.get("messages", [])
        
        # Load unified schema
        unified_schema = _load_unified_schema()
        
        # Create planning prompt
        planning_prompt = _create_planning_prompt(current_message, unified_schema)
        
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
                
                logger.info(f"Planning analysis completed: {planning_result.get('needs_database_query', False)}")
                
                # Extract planning information
                needs_query = planning_result.get("needs_database_query", False)
                reasoning = planning_result.get("reasoning", "No reasoning provided")
                relevant_collections = planning_result.get("relevant_collections", [])
                query_type = planning_result.get("query_type", "unknown")
                confidence = planning_result.get("confidence", 0.0)
                
                planning_data = {
                    "needs_database_query": needs_query,
                    "reasoning": reasoning,
                    "relevant_collections": relevant_collections,
                    "query_type": query_type,
                    "confidence": confidence,
                    "user_message": current_message,
                    "schema_used": "unified_schema.txt"
                }
                
                # Determine next steps - can route to both metrics and RAG
                trigger_metrics = needs_query and confidence > 0.5
                trigger_rag = True  # Always trigger RAG for general context
                
                logger.info(f"Planning determined: metrics={trigger_metrics}, rag={trigger_rag} (confidence: {confidence})")
                
                result = {
                    "planning_data": planning_data,
                    "trigger_metrics": trigger_metrics,
                    "trigger_rag": trigger_rag,
                    "needs_metrics": trigger_metrics,
                    "needs_rag": trigger_rag,
                    # Also set the key values directly in the state for easier access
                    "needs_database_query": needs_query,
                    "confidence": confidence
                }
                
                logger.info(f"Planner node returning: {result}")
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse planning response: {e}")
                logger.error(f"Raw response: {response.get('content', '')}")
                
                # Fallback to keyword-based detection
                fallback_needs_query = _fallback_intent_detection(current_message)
                
                result = {
                    "planning_data": {
                        "needs_database_query": fallback_needs_query,
                        "reasoning": "Fallback to keyword detection due to parsing error",
                        "relevant_collections": [],
                        "query_type": "fallback",
                        "confidence": 0.3,
                        "user_message": current_message,
                        "schema_used": "unified_schema.txt"
                    },
                    "trigger_metrics": fallback_needs_query,
                    "trigger_rag": True,
                    "needs_metrics": fallback_needs_query,
                    "needs_rag": True,
                    # Also set the key values directly in the state for easier access
                    "needs_database_query": fallback_needs_query,
                    "confidence": 0.3
                }
                
                logger.info(f"Planner node fallback returning: {result}")
                return result
                
        except Exception as llm_error:
            logger.error(f"Error in LLM planning: {llm_error}")
            
            # Fallback to keyword-based detection
            fallback_needs_query = _fallback_intent_detection(current_message)
            
            result = {
                "planning_data": {
                    "needs_database_query": fallback_needs_query,
                    "reasoning": "Fallback to keyword detection due to LLM error",
                    "relevant_collections": [],
                    "query_type": "fallback",
                    "confidence": 0.2,
                    "user_message": current_message,
                    "schema_used": "unified_schema.txt"
                },
                "trigger_metrics": fallback_needs_query,
                "trigger_rag": True,
                "needs_metrics": fallback_needs_query,
                "needs_rag": True,
                # Also set the key values directly in the state for easier access
                "needs_database_query": fallback_needs_query,
                "confidence": 0.2
            }
            
            logger.info(f"Planner node LLM error fallback returning: {result}")
            return result
        
    except Exception as e:
        logger.error(f"Error in planner node: {str(e)}")
        result = {
            "planning_data": {
                "needs_database_query": False,
                "reasoning": f"Planner node error: {str(e)}",
                "relevant_collections": [],
                "query_type": "error",
                "confidence": 0.0,
                "user_message": state.get("current_message", ""),
                "schema_used": "unified_schema.txt"
            },
            "trigger_metrics": False,
            "trigger_rag": True,
            "needs_metrics": False,
            "needs_rag": True,
            # Also set the key values directly in the state for easier access
            "needs_database_query": False,
            "confidence": 0.0
        }
        
        logger.info(f"Planner node exception fallback returning: {result}")
        return result


def _fallback_intent_detection(message: str) -> bool:
    """
    Fallback intent detection using keywords when LLM planning fails.
    
    Args:
        message: User's message
        
    Returns:
        True if database query is likely needed, False otherwise
    """
    message_lower = message.lower()
    
    # Keywords that indicate database query needs
    database_keywords = [
        "application", "applications", "app", "apps", "snapshot", "snapshots",
        "employee", "employees", "ratio", "ratios", "engineer", "engineers",
        "enabler", "enablers", "csi", "se", "achievement", "metrics",
        "management", "segment", "segments", "statistic", "statistics",
        "performance", "metric", "data", "numbers", "figures",
        "schema", "database", "collection", "collections", "structure",
        "table", "tables", "field", "fields", "query", "queries",
        "find", "search", "get", "show", "list", "count", "how many",
        "what", "which", "where", "when", "who", "status", "criticality",
        "sector", "development", "hosting", "model", "organization",
        "hierarchy", "hierarchical", "reporting", "level", "levels",
        "tree", "trees", "parent", "child", "tools", "adoption",
        "headcount", "structure", "organizational"
    ]
    
    # Check if any database keywords are present
    return any(keyword in message_lower for keyword in database_keywords)


def create_planner_node_tools() -> Dict[str, Any]:
    """Create tools and utilities for the planner node."""
    return {
        "supported_analysis": ["intent_detection", "query_planning", "schema_analysis"],
        "available_planning": [
            "llm_based_planning",
            "fallback_keyword_detection"
        ],
        "default_config": {
            "confidence_threshold": 0.5,
            "schema_file": "schemas/unified_schema.txt",
            "planning_method": "llm_analysis"
        }
    } 