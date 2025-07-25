"""Metrics extraction node for LangGraph workflow."""

import json
from typing import Dict, Any, List

from app.models.state import MultiHopState
from app.core.llm import llm_client
from app.tools.dynamic_db_tool import create_dynamic_db_tool
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


def _should_extract_metrics(state: MultiHopState) -> bool:
    """
    Determine if metrics extraction is needed based on subqueries.
    
    This function checks if there are database subqueries that need to be executed.
    """
    subqueries = state.get("subqueries", {})
    
    # Check if there are database subqueries
    if "Database" in subqueries:
        logger.info("Database subqueries found, metrics extraction needed")
        return True
    
    # Check for any subquery keys that contain database-related terms
    db_related_keys = ["employee_ratio", "application_snapshot", "statistic", "enabler_csi_snapshots", "employee_tree_archived", "management_segment_tree"]
    for key in subqueries.keys():
        if any(db_term in key.lower() for db_term in db_related_keys):
            logger.info(f"Database-related subquery found: {key}, metrics extraction needed")
            return True
    
    # Fallback checks for backward compatibility
    planning_data = state.get("planning_data", {})
    if planning_data.get("needs_database_query", False):
        logger.info("Planning data indicates database query needed")
        return True
    
    # Check for database-related keywords in user query
    user_query = state.get("user_query", "").lower()
    db_keywords = ["database", "db", "soeid", "employee", "list", "get", "find", "show", "query"]
    if any(keyword in user_query for keyword in db_keywords):
        logger.info("Database keywords found in user query")
        return True
    
    logger.info("No metrics extraction needed")
    return False


async def metrics_extraction_node(state: MultiHopState) -> Dict[str, Any]:
    """
    LangGraph node that performs data extraction using dynamic database tool.
    
    This node:
    1. Determines if the user's query requires database querying
    2. If needed, uses the dynamic database tool to generate and execute queries
    3. Returns extracted data in a structured format
    
    Configuration:
    - Uses dynamic database tool for flexible query generation
    - Supports natural language queries across all collections
    - Handles complex queries with joins and aggregations
    """
    try:
        logger.info(f"Metrics node processing query for session: {state['session_id']}")
        
        user_query = state["user_query"]
        conversation_history = state.get("conversation_history", "")
        
        # Check if metrics extraction is needed based on subqueries
        if not _should_extract_metrics(state):
            logger.info("No metrics extraction required based on subqueries")
            return {"subquery_responses": {}}
        
        # Load unified schema
        unified_schema = _load_unified_schema()
        
        # Create dynamic database tool with LLM client
        logger.info(f"DEBUG: About to create dynamic database tool")
        logger.info(f"DEBUG: llm_client type: {type(llm_client)}")
        
        try:
            dynamic_tool = create_dynamic_db_tool(llm_client=llm_client)
            logger.info(f"DEBUG: Dynamic database tool created successfully")
            logger.info(f"DEBUG: dynamic_tool type: {type(dynamic_tool)}")
        except Exception as tool_creation_error:
            logger.error(f"DEBUG: Error creating dynamic database tool: {tool_creation_error}")
            logger.error(f"DEBUG: Tool creation error type: {type(tool_creation_error)}")
            import traceback
            logger.error(f"DEBUG: Tool creation traceback: {traceback.format_exc()}")
            raise
        
        logger.info(f"Using dynamic database tool for query: {user_query[:100]}...")
        
        # Execute the dynamic database query
        try:
            logger.info(f"DEBUG: About to prepare conversation context for better query generation")
            # Prepare conversation context for better query generation
            context_messages = []
            if conversation_history:
                # Use conversation history for context
                context_limit_raw = state.get("metrics_context_limit", 3)
                logger.info(f"DEBUG: context_limit_raw: {context_limit_raw}, type: {type(context_limit_raw)}")
                
                # Ensure context_limit is a valid integer
                if context_limit_raw is None:
                    context_limit = 3
                    logger.info(f"DEBUG: context_limit_raw is None, using default 3")
                elif not isinstance(context_limit_raw, int):
                    try:
                        context_limit = int(context_limit_raw)
                        logger.info(f"DEBUG: Converted context_limit_raw to int: {context_limit}")
                    except (ValueError, TypeError):
                        context_limit = 3
                        logger.info(f"DEBUG: Could not convert context_limit_raw to int, using default 3")
                else:
                    context_limit = context_limit_raw
                    logger.info(f"DEBUG: Using context_limit: {context_limit}")
                
                logger.info(f"DEBUG: Final context_limit: {context_limit}, type: {type(context_limit)}")
                
                # Parse conversation history to get recent messages
                lines = conversation_history.strip().split('\n')
                recent_lines = lines[-context_limit * 2:]  # Each message has 2 lines (role and content)
                for line in recent_lines:
                    if line.strip():
                        context_messages.append(line.strip())
            
            # Create enhanced prompt with context
            enhanced_prompt = user_query
            if context_messages:
                context_text = "\n".join(context_messages)
                enhanced_prompt = f"Context from previous conversation:\n{context_text}\n\nCurrent query: {user_query}"
            
            # Get limit parameter
            limit_param = state.get("metrics_limit", 100)
            logger.info(f"DEBUG: limit_param: {limit_param}, type: {type(limit_param)}")
            
            # Ensure limit_param is a valid integer
            if limit_param is None:
                limit_param = 100
                logger.info(f"DEBUG: limit_param is None, using default 100")
            elif not isinstance(limit_param, int):
                try:
                    limit_param = int(limit_param)
                    logger.info(f"DEBUG: Converted limit_param to int: {limit_param}")
                except (ValueError, TypeError):
                    limit_param = 100
                    logger.info(f"DEBUG: Could not convert limit_param to int, using default 100")
            
            logger.info(f"DEBUG: Final limit_param: {limit_param}, type: {type(limit_param)}")
            
            # Check other parameters
            try:
                logger.info(f"DEBUG: enhanced_prompt type: {type(enhanced_prompt)}")
                logger.info(f"DEBUG: enhanced_prompt is None: {enhanced_prompt is None}")
                logger.info(f"DEBUG: unified_schema type: {type(unified_schema)}")
                logger.info(f"DEBUG: unified_schema is None: {unified_schema is None}")
                
                # Ensure parameters are not None
                if enhanced_prompt is None:
                    logger.error(f"DEBUG: enhanced_prompt is None!")
                    enhanced_prompt = user_query
                
                if unified_schema is None:
                    logger.error(f"DEBUG: unified_schema is None!")
                    raise ValueError("unified_schema is None")
                
                logger.info(f"DEBUG: About to call _arun with validated parameters")
            except Exception as e:
                logger.error(f"DEBUG: Error validating parameters: {e}")
                logger.error(f"DEBUG: Error type: {type(e)}")
                import traceback
                logger.error(f"DEBUG: Parameter validation traceback: {traceback.format_exc()}")
                raise
            
            result = await dynamic_tool._arun(
                user_prompt=enhanced_prompt,
                unified_schema=unified_schema,
                limit=limit_param,
                include_aggregation=True,
                join_strategy="lookup"
            )
            
            logger.info(f"DEBUG: dynamic_tool._arun completed successfully")
            logger.info(f"DEBUG: result type: {type(result)}")
            logger.info(f"DEBUG: result length: {len(result) if isinstance(result, str) else 'Not a string'}")
            
        except Exception as arun_error:
            logger.error(f"DEBUG: Error in dynamic_tool._arun call: {arun_error}")
            logger.error(f"DEBUG: Error type: {type(arun_error)}")
            import traceback
            logger.error(f"DEBUG: _arun call traceback: {traceback.format_exc()}")
            raise
        
        # Parse the result
        if result.startswith("Error:"):
            logger.error(f"Dynamic database tool error: {result}")
            subquery_responses = {
                "Database": {
                    "error": result,
                    "user_prompt": user_query,
                    "tool_type": "dynamic_db"
                }
            }
        else:
            # Parse the JSON result
            try:
                parsed_result = json.loads(result)
                subquery_responses = {
                    "Database": {
                        "result": parsed_result,
                        "user_prompt": user_query,
                        "tool_type": "dynamic_db",
                        "config": {
                            "database": "ee-productivities",
                            "tool_name": "dynamic_db_query",
                            "schema_used": "unified_schema.txt"
                        }
                    }
                }
                logger.info(f"Successfully executed dynamic database query")
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse dynamic database result: {e}")
                subquery_responses = {
                    "Database": {
                        "error": f"Failed to parse result: {str(e)}",
                        "raw_result": result,
                        "user_prompt": user_query,
                        "tool_type": "dynamic_db"
                    }
                }
        
        return {"subquery_responses": subquery_responses}
        
    except Exception as e:
        logger.error(f"Error in metrics extraction node: {str(e)}")
        return {
            "error": f"Metrics extraction failed: {str(e)}",
            "subquery_responses": {}
        }


def create_metrics_node_tools() -> Dict[str, Any]:
    """Create tools and utilities for the metrics node."""
    return {
        "supported_databases": ["ee-productivities"],
        "available_tools": [
            "dynamic_db_query"
        ],
        "default_config": {
            "database": "ee-productivities",
            "tool_type": "dynamic_db",
            "schema_file": "schemas/unified_schema.txt"
        }
    } 