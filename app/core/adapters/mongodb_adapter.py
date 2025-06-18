"""MongoDB adapter for metrics storage with generic database interface."""

import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from uuid import uuid4
import motor.motor_asyncio

from app.core.database_abstraction import MetricsAdapter, MetricTuple, QueryFilter, DatabaseConfig, AggregationQuery, DatabaseQuery
from app.utils.logging import logger


class MongoDBMetricsAdapter(MetricsAdapter):
    """MongoDB implementation of the metrics adapter with generic interface."""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.connection_string = config.connection_params.get("connection_string")
        self.database_name = config.connection_params.get("database_name", "metrics_db")
        self.collection_name = config.connection_params.get("collection_name", "metrics")
        
        self.client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
        self.database = None
        self.collection = None
    
    async def connect(self) -> None:
        """Establish connection to MongoDB."""
        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(
                self.connection_string,
                maxPoolSize=self.config.connection_pool_size,
                serverSelectionTimeoutMS=self.config.query_timeout * 1000
            )
            
            # Test the connection
            await self.client.admin.command('ping')
            
            self.database = self.client[self.database_name]
            self.collection = self.database[self.collection_name]
            
            # Create indexes if they don't exist
            await self.create_schema()
            
            logger.info(f"Connected to MongoDB database: {self.database_name}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close connection to MongoDB."""
        if self.client:
            self.client.close()
            self.client = None
            self.database = None
            self.collection = None
            logger.info("Disconnected from MongoDB")
    
    async def create_schema(self) -> None:
        """Create necessary indexes for the collection."""
        if not self.collection:
            raise RuntimeError("Database not connected")
        
        try:
            # Create indexes for better query performance
            indexes = [
                ("timestamp", 1),  # Ascending index on timestamp
                ("timestamp", -1),  # Descending index on timestamp
                ("attributes.category", 1),  # Index on category attribute
                ("attributes.metric_name", 1),  # Index on metric_name attribute
            ]
            
            for index_spec in indexes:
                try:
                    await self.collection.create_index([index_spec])
                except Exception as e:
                    # Index might already exist, that's okay
                    logger.debug(f"Index creation skipped (might exist): {e}")
            
            logger.info("MongoDB metrics indexes created successfully")
        except Exception as e:
            logger.error(f"Failed to create MongoDB indexes: {e}")
            raise
    
    async def insert_metric(self, metric: MetricTuple) -> str:
        """Insert a single metric tuple."""
        if not self.collection:
            raise RuntimeError("Database not connected")
        
        metric_id = str(uuid4())
        
        document = {
            "_id": metric_id,
            "attributes": metric.attributes,
            "values": metric.values,
            "timestamp": metric.timestamp,
            "created_at": datetime.utcnow()
        }
        
        try:
            await self.collection.insert_one(document)
            logger.debug(f"Inserted metric with ID: {metric_id}")
            return metric_id
        except Exception as e:
            logger.error(f"Failed to insert metric: {e}")
            raise
    
    async def insert_metrics_batch(self, metrics: List[MetricTuple]) -> List[str]:
        """Insert multiple metric tuples."""
        if not self.collection:
            raise RuntimeError("Database not connected")
        
        metric_ids = [str(uuid4()) for _ in metrics]
        
        documents = [
            {
                "_id": metric_ids[i],
                "attributes": metric.attributes,
                "values": metric.values,
                "timestamp": metric.timestamp,
                "created_at": datetime.utcnow()
            }
            for i, metric in enumerate(metrics)
        ]
        
        try:
            await self.collection.insert_many(documents)
            logger.info(f"Inserted {len(metrics)} metrics in batch")
            return metric_ids
        except Exception as e:
            logger.error(f"Failed to insert metrics batch: {e}")
            raise
    
    def _build_mongo_filter(self, filters: QueryFilter) -> Dict[str, Any]:
        """Build MongoDB filter from QueryFilter."""
        mongo_filter = {}
        
        # Add time range filter
        if filters.time_range:
            start_time, end_time = filters.time_range
            mongo_filter["timestamp"] = {
                "$gte": start_time,
                "$lte": end_time
            }
        
        # Add attribute filters
        if filters.attributes:
            for key, value in filters.attributes.items():
                mongo_filter[f"attributes.{key}"] = value
        
        # Add value filters
        if filters.value_filters:
            for value_key, conditions in filters.value_filters.items():
                for operator, threshold in conditions.items():
                    # Convert our operator format to MongoDB operators
                    mongo_op = operator.replace("$", "$")  # Already in correct format
                    mongo_filter[f"values.{value_key}"] = {mongo_op: threshold}
        
        return mongo_filter
    
    async def query_metrics(self, filters: QueryFilter) -> List[MetricTuple]:
        """Query metrics based on filter criteria."""
        if not self.collection:
            raise RuntimeError("Database not connected")
        
        try:
            mongo_filter = self._build_mongo_filter(filters)
            
            # Build sort criteria
            sort_criteria = []
            if filters.sort_by:
                sort_direction = -1 if filters.sort_order == "desc" else 1
                sort_criteria.append((filters.sort_by, sort_direction))
            else:
                sort_criteria.append(("timestamp", -1))  # Default: newest first
            
            # Execute query
            cursor = self.collection.find(mongo_filter)
            
            if sort_criteria:
                cursor = cursor.sort(sort_criteria)
            
            if filters.limit:
                cursor = cursor.limit(filters.limit)
            
            documents = await cursor.to_list(length=filters.limit)
            
            # Convert documents to MetricTuple objects
            results = []
            for doc in documents:
                results.append(MetricTuple(
                    attributes=doc["attributes"],
                    values=doc["values"],
                    timestamp=doc["timestamp"]
                ))
            
            logger.debug(f"Query returned {len(results)} metrics")
            return results
            
        except Exception as e:
            logger.error(f"Failed to query metrics: {e}")
            raise
    
    async def aggregate_metrics(self, aggregation_query: AggregationQuery) -> List[Dict[str, Any]]:
        """Perform aggregations on metrics data using MongoDB aggregation pipeline."""
        if not self.collection:
            raise RuntimeError("Database not connected")
        
        try:
            pipeline = []
            
            # Add match stage for filtering
            if aggregation_query.filters:
                mongo_filter = self._build_mongo_filter(aggregation_query.filters)
                if mongo_filter:
                    pipeline.append({"$match": mongo_filter})
            
            # Build group stage
            group_id = {}
            for field in aggregation_query.group_by:
                # Handle nested fields (e.g., "attributes.category")
                if field.startswith("attributes."):
                    group_id[field.replace("attributes.", "")] = f"${field}"
                else:
                    group_id[field] = f"$attributes.{field}"
            
            group_stage = {"_id": group_id}
            
            # Add aggregation operations
            for field, operation in aggregation_query.aggregations.items():
                value_field = f"$values.{field}"
                
                if operation == "sum":
                    group_stage[f"{operation}_{field}"] = {"$sum": value_field}
                elif operation == "avg":
                    group_stage[f"{operation}_{field}"] = {"$avg": value_field}
                elif operation == "count":
                    group_stage[f"{operation}_{field}"] = {"$sum": 1}
                elif operation == "max":
                    group_stage[f"{operation}_{field}"] = {"$max": value_field}
                elif operation == "min":
                    group_stage[f"{operation}_{field}"] = {"$min": value_field}
            
            pipeline.append({"$group": group_stage})
            
            # Execute aggregation
            cursor = self.collection.aggregate(pipeline)
            documents = await cursor.to_list(length=None)
            
            # Convert results to the expected format
            results = []
            for doc in documents:
                result = {}
                
                # Add group by fields
                if doc["_id"]:
                    for key, value in doc["_id"].items():
                        result[key] = value
                
                # Add aggregation results
                for key, value in doc.items():
                    if key != "_id":
                        result[key] = value
                
                results.append(result)
            
            logger.debug(f"Aggregation returned {len(results)} groups")
            return results
            
        except Exception as e:
            logger.error(f"Failed to aggregate metrics: {e}")
            raise

    async def count_metrics(self, filters: QueryFilter) -> int:
        """Count metrics matching the filter criteria."""
        if not self.collection:
            raise RuntimeError("Database not connected")
        
        try:
            mongo_filter = self._build_mongo_filter(filters)
            count = await self.collection.count_documents(mongo_filter)
            
            logger.debug(f"Count query returned {count} metrics")
            return count
            
        except Exception as e:
            logger.error(f"Failed to count metrics: {e}")
            raise

    async def distinct_values(self, field: str, filters: Optional[QueryFilter] = None) -> List[Any]:
        """Get distinct values for a field."""
        if not self.collection:
            raise RuntimeError("Database not connected")
        
        try:
            mongo_filter = self._build_mongo_filter(filters) if filters else {}
            
            # Handle nested field access
            mongo_field = field
            if field.startswith("attributes.") or field.startswith("values."):
                mongo_field = field
            elif field == "timestamp":
                mongo_field = "timestamp"
            else:
                # Assume it's an attribute field
                mongo_field = f"attributes.{field}"
            
            distinct_values = await self.collection.distinct(mongo_field, mongo_filter)
            
            logger.debug(f"Distinct values query returned {len(distinct_values)} unique values")
            return distinct_values
            
        except Exception as e:
            logger.error(f"Failed to get distinct values: {e}")
            raise

    async def execute_native_query(self, query: DatabaseQuery) -> List[Dict[str, Any]]:
        """Execute database-specific native queries (aggregation pipelines for MongoDB)."""
        if not self.collection:
            raise RuntimeError("Database not connected")
        
        try:
            if query.native_query and "pipeline" in query.native_query:
                # Execute MongoDB aggregation pipeline
                pipeline = query.native_query["pipeline"]
                cursor = self.collection.aggregate(pipeline)
                documents = await cursor.to_list(length=None)
                
                # Convert to the expected format
                results = []
                for doc in documents:
                    # Convert ObjectId to string if present
                    if "_id" in doc and hasattr(doc["_id"], "__str__"):
                        doc["_id"] = str(doc["_id"])
                    
                    # Convert datetime objects to ISO format
                    if "timestamp" in doc and hasattr(doc["timestamp"], "isoformat"):
                        doc["timestamp"] = doc["timestamp"].isoformat()
                    if "created_at" in doc and hasattr(doc["created_at"], "isoformat"):
                        doc["created_at"] = doc["created_at"].isoformat()
                    
                    results.append(doc)
                
                logger.debug(f"Native aggregation pipeline returned {len(results)} documents")
                return results
            else:
                # Convert generic query to MongoDB operations
                if query.operation == "find":
                    metrics = await self.query_metrics(query.filters or QueryFilter())
                    return [
                        {
                            "attributes": metric.attributes,
                            "values": metric.values,
                            "timestamp": metric.timestamp.isoformat()
                        }
                        for metric in metrics
                    ]
                elif query.operation == "aggregate" and query.aggregation:
                    return await self.aggregate_metrics(query.aggregation)
                elif query.operation == "count":
                    count = await self.count_metrics(query.filters or QueryFilter())
                    return [{"count": count}]
                elif query.operation == "distinct" and query.projection:
                    field = query.projection[0] if query.projection else "timestamp"
                    values = await self.distinct_values(field, query.filters)
                    return [{"distinct_values": values}]
                else:
                    raise ValueError(f"Unsupported operation: {query.operation}")
                    
        except Exception as e:
            logger.error(f"Failed to execute native query: {e}")
            raise

    async def get_schema_info(self) -> Dict[str, Any]:
        """Get information about available collections and their structure."""
        if not self.database:
            raise RuntimeError("Database not connected")
        
        try:
            # Get collection stats
            stats = await self.database.command("collStats", self.collection_name)
            
            # Get sample document to infer schema
            sample_doc = await self.collection.find_one()
            
            schema_info = {
                "database_type": "mongodb",
                "database_name": self.database_name,
                "collections": {
                    self.collection_name: {
                        "document_count": stats.get("count", 0),
                        "size_bytes": stats.get("size", 0),
                        "indexes": []
                    }
                }
            }
            
            # Get index information
            indexes = await self.collection.list_indexes().to_list(length=None)
            for index in indexes:
                schema_info["collections"][self.collection_name]["indexes"].append({
                    "name": index.get("name", ""),
                    "key": index.get("key", {}),
                    "unique": index.get("unique", False)
                })
            
            # Add sample document structure if available
            if sample_doc:
                schema_info["collections"][self.collection_name]["sample_structure"] = {
                    "attributes": sample_doc.get("attributes", {}),
                    "values": sample_doc.get("values", {}),
                    "timestamp": "datetime",
                    "created_at": "datetime"
                }
            
            return schema_info
            
        except Exception as e:
            logger.error(f"Failed to get schema info: {e}")
            raise

    async def explain_query(self, query: DatabaseQuery) -> Dict[str, Any]:
        """Explain query execution plan for optimization."""
        if not self.collection:
            raise RuntimeError("Database not connected")
        
        try:
            explain_result = {
                "database_type": "mongodb",
                "collection": self.collection_name,
                "query_type": "find"
            }
            
            if query.native_query and "pipeline" in query.native_query:
                # Explain aggregation pipeline
                pipeline = query.native_query["pipeline"]
                explain_info = await self.collection.aggregate(pipeline).explain()
                explain_result.update({
                    "query_type": "aggregate",
                    "pipeline": pipeline,
                    "explain_info": explain_info
                })
            else:
                # Use a basic find operation for explanation
                mongo_filter = {}
                if query.filters:
                    mongo_filter = self._build_mongo_filter(query.filters)
                
                cursor = self.collection.find(mongo_filter).limit(1)
                explain_info = await cursor.explain()
                
                explain_result.update({
                    "filter": mongo_filter,
                    "execution_stats": explain_info.get("executionStats", {}),
                    "query_planner": explain_info.get("queryPlanner", {}),
                    "server_info": explain_info.get("serverInfo", {})
                })
            
            return explain_result
            
        except Exception as e:
            logger.error(f"Failed to explain query: {e}")
            raise

    async def update_metric(self, metric_id: str, updates: Dict[str, Any]) -> bool:
        """Update a metric by ID."""
        if not self.collection:
            raise RuntimeError("Database not connected")
        
        try:
            # Build update document
            update_doc = {}
            
            if "attributes" in updates:
                for key, value in updates["attributes"].items():
                    update_doc[f"attributes.{key}"] = value
            
            if "values" in updates:
                for key, value in updates["values"].items():
                    update_doc[f"values.{key}"] = value
            
            if not update_doc:
                logger.warning("No valid updates provided")
                return False
            
            # Perform the update
            result = await self.collection.update_one(
                {"_id": metric_id},
                {"$set": update_doc}
            )
            
            updated = result.modified_count > 0
            if updated:
                logger.debug(f"Updated metric with ID: {metric_id}")
            else:
                logger.warning(f"Metric with ID {metric_id} not found or no changes made")
            
            return updated
            
        except Exception as e:
            logger.error(f"Failed to update metric: {e}")
            raise

    async def delete_metric(self, metric_id: str) -> bool:
        """Delete a metric by ID."""
        if not self.collection:
            raise RuntimeError("Database not connected")
        
        try:
            result = await self.collection.delete_one({"_id": metric_id})
            
            deleted = result.deleted_count > 0
            if deleted:
                logger.debug(f"Deleted metric with ID: {metric_id}")
            else:
                logger.warning(f"Metric with ID {metric_id} not found")
            
            return deleted
            
        except Exception as e:
            logger.error(f"Failed to delete metric: {e}")
            raise

    async def delete_metrics(self, filters: QueryFilter) -> int:
        """Delete metrics matching the filter criteria."""
        if not self.collection:
            raise RuntimeError("Database not connected")
        
        try:
            mongo_filter = self._build_mongo_filter(filters)
            
            if not mongo_filter:
                logger.warning("Delete operation with empty filter - this would delete all documents")
                return 0
            
            result = await self.collection.delete_many(mongo_filter)
            delete_count = result.deleted_count
            
            logger.info(f"Deleted {delete_count} metrics")
            return delete_count
            
        except Exception as e:
            logger.error(f"Failed to delete metrics: {e}")
            raise

    async def health_check(self) -> bool:
        """Check if the database connection is healthy."""
        if not self.client:
            return False
        
        try:
            await self.client.admin.command('ping')
            return True
        except Exception as e:
            logger.error(f"MongoDB health check failed: {e}")
            return False 