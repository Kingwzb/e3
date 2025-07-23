"""Dynamic database tool that generates MongoDB queries on the fly using LLM."""

import asyncio
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from langchain.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr
import os
import re

from app.core.database_abstraction import (
    get_mongodb_ee_productivities_query_config,
    MetricsQueryDatabase,
    DatabaseQuery
)
from app.utils.logging import logger


class DynamicDBQueryInput(BaseModel):
    """Input for dynamic database queries."""
    user_prompt: str = Field(..., description="Natural language description of what data to query")
    unified_schema: str = Field(..., description="Comprehensive schema document describing all collections, their relationships, and field definitions")
    limit: Optional[int] = Field(100, description="Maximum number of results to return")
    include_aggregation: Optional[bool] = Field(False, description="Whether to include aggregation pipeline in the query")
    join_strategy: Optional[str] = Field("lookup", description="Join strategy: 'lookup' for aggregation joins, 'application' for application-level joins")


class DynamicDBQueryTool(BaseTool):
    """Dynamic database tool that generates MongoDB queries using LLM."""
    
    name: str = "dynamic_db_query"
    description: str = "Generate and execute MongoDB queries dynamically based on natural language prompts and schema documents. Use this to query any MongoDB collection with flexible, natural language requests."
    args_schema: type = DynamicDBQueryInput
    
    _db: Optional[MetricsQueryDatabase] = PrivateAttr(default=None)
    _llm_client: Optional[Any] = PrivateAttr(default=None)
    
    def __init__(self):
        super().__init__()
        self._db = None
        self._llm_client = None
    
    async def _get_database(self) -> MetricsQueryDatabase:
        """Get or initialize the database connection."""
        if self._db is None:
            try:
                logger.info("Initializing dynamic database connection...")
                
                # Get connection string from environment or use default
                connection_string = os.getenv("METRICS_MONGODB_URI", "mongodb://localhost:27017")
                database_name = os.getenv("METRICS_MONGODB_DATABASE", "ee-productivities")
                
                logger.info(f"Using connection string: {connection_string}")
                logger.info(f"Using database: {database_name}")
                
                config = get_mongodb_ee_productivities_query_config(
                    connection_string=connection_string,
                    database_name=database_name,
                    collection_name=None
                )
                self._db = MetricsQueryDatabase(config)
                await self._db.initialize()
                logger.info(f"Database initialized. Adapter type: {type(self._db.adapter)}")
            except Exception as e:
                logger.error(f"Failed to initialize database: {e}")
                raise
        return self._db
    
    async def _get_llm_client(self):
        """Get or initialize the LLM client."""
        if self._llm_client is None:
            try:
                # Import here to avoid circular imports
                from app.core.llm import llm_client
                self._llm_client = llm_client
                logger.info("LLM client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize LLM client: {e}")
                raise
        return self._llm_client
    
    async def _switch_collection(self, collection_name: str) -> None:
        """Switch to a different collection within the same database."""
        try:
            db = await self._get_database()
            logger.info(f"Switching to collection: {collection_name}")
            
            if db.adapter is None:
                raise RuntimeError("Database adapter is None. Database may not be properly initialized.")
            
            if hasattr(db.adapter, 'switch_collection'):
                await db.adapter.switch_collection(collection_name)
                logger.info(f"Successfully switched to collection: {collection_name}")
            else:
                logger.warning(f"Adapter does not support collection switching: {type(db.adapter)}")
        except Exception as e:
            logger.error(f"Failed to switch collection to {collection_name}: {e}")
            raise
    
    def _create_query_generation_prompt(self, user_prompt: str, unified_schema: str, limit: int, include_aggregation: bool, join_strategy: str) -> str:
        """Create a prompt for the LLM to generate MongoDB queries with unified schema support."""
        
        prompt = f"""
You are a MongoDB query generator. Based on the user's request and the provided unified schema, generate a MongoDB query that may involve multiple collections.

UNIFIED SCHEMA DOCUMENT:
{unified_schema}

USER REQUEST: {user_prompt}

JOIN STRATEGY: {join_strategy}

IMPORTANT CONSTRAINTS:
- Only use relationships that are explicitly defined in the schema
- If no relationships exist between collections, use single-collection queries only
- Always verify field names match exactly with the schema
- For aggregations, ensure all referenced fields exist in the schema
- Use proper error handling for missing fields

REQUIREMENTS:
- Generate a valid MongoDB query that matches the user's request
- Use the exact field names from the unified schema
- Limit results to {limit} documents
- Return the query as a JSON object with the following structure:
{{
  "primary_collection": "collection_name", // Main collection to query
  "filter": {{}}, // MongoDB filter object
  "projection": {{}}, // Optional projection object
  "sort": {{}}, // Optional sort object
  "limit": {limit},
  "aggregation": [], // Optional aggregation pipeline
  "joins": [ // Array of join operations
    {{
      "collection": "collection_name",
      "type": "lookup", // or "match" for filtering
      "local_field": "field_name",
      "foreign_field": "field_name",
      "as": "alias_name"
    }}
  ]
}}

EXAMPLES:

1. Simple single collection query (RECOMMENDED when no relationships exist):
{{
  "primary_collection": "application_snapshot",
  "filter": {{"application.criticality": "High"}},
  "projection": {{"_id": 0, "application.criticality": 1, "application.csiId": 1}},
  "sort": {{"application.csiId": 1}},
  "limit": {limit},
  "aggregation": [],
  "joins": []
}}

2. Simple aggregation without joins:
{{
  "primary_collection": "application_snapshot",
  "filter": {{}},
  "projection": {{}},
  "sort": {{}},
  "limit": {limit},
  "aggregation": [
    {{
      "$group": {{
        "_id": "$application.criticality",
        "count": {{"$sum": 1}}
      }}
    }},
    {{
      "$sort": {{"count": -1}}
    }}
  ],
  "joins": []
}}

3. Multi-collection join query (ONLY if relationships exist in schema):
{{
  "primary_collection": "application_snapshot",
  "filter": {{}},
  "projection": {{}},
  "sort": {{}},
  "limit": {limit},
  "aggregation": [
    {{
      "$lookup": {{
        "from": "employee_ratio",
        "localField": "application.csiId",
        "foreignField": "csiId",
        "as": "employee_data"
      }}
    }},
    {{
      "$match": {{
        "application.criticality": "High",
        "employee_data": {{"$ne": []}}
      }}
    }}
  ],
  "joins": [
    {{
      "collection": "employee_ratio",
      "type": "lookup",
      "local_field": "application.csiId",
      "foreign_field": "csiId",
      "as": "employee_data"
    }}
  ]
}}

CRITICAL RULES:
- If the schema shows "No explicit relationships identified" for collections, DO NOT create joins
- Always use exact field names from the schema (e.g., "High" not "HIGH" for criticality)
- For aggregations, only reference fields that exist in the PRIMARY COLLECTION schema
- NEVER reference fields from other collections unless there's an explicit $lookup join
- If unsure about relationships, prefer single-collection queries
- Use proper MongoDB syntax for all operations
- When grouping by criticality, use "$application.criticality" not "$criticality"
- When counting documents, use "$sum": 1, not "$size" on non-existent fields
      "$lookup": {{
        "from": "management_segment_tree",
        "localField": "application.level3",
        "foreignField": "name",
        "as": "segment_data"
      }}
    }},
    {{
      "$group": {{
        "_id": "$application.criticality",
        "count": {{"$sum": 1}},
        "avg_employee_count": {{"$avg": {{"$size": "$employee_data"}}}}
      }}
    }},
    {{
      "$sort": {{"count": -1}}
    }}
  ],
  "joins": [
    {{
      "collection": "employee_ratio",
      "type": "lookup",
      "local_field": "application.csiId",
      "foreign_field": "csiId",
      "as": "employee_data"
    }},
    {{
      "collection": "management_segment_tree",
      "type": "lookup",
      "local_field": "application.level3",
      "foreign_field": "name",
      "as": "segment_data"
    }}
  ]
}}

IMPORTANT RULES:
1. Only use fields that exist in the unified schema
2. Use proper MongoDB syntax and operators
3. For multi-collection queries, use $lookup for joins
4. Always specify the primary_collection
5. Use proper field references (e.g., "application.criticality")
6. For date fields, use proper date objects or string comparisons
7. Include joins array even if empty
8. Use meaningful aliases for joined data
9. Consider performance - limit the number of joins when possible
10. Use aggregation pipeline for complex queries involving multiple collections
11. Pay attention to relationships and keys defined in the unified schema
12. Use the collection names and field names exactly as specified in the schema

Generate only the JSON query object, no additional text or explanation.
"""

        if include_aggregation:
            prompt += "\nNOTE: Include aggregation pipeline when appropriate for the user's request."
        
        return prompt
    
    async def _generate_mongodb_query(self, user_prompt: str, unified_schema: str, limit: int, include_aggregation: bool, join_strategy: str) -> Dict[str, Any]:
        """Generate MongoDB query using LLM with unified schema support."""
        try:
            llm_client = await self._get_llm_client()
            
            prompt = self._create_query_generation_prompt(
                user_prompt, unified_schema, limit, include_aggregation, join_strategy
            )
            
            logger.info(f"Generating MongoDB query for prompt: {user_prompt[:100]}...")
            
            # Generate query using LLM
            response = await llm_client.generate_response(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,  # Low temperature for consistent query generation
                max_tokens=2000  # Increased for complex unified schema queries
            )
            
            query_text = response.get("content", "").strip()
            
            # Extract JSON from response (handle cases where LLM adds extra text)
            json_match = re.search(r'\{.*\}', query_text, re.DOTALL)
            if json_match:
                query_text = json_match.group(0)
            
            # Parse the generated query
            query_dict = json.loads(query_text)
            
            logger.info(f"Generated query: {json.dumps(query_dict, indent=2)}")
            
            return query_dict
            
        except Exception as e:
            logger.error(f"Failed to generate MongoDB query: {e}")
            raise
    
    async def _execute_query(self, query_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute the generated MongoDB query with multi-collection support."""
        try:
            db = await self._get_database()
            
            # Get primary collection
            primary_collection = query_dict.get("primary_collection")
            if not primary_collection:
                raise ValueError("No primary_collection specified in query")
            
            # Switch to the primary collection
            await self._switch_collection(primary_collection)
            
            # Check if we have an aggregation pipeline
            if query_dict.get("aggregation") and query_dict["aggregation"]:
                # Execute aggregation pipeline
                pipeline = query_dict["aggregation"]
                if query_dict.get("limit"):
                    pipeline.append({"$limit": query_dict["limit"]})
                
                logger.info(f"Executing aggregation pipeline on {primary_collection}: {json.dumps(pipeline, indent=2)}")
                
                # Validate pipeline before execution
                try:
                    # Check for common issues
                    for stage in pipeline:
                        if "$lookup" in stage:
                            lookup = stage["$lookup"]
                            logger.info(f"Lookup stage: {lookup}")
                        elif "$group" in stage:
                            group = stage["$group"]
                            logger.info(f"Group stage: {group}")
                            # Check for invalid field references
                            for field_name, field_expr in group.items():
                                if isinstance(field_expr, dict) and "$size" in field_expr:
                                    size_field = field_expr["$size"]
                                    if not size_field.startswith("$") or "employeeRatioSnapshot" in size_field:
                                        logger.warning(f"Potentially invalid $size reference: {size_field}")
                        elif "$sort" in stage:
                            sort = stage["$sort"]
                            logger.info(f"Sort stage: {sort}")
                
                except Exception as validation_error:
                    logger.warning(f"Pipeline validation warning: {validation_error}")
                
                native_query = DatabaseQuery(
                    operation="aggregate",
                    collection_table=primary_collection,
                    native_query={"pipeline": pipeline}
                )
                
                try:
                    results = await db.execute_native_query(native_query)
                except Exception as agg_error:
                    logger.error(f"Aggregation execution failed: {agg_error}")
                    # Try to provide helpful error message
                    if "missing" in str(agg_error) and "$size" in str(agg_error):
                        logger.error("This error typically occurs when trying to use $size on a field that doesn't exist or isn't an array. Check that all referenced fields exist in the schema.")
                    elif "lookup" in str(agg_error).lower():
                        logger.error("Lookup error - check that the collections have matching field values for the join.")
                    raise
                
            else:
                # Execute find query
                filter_obj = query_dict.get("filter", {})
                projection = query_dict.get("projection", {})
                sort_obj = query_dict.get("sort", {})
                limit_val = query_dict.get("limit", 100)
                
                logger.info(f"Executing find query on {primary_collection}: filter={filter_obj}, projection={projection}, sort={sort_obj}, limit={limit_val}")
                
                native_query = DatabaseQuery(
                    operation="find",
                    collection_table=primary_collection,
                    native_query={
                        "filter": filter_obj,
                        "projection": projection,
                        "sort": sort_obj,
                        "limit": limit_val
                    }
                )
                
                results = await db.execute_native_query(native_query)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to execute query: {e}")
            raise
    
    def _format_results(self, results: List[Dict[str, Any]], query_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Format the query results into a structured response."""
        try:
            # Convert ObjectId to string for JSON serialization
            def convert_objectid(obj):
                if isinstance(obj, dict):
                    return {k: convert_objectid(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_objectid(item) for item in obj]
                elif hasattr(obj, '__class__') and obj.__class__.__name__ == 'ObjectId':
                    return str(obj)
                elif isinstance(obj, datetime):
                    return obj.isoformat()
                else:
                    return obj
            
            formatted_results = convert_objectid(results)
            
            response = {
                "query_info": {
                    "primary_collection": query_dict.get("primary_collection", "unknown"),
                    "query_type": "aggregation" if query_dict.get("aggregation") else "find",
                    "limit": query_dict.get("limit", 100),
                    "joins": query_dict.get("joins", []),
                    "generated_query": query_dict
                },
                "results": {
                    "total_count": len(formatted_results),
                    "data": formatted_results
                },
                "summary": {
                    "execution_time": datetime.now().isoformat(),
                    "result_count": len(formatted_results),
                    "collections_involved": self._get_collections_involved(query_dict)
                }
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to format results: {e}")
            return {
                "error": f"Failed to format results: {str(e)}",
                "raw_results": results
            }
    
    def _get_collections_involved(self, query_dict: Dict[str, Any]) -> List[str]:
        """Get list of collections involved in the query."""
        collections = set()
        
        # Add primary collection
        primary_collection = query_dict.get("primary_collection")
        if primary_collection:
            collections.add(primary_collection)
        
        # Add collections from joins
        joins = query_dict.get("joins", [])
        for join in joins:
            collection = join.get("collection")
            if collection:
                collections.add(collection)
        
        # Add collections from aggregation pipeline
        aggregation = query_dict.get("aggregation", [])
        for stage in aggregation:
            if isinstance(stage, dict) and "$lookup" in stage:
                lookup = stage["$lookup"]
                from_collection = lookup.get("from")
                if from_collection:
                    collections.add(from_collection)
        
        return list(collections)
    
    async def _arun(self, **kwargs) -> str:
        """Execute the dynamic database query tool."""
        try:
            user_prompt = kwargs["user_prompt"]
            unified_schema = kwargs["unified_schema"]
            limit = kwargs.get("limit", 100)
            include_aggregation = kwargs.get("include_aggregation", False)
            join_strategy = kwargs.get("join_strategy", "lookup")
            
            logger.info(f"Processing dynamic query request: {user_prompt[:100]}...")
            logger.info(f"Using unified schema with length: {len(unified_schema)} characters")
            
            # Step 1: Generate MongoDB query using LLM
            query_dict = await self._generate_mongodb_query(
                user_prompt, unified_schema, limit, include_aggregation, join_strategy
            )
            
            # Step 2: Execute the generated query
            results = await self._execute_query(query_dict)
            
            # Step 3: Format and return results
            formatted_response = self._format_results(results, query_dict)
            
            return json.dumps(formatted_response, indent=2, default=str)
            
        except Exception as e:
            logger.error(f"Failed to execute dynamic database query: {e}")
            error_response = {
                "error": f"Failed to execute dynamic database query: {str(e)}",
                "user_prompt": kwargs.get("user_prompt", ""),
                "unified_schema_length": len(kwargs.get("unified_schema", "")),
                "timestamp": datetime.now().isoformat()
            }
            return json.dumps(error_response, indent=2)
    
    def _run(self, *args, **kwargs):
        raise NotImplementedError("Synchronous run is not supported. Use async.")
    
    async def _close_database(self):
        """Close the database connection."""
        if self._db:
            await self._db.close()
            self._db = None


def create_dynamic_db_tool() -> DynamicDBQueryTool:
    """Create the dynamic database query tool."""
    return DynamicDBQueryTool() 