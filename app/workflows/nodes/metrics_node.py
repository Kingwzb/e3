"""Metrics extraction node for LangGraph workflow using dynamic database tool."""

import json
import os
from typing import Dict, Any, List, Optional
from app.models.state import WorkflowState
from app.tools.dynamic_db_tool import create_dynamic_db_tool
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


def _should_extract_metrics(state: WorkflowState) -> bool:
    """
    Determine if metrics extraction is needed based on planner node decision.
    
    Args:
        state: Workflow state containing planning data
        
    Returns:
        True if metrics extraction is needed, False otherwise
    """
    # Check for trigger_metrics at top level (from planner node)
    if state.get("trigger_metrics", False):
        logger.info("Metrics extraction triggered by trigger_metrics=True")
        return True
    
    # Check for needs_metrics at top level (alternative field)
    if state.get("needs_metrics", False):
        logger.info("Metrics extraction triggered by needs_metrics=True")
        return True
    
    # Fallback to planning_data.trigger_metrics if not at top level
    planning_data = state.get("planning_data", {})
    if planning_data.get("trigger_metrics", False) or planning_data.get("needs_metrics", False):
        logger.info("Metrics extraction triggered by planning_data")
        return True
    
    # Additional fallback: check direct state values
    if state.get("needs_database_query", False) and state.get("confidence", 0.0) > 0.5:
        logger.info("Metrics extraction triggered by direct state values")
        return True
    
    # Final fallback: check planning_data.needs_database_query
    if planning_data.get("needs_database_query", False) and planning_data.get("confidence", 0.0) > 0.5:
        logger.info("Metrics extraction triggered by planning_data.needs_database_query")
        return True
    
    # Last resort: check message keywords
    current_message = state.get("current_message", "").lower()
    db_keywords = ["database", "db", "query", "soeid", "employee", "list", "get", "find", "show"]
    has_db_keywords = any(keyword in current_message for keyword in db_keywords)
    
    if has_db_keywords:
        logger.info(f"Metrics extraction triggered by message keywords: {current_message}")
        return True
    
    logger.info("No metrics extraction required - all checks failed")
    return False


async def metrics_extraction_node(state: WorkflowState) -> Dict[str, Any]:
    """
    LangGraph node that performs data extraction using dynamic database tool.
    
    This node:
    1. Determines if the user's message requires database querying
    2. If needed, uses the dynamic database tool to generate and execute queries
    3. Returns extracted data in a structured format
    
    Configuration:
    - Uses dynamic database tool for flexible query generation
    - Supports natural language queries across all collections
    - Handles complex queries with joins and aggregations
    """
    try:
        logger.info(f"Metrics node processing message for conversation: {state['conversation_id']}")
        
        current_message = state["current_message"]
        conversation_history = state.get("messages", [])
        
        # Check if metrics extraction is needed based on planner decision
        if not _should_extract_metrics(state):
            logger.info("No metrics extraction required based on planner decision")
            return {"metrics_data": None}
        
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
        
        logger.info(f"Using dynamic database tool for message: {current_message[:100]}...")
        
        # Execute the dynamic database query
        try:
            logger.info(f"DEBUG: About to prepare conversation context for better query generation, state: {state}, conversation_history: {conversation_history}")
            # Prepare conversation context for better query generation
            context_messages = []
            if conversation_history:
                # Use last few messages for context
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
                for msg in conversation_history[-context_limit:]:
                    context_messages.append(f"{msg['role']}: {msg['content']}")
            
            # Create enhanced prompt with context
            enhanced_prompt = current_message
            if context_messages:
                context_text = "\n".join(context_messages)
                enhanced_prompt = f"Context:\n{context_text}\n\nCurrent request: {current_message}"
            logger.info(f"DEBUG: About to call dynamic_tool._arun")
            logger.info(f"DEBUG: enhanced_prompt length: {len(enhanced_prompt)}")
            logger.info(f"DEBUG: unified_schema length: {len(unified_schema)}")
            
            # Check state values that might be None
            metrics_limit_raw = state.get("metrics_limit")
            logger.info(f"DEBUG: metrics_limit_raw: {metrics_limit_raw}, type: {type(metrics_limit_raw)}")
            metrics_limit = state.get("metrics_limit", 100)
            logger.info(f"DEBUG: metrics_limit: {metrics_limit}, type: {type(metrics_limit)}")
            
            logger.info(f"DEBUG: dynamic_tool type: {type(dynamic_tool)}")
            
            try:
                
                logger.info(f"DEBUG: Calling dynamic_tool._arun with parameters:")
                
                # Debug enhanced_prompt safely
                try:
                    prompt_preview = enhanced_prompt[:100] if enhanced_prompt else "None"
                    logger.info(f"DEBUG: - user_prompt: {prompt_preview}...")
                except Exception as e:
                    logger.error(f"DEBUG: Error getting prompt preview: {e}")
                    logger.info(f"DEBUG: - user_prompt: [ERROR]")
                
                # Debug unified_schema safely
                try:
                    schema_length = len(unified_schema) if unified_schema else "None"
                    logger.info(f"DEBUG: - unified_schema: {schema_length} chars")
                except Exception as e:
                    logger.error(f"DEBUG: Error getting schema length: {e}")
                    logger.info(f"DEBUG: - unified_schema: [ERROR]")
                
                # Debug limit safely
                try:
                    limit_value = state.get('metrics_limit', 100)
                    logger.info(f"DEBUG: - limit: {limit_value}")
                except Exception as e:
                    logger.error(f"DEBUG: Error getting limit: {e}")
                    logger.info(f"DEBUG: - limit: [ERROR]")
                
                logger.info(f"DEBUG: - include_aggregation: True")
                logger.info(f"DEBUG: - join_strategy: lookup")
                
                logger.info(f"DEBUG: About to call await dynamic_tool._arun")
                logger.info(f"DEBUG: dynamic_tool._arun method: {dynamic_tool._arun}")
                logger.info(f"DEBUG: dynamic_tool._arun type: {type(dynamic_tool._arun)}")
                
                # Check if the method is callable
                if not callable(dynamic_tool._arun):
                    logger.error(f"DEBUG: dynamic_tool._arun is not callable!")
                    raise RuntimeError("dynamic_tool._arun is not callable")
                
                # Prepare the limit parameter carefully
                try:
                    limit_param = state.get("metrics_limit", 100)
                    logger.info(f"DEBUG: limit_param: {limit_param}, type: {type(limit_param)}")
                    
                    # Ensure limit is a valid integer
                    if limit_param is None:
                        logger.warning(f"DEBUG: limit_param is None, using default 100")
                        limit_param = 100
                    elif not isinstance(limit_param, int):
                        logger.warning(f"DEBUG: limit_param is not int, converting from {type(limit_param)}")
                        try:
                            limit_param = int(limit_param)
                        except (ValueError, TypeError):
                            logger.warning(f"DEBUG: Could not convert limit_param to int, using default 100")
                            limit_param = 100
                    
                    logger.info(f"DEBUG: Final limit_param: {limit_param}, type: {type(limit_param)}")
                except Exception as e:
                    logger.error(f"DEBUG: Error preparing limit_param: {e}")
                    logger.error(f"DEBUG: Error type: {type(e)}")
                    import traceback
                    logger.error(f"DEBUG: Limit preparation traceback: {traceback.format_exc()}")
                    limit_param = 100  # Use safe default
                
                # Check other parameters
                try:
                    logger.info(f"DEBUG: enhanced_prompt type: {type(enhanced_prompt)}")
                    logger.info(f"DEBUG: enhanced_prompt is None: {enhanced_prompt is None}")
                    logger.info(f"DEBUG: unified_schema type: {type(unified_schema)}")
                    logger.info(f"DEBUG: unified_schema is None: {unified_schema is None}")
                    
                    # Ensure parameters are not None
                    if enhanced_prompt is None:
                        logger.error(f"DEBUG: enhanced_prompt is None!")
                        enhanced_prompt = current_message
                    
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
                metrics_data = {
                    "dynamic_db_query": {
                        "error": result,
                        "user_prompt": current_message,
                        "tool_type": "dynamic_db"
                    }
                }
            else:
                # Parse the JSON result
                try:
                    parsed_result = json.loads(result)
                    metrics_data = {
                        "dynamic_db_query": {
                            "result": parsed_result,
                            "user_prompt": current_message,
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
                    metrics_data = {
                        "dynamic_db_query": {
                            "error": f"Failed to parse result: {str(e)}",
                            "raw_result": result,
                            "user_prompt": current_message,
                            "tool_type": "dynamic_db"
                        }
                    }
            
        except Exception as tool_error:
            logger.error(f"Error executing dynamic database tool: {tool_error}")
            metrics_data = {
                "dynamic_db_query": {
                    "error": str(tool_error),
                    "user_prompt": current_message,
                    "tool_type": "dynamic_db"
                }
            }
        
        # Return only the keys this node modifies
        result = {"metrics_data": metrics_data}
        
        if metrics_data and "error" not in metrics_data.get("dynamic_db_query", {}):
            logger.info(f"Metrics extraction completed successfully")
        else:
            logger.info("Metrics extraction completed with errors")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in metrics extraction node: {str(e)}")
        return {
            "metrics_data": {
                "dynamic_db_query": {
                    "error": f"Metrics extraction failed: {str(e)}",
                    "user_prompt": state.get("current_message", ""),
                    "tool_type": "dynamic_db"
                }
            }
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