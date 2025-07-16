"""Metrics extraction node for LangGraph workflow using LangChain tools."""

import json
from typing import Dict, Any, List, Optional
from app.models.state import WorkflowState
from app.tools.ee_productivities_tools import create_ee_productivities_tools
from app.core.llm import llm_client

from app.utils.logging import logger


def _clean_schema_for_vertex_ai(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean JSON schema to be compatible with Vertex AI by removing NULL values and fixing anyOf issues.
    
    Vertex AI's protobuf parser doesn't handle "NULL" string values well,
    and has strict requirements for anyOf schemas.
    """
    if not isinstance(schema, dict):
        return schema
    
    cleaned = {}
    for key, value in schema.items():
        if key == "anyOf" and isinstance(value, list):
            # Filter out null types from anyOf arrays
            cleaned_any_of = []
            for item in value:
                if isinstance(item, dict) and item.get("type") != "null":
                    cleaned_any_of.append(_clean_schema_for_vertex_ai(item))
            if cleaned_any_of:
                # If we have anyOf, it should be the only field in this schema object
                if len(cleaned_any_of) == 1:
                    # If only one type remains, flatten it
                    cleaned.update(cleaned_any_of[0])
                else:
                    cleaned[key] = cleaned_any_of
        elif key == "type" and value == "null":
            # Skip null types
            continue
        elif key == "properties" and isinstance(value, dict):
            # Clean properties recursively
            cleaned_properties = {}
            for prop_name, prop_schema in value.items():
                cleaned_prop = _clean_schema_for_vertex_ai(prop_schema)
                if cleaned_prop:  # Only add if not empty
                    cleaned_properties[prop_name] = cleaned_prop
            if cleaned_properties:
                cleaned[key] = cleaned_properties
        elif isinstance(value, dict):
            cleaned[key] = _clean_schema_for_vertex_ai(value)
        elif isinstance(value, list):
            cleaned[key] = [_clean_schema_for_vertex_ai(item) for item in value]
        else:
            cleaned[key] = value
    
    return cleaned


def _select_most_appropriate_tool(message: str, tools: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Select the most appropriate tool based on the user's message content.
    
    Args:
        message: User's message
        tools: List of available tools
        
    Returns:
        The most appropriate tool or None if no specific tool is needed
    """
    message_lower = message.lower()
    
    # Define keyword mappings for each tool
    tool_keywords = {
        "query_application_snapshots": [
            "application", "applications", "app", "apps", "snapshot", "snapshots",
            "status", "criticality", "sector", "development", "hosting", "model"
        ],
        "query_employee_ratios": [
            "employee", "employees", "ratio", "ratios", "engineer", "engineers",
            "tools", "adoption", "count", "headcount"
        ],
        "query_employee_trees": [
            "tree", "trees", "hierarchy", "hierarchical", "organization", "organizational",
            "structure", "reporting", "level", "levels"
        ],
        "query_enablers": [
            "enabler", "enablers", "csi", "se", "achievement", "metrics"
        ],
        "query_management_segments": [
            "management", "segment", "segments", "parent", "child"
        ],
        "query_statistics": [
            "statistic", "statistics", "performance", "metric", "metrics",
            "data", "numbers", "figures"
        ],
        "get_database_schema": [
            "schema", "database", "collection", "collections", "structure",
            "table", "tables", "field", "fields"
        ]
    }
    
    # Score each tool based on keyword matches
    tool_scores = {}
    for tool in tools:
        tool_name = tool["function"]["name"]
        if tool_name in tool_keywords:
            score = 0
            for keyword in tool_keywords[tool_name]:
                if keyword in message_lower:
                    score += 1
            if score > 0:
                tool_scores[tool_name] = score
    
    # Return the tool with the highest score, or None if no matches
    if tool_scores:
        best_tool_name = max(tool_scores, key=tool_scores.get)
        return next(tool for tool in tools if tool["function"]["name"] == best_tool_name)
    
    return None


async def metrics_extraction_node(state: WorkflowState) -> Dict[str, Any]:
    """
    LangGraph node that performs data extraction using ee-productivities tools.
    
    This node:
    1. Uses LLM to determine if data from the ee-productivities database is needed
    2. If needed, calls appropriate ee-productivities tools
    3. Returns extracted data
    
    Configuration:
    - Uses ee-productivities database tools for data extraction
    - Supports queries for applications, employees, enablers, statistics, and organizational data
    """
    try:
        logger.info(f"Metrics node processing message for conversation: {state['conversation_id']}")
        
        current_message = state["current_message"]
        conversation_history = state.get("messages", [])
        
        # Create ee-productivities tools
        ee_tools = create_ee_productivities_tools()
        tool_map = {tool.name: tool for tool in ee_tools}
        
        logger.debug(f"Using ee-productivities tools: {[tool.name for tool in ee_tools]}")
        
        # Prepare messages for LLM
        system_message = """You are a data extraction agent for the ee-productivities database. Your job is to extract data from the database using the available tools.

IMPORTANT: You MUST use the available tools to extract data when the user asks about:
- Applications, snapshots, status, criticality, sector, development model
- Employees, ratios, organizational hierarchy, engineer data
- Enablers, CSI snapshots, SE metrics
- Management segments, organizational structures
- Statistics, performance metrics, data
- Database schema, collections, structure

Available tools and their capabilities:
- query_application_snapshots: Query application snapshots (status, criticality, sector, development model, etc.)
- query_employee_ratios: Query employee ratios and engineer data
- query_employee_trees: Query organizational hierarchy and employee structures
- query_enablers: Query enabler CSI snapshots and SE metrics
- query_management_segments: Query management segment trees
- query_statistics: Query performance metrics and statistics
- get_database_schema: Get database schema information

DO NOT respond with generic messages. If the user asks about any of the above topics, you MUST call the appropriate tool to get the data. Only respond with "No data required" if the query is completely unrelated to the database."""

        messages = [
            {"role": "system", "content": system_message},
        ]
        
        # Add conversation history (use configurable limit)
        # Check for metrics-specific context limit, otherwise use general history limit
        metrics_context_limit = state.get("metrics_context_limit") 
        if metrics_context_limit is None:
            # Use the general conversation history limit, but cap at 8 for LLM efficiency
            general_limit = state.get("conversation_history_limit", 10)
            metrics_context_limit = min(general_limit, 8) if general_limit > 0 else 5
        
        logger.debug(f"Using {metrics_context_limit} messages for metrics context (from {len(conversation_history)} total)")
        
        for msg in conversation_history[-metrics_context_limit:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Add current message
        messages.append({"role": "user", "content": current_message})
        
        # Convert ee-productivities tools to OpenAI function format
        tools_for_llm = []
        for tool in ee_tools:
            # Get the raw schema and clean it for Vertex AI compatibility
            raw_schema = tool.args_schema.model_json_schema()
            
            # Clean the schema to remove NULL values that cause Vertex AI issues
            cleaned_schema = _clean_schema_for_vertex_ai(raw_schema)
            
            tool_schema = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": cleaned_schema
                }
            }
            tools_for_llm.append(tool_schema)
        
        # Select the most appropriate tool based on the query content
        selected_tool = _select_most_appropriate_tool(current_message, tools_for_llm)
        if selected_tool:
            tools_for_llm = [selected_tool]
            logger.info(f"Selected tool based on query: {selected_tool['function']['name']}")
        else:
            logger.info("No specific tool selected, using all tools")
        
        logger.debug(f"Created {len(tools_for_llm)} ee-productivities tools for LLM")
        logger.info(f"Available tools for LLM: {[tool['function']['name'] for tool in tools_for_llm]}")
        
        # Call LLM with tools
        logger.info(f"Calling LLM with {len(tools_for_llm)} tools for message: {current_message[:100]}...")
        llm_response = await llm_client.generate_response(
            messages=messages,
            tools=tools_for_llm,
            temperature=0.3
        )
        
        logger.info(f"LLM response received. Has tool calls: {bool(llm_response.get('tool_calls'))}")
        if llm_response.get("tool_calls"):
            logger.info(f"Tool calls found: {len(llm_response['tool_calls'])}")
        else:
            logger.info(f"No tool calls. LLM response content: {llm_response.get('content', 'No content')[:200]}...")
        
        # Process tool calls if any
        metrics_data = None
        if llm_response.get("tool_calls"):
            metrics_data = {}
            
            # Execute each tool call using ee-productivities tools
            for tool_call in llm_response["tool_calls"]:
                function_name = tool_call["function"]["name"]
                function_args = tool_call["function"]["arguments"]
                
                logger.info(f"Executing ee-productivities tool: {function_name} with args: {function_args}")
                
                try:
                    # Find the corresponding ee-productivities tool
                    ee_tool = tool_map.get(function_name)
                    
                    if ee_tool:
                        # Execute the ee-productivities tool
                        if isinstance(function_args, str):
                            function_args = json.loads(function_args)
                        
                        logger.info(f"Tool '{function_name}' found and executing with args: {function_args}")
                        result = await ee_tool._arun(**function_args)
                        
                        metrics_data[function_name] = {
                            "result": result,
                            "arguments": function_args,
                            "tool_type": "ee_productivities",
                            "config": {
                                "database": "ee-productivities",
                                "tool_name": function_name
                            }
                        }
                        
                        logger.info(f"Successfully executed ee-productivities tool {function_name}")
                    else:
                        available_tools = list(tool_map.keys())
                        logger.error(f"Tool '{function_name}' not found in available tools: {available_tools}")
                        logger.error(f"LLM attempted to call undefined tool: {function_name}")
                        metrics_data[function_name] = {
                            "error": f"Unknown tool: {function_name}",
                            "arguments": function_args,
                            "available_tools": available_tools
                        }
                    
                except Exception as tool_error:
                    # Enhanced exception logging with traceback and input parameters
                    import traceback
                    logger.error(f"Error executing ee-productivities tool at line {tool_error.__traceback__.tb_lineno if tool_error.__traceback__ else 'unknown'}: {str(tool_error)}")
                    logger.error(f"Input parameters - function_name: {function_name}, function_args: {function_args}")
                    logger.error(f"Full traceback: {traceback.format_exc()}")
                    metrics_data[function_name] = {
                        "error": str(tool_error),
                        "arguments": function_args,
                        "tool_type": "ee_productivities"
                    }
        
        # Return only the keys this node modifies
        result = {"metrics_data": metrics_data}
        
        if metrics_data:
            logger.info(f"Metrics extraction completed. Retrieved {len(metrics_data)} tool results")
        else:
            logger.info("No metrics extraction required for this query")
        
        return result
        
    except Exception as e:
        # Enhanced exception logging with traceback and input parameters
        import traceback
        logger.error(f"Error in metrics extraction node at line {e.__traceback__.tb_lineno if e.__traceback__ else 'unknown'}: {str(e)}")
        logger.error(f"Input parameters - conversation_id: {state.get('conversation_id', 'unknown')}, current_message: {state.get('current_message', 'unknown')[:100]}...")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        # Return only the keys this node modifies, even in error case
        return {
            "error": f"Metrics extraction failed: {str(e)}",
            "metrics_data": None
        }


def create_metrics_node_tools() -> Dict[str, Any]:
    """Create tools and utilities for the metrics node."""
    return {
        "supported_databases": ["ee-productivities"],
        "available_tools": [
            "query_application_snapshots",
            "query_employee_ratios", 
            "query_employee_trees",
            "query_enablers",
            "query_management_segments",
            "query_statistics",
            "get_database_schema"
        ],
        "default_config": {
            "database": "ee-productivities",
            "tool_type": "ee_productivities"
        }
    } 