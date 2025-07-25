"""Self-contained dynamic database tool that generates MongoDB queries on the fly using LLM."""

import asyncio
import json
import os
import re
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from langchain.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DynamicDBQueryInput(BaseModel):
    """Input for dynamic database queries."""
    user_prompt: str = Field(..., description="Natural language description of what data to query")
    unified_schema: str = Field(..., description="Comprehensive schema document describing all collections, their relationships, and field definitions")
    limit: Optional[int] = Field(100, description="Maximum number of results to return")
    include_aggregation: Optional[bool] = Field(False, description="Whether to include aggregation pipeline in the query")
    join_strategy: Optional[str] = Field("lookup", description="Join strategy: 'lookup' for aggregation joins, 'application' for application-level joins")


class DatabaseQuery:
    """Simple database query representation."""
    def __init__(self, operation: str, collection_table: str, native_query: Dict[str, Any]):
        self.operation = operation
        self.collection_table = collection_table
        self.native_query = native_query


class MetricsQueryDatabase:
    """Simple database wrapper that works with any MongoDB adapter."""
    
    def __init__(self, adapter):
        self.adapter = adapter
        self._initialized = False
    
    async def initialize(self):
        """Initialize the database connection."""
        if not self._initialized:
            await self.adapter.initialize()
            self._initialized = True
    
    async def execute_native_query(self, query: DatabaseQuery) -> List[Dict[str, Any]]:
        """Execute a native database query."""
        if not self._initialized:
            await self.initialize()
        
        return await self.adapter.execute_native_query(query)


class DynamicDBQueryTool(BaseTool):
    """Self-contained dynamic database tool that generates MongoDB queries using LLM."""
    
    name: str = "dynamic_db_query"
    description: str = "Generate and execute MongoDB queries dynamically based on natural language prompts and schema documents. Use this to query any MongoDB collection with flexible, natural language requests."
    args_schema: type = DynamicDBQueryInput
    
    _db: Optional[MetricsQueryDatabase] = PrivateAttr(default=None)
    _llm_client: Optional[Any] = PrivateAttr(default=None)
    _adapter: Optional[Any] = PrivateAttr(default=None)
    
    def __init__(self, adapter=None, llm_client=None):
        try:
            logger.info(f"DEBUG: Initializing DynamicDBQueryTool")
            logger.info(f"DEBUG: adapter: {adapter}")
            logger.info(f"DEBUG: llm_client: {llm_client}")
            
            super().__init__()
            logger.info(f"DEBUG: BaseTool initialized")
            
            self._adapter = adapter
            self._llm_client = llm_client
            self._db = None
            
            logger.info(f"DEBUG: DynamicDBQueryTool initialization completed")
        except Exception as e:
            logger.error(f"DEBUG: Error in DynamicDBQueryTool.__init__: {e}")
            logger.error(f"DEBUG: Error type: {type(e)}")
            import traceback
            logger.error(f"DEBUG: Init traceback: {traceback.format_exc()}")
            raise
    
    async def _get_database(self) -> MetricsQueryDatabase:
        """Get or initialize the database connection."""
        logger.info(f"DEBUG: _get_database called, self._db is None: {self._db is None}")
        
        if self._db is None:
            try:
                logger.info("Initializing dynamic database connection...")
                
                if self._adapter is None:
                    # Try to get adapter from environment or create default
                    connection_string = os.getenv("METRICS_MONGODB_URI", "mongodb://localhost:27017")
                    database_name = os.getenv("METRICS_MONGODB_DATABASE", "ee-productivities")
                    
                    logger.info(f"Using connection string: {connection_string}")
                    logger.info(f"Using database: {database_name}")
                    
                    # Create a simple adapter if none provided
                    from pymongo import MongoClient
                    client = MongoClient(connection_string)
                    db = client[database_name]
                    
                    # Create a simple adapter wrapper
                    class SimpleMongoAdapter:
                        def __init__(self, db, collection_name=None):
                            self.db = db
                            self.collection_name = collection_name or "application_snapshot"
                        
                        async def initialize(self):
                            # List available collections
                            collections = self.db.list_collection_names()
                            logger.info(f"Available collections in {self.db.name}: {collections}")
                            logger.info(f"Connected to MongoDB database: {self.db.name}")
                        
                        async def switch_collection(self, collection_name: str):
                            self.collection_name = collection_name
                            logger.info(f"Switched to collection: {collection_name}")
                        
                        async def execute_native_query(self, query: DatabaseQuery) -> List[Dict[str, Any]]:
                            collection = self.db[query.collection_table]
                            
                            if query.operation == "aggregate":
                                pipeline = query.native_query["pipeline"]
                                logger.info(f"Executing aggregation pipeline on {query.collection_table}: {json.dumps(pipeline, indent=2)}")
                                cursor = collection.aggregate(pipeline)
                                return list(cursor)
                            elif query.operation == "find":
                                filter_obj = query.native_query.get("filter", {})
                                projection = query.native_query.get("projection", {})
                                sort_obj = query.native_query.get("sort", {})
                                limit_val = query.native_query.get("limit", 100)
                                
                                logger.info(f"Executing find query on {query.collection_table}: filter={filter_obj}, projection={projection}, sort={sort_obj}, limit={limit_val}")
                                
                                # Handle empty sort object - MongoDB doesn't accept empty sort
                                if sort_obj and len(sort_obj) > 0:
                                    cursor = collection.find(filter_obj, projection).sort(list(sort_obj.items())).limit(limit_val)
                                else:
                                    cursor = collection.find(filter_obj, projection).limit(limit_val)
                                return list(cursor)
                            else:
                                raise ValueError(f"Unsupported operation: {query.operation}")
                    
                    self._adapter = SimpleMongoAdapter(db)
                
                self._db = MetricsQueryDatabase(self._adapter)
                await self._db.initialize()
                logger.info(f"Database initialized. Adapter type: {type(self._db.adapter)}")
            except Exception as e:
                logger.error(f"Failed to initialize database: {e}")
                raise
        return self._db
    
    async def _get_llm_client(self):
        """Get or initialize the LLM client."""
        if self._llm_client is None:
            raise RuntimeError("LLM client not provided. Please pass an LLM client to the constructor.")
        
        # Return the LLM client directly - it should have the simple interface
        if not hasattr(self._llm_client, 'generate_response'):
            raise RuntimeError("LLM client must have a generate_response method")
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

Generate a valid MongoDB query that matches the user's request. Return only the JSON object, no additional text.
"""
        return prompt
    
    async def _generate_mongodb_query(self, user_prompt: str, unified_schema: str, limit: int, include_aggregation: bool, join_strategy: str) -> Dict[str, Any]:
        """Generate a MongoDB query using the LLM."""
        try:
            logger.info(f"DEBUG: Starting _generate_mongodb_query with user_prompt='{user_prompt}'")
            logger.info(f"DEBUG: Parameters - limit={limit}, include_aggregation={include_aggregation}, join_strategy={join_strategy}")
            
            llm_client = await self._get_llm_client()
            logger.info(f"DEBUG: LLM client obtained successfully")
            
            # Create the prompt
            prompt = self._create_query_generation_prompt(user_prompt, unified_schema, limit, include_aggregation, join_strategy)
            logger.info(f"DEBUG: Prompt created, length={len(prompt)}")
            
            # Generate the query using LLM
            logger.info(f"Generating MongoDB query for prompt: {user_prompt}")
            logger.info(f"DEBUG: Calling llm_client.generate_response with messages=[{{'role': 'user', 'content': '...'}}]")
            
            try:
                response = await llm_client.generate_response([{"role": "user", "content": prompt}])
                logger.info(f"DEBUG: LLM response received: {type(response)}")
                logger.info(f"DEBUG: LLM response keys: {list(response.keys()) if isinstance(response, dict) else 'Not a dict'}")
                
                response_content = response.get("content", "")
                logger.info(f"DEBUG: Response content type: {type(response_content)}")
                logger.info(f"DEBUG: Response content length: {len(response_content) if response_content else 'None'}")
                logger.info(f"DEBUG: Response content preview: {response_content[:200] if response_content else 'None'}")
                
            except Exception as llm_error:
                logger.error(f"DEBUG: LLM client error: {llm_error}")
                logger.error(f"DEBUG: LLM error type: {type(llm_error)}")
                raise
            
            # Parse the JSON response - handle markdown code blocks
            try:
                logger.info(f"DEBUG: Attempting to parse response_content as JSON")
                # First try to parse the entire response as JSON
                query_dict = json.loads(response_content)
                logger.info(f"DEBUG: Successfully parsed JSON directly")
            except json.JSONDecodeError as json_error:
                logger.info(f"DEBUG: Direct JSON parsing failed: {json_error}")
                # If that fails, try to extract JSON from markdown code blocks
                import re
                
                # Look for JSON code blocks (```json ... ```)
                json_block_match = re.search(r'```json\s*\n(.*?)\n```', response_content, re.DOTALL)
                if json_block_match:
                    json_content = json_block_match.group(1).strip()
                    logger.info(f"DEBUG: Found JSON code block, length={len(json_content)}")
                    try:
                        query_dict = json.loads(json_content)
                        logger.info(f"DEBUG: Successfully parsed JSON from code block")
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse JSON from code block: {e}")
                        logger.error(f"JSON content: {json_content[:200]}...")
                        raise
                else:
                    logger.info(f"DEBUG: No JSON code block found, looking for JSON object")
                    # Look for any JSON object in the response
                    json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
                    if json_match:
                        json_content = json_match.group(0)
                        logger.info(f"DEBUG: Found JSON object, length={len(json_content)}")
                        try:
                            query_dict = json.loads(json_content)
                            logger.info(f"DEBUG: Successfully parsed extracted JSON")
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse extracted JSON: {e}")
                            logger.error(f"Extracted content: {json_content[:200]}...")
                            raise
                    else:
                        logger.error(f"No JSON found in response: {response_content[:200]}...")
                        raise ValueError("No valid JSON found in LLM response")
            
            logger.info(f"DEBUG: Query dict type: {type(query_dict)}")
            logger.info(f"DEBUG: Query dict keys: {list(query_dict.keys()) if isinstance(query_dict, dict) else 'Not a dict'}")
            logger.info(f"Generated query: {json.dumps(query_dict, indent=2)}")
            return query_dict
            
        except Exception as e:
            logger.error(f"DEBUG: Exception in _generate_mongodb_query: {e}")
            logger.error(f"DEBUG: Exception type: {type(e)}")
            logger.error(f"DEBUG: Exception args: {e.args}")
            import traceback
            logger.error(f"DEBUG: Full traceback: {traceback.format_exc()}")
            logger.error(f"Failed to generate MongoDB query: {e}")
            raise
    
    async def _execute_query(self, query_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute a MongoDB query."""
        try:
            logger.info(f"DEBUG: Starting _execute_query with query_dict type: {type(query_dict)}")
            logger.info(f"DEBUG: Query dict keys: {list(query_dict.keys()) if isinstance(query_dict, dict) else 'Not a dict'}")
            
            db = await self._get_database()
            logger.info(f"DEBUG: Database obtained successfully")
            
            # Get primary collection
            primary_collection = query_dict.get("primary_collection")
            logger.info(f"DEBUG: Primary collection: {primary_collection}")
            if not primary_collection:
                raise ValueError("No primary_collection specified in query")
            
            # Switch to the primary collection
            logger.info(f"DEBUG: Switching to collection: {primary_collection}")
            await self._switch_collection(primary_collection)
            
            # Check if we have an aggregation pipeline
            aggregation = query_dict.get("aggregation")
            logger.info(f"DEBUG: Aggregation present: {bool(aggregation)}")
            logger.info(f"DEBUG: Aggregation type: {type(aggregation)}")
            logger.info(f"DEBUG: Aggregation content: {aggregation}")
            
            if aggregation and aggregation:
                # Execute aggregation pipeline
                pipeline = aggregation
                logger.info(f"DEBUG: Pipeline type: {type(pipeline)}")
                logger.info(f"DEBUG: Pipeline length: {len(pipeline) if isinstance(pipeline, list) else 'Not a list'}")
                
                limit_val = query_dict.get("limit")
                logger.info(f"DEBUG: Limit value: {limit_val}, type: {type(limit_val)}")
                
                if limit_val is not None:
                    logger.info(f"DEBUG: Adding limit to pipeline: {limit_val}")
                    pipeline.append({"$limit": limit_val})
                
                logger.info(f"Executing aggregation pipeline on {primary_collection}: {json.dumps(pipeline, indent=2)}")
                
                # Validate pipeline before execution
                try:
                    logger.info(f"DEBUG: Validating pipeline stages")
                    # Check for common issues
                    for i, stage in enumerate(pipeline):
                        logger.info(f"DEBUG: Stage {i}: {stage}")
                        if "$lookup" in stage:
                            lookup = stage["$lookup"]
                            logger.info(f"Lookup stage: {lookup}")
                        elif "$group" in stage:
                            group = stage["$group"]
                            logger.info(f"Group stage: {group}")
                            # Check for invalid field references
                            for field_name, field_expr in group.items():
                                logger.info(f"DEBUG: Group field '{field_name}': {field_expr}")
                                if isinstance(field_expr, dict) and "$size" in field_expr:
                                    size_field = field_expr["$size"]
                                    logger.info(f"DEBUG: Size field: {size_field}")
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
                    logger.info(f"DEBUG: Executing native query")
                    results = await db.execute_native_query(native_query)
                    logger.info(f"DEBUG: Query executed successfully, results type: {type(results)}")
                    logger.info(f"DEBUG: Results length: {len(results) if isinstance(results, list) else 'Not a list'}")
                except Exception as agg_error:
                    logger.error(f"DEBUG: Aggregation execution error: {agg_error}")
                    logger.error(f"DEBUG: Error type: {type(agg_error)}")
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
                
                logger.info(f"DEBUG: Find query parameters - filter: {filter_obj}, projection: {projection}, sort: {sort_obj}, limit: {limit_val}")
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
                
                logger.info(f"DEBUG: Executing find query")
                results = await db.execute_native_query(native_query)
                logger.info(f"DEBUG: Find query executed successfully, results type: {type(results)}")
                logger.info(f"DEBUG: Results length: {len(results) if isinstance(results, list) else 'Not a list'}")
            
            return results
            
        except Exception as e:
            logger.error(f"DEBUG: Exception in _execute_query: {e}")
            logger.error(f"DEBUG: Exception type: {type(e)}")
            logger.error(f"DEBUG: Exception args: {e.args}")
            import traceback
            logger.error(f"DEBUG: Full traceback: {traceback.format_exc()}")
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
        collections = [query_dict.get("primary_collection", "unknown")]
        
        # Add collections from joins
        joins = query_dict.get("joins", [])
        for join in joins:
            collection = join.get("collection")
            if collection and collection not in collections:
                collections.append(collection)
        
        return collections
    
    async def _arun(self, **kwargs) -> str:
        """Async run method for the tool."""
        try:
            logger.info(f"DEBUG: Starting _arun with kwargs: {list(kwargs.keys())}")
            
            # Extract parameters
            user_prompt = kwargs.get("user_prompt", "")
            unified_schema = kwargs.get("unified_schema", "")
            limit = kwargs.get("limit", 100)
            include_aggregation = kwargs.get("include_aggregation", False)
            join_strategy = kwargs.get("join_strategy", "lookup")
            
            logger.info(f"DEBUG: Extracted parameters - user_prompt length: {len(user_prompt)}, unified_schema length: {len(unified_schema)}, limit: {limit}, include_aggregation: {include_aggregation}, join_strategy: {join_strategy}")
            
            if not user_prompt:
                logger.error(f"DEBUG: user_prompt is empty")
                return "Error: user_prompt is required"
            
            if not unified_schema:
                logger.error(f"DEBUG: unified_schema is empty")
                return "Error: unified_schema is required"
            
            # Generate the query
            logger.info(f"DEBUG: Calling _generate_mongodb_query")
            query_dict = await self._generate_mongodb_query(
                user_prompt=user_prompt,
                unified_schema=unified_schema,
                limit=limit,
                include_aggregation=include_aggregation,
                join_strategy=join_strategy
            )
            logger.info(f"DEBUG: _generate_mongodb_query completed successfully")
            
            # Execute the query
            logger.info(f"DEBUG: Calling _execute_query")
            results = await self._execute_query(query_dict)
            logger.info(f"DEBUG: _execute_query completed successfully")
            
            # Format the results
            logger.info(f"DEBUG: Calling _format_results")
            formatted_response = self._format_results(results, query_dict)
            logger.info(f"DEBUG: _format_results completed successfully")
            
            logger.info(f"DEBUG: Returning JSON response")
            return json.dumps(formatted_response, indent=2, default=str)
            
        except Exception as e:
            logger.error(f"DEBUG: Exception in _arun: {e}")
            logger.error(f"DEBUG: Exception type: {type(e)}")
            logger.error(f"DEBUG: Exception args: {e.args}")
            import traceback
            logger.error(f"DEBUG: Full traceback: {traceback.format_exc()}")
            logger.error(f"Tool execution failed: {e}")
            return f"Error: {str(e)}"
    
    def _run(self, *args, **kwargs):
        """Synchronous run method for the tool."""
        return asyncio.run(self._arun(**kwargs))
    
    async def _close_database(self):
        """Close the database connection."""
        if self._db and hasattr(self._db.adapter, 'close'):
            await self._db.adapter.close()


def create_dynamic_db_tool(adapter=None, llm_client=None) -> DynamicDBQueryTool:
    """Create a dynamic database tool instance."""
    try:
        logger.info(f"DEBUG: Creating DynamicDBQueryTool")
        logger.info(f"DEBUG: adapter type: {type(adapter)}")
        logger.info(f"DEBUG: llm_client type: {type(llm_client)}")
        
        tool = DynamicDBQueryTool(adapter=adapter, llm_client=llm_client)
        logger.info(f"DEBUG: DynamicDBQueryTool created successfully")
        return tool
    except Exception as e:
        logger.error(f"DEBUG: Error creating DynamicDBQueryTool: {e}")
        logger.error(f"DEBUG: Error type: {type(e)}")
        import traceback
        logger.error(f"DEBUG: Creation traceback: {traceback.format_exc()}")
        raise 