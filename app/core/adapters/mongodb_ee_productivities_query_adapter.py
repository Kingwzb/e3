"""MongoDB query adapter for ee-productivities database with read-only access."""

import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import motor.motor_asyncio
from bson import ObjectId

from app.core.database_abstraction import (
    MetricsQueryAdapter, MetricTuple, QueryFilter, DatabaseQuery, 
    AggregationQuery, DatabaseConfig
)
from app.utils.logging import logger


class MongoDBEEProductivitiesQueryAdapter(MetricsQueryAdapter):
    """MongoDB implementation for read-only querying of ee-productivities database."""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.connection_string = config.connection_params.get("connection_string")
        self.database_name = config.connection_params.get("database_name", "ee-productivities")
        self.collection_name = config.connection_params.get("collection_name", None)  # Allow None for dynamic collection switching
        
        self.client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
        self.database = None
        self.collection = None
        
        # Available collections in ee-productivities database (for reference only)
        self.available_collections = [
            "application_snapshot",
            "employee_ratio", 
            "employee_tree_archived",
            "enabler_csi_snapshots",
            "management_segment_tree",
            "statistic"
        ]
    
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
            # Only set collection if collection_name is provided
            if self.collection_name:
                self.collection = self.database[self.collection_name]
            else:
                self.collection = None  # Will be set when switching collections
            
            # Verify the database exists and has collections
            await self._verify_database()
            
            logger.info(f"Connected to MongoDB database: {self.database_name}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def _verify_database(self) -> None:
        """Verify that the ee-productivities database exists and log available collections."""
        try:
            collections = await self.database.list_collection_names()
            logger.info(f"Available collections in {self.database_name}: {collections}")
            
            # Log the current collection being used
            if self.collection_name:
                logger.info(f"Using collection: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to verify database: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close connection to MongoDB."""
        if self.client:
            self.client.close()
            self.client = None
            self.database = None
            self.collection = None
            logger.info("Disconnected from MongoDB")
    
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
                mongo_filter[key] = value
        
        # Add value filters
        if filters.value_filters:
            for value_key, conditions in filters.value_filters.items():
                for operator, threshold in conditions.items():
                    mongo_op = operator.replace("$", "$")
                    mongo_filter[value_key] = {mongo_op: threshold}
        
        return mongo_filter
    
    async def query_metrics(self, filters: QueryFilter) -> List[MetricTuple]:
        """Query metrics based on filter criteria."""
        if self.collection is None:
            raise RuntimeError("No collection selected. Use switch_collection() to select a collection first.")
        
        try:
            mongo_filter = self._build_mongo_filter(filters)
            
            # Build sort criteria
            sort_criteria = []
            if filters.sort_by:
                sort_direction = -1 if filters.sort_order == "desc" else 1
                sort_criteria.append((filters.sort_by, sort_direction))
            else:
                sort_criteria.append(("createdAt", -1))  # Default: newest first
            
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
                metric_tuple = self._convert_document_to_metric(doc)
                if metric_tuple:
                    results.append(metric_tuple)
            
            logger.debug(f"Query returned {len(results)} metrics")
            return results
            
        except Exception as e:
            logger.error(f"Failed to query metrics: {e}")
            raise
    
    def _convert_document_to_metric(self, doc: Dict[str, Any]) -> Optional[MetricTuple]:
        """Convert MongoDB document to MetricTuple."""
        try:
            from app.core.database_abstraction import MetricTuple
            
            # Extract attributes and values based on collection type
            if self.collection_name == "application_snapshot":
                attributes = {
                    "year": doc.get("year"),
                    "month": doc.get("month"),
                    "name": doc.get("name"),
                    "status": doc.get("status"),
                    "sector": doc.get("sector"),
                    "type": doc.get("type"),
                    "organization": doc.get("organization"),
                    "csiId": doc.get("application", {}).get("csiId") if doc.get("application") else None,
                    "criticality": doc.get("application", {}).get("criticality") if doc.get("application") else None
                }
                values = {
                    "isRetired": doc.get("isRetired", False),
                    "developmentModel": doc.get("developmentModel"),
                    "hostingModel": doc.get("hostingModel")
                }
            elif self.collection_name == "employee_ratio":
                attributes = {
                    "soeId": doc.get("soeId")
                }
                values = {
                    "employeeRatioSnapshot": doc.get("employeeRatioSnapshot", []),
                    "toolsAdoptionRatioSnapshot": doc.get("toolsAdoptionRatioSnapshot", [])
                }
            elif self.collection_name == "employee_tree_archived":
                attributes = {
                    "soeId": doc.get("soeId"),
                    "year": doc.get("year"),
                    "month": doc.get("month"),
                    "hierarchy": doc.get("hierarchy")
                }
                values = {
                    "employeeNum": doc.get("employeeNum", 0),
                    "engineerNum": doc.get("engineerNum", 0),
                    "totalNum": doc.get("totalNum", 0)
                }
            elif self.collection_name == "enabler_csi_snapshots":
                attributes = {
                    "csiId": doc.get("csiId")
                }
                values = {
                    "enablersAggregation": doc.get("enablersAggregation", [])
                }
            elif self.collection_name == "management_segment_tree":
                attributes = {
                    "name": doc.get("name"),
                    "year": doc.get("year"),
                    "month": doc.get("month"),
                    "hierarchy": doc.get("hierarchy")
                }
                values = {
                    "path": doc.get("path", []),
                    "version": doc.get("version")
                }
            elif self.collection_name == "statistic":
                attributes = {
                    "nativeID": doc.get("nativeID"),
                    "nativeIDType": doc.get("nativeIDType")
                }
                values = {
                    "statistics": doc.get("statistics", [])
                }
            else:
                # Generic conversion - include all fields as attributes and values
                # Remove common MongoDB fields and use the rest as attributes
                exclude_fields = {"_id", "createdAt", "updatedAt", "timestamp", "__v"}
                attributes = {}
                values = {}
                
                for key, value in doc.items():
                    if key not in exclude_fields:
                        # Try to categorize as attribute or value based on common patterns
                        if isinstance(value, (str, int, float, bool)) or value is None:
                            attributes[key] = value
                        else:
                            values[key] = value
            
            # Remove None values from attributes and values to keep them clean
            attributes = {k: v for k, v in attributes.items() if v is not None}
            values = {k: v for k, v in values.items() if v is not None}
            
            timestamp = doc.get("timestamp", doc.get("createdAt", datetime.utcnow()))
            
            return MetricTuple(
                attributes=attributes,
                values=values,
                timestamp=timestamp
            )
            
        except Exception as e:
            logger.error(f"Failed to convert document to MetricTuple: {e}")
            return None
    
    async def aggregate_metrics(self, aggregation_query: AggregationQuery) -> List[Dict[str, Any]]:
        """Perform aggregations on metrics data using MongoDB aggregation pipeline."""
        if self.collection is None:
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
                group_id[field] = f"${field}"
            
            group_stage = {"_id": group_id}
            
            # Add aggregation operations
            for field, operation in aggregation_query.aggregations.items():
                if operation == "sum":
                    group_stage[f"{operation}_{field}"] = {"$sum": f"${field}"}
                elif operation == "avg":
                    group_stage[f"{operation}_{field}"] = {"$avg": f"${field}"}
                elif operation == "count":
                    group_stage[f"{operation}_{field}"] = {"$sum": 1}
                elif operation == "max":
                    group_stage[f"{operation}_{field}"] = {"$max": f"${field}"}
                elif operation == "min":
                    group_stage[f"{operation}_{field}"] = {"$min": f"${field}"}
            
            pipeline.append({"$group": group_stage})
            
            # Execute aggregation
            cursor = self.collection.aggregate(pipeline)
            documents = await cursor.to_list(length=None)
            
            # Convert results to the expected format
            results = []
            for doc in documents:
                # Convert ObjectId to string if present
                if "_id" in doc and hasattr(doc["_id"], "__str__"):
                    doc["_id"] = str(doc["_id"])
                
                results.append(doc)
            
            logger.debug(f"Aggregation returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Failed to aggregate metrics: {e}")
            raise
    
    async def count_metrics(self, filters: QueryFilter) -> int:
        """Count metrics matching the filter criteria."""
        if self.collection is None:
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
        if self.collection is None:
            raise RuntimeError("No collection selected. Use switch_collection() to select a collection first.")
        
        try:
            mongo_filter = {}
            if filters:
                mongo_filter = self._build_mongo_filter(filters)
            
            distinct_values = await self.collection.distinct(field, mongo_filter)
            
            logger.debug(f"Distinct query for {field} returned {len(distinct_values)} values")
            return distinct_values
            
        except Exception as e:
            logger.error(f"Failed to get distinct values: {e}")
            raise
    
    async def execute_native_query(self, query: DatabaseQuery) -> List[Dict[str, Any]]:
        """Execute database-specific native queries (aggregation pipelines for MongoDB)."""
        if self.collection is None:
            raise RuntimeError("No collection selected. Use switch_collection() to select a collection first.")
        
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
                    if "createdAt" in doc and hasattr(doc["createdAt"], "isoformat"):
                        doc["createdAt"] = doc["createdAt"].isoformat()
                    if "updatedAt" in doc and hasattr(doc["updatedAt"], "isoformat"):
                        doc["updatedAt"] = doc["updatedAt"].isoformat()
                    
                    results.append(doc)
                
                logger.debug(f"Native aggregation pipeline returned {len(results)} documents")
                return results
            else:
                # Execute find query
                mongo_filter = query.native_query.get("filter", {}) if query.native_query else {}
                limit = query.native_query.get("limit", 100) if query.native_query else 100
                cursor = self.collection.find(mongo_filter)
                
                if limit:
                    cursor = cursor.limit(limit)
                
                documents = await cursor.to_list(length=limit)
                
                # Convert to the expected format
                results = []
                for doc in documents:
                    # Convert ObjectId to string if present
                    if "_id" in doc and hasattr(doc["_id"], "__str__"):
                        doc["_id"] = str(doc["_id"])
                    
                    results.append(doc)
                
                logger.debug(f"Native find query returned {len(results)} documents")
                return results
                
        except Exception as e:
            logger.error(f"Failed to execute native query: {e}")
            raise
    
    async def get_schema_info(self) -> Dict[str, Any]:
        """Get schema information for the current collection."""
        if self.collection is None:
            raise RuntimeError("No collection selected. Use switch_collection() to select a collection first.")
        
        try:
            # Get collection stats
            stats = await self.database.command("collStats", self.collection_name)
            
            # Get index information
            indexes = await self.collection.list_indexes().to_list(length=None)
            
            # Get sample document for schema inference
            sample_doc = await self.collection.find_one()
            
            schema_info = {
                "collection_name": self.collection_name,
                "database_name": self.database_name,
                "document_count": stats.get("count", 0),
                "storage_size": stats.get("size", 0),
                "indexes": [{"name": idx["name"], "key": idx["key"]} for idx in indexes],
                "sample_document": sample_doc
            }
            
            logger.debug(f"Retrieved schema info for {self.collection_name}")
            return schema_info
            
        except Exception as e:
            logger.error(f"Failed to get schema info: {e}")
            raise
    
    async def explain_query(self, query: DatabaseQuery) -> Dict[str, Any]:
        """Explain query execution plan."""
        if self.collection is None:
            raise RuntimeError("No collection selected. Use switch_collection() to select a collection first.")
        
        try:
            if query.native_query and "pipeline" in query.native_query:
                # Explain aggregation pipeline
                pipeline = query.native_query["pipeline"]
                explanation = await self.collection.aggregate(pipeline).explain()
            else:
                # Explain find query
                mongo_filter = query.native_query.get("filter", {}) if query.native_query else {}
                explanation = await self.collection.find(mongo_filter).explain()
            
            logger.debug(f"Query explanation generated for {self.collection_name}")
            return explanation
            
        except Exception as e:
            logger.error(f"Failed to explain query: {e}")
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
    
    async def switch_collection(self, collection_name: str) -> None:
        """Switch to a different collection within the same database."""
        try:
            # Verify the collection exists
            collections = await self.database.list_collection_names()
            if collection_name not in collections:
                logger.warning(f"Collection {collection_name} not found. Available collections: {collections}")
                # Still allow switching, as the collection might be created later
            
            self.collection_name = collection_name
            self.collection = self.database[collection_name]
            
            logger.info(f"Switched to collection: {collection_name}")
        except Exception as e:
            logger.error(f"Failed to switch to collection {collection_name}: {e}")
            raise
    
    async def list_collections(self) -> List[str]:
        """List all available collections in the database."""
        try:
            collections = await self.database.list_collection_names()
            return collections
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            raise
    
    async def get_collection_stats(self, collection_name: str = None) -> Dict[str, Any]:
        """Get statistics for a specific collection or current collection."""
        if self.database is None:
            raise RuntimeError("Database not connected")
        
        try:
            target_collection = collection_name or self.collection_name
            stats = await self.database.command("collStats", target_collection)
            
            # Get index information
            collection = self.database[target_collection]
            indexes = await collection.list_indexes().to_list(length=None)
            
            return {
                "collection_name": target_collection,
                "document_count": stats.get("count", 0),
                "storage_size": stats.get("size", 0),
                "avg_document_size": stats.get("avgObjSize", 0),
                "indexes": [{"name": idx["name"], "key": idx["key"]} for idx in indexes]
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            raise 