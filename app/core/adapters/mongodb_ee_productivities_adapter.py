"""MongoDB adapter for ee-productivities database with specific collection support."""

import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from uuid import uuid4
import motor.motor_asyncio
from bson import ObjectId

from app.core.database_abstraction import MetricsAdapter, MetricTuple, QueryFilter, DatabaseConfig, AggregationQuery, DatabaseQuery
from app.utils.logging import logger


class MongoDBEEProductivitiesAdapter(MetricsAdapter):
    """MongoDB implementation for ee-productivities database with specific collection support."""
    
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
    
    async def create_schema(self) -> None:
        """Create necessary indexes for the collection."""
        if self.collection is None:
            raise RuntimeError("No collection selected. Use switch_collection() to select a collection first.")
        
        try:
            # Create indexes based on the collection type
            indexes = self._get_collection_indexes(self.collection_name)
            
            for index_spec in indexes:
                try:
                    await self.collection.create_index(index_spec)
                except Exception as e:
                    # Index might already exist, that's okay
                    logger.debug(f"Index creation skipped (might exist): {e}")
            
            logger.info(f"MongoDB indexes created for {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to create MongoDB indexes: {e}")
            raise
    
    def _get_collection_indexes(self, collection_name: str) -> List:
        """Get appropriate indexes for each collection."""
        if collection_name == "application_snapshot":
            return [
                [("year", 1), ("month", 1)],
                [("application.csiId", 1)],
                [("application.criticality", 1)],
                [("status", 1)],
                [("sector", 1)],
                [("name", 1)],
                [("organization", 1)]
            ]
        elif collection_name == "employee_ratio":
            return [
                [("soeId", 1)],
                [("employeeRatioSnapshot.year", 1), ("employeeRatioSnapshot.month", 1)],
                [("toolsAdoptionRatioSnapshot.year", 1), ("toolsAdoptionRatioSnapshot.month", 1)]
            ]
        elif collection_name == "employee_tree_archived":
            return [
                [("soeId", 1)],
                [("year", 1), ("month", 1)],
                [("hierarchy", 1)],
                [("archivedKey", 1)],
                [("parentSoeId", 1)]
            ]
        elif collection_name == "enabler_csi_snapshots":
            return [
                [("csiId", 1)],
                [("enablersAggregation.year", 1), ("enablersAggregation.month", 1)]
            ]
        elif collection_name == "management_segment_tree":
            return [
                [("name", 1)],
                [("year", 1), ("month", 1)],
                [("hierarchy", 1)],
                [("path", 1)],
                [("parent", 1)]
            ]
        elif collection_name == "statistic":
            return [
                [("nativeID", 1)],
                [("nativeIDType", 1)],
                [("statistics.year", 1), ("statistics.month", 1)]
            ]
        else:
            return []
    
    async def insert_metric(self, metric: MetricTuple) -> str:
        """Insert a single metric tuple."""
        if self.collection is None:
            raise RuntimeError("No collection selected. Use switch_collection() to select a collection first.")
        
        metric_id = str(uuid4())
        
        # Convert MetricTuple to appropriate document format based on collection
        document = self._convert_metric_to_document(metric, metric_id)
        
        try:
            await self.collection.insert_one(document)
            logger.debug(f"Inserted metric with ID: {metric_id}")
            return metric_id
        except Exception as e:
            logger.error(f"Failed to insert metric: {e}")
            raise
    
    def _convert_metric_to_document(self, metric: MetricTuple, metric_id: str) -> Dict[str, Any]:
        """Convert MetricTuple to appropriate document format for the collection."""
        base_document = {
            "_id": metric_id,
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }
        
        if self.collection_name == "application_snapshot":
            # Convert generic metric to application snapshot format
            return {
                **base_document,
                "year": metric.attributes.get("year", datetime.utcnow().year),
                "month": metric.attributes.get("month", datetime.utcnow().month),
                "application": {
                    "csiId": metric.attributes.get("csiId", 0),
                    "criticality": metric.attributes.get("criticality", "Medium")
                },
                "name": metric.attributes.get("name", "Unknown Application"),
                "status": metric.attributes.get("status", "Active"),
                "sector": metric.attributes.get("sector", "Technology"),
                "type": metric.attributes.get("type", "Web Application"),
                "organization": metric.attributes.get("organization", "Default Org"),
                "isRetired": metric.attributes.get("isRetired", False),
                "developmentModel": metric.attributes.get("developmentModel", "Agile"),
                "hostingModel": metric.attributes.get("hostingModel", "Cloud")
            }
        elif self.collection_name == "employee_ratio":
            return {
                **base_document,
                "soeId": metric.attributes.get("soeId", f"SOE{metric_id[:8]}"),
                "employeeRatioSnapshot": metric.values.get("employeeRatioSnapshot", []),
                "toolsAdoptionRatioSnapshot": metric.values.get("toolsAdoptionRatioSnapshot", [])
            }
        elif self.collection_name == "employee_tree_archived":
            return {
                **base_document,
                "soeId": metric.attributes.get("soeId", f"SOE{metric_id[:8]}"),
                "year": metric.attributes.get("year", datetime.utcnow().year),
                "month": metric.attributes.get("month", datetime.utcnow().month),
                "hierarchy": metric.attributes.get("hierarchy", 1),
                "employeeNum": metric.values.get("employeeNum", 0),
                "engineerNum": metric.values.get("engineerNum", 0),
                "totalNum": metric.values.get("totalNum", 0)
            }
        elif self.collection_name == "enabler_csi_snapshots":
            return {
                **base_document,
                "csiId": metric.attributes.get("csiId", f"CSI{metric_id[:8]}"),
                "enablersAggregation": metric.values.get("enablersAggregation", [])
            }
        elif self.collection_name == "mangement_segment_tree":
            return {
                **base_document,
                "name": metric.attributes.get("name", f"Segment_{metric_id[:8]}"),
                "year": metric.attributes.get("year", datetime.utcnow().year),
                "month": metric.attributes.get("month", datetime.utcnow().month),
                "hierarchy": metric.attributes.get("hierarchy", 1),
                "path": metric.attributes.get("path", []),
                "version": metric.attributes.get("version", "v1.0")
            }
        elif self.collection_name == "statistic":
            return {
                **base_document,
                "nativeID": metric.attributes.get("nativeID", f"NATIVE_{metric_id[:8]}"),
                "nativeIDType": metric.attributes.get("nativeIDType", "Application"),
                "statistics": metric.values.get("statistics", [])
            }
        else:
            # Generic format for unknown collections
            return {
                **base_document,
                "attributes": metric.attributes,
                "values": metric.values,
                "timestamp": metric.timestamp
            }
    
    async def insert_metrics_batch(self, metrics: List[MetricTuple]) -> List[str]:
        """Insert multiple metric tuples."""
        if self.collection is None:
            raise RuntimeError("Database not connected")
        
        metric_ids = [str(uuid4()) for _ in metrics]
        
        documents = [
            self._convert_metric_to_document(metric, metric_ids[i])
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
            raise RuntimeError("Database not connected")
        
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
            elif self.collection_name == "employeed_ratio":
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
            raise RuntimeError("Database not connected")
        
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
                    if "createdAt" in doc and hasattr(doc["createdAt"], "isoformat"):
                        doc["createdAt"] = doc["createdAt"].isoformat()
                    if "updatedAt" in doc and hasattr(doc["updatedAt"], "isoformat"):
                        doc["updatedAt"] = doc["updatedAt"].isoformat()
                    
                    results.append(doc)
                
                logger.debug(f"Native aggregation pipeline returned {len(results)} documents")
                return results
            else:
                # Execute find query
                mongo_filter = query.native_query.get("filter", {})
                limit = query.native_query.get("limit", 100)
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
            raise RuntimeError("Database not connected")
        
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
            raise RuntimeError("Database not connected")
        
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
    
    async def update_metric(self, metric_id: str, updates: Dict[str, Any]) -> bool:
        """Update a metric by ID."""
        if self.collection is None:
            raise RuntimeError("Database not connected")
        
        try:
            # Add updatedAt timestamp
            updates["updatedAt"] = datetime.utcnow()
            
            result = await self.collection.update_one(
                {"_id": metric_id},
                {"$set": updates}
            )
            
            updated = result.modified_count > 0
            if updated:
                logger.debug(f"Updated metric with ID: {metric_id}")
            else:
                logger.warning(f"Metric with ID {metric_id} not found or not modified")
            
            return updated
            
        except Exception as e:
            logger.error(f"Failed to update metric: {e}")
            raise
    
    async def delete_metric(self, metric_id: str) -> bool:
        """Delete a metric by ID."""
        if self.collection is None:
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
        if self.collection is None:
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
            
            # Create indexes for the new collection
            await self.create_schema()
            
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