"""Metrics extraction node for LangGraph workflow using LangChain tools."""

import json
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.state import WorkflowState
from app.tools.langchain_db_tools import (
    create_langchain_db_tools, 
    create_tool_config_for_environment, 
    DatabaseToolsConfig
)
from app.core.llm import llm_client
from app.core.database import get_db
from app.utils.logging import logger


async def metrics_extraction_node(state: WorkflowState) -> Dict[str, Any]:
    """
    LangGraph node that performs metrics extraction using LangChain tools.
    
    This node:
    1. Uses LLM to determine if metrics data is needed
    2. If needed, calls appropriate LangChain database tools
    3. Returns extracted metrics data
    
    Configuration:
    - Uses state.get("metrics_tools_config") for tool configuration
    - Uses state.get("metrics_environment", "production") for environment-based config
    """
    try:
        logger.info(f"Metrics node processing message for conversation: {state['conversation_id']}")
        
        current_message = state["current_message"]
        conversation_history = state.get("messages", [])
        
        # Get tool configuration from state or use environment-based config
        environment = state.get("metrics_environment", "production")
        custom_config = state.get("metrics_tools_config")
        
        if custom_config:
            tools_config = DatabaseToolsConfig(**custom_config)
        else:
            tools_config = create_tool_config_for_environment(environment)
        
        logger.debug(f"Using metrics tools config for environment: {environment}")
        
        # Prepare messages for LLM
        system_message = f"""You are a metrics extraction agent. Your job is to determine if the user's query requires metrics data from the database and extract that data using the available tools.

Available tools and their capabilities:
- get_metrics_by_category: Get metrics by category for the last N days (max {tools_config.max_days_back} days)
  Available categories: {', '.join(tools_config.allowed_categories)}
- get_top_metrics: Get top N metrics by value for a specific metric name (max {tools_config.max_limit} results)
  Available metrics: {', '.join(tools_config.allowed_metric_names[:10])}{'...' if len(tools_config.allowed_metric_names) > 10 else ''}
{f'- execute_custom_query: Execute custom SQL SELECT queries' if tools_config.enable_custom_queries else ''}

If the user's query mentions metrics, data, statistics, numbers, performance, or similar terms, you should use the appropriate tool to extract the relevant data. If no metrics are needed, respond with "No metrics required."

Consider the conversation history for context about what metrics might be relevant."""

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
        
        # Get database session and create LangChain tools
        async for db_session in get_db():
            langchain_tools = create_langchain_db_tools(db_session, tools_config)
            
            # Convert LangChain tools to OpenAI function format
            tools_for_llm = []
            for tool in langchain_tools:
                tool_schema = {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.args_schema.schema()
                    }
                }
                tools_for_llm.append(tool_schema)
            
            logger.debug(f"Created {len(tools_for_llm)} LangChain tools for LLM")
            
            # For Vertex AI compatibility, prioritize tools based on query content
            if len(tools_for_llm) > 1:
                # Analyze the current message to determine the most relevant tool
                message_lower = current_message.lower()
                
                # Prioritize tools based on query keywords
                if any(word in message_lower for word in ['category', 'categories', 'type', 'types']):
                    # Prioritize category-based queries
                    category_tools = [t for t in tools_for_llm if 'category' in t['function']['name']]
                    if category_tools:
                        tools_for_llm = category_tools + [t for t in tools_for_llm if t not in category_tools]
                
                elif any(word in message_lower for word in ['top', 'highest', 'best', 'maximum', 'largest']):
                    # Prioritize top/ranking queries
                    top_tools = [t for t in tools_for_llm if 'top' in t['function']['name']]
                    if top_tools:
                        tools_for_llm = top_tools + [t for t in tools_for_llm if t not in top_tools]
                
                elif any(word in message_lower for word in ['custom', 'specific', 'where', 'select']):
                    # Prioritize custom query tools
                    custom_tools = [t for t in tools_for_llm if 'custom' in t['function']['name'] or 'query' in t['function']['name']]
                    if custom_tools:
                        tools_for_llm = custom_tools + [t for t in tools_for_llm if t not in custom_tools]
                
                logger.debug(f"Reordered tools based on query analysis. Primary tool: {tools_for_llm[0]['function']['name']}")
            
            # Call LLM with tools
            llm_response = await llm_client.generate_response(
                messages=messages,
                tools=tools_for_llm,
                temperature=0.3
            )
            
            # Process tool calls if any
            metrics_data = None
            if llm_response.get("tool_calls"):
                metrics_data = {}
                
                # Execute each tool call using LangChain tools
                for tool_call in llm_response["tool_calls"]:
                    function_name = tool_call["function"]["name"]
                    function_args = tool_call["function"]["arguments"]
                    
                    logger.info(f"Executing LangChain tool: {function_name} with args: {function_args}")
                    
                    try:
                        # Find the corresponding LangChain tool
                        langchain_tool = next((t for t in langchain_tools if t.name == function_name), None)
                        
                        if langchain_tool:
                            # Execute the LangChain tool
                            if isinstance(function_args, str):
                                function_args = json.loads(function_args)
                            
                            result = await langchain_tool._arun(**function_args)
                            
                            metrics_data[function_name] = {
                                "result": result,
                                "arguments": function_args,
                                "tool_type": "langchain",
                                "config": {
                                    "environment": environment,
                                    "max_days_back": tools_config.max_days_back,
                                    "max_limit": tools_config.max_limit
                                }
                            }
                            
                            logger.info(f"Successfully executed LangChain tool {function_name}")
                        else:
                            logger.warning(f"Unknown LangChain tool: {function_name}")
                            metrics_data[function_name] = {
                                "error": f"Unknown tool: {function_name}",
                                "arguments": function_args
                            }
                        
                    except Exception as tool_error:
                        logger.error(f"Error executing LangChain tool {function_name}: {str(tool_error)}")
                        metrics_data[function_name] = {
                            "error": str(tool_error),
                            "arguments": function_args,
                            "tool_type": "langchain"
                        }
            
            break  # Exit the async generator loop
        
        # Return only the keys this node modifies
        result = {"metrics_data": metrics_data}
        
        if metrics_data:
            logger.info(f"Metrics extraction completed. Retrieved {len(metrics_data)} tool results")
        else:
            logger.info("No metrics extraction required for this query")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in metrics extraction node: {str(e)}")
        # Return only the keys this node modifies, even in error case
        return {
            "error": f"Metrics extraction failed: {str(e)}",
            "metrics_data": None
        }


def create_metrics_node_tools() -> Dict[str, Any]:
    """Create tools and utilities for the metrics node."""
    return {
        "supported_environments": ["development", "testing", "production"],
        "default_config": {
            "max_days_back": 90,
            "max_limit": 50,
            "enable_custom_queries": False
        },
        "environment_configs": {
            "development": {
                "max_days_back": 30,
                "max_limit": 20,
                "enable_custom_queries": True
            },
            "testing": {
                "max_days_back": 7,
                "max_limit": 10,
                "enable_custom_queries": False
            },
            "production": {
                "max_days_back": 90,
                "max_limit": 50,
                "enable_custom_queries": False
            }
        }
    } 