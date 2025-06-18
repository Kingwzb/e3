"""SQLite adapter optimized for read-only metrics querying with generic database interface."""

import json
import sqlite3
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import aiosqlite
from contextlib import asynccontextmanager

from app.core.database_abstraction import (
    MetricsQueryAdapter, MetricTuple, QueryFilter, DatabaseQuery, 
    AggregationQuery, DatabaseConfig
)
from app.utils.logging import logger


class SQLiteQueryAdapter(MetricsQueryAdapter):
    """SQLite implementation optimized for read-only querying with generic interface."""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.db_path = config.connection_params.get("database_path", "./metrics.db")
        self.connection_pool: List[aiosqlite.Connection] = []
        self.pool_size = config.connection_pool_size
        self._initialized = False
    
    async def connect(self) -> None:
        """Establish connection pool to SQLite database."""
        try:
            # Create connection pool for read-heavy workloads
            for _ in range(self.pool_size):
                conn = await aiosqlite.connect(self.db_path)
                # Optimize for read operations
                await conn.execute("PRAGMA journal_mode=WAL")
                await conn.execute("PRAGMA synchronous=NORMAL")
                await conn.execute("PRAGMA cache_size=10000")
                await conn.execute("PRAGMA temp_store=memory")
                await conn.execute("PRAGMA mmap_size=268435456")  # 256MB
                self.connection_pool.append(conn)
            
            self._initialized = True
            logger.info(f"Connected to SQLite database at {self.db_path} with {self.pool_size} connections")
        except Exception as e:
            logger.error(f"Failed to connect to SQLite database: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close all connections in the pool."""
        for conn in self.connection_pool:
            await conn.close()
        self.connection_pool.clear()
        self._initialized = False
        logger.info("Disconnected from SQLite database")
    
    @asynccontextmanager
    async def get_connection(self):
        """Get a connection from the pool."""
        if not self._initialized:
            raise RuntimeError("Database not connected")
        
        # Simple round-robin connection selection
        conn = self.connection_pool[0]
        self.connection_pool = self.connection_pool[1:] + [conn]
        
        try:
            yield conn
        finally:
            pass  # Connection stays in pool
    
    async def query_metrics(self, filters: QueryFilter) -> List[MetricTuple]:
        """Query metrics based on filter criteria."""
        async with self.get_connection() as conn:
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
                
                cursor = await conn.execute(query, params)
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
        async with self.get_connection() as conn:
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
        async with self.get_connection() as conn:
            try:
                query_parts = ["SELECT COUNT(*) FROM metrics WHERE 1=1"]
                params = []
                
                # Add time range filter
                if filters.time_range:
                    start_time, end_time = filters.time_range
                    query_parts.append("AND timestamp >= ? AND timestamp <= ?")
                    params.extend([start_time.isoformat(), end_time.isoformat()])
                
                query = " ".join(query_parts)
                cursor = await conn.execute(query, params)
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
        async with self.get_connection() as conn:
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
        async with self.get_connection() as conn:
            try:
                if query.native_query and "sql" in query.native_query:
                    # Execute raw SQL
                    sql = query.native_query["sql"]
                    params = query.native_query.get("params", [])
                    
                    # Safety check - only allow SELECT statements
                    if not sql.strip().upper().startswith("SELECT"):
                        raise ValueError("Only SELECT statements are allowed in native queries")
                    
                    if params:
                        cursor = await conn.execute(sql, params)
                    else:
                        cursor = await conn.execute(sql)
                    
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
        async with self.get_connection() as conn:
            try:
                # Get table info
                cursor = await conn.execute("PRAGMA table_info(metrics)")
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
        async with self.get_connection() as conn:
            try:
                # For generic queries, we'll explain a basic SELECT
                sql = "SELECT * FROM metrics LIMIT 1"
                
                if query.native_query and "sql" in query.native_query:
                    sql = query.native_query["sql"]
                
                # SQLite EXPLAIN QUERY PLAN
                cursor = await conn.execute(f"EXPLAIN QUERY PLAN {sql}")
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

    async def health_check(self) -> bool:
        """Check if the database connection is healthy."""
        if not self._initialized:
            return False
        
        try:
            async with self.get_connection() as conn:
                cursor = await conn.execute("SELECT 1")
                await cursor.fetchone()
                return True
        except Exception as e:
            logger.error(f"SQLite health check failed: {e}")
            return False 