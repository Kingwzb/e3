"""SQLite adapter for metrics storage with generic database interface."""

import json
import sqlite3
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import aiosqlite
from uuid import uuid4

from app.core.database_abstraction import MetricsAdapter, MetricTuple, QueryFilter, DatabaseConfig, AggregationQuery, DatabaseQuery
from app.utils.logging import logger


class SQLiteMetricsAdapter(MetricsAdapter):
    """SQLite implementation of the metrics adapter with generic interface."""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.db_path = config.connection_params.get("database_path", "./metrics.db")
        self.connection: Optional[aiosqlite.Connection] = None
    
    async def connect(self) -> None:
        """Establish connection to SQLite database."""
        try:
            self.connection = await aiosqlite.connect(self.db_path)
            await self.connection.execute("PRAGMA foreign_keys = ON")
            await self.connection.commit()
            
            # Create schema if it doesn't exist
            await self.create_schema()
            
            logger.info(f"Connected to SQLite database at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to connect to SQLite database: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close connection to SQLite database."""
        if self.connection:
            await self.connection.close()
            self.connection = None
            logger.info("Disconnected from SQLite database")
    
    async def create_schema(self) -> None:
        """Create the metrics table schema."""
        if not self.connection:
            raise RuntimeError("Database not connected")
        
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS metrics (
            id TEXT PRIMARY KEY,
            attributes TEXT NOT NULL,
            metric_values TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # Create indexes for better query performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_metrics_created_at ON metrics(created_at)"
        ]
        
        try:
            await self.connection.execute(create_table_sql)
            for index_sql in indexes:
                await self.connection.execute(index_sql)
            await self.connection.commit()
            logger.info("SQLite metrics schema created successfully")
        except Exception as e:
            logger.error(f"Failed to create SQLite schema: {e}")
            raise
    
    async def insert_metric(self, metric: MetricTuple) -> str:
        """Insert a single metric tuple."""
        if not self.connection:
            raise RuntimeError("Database not connected")
        
        metric_id = str(uuid4())
        
        try:
            await self.connection.execute(
                """
                INSERT INTO metrics (id, attributes, metric_values, timestamp)
                VALUES (?, ?, ?, ?)
                """,
                (
                    metric_id,
                    json.dumps(metric.attributes),
                    json.dumps(metric.values),
                    metric.timestamp.isoformat()
                )
            )
            await self.connection.commit()
            logger.debug(f"Inserted metric with ID: {metric_id}")
            return metric_id
        except Exception as e:
            logger.error(f"Failed to insert metric: {e}")
            raise
    
    async def insert_metrics_batch(self, metrics: List[MetricTuple]) -> List[str]:
        """Insert multiple metric tuples."""
        if not self.connection:
            raise RuntimeError("Database not connected")
        
        metric_ids = [str(uuid4()) for _ in metrics]
        
        try:
            data = [
                (
                    metric_ids[i],
                    json.dumps(metric.attributes),
                    json.dumps(metric.values),
                    metric.timestamp.isoformat()
                )
                for i, metric in enumerate(metrics)
            ]
            
            await self.connection.executemany(
                """
                INSERT INTO metrics (id, attributes, metric_values, timestamp)
                VALUES (?, ?, ?, ?)
                """,
                data
            )
            await self.connection.commit()
            logger.info(f"Inserted {len(metrics)} metrics in batch")
            return metric_ids
        except Exception as e:
            logger.error(f"Failed to insert metrics batch: {e}")
            raise
    
    async def query_metrics(self, filters: QueryFilter) -> List[MetricTuple]:
        """Query metrics based on filter criteria."""
        if not self.connection:
            raise RuntimeError("Database not connected")
        
        try:
            query_parts = ["SELECT attributes, metric_values, timestamp FROM metrics WHERE 1=1"]
            params = []
            
            # Add time range filter
            if filters.time_range:
                start_time, end_time = filters.time_range
                query_parts.append("AND timestamp >= ? AND timestamp <= ?")
                params.extend([start_time.isoformat(), end_time.isoformat()])
            
            # Add sorting
            if filters.sort_by:
                order = "DESC" if filters.sort_order == "desc" else "ASC"
                if filters.sort_by == "timestamp":
                    query_parts.append(f"ORDER BY timestamp {order}")
            else:
                query_parts.append("ORDER BY timestamp DESC")
            
            # Add limit
            if filters.limit:
                query_parts.append("LIMIT ?")
                params.append(filters.limit)
            
            query = " ".join(query_parts)
            
            cursor = await self.connection.execute(query, params)
            rows = await cursor.fetchall()
            
            results = []
            for row in rows:
                attributes = json.loads(row[0])
                values = json.loads(row[1])
                timestamp = datetime.fromisoformat(row[2])
                
                # Apply attribute filters in Python (for complex filtering)
                if filters.attributes:
                    match = True
                    for key, value in filters.attributes.items():
                        if key not in attributes or attributes[key] != value:
                            match = False
                            break
                    if not match:
                        continue
                
                # Apply value filters
                if filters.value_filters:
                    match = True
                    for value_key, conditions in filters.value_filters.items():
                        if value_key not in values:
                            match = False
                            break
                        
                        value = values[value_key]
                        for operator, threshold in conditions.items():
                            if operator == "$gte" and value < threshold:
                                match = False
                                break
                            elif operator == "$lte" and value > threshold:
                                match = False
                                break
                            elif operator == "$gt" and value <= threshold:
                                match = False
                                break
                            elif operator == "$lt" and value >= threshold:
                                match = False
                                break
                            elif operator == "$eq" and value != threshold:
                                match = False
                                break
                    if not match:
                        continue
                
                results.append(MetricTuple(
                    attributes=attributes,
                    values=values,
                    timestamp=timestamp
                ))
            
            logger.debug(f"Query returned {len(results)} metrics")
            return results
            
        except Exception as e:
            logger.error(f"Failed to query metrics: {e}")
            raise
    
    async def aggregate_metrics(self, aggregation_query: AggregationQuery) -> List[Dict[str, Any]]:
        """Perform aggregations on metrics data."""
        if not self.connection:
            raise RuntimeError("Database not connected")
        
        try:
            # First, get all matching metrics
            metrics = await self.query_metrics(aggregation_query.filters or QueryFilter())
            
            # Group metrics by the specified fields
            groups = {}
            for metric in metrics:
                # Create group key based on attributes
                group_key = tuple(
                    str(metric.attributes.get(field, "")) for field in aggregation_query.group_by
                )
                
                if group_key not in groups:
                    groups[group_key] = []
                groups[group_key].append(metric)
            
            # Perform aggregations for each group
            results = []
            for group_key, group_metrics in groups.items():
                result = {}
                
                # Add group by fields to result
                for i, field in enumerate(aggregation_query.group_by):
                    result[field] = group_key[i] if group_key[i] else None
                
                # Perform aggregations
                for field, operation in aggregation_query.aggregations.items():
                    values = []
                    for metric in group_metrics:
                        if field in metric.values:
                            values.append(metric.values[field])
                    
                    if not values:
                        result[f"{operation}_{field}"] = None
                        continue
                    
                    if operation == "sum":
                        result[f"{operation}_{field}"] = sum(values)
                    elif operation == "avg":
                        result[f"{operation}_{field}"] = sum(values) / len(values)
                    elif operation == "count":
                        result[f"{operation}_{field}"] = len(values)
                    elif operation == "max":
                        result[f"{operation}_{field}"] = max(values)
                    elif operation == "min":
                        result[f"{operation}_{field}"] = min(values)
                
                results.append(result)
            
            logger.debug(f"Aggregation returned {len(results)} groups")
            return results
            
        except Exception as e:
            logger.error(f"Failed to aggregate metrics: {e}")
            raise

    async def count_metrics(self, filters: QueryFilter) -> int:
        """Count metrics matching the filter criteria."""
        if not self.connection:
            raise RuntimeError("Database not connected")
        
        try:
            query_parts = ["SELECT COUNT(*) FROM metrics WHERE 1=1"]
            params = []
            
            # Add time range filter
            if filters.time_range:
                start_time, end_time = filters.time_range
                query_parts.append("AND timestamp >= ? AND timestamp <= ?")
                params.extend([start_time.isoformat(), end_time.isoformat()])
            
            query = " ".join(query_parts)
            cursor = await self.connection.execute(query, params)
            result = await cursor.fetchone()
            
            count = result[0] if result else 0
            
            # For attribute and value filters, we need to count in Python
            if filters.attributes or filters.value_filters:
                metrics = await self.query_metrics(filters)
                count = len(metrics)
            
            logger.debug(f"Count query returned {count} metrics")
            return count
            
        except Exception as e:
            logger.error(f"Failed to count metrics: {e}")
            raise

    async def distinct_values(self, field: str, filters: Optional[QueryFilter] = None) -> List[Any]:
        """Get distinct values for a field."""
        if not self.connection:
            raise RuntimeError("Database not connected")
        
        try:
            # For SQLite, we'll get all metrics and extract distinct values in Python
            metrics = await self.query_metrics(filters or QueryFilter())
            
            distinct_values = set()
            for metric in metrics:
                # Handle nested field access (e.g., "attributes.category")
                if field.startswith("attributes."):
                    attr_field = field.replace("attributes.", "")
                    if attr_field in metric.attributes:
                        distinct_values.add(metric.attributes[attr_field])
                elif field.startswith("values."):
                    value_field = field.replace("values.", "")
                    if value_field in metric.values:
                        distinct_values.add(metric.values[value_field])
                elif field == "timestamp":
                    distinct_values.add(metric.timestamp.isoformat())
            
            result = list(distinct_values)
            logger.debug(f"Distinct values query returned {len(result)} unique values")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get distinct values: {e}")
            raise

    async def execute_native_query(self, query: DatabaseQuery) -> List[Dict[str, Any]]:
        """Execute database-specific native queries (SQL for SQLite)."""
        if not self.connection:
            raise RuntimeError("Database not connected")
        
        try:
            if query.native_query and "sql" in query.native_query:
                # Execute raw SQL
                sql = query.native_query["sql"]
                params = query.native_query.get("params", [])
                
                # Safety check - only allow SELECT statements
                if not sql.strip().upper().startswith("SELECT"):
                    raise ValueError("Only SELECT statements are allowed in native queries")
                
                if params:
                    cursor = await self.connection.execute(sql, params)
                else:
                    cursor = await self.connection.execute(sql)
                
                rows = await cursor.fetchall()
                
                # Get column names
                column_names = [description[0] for description in cursor.description] if cursor.description else []
                
                # Convert rows to dictionaries
                results = []
                for row in rows:
                    result = {}
                    for i, value in enumerate(row):
                        if i < len(column_names):
                            result[column_names[i]] = value
                    results.append(result)
                
                logger.debug(f"Native SQL query returned {len(results)} rows")
                return results
            else:
                # Convert generic query to SQL and execute
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
                else:
                    raise ValueError(f"Unsupported operation: {query.operation}")
                    
        except Exception as e:
            logger.error(f"Failed to execute native query: {e}")
            raise

    async def get_schema_info(self) -> Dict[str, Any]:
        """Get information about available tables, fields, and their types."""
        if not self.connection:
            raise RuntimeError("Database not connected")
        
        try:
            # Get table info
            cursor = await self.connection.execute("PRAGMA table_info(metrics)")
            columns = await cursor.fetchall()
            
            schema_info = {
                "database_type": "sqlite",
                "tables": {
                    "metrics": {
                        "columns": []
                    }
                }
            }
            
            for column in columns:
                schema_info["tables"]["metrics"]["columns"].append({
                    "name": column[1],  # column name
                    "type": column[2],  # column type
                    "nullable": not column[3],  # not null flag
                    "primary_key": bool(column[5])  # primary key flag
                })
            
            return schema_info
            
        except Exception as e:
            logger.error(f"Failed to get schema info: {e}")
            raise

    async def explain_query(self, query: DatabaseQuery) -> Dict[str, Any]:
        """Explain query execution plan for optimization."""
        if not self.connection:
            raise RuntimeError("Database not connected")
        
        try:
            # For generic queries, we'll explain a basic SELECT
            sql = "SELECT * FROM metrics LIMIT 1"
            
            if query.native_query and "sql" in query.native_query:
                sql = query.native_query["sql"]
            
            # SQLite EXPLAIN QUERY PLAN
            cursor = await self.connection.execute(f"EXPLAIN QUERY PLAN {sql}")
            plan_rows = await cursor.fetchall()
            
            explain_result = {
                "database_type": "sqlite",
                "query": sql,
                "execution_plan": []
            }
            
            for row in plan_rows:
                explain_result["execution_plan"].append({
                    "id": row[0],
                    "parent": row[1],
                    "detail": row[3] if len(row) > 3 else str(row)
                })
            
            return explain_result
            
        except Exception as e:
            logger.error(f"Failed to explain query: {e}")
            raise

    async def update_metric(self, metric_id: str, updates: Dict[str, Any]) -> bool:
        """Update a metric by ID."""
        if not self.connection:
            raise RuntimeError("Database not connected")
        
        try:
            # Check if metric exists
            cursor = await self.connection.execute(
                "SELECT attributes, metric_values FROM metrics WHERE id = ?",
                (metric_id,)
            )
            row = await cursor.fetchone()
            
            if not row:
                logger.warning(f"Metric with ID {metric_id} not found")
                return False
            
            # Parse existing data
            current_attributes = json.loads(row[0])
            current_values = json.loads(row[1])
            
            # Apply updates
            if "attributes" in updates:
                current_attributes.update(updates["attributes"])
            if "values" in updates:
                current_values.update(updates["values"])
            
            # Update the record
            await self.connection.execute(
                """
                UPDATE metrics 
                SET attributes = ?, metric_values = ?
                WHERE id = ?
                """,
                (
                    json.dumps(current_attributes),
                    json.dumps(current_values),
                    metric_id
                )
            )
            await self.connection.commit()
            
            logger.debug(f"Updated metric with ID: {metric_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update metric: {e}")
            raise

    async def delete_metric(self, metric_id: str) -> bool:
        """Delete a metric by ID."""
        if not self.connection:
            raise RuntimeError("Database not connected")
        
        try:
            cursor = await self.connection.execute(
                "DELETE FROM metrics WHERE id = ?",
                (metric_id,)
            )
            await self.connection.commit()
            
            deleted = cursor.rowcount > 0
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
        if not self.connection:
            raise RuntimeError("Database not connected")
        
        try:
            # For safety, we'll first query to get IDs, then delete
            # This allows us to apply complex filters in Python
            metrics = await self.query_metrics(filters)
            
            if not metrics:
                return 0
            
            # Since we don't store IDs in the query result, we need a different approach
            # For now, we'll delete based on timestamp ranges and rebuild filters
            delete_count = 0
            
            if filters.time_range:
                start_time, end_time = filters.time_range
                cursor = await self.connection.execute(
                    "DELETE FROM metrics WHERE timestamp >= ? AND timestamp <= ?",
                    (start_time.isoformat(), end_time.isoformat())
                )
                delete_count = cursor.rowcount
                await self.connection.commit()
            
            logger.info(f"Deleted {delete_count} metrics")
            return delete_count
            
        except Exception as e:
            logger.error(f"Failed to delete metrics: {e}")
            raise

    async def health_check(self) -> bool:
        """Check if the database connection is healthy."""
        if not self.connection:
            return False
        
        try:
            cursor = await self.connection.execute("SELECT 1")
            await cursor.fetchone()
            return True
        except Exception as e:
            logger.error(f"SQLite health check failed: {e}")
            return False 