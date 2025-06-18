"""PostgreSQL adapter optimized for read-only metrics querying with generic database interface."""

import json
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import asyncpg
from contextlib import asynccontextmanager

from app.core.database_abstraction import (
    MetricsQueryAdapter, MetricTuple, QueryFilter, DatabaseQuery, 
    AggregationQuery, DatabaseConfig
)
from app.utils.logging import logger


class PostgreSQLQueryAdapter(MetricsQueryAdapter):
    """PostgreSQL implementation optimized for read-only querying with generic interface."""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.host = config.connection_params.get("host", "localhost")
        self.port = config.connection_params.get("port", 5432)
        self.database = config.connection_params.get("database", "metrics")
        self.username = config.connection_params.get("username", "postgres")
        self.password = config.connection_params.get("password", "")
        
        self.connection_pool: Optional[asyncpg.Pool] = None
    
    async def connect(self) -> None:
        """Establish connection pool to PostgreSQL database."""
        try:
            self.connection_pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.username,
                password=self.password,
                min_size=5,
                max_size=self.config.connection_pool_size,
                command_timeout=self.config.query_timeout
            )
            
            logger.info(f"Connected to PostgreSQL database at {self.host}:{self.port}/{self.database}")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL database: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close the connection pool."""
        if self.connection_pool:
            await self.connection_pool.close()
            self.connection_pool = None
            logger.info("Disconnected from PostgreSQL database")
    
    @asynccontextmanager
    async def get_connection(self):
        """Get a connection from the pool."""
        if not self.connection_pool:
            raise RuntimeError("Database not connected")
        
        async with self.connection_pool.acquire() as conn:
            yield conn
    
    async def query_metrics(self, filters: QueryFilter) -> List[MetricTuple]:
        """Query metrics based on filter criteria."""
        async with self.get_connection() as conn:
            try:
                query_parts = ["SELECT attributes, metric_values, timestamp FROM metrics WHERE 1=1"]
                params = []
                param_count = 0
                
                # Add time range filter
                if filters.time_range:
                    start_time, end_time = filters.time_range
                    param_count += 1
                    query_parts.append(f"AND timestamp >= ${param_count}")
                    params.append(start_time)
                    param_count += 1
                    query_parts.append(f"AND timestamp <= ${param_count}")
                    params.append(end_time)
                
                # Add attribute filters using JSONB operations
                if filters.attributes:
                    for key, value in filters.attributes.items():
                        param_count += 1
                        query_parts.append(f"AND attributes->>'{key}' = ${param_count}")
                        params.append(str(value))
                
                # Add value filters using JSONB operations
                if filters.value_filters:
                    for value_key, conditions in filters.value_filters.items():
                        for operator, threshold in conditions.items():
                            pg_op = self._convert_operator(operator)
                            param_count += 1
                            query_parts.append(f"AND (metric_values->>'{value_key}')::numeric {pg_op} ${param_count}")
                            params.append(threshold)
                
                # Add sorting
                if filters.sort_by:
                    order = "DESC" if filters.sort_order == "desc" else "ASC"
                    if filters.sort_by == "timestamp":
                        query_parts.append(f"ORDER BY timestamp {order}")
                else:
                    query_parts.append("ORDER BY timestamp DESC")
                
                # Add limit
                if filters.limit:
                    param_count += 1
                    query_parts.append(f"LIMIT ${param_count}")
                    params.append(filters.limit)
                
                query = " ".join(query_parts)
                
                rows = await conn.fetch(query, *params)
                
                results = []
                for row in rows:
                    results.append(MetricTuple(
                        attributes=row['attributes'],
                        values=row['metric_values'],
                        timestamp=row['timestamp']
                    ))
                
                logger.debug(f"Query returned {len(results)} metrics")
                return results
                
            except Exception as e:
                logger.error(f"Failed to query metrics: {e}")
                raise
    
    def _convert_operator(self, op: str) -> str:
        """Convert MongoDB-style operators to PostgreSQL."""
        operator_map = {
            "$gte": ">=",
            "$lte": "<=", 
            "$gt": ">",
            "$lt": "<",
            "$eq": "=",
            "$ne": "!="
        }
        return operator_map.get(op, "=")
    
    async def aggregate_metrics(self, aggregation_query: AggregationQuery) -> List[Dict[str, Any]]:
        """Perform aggregations using PostgreSQL's advanced aggregation features."""
        async with self.get_connection() as conn:
            try:
                # Build aggregation query using PostgreSQL JSONB operations
                select_parts = []
                params = []
                param_count = 0
                
                # Add group by fields
                for field in aggregation_query.group_by:
                    if field.startswith("attributes."):
                        attr_field = field.replace("attributes.", "")
                        select_parts.append(f"attributes->>'{attr_field}' as {attr_field}")
                    else:
                        select_parts.append(f"attributes->>'{field}' as {field}")
                
                # Add aggregation functions
                for field, operation in aggregation_query.aggregations.items():
                    if field.startswith("values."):
                        value_field = field.replace("values.", "")
                        if operation in ["sum", "avg", "count", "max", "min"]:
                            select_parts.append(f"{operation.upper()}((metric_values->>'{value_field}')::numeric) as {operation}_{value_field}")
                    else:
                        if operation in ["sum", "avg", "count", "max", "min"]:
                            select_parts.append(f"{operation.upper()}((metric_values->>'{field}')::numeric) as {operation}_{field}")
                
                sql_parts = [f"SELECT {', '.join(select_parts)}", "FROM metrics"]
                
                # Add WHERE clause from filters
                if aggregation_query.filters:
                    where_conditions = []
                    
                    # Time range
                    if aggregation_query.filters.time_range:
                        start_time, end_time = aggregation_query.filters.time_range
                        param_count += 1
                        where_conditions.append(f"timestamp >= ${param_count}")
                        params.append(start_time)
                        param_count += 1
                        where_conditions.append(f"timestamp <= ${param_count}")
                        params.append(end_time)
                    
                    # Attribute filters
                    if aggregation_query.filters.attributes:
                        for key, value in aggregation_query.filters.attributes.items():
                            param_count += 1
                            where_conditions.append(f"attributes->>'{key}' = ${param_count}")
                            params.append(str(value))
                    
                    # Value filters
                    if aggregation_query.filters.value_filters:
                        for value_key, conditions in aggregation_query.filters.value_filters.items():
                            for operator, threshold in conditions.items():
                                pg_op = self._convert_operator(operator)
                                param_count += 1
                                where_conditions.append(f"(metric_values->>'{value_key}')::numeric {pg_op} ${param_count}")
                                params.append(threshold)
                    
                    if where_conditions:
                        sql_parts.append(f"WHERE {' AND '.join(where_conditions)}")
                
                # Add GROUP BY
                group_fields = []
                for field in aggregation_query.group_by:
                    if field.startswith("attributes."):
                        attr_field = field.replace("attributes.", "")
                        group_fields.append(f"attributes->>'{attr_field}'")
                    else:
                        group_fields.append(f"attributes->>'{field}'")
                
                sql_parts.append(f"GROUP BY {', '.join(group_fields)}")
                
                # Add HAVING clause if specified
                if aggregation_query.having:
                    having_conditions = []
                    for field, condition in aggregation_query.having.items():
                        if isinstance(condition, dict):
                            for op, value in condition.items():
                                pg_op = self._convert_operator(op)
                                param_count += 1
                                having_conditions.append(f"{field} {pg_op} ${param_count}")
                                params.append(value)
                        else:
                            param_count += 1
                            having_conditions.append(f"{field} = ${param_count}")
                            params.append(condition)
                    
                    if having_conditions:
                        sql_parts.append(f"HAVING {' AND '.join(having_conditions)}")
                
                query = " ".join(sql_parts)
                logger.debug(f"Executing aggregation query: {query}")
                
                rows = await conn.fetch(query, *params)
                
                results = []
                for row in rows:
                    result = {}
                    for key, value in row.items():
                        result[key] = value
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
                param_count = 0
                
                # Add time range filter
                if filters.time_range:
                    start_time, end_time = filters.time_range
                    param_count += 1
                    query_parts.append(f"AND timestamp >= ${param_count}")
                    params.append(start_time)
                    param_count += 1
                    query_parts.append(f"AND timestamp <= ${param_count}")
                    params.append(end_time)
                
                # Add attribute filters
                if filters.attributes:
                    for key, value in filters.attributes.items():
                        param_count += 1
                        query_parts.append(f"AND attributes->>'{key}' = ${param_count}")
                        params.append(str(value))
                
                # Add value filters
                if filters.value_filters:
                    for value_key, conditions in filters.value_filters.items():
                        for operator, threshold in conditions.items():
                            pg_op = self._convert_operator(operator)
                            param_count += 1
                            query_parts.append(f"AND (metric_values->>'{value_key}')::numeric {pg_op} ${param_count}")
                            params.append(threshold)
                
                query = " ".join(query_parts)
                result = await conn.fetchval(query, *params)
                
                count = result if result else 0
                logger.debug(f"Count query returned {count} metrics")
                return count
                
            except Exception as e:
                logger.error(f"Failed to count metrics: {e}")
                raise

    async def distinct_values(self, field: str, filters: Optional[QueryFilter] = None) -> List[Any]:
        """Get distinct values for a field using PostgreSQL DISTINCT."""
        async with self.get_connection() as conn:
            try:
                params = []
                param_count = 0
                
                # Handle nested field access
                if field.startswith("attributes."):
                    attr_field = field.replace("attributes.", "")
                    select_field = f"attributes->>'{attr_field}'"
                elif field.startswith("values."):
                    value_field = field.replace("values.", "")
                    select_field = f"metric_values->>'{value_field}'"
                elif field == "timestamp":
                    select_field = "timestamp"
                else:
                    # Assume it's an attribute field
                    select_field = f"attributes->>'{field}'"
                
                query_parts = [f"SELECT DISTINCT {select_field} FROM metrics"]
                
                # Add WHERE clause from filters
                if filters:
                    where_conditions = []
                    
                    # Time range
                    if filters.time_range:
                        start_time, end_time = filters.time_range
                        param_count += 1
                        where_conditions.append(f"timestamp >= ${param_count}")
                        params.append(start_time)
                        param_count += 1
                        where_conditions.append(f"timestamp <= ${param_count}")
                        params.append(end_time)
                    
                    # Attribute filters
                    if filters.attributes:
                        for key, value in filters.attributes.items():
                            param_count += 1
                            where_conditions.append(f"attributes->>'{key}' = ${param_count}")
                            params.append(str(value))
                    
                    # Value filters
                    if filters.value_filters:
                        for value_key, conditions in filters.value_filters.items():
                            for operator, threshold in conditions.items():
                                pg_op = self._convert_operator(operator)
                                param_count += 1
                                where_conditions.append(f"(metric_values->>'{value_key}')::numeric {pg_op} ${param_count}")
                                params.append(threshold)
                    
                    if where_conditions:
                        query_parts.append(f"WHERE {' AND '.join(where_conditions)}")
                
                query_parts.append(f"ORDER BY {select_field}")
                query = " ".join(query_parts)
                
                rows = await conn.fetch(query, *params)
                distinct_values = [row[0] for row in rows if row[0] is not None]
                
                logger.debug(f"Distinct values query returned {len(distinct_values)} unique values")
                return distinct_values
                
            except Exception as e:
                logger.error(f"Failed to get distinct values: {e}")
                raise

    async def execute_native_query(self, query: DatabaseQuery) -> List[Dict[str, Any]]:
        """Execute database-specific native queries (SQL for PostgreSQL)."""
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
                        rows = await conn.fetch(sql, *params)
                    else:
                        rows = await conn.fetch(sql)
                    
                    # Convert rows to dictionaries
                    results = []
                    for row in rows:
                        result = {}
                        for key, value in row.items():
                            # Convert datetime objects to ISO format
                            if hasattr(value, "isoformat"):
                                result[key] = value.isoformat()
                            else:
                                result[key] = value
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
                # Get table information
                table_query = """
                SELECT 
                    column_name, 
                    data_type, 
                    is_nullable,
                    column_default
                FROM information_schema.columns 
                WHERE table_name = 'metrics'
                ORDER BY ordinal_position
                """
                
                columns = await conn.fetch(table_query)
                
                schema_info = {
                    "database_type": "postgresql",
                    "tables": {
                        "metrics": {
                            "columns": []
                        }
                    }
                }
                
                for column in columns:
                    schema_info["tables"]["metrics"]["columns"].append({
                        "name": column['column_name'],
                        "type": column['data_type'],
                        "nullable": column['is_nullable'] == 'YES',
                        "default": column['column_default']
                    })
                
                # Get index information
                index_query = """
                SELECT 
                    indexname,
                    indexdef
                FROM pg_indexes 
                WHERE tablename = 'metrics'
                """
                
                indexes = await conn.fetch(index_query)
                schema_info["tables"]["metrics"]["indexes"] = [
                    {"name": idx['indexname'], "definition": idx['indexdef']}
                    for idx in indexes
                ]
                
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
                
                # PostgreSQL EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
                explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {sql}"
                result = await conn.fetchval(explain_query)
                
                explain_result = {
                    "database_type": "postgresql",
                    "query": sql,
                    "execution_plan": result[0] if result else {}
                }
                
                return explain_result
                
            except Exception as e:
                logger.error(f"Failed to explain query: {e}")
                raise

    async def health_check(self) -> bool:
        """Check if the database connection is healthy."""
        if not self.connection_pool:
            return False
        
        try:
            async with self.get_connection() as conn:
                await conn.fetchval("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")
            return False 