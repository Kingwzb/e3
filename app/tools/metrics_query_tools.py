"""LLM tools for read-only metrics database querying with complex SQL support."""

from typing import Dict, Any, List, Optional, Union, Type
from datetime import datetime
from pydantic import BaseModel, Field
from langchain.tools import BaseTool

from app.core.database_abstraction import (
    MetricsQueryDatabase, DatabaseConfig, QueryFilter, ComplexQuery, 
    JoinConfig, get_sqlite_query_config, get_mongodb_query_config, 
    get_postgresql_query_config
)
from app.core.config import settings


# Global database instance for LLM tools
_metrics_db: Optional[MetricsQueryDatabase] = None


async def get_metrics_database() -> MetricsQueryDatabase:
    """Get or create the global metrics database instance."""
    global _metrics_db
    
    if _metrics_db is None:
        # Create database config based on settings
        if hasattr(settings, 'metrics_db_type'):
            db_type = settings.metrics_db_type.lower()
            
            if db_type == "sqlite":
                config = get_sqlite_query_config(
                    db_path=getattr(settings, 'metrics_db_path', './metrics.db')
                )
            elif db_type == "mongodb":
                config = get_mongodb_query_config(
                    connection_string=getattr(settings, 'metrics_mongodb_uri', 'mongodb://localhost:27017'),
                    database_name=getattr(settings, 'metrics_mongodb_db', 'metrics_db'),
                    collection_name=getattr(settings, 'metrics_mongodb_collection', 'metrics')
                )
            elif db_type == "postgresql":
                config = get_postgresql_query_config(
                    host=getattr(settings, 'metrics_pg_host', 'localhost'),
                    port=getattr(settings, 'metrics_pg_port', 5432),
                    database=getattr(settings, 'metrics_pg_database', 'metrics'),
                    username=getattr(settings, 'metrics_pg_username', 'postgres'),
                    password=getattr(settings, 'metrics_pg_password', '')
                )
            else:
                # Default to SQLite
                config = get_sqlite_query_config()
        else:
            # Default configuration
            config = get_sqlite_query_config()
        
        _metrics_db = MetricsQueryDatabase(config)
        await _metrics_db.initialize()
    
    return _metrics_db


async def close_metrics_database() -> None:
    """Close the global metrics database connection."""
    global _metrics_db
    if _metrics_db:
        await _metrics_db.close()
        _metrics_db = None


# Pydantic models for tool inputs
class QueryMetricsInput(BaseModel):
    """Input for querying metrics with filters."""
    attributes: Optional[Dict[str, Any]] = Field(None, description="Attribute filters (key-value pairs)")
    value_filters: Optional[Dict[str, Dict[str, Union[float, int]]]] = Field(
        None, description="Value filters with operators like {'metric_name': {'$gte': 100}}"
    )
    start_time: Optional[str] = Field(None, description="Start time (ISO format)")
    end_time: Optional[str] = Field(None, description="End time (ISO format)")
    limit: Optional[int] = Field(100, description="Maximum number of results")
    sort_by: Optional[str] = Field("timestamp", description="Field to sort by")
    sort_order: Optional[str] = Field("desc", description="Sort order: 'asc' or 'desc'")


class ComplexQueryInput(BaseModel):
    """Input for complex queries with joins and advanced filtering."""
    base_table: str = Field(..., description="Primary table/collection to query")
    raw_sql: Optional[str] = Field(None, description="Raw SQL for complex queries")
    joins: Optional[List[Dict[str, Any]]] = Field(None, description="Join configurations")
    group_by: Optional[List[str]] = Field(None, description="Fields to group by")
    aggregations: Optional[Dict[str, str]] = Field(None, description="Aggregation operations")
    filters: Optional[Dict[str, Any]] = Field(None, description="Standard filters")
    limit: Optional[int] = Field(1000, description="Maximum number of results")


class AggregateMetricsInput(BaseModel):
    """Input for aggregating metrics data."""
    group_by: List[str] = Field(..., description="Fields to group by")
    aggregations: Dict[str, str] = Field(..., description="Aggregation operations (sum, avg, count, max, min)")
    attributes: Optional[Dict[str, Any]] = Field(None, description="Attribute filters")
    value_filters: Optional[Dict[str, Dict[str, Union[float, int]]]] = Field(None, description="Value filters")
    start_time: Optional[str] = Field(None, description="Start time filter")
    end_time: Optional[str] = Field(None, description="End time filter")


class RawSQLInput(BaseModel):
    """Input for executing raw SQL queries."""
    sql: str = Field(..., description="SQL query to execute (SELECT only)")
    params: Optional[List[Any]] = Field(None, description="Query parameters")


class SchemaInfoInput(BaseModel):
    """Input for getting database schema information."""
    table_name: Optional[str] = Field(None, description="Specific table name (optional)")


class ExplainQueryInput(BaseModel):
    """Input for explaining query execution plans."""
    query: str = Field(..., description="SQL query to explain")


# LangChain Tools
class QueryMetricsTool(BaseTool):
    """Tool for querying metrics with flexible filtering."""
    
    name: str = "query_metrics"
    description: str = """
    Query metrics data with flexible filtering options.
    
    Use this tool to:
    - Find metrics by attributes (e.g., category, region, metric_name)
    - Filter by metric values with operators ($gte, $lte, $gt, $lt, $eq)
    - Filter by time ranges
    - Sort and limit results
    
    Example usage:
    - Find engagement metrics: attributes={"category": "engagement"}
    - Find high-value metrics: value_filters={"daily_users": {"$gte": 1000}}
    - Recent metrics: start_time="2024-01-01T00:00:00"
    """
    args_schema: Type[BaseModel] = QueryMetricsInput
    
    def _run(self, **kwargs) -> str:
        """Run the query metrics tool synchronously."""
        import asyncio
        return asyncio.run(self._arun(**kwargs))
    
    async def _arun(self, **kwargs) -> str:
        """Query metrics based on provided filters."""
        try:
            db = await get_metrics_database()
            
            # Build time range if provided
            time_range = None
            if kwargs.get('start_time') or kwargs.get('end_time'):
                start_time = datetime.fromisoformat(kwargs['start_time']) if kwargs.get('start_time') else None
                end_time = datetime.fromisoformat(kwargs['end_time']) if kwargs.get('end_time') else None
                if start_time or end_time:
                    time_range = (
                        start_time or datetime.min.replace(tzinfo=None),
                        end_time or datetime.max.replace(tzinfo=None)
                    )
            
            # Build filters
            filters = QueryFilter(
                attributes=kwargs.get('attributes'),
                value_filters=kwargs.get('value_filters'),
                time_range=time_range,
                limit=kwargs.get('limit', 100),
                sort_by=kwargs.get('sort_by', 'timestamp'),
                sort_order=kwargs.get('sort_order', 'desc')
            )
            
            results = await db.query_metrics(filters)
            
            return f"Found {len(results)} metrics matching the criteria. Sample results:\n" + \
                   "\n".join([f"- {r.attributes} | {r.values} | {r.timestamp}" for r in results[:5]])
            
        except Exception as e:
            return f"Error querying metrics: {str(e)}"


class ComplexQueryTool(BaseTool):
    """Tool for executing complex queries with joins and advanced SQL."""
    
    name: str = "execute_complex_query"
    description: str = """
    Execute complex database queries with joins, subqueries, and advanced filtering.
    
    Use this tool for:
    - Multi-table joins
    - Complex analytical queries
    - Raw SQL execution for maximum flexibility
    - Advanced filtering and grouping
    
    You can provide either:
    - raw_sql: Direct SQL query (PostgreSQL/SQLite syntax)
    - Structured query with joins, group_by, aggregations
    
    Example raw SQL:
    "SELECT m1.*, m2.value FROM metrics m1 JOIN user_data m2 ON m1.user_id = m2.id"
    """
    args_schema: Type[BaseModel] = ComplexQueryInput
    
    def _run(self, **kwargs) -> str:
        """Run the complex query tool synchronously."""
        import asyncio
        return asyncio.run(self._arun(**kwargs))
    
    async def _arun(self, **kwargs) -> str:
        """Execute complex queries."""
        try:
            db = await get_metrics_database()
            
            # Build complex query
            query = ComplexQuery(
                base_table=kwargs['base_table'],
                raw_sql=kwargs.get('raw_sql'),
                joins=[JoinConfig(**join) for join in kwargs.get('joins', [])] if kwargs.get('joins') else None,
                group_by=kwargs.get('group_by'),
                aggregations=kwargs.get('aggregations'),
                filters=QueryFilter(**kwargs['filters']) if kwargs.get('filters') else None
            )
            
            results = await db.execute_complex_query(query)
            
            if not results:
                return "Query completed successfully but returned no results."
            
            # Format results for display
            output = f"Query returned {len(results)} rows:\n\n"
            
            # Show column headers
            if results:
                headers = list(results[0].keys())
                output += " | ".join(headers) + "\n"
                output += "-" * (len(" | ".join(headers))) + "\n"
                
                # Show first few rows
                for row in results[:10]:
                    values = [str(row.get(h, "")) for h in headers]
                    output += " | ".join(values) + "\n"
                
                if len(results) > 10:
                    output += f"\n... and {len(results) - 10} more rows"
            
            return output
            
        except Exception as e:
            return f"Error executing complex query: {str(e)}"


class AggregateMetricsTool(BaseTool):
    """Tool for aggregating metrics data with grouping."""
    
    name: str = "aggregate_metrics"
    description: str = """
    Perform aggregations on metrics data with grouping and filtering.
    
    Use this tool to:
    - Calculate sums, averages, counts, max, min values
    - Group by attributes or time periods
    - Get statistical summaries of metric data
    - Perform analytical calculations
    
    Supported aggregations: sum, avg, count, max, min, stddev (PostgreSQL only)
    
    Example usage:
    - Daily totals: group_by=["attributes.date"], aggregations={"values.revenue": "sum"}
    - Regional averages: group_by=["attributes.region"], aggregations={"values.score": "avg"}
    """
    args_schema: Type[BaseModel] = AggregateMetricsInput
    
    def _run(self, **kwargs) -> str:
        """Run the aggregate metrics tool synchronously."""
        import asyncio
        return asyncio.run(self._arun(**kwargs))
    
    async def _arun(self, **kwargs) -> str:
        """Aggregate metrics data."""
        try:
            db = await get_metrics_database()
            
            # Build time range if provided
            time_range = None
            if kwargs.get('start_time') or kwargs.get('end_time'):
                start_time = datetime.fromisoformat(kwargs['start_time']) if kwargs.get('start_time') else None
                end_time = datetime.fromisoformat(kwargs['end_time']) if kwargs.get('end_time') else None
                if start_time or end_time:
                    time_range = (
                        start_time or datetime.min.replace(tzinfo=None),
                        end_time or datetime.max.replace(tzinfo=None)
                    )
            
            # Build filters
            filters = QueryFilter(
                attributes=kwargs.get('attributes'),
                value_filters=kwargs.get('value_filters'),
                time_range=time_range
            )
            
            results = await db.aggregate_metrics(
                filters=filters,
                group_by=kwargs['group_by'],
                aggregations=kwargs['aggregations']
            )
            
            if not results:
                return "Aggregation completed but returned no results."
            
            # Format aggregation results
            output = f"Aggregation results ({len(results)} groups):\n\n"
            
            for result in results[:20]:  # Show first 20 groups
                output += "Group: " + " | ".join([f"{k}: {v}" for k, v in result.items()]) + "\n"
            
            if len(results) > 20:
                output += f"\n... and {len(results) - 20} more groups"
            
            return output
            
        except Exception as e:
            return f"Error aggregating metrics: {str(e)}"


class RawSQLTool(BaseTool):
    """Tool for executing raw SQL queries with safety checks."""
    
    name: str = "execute_raw_sql"
    description: str = """
    Execute raw SQL queries for maximum flexibility (read-only).
    
    Use this tool for:
    - Complex analytical queries
    - Custom joins and subqueries
    - Database-specific optimizations
    - Advanced SQL features
    
    Safety features:
    - Only SELECT statements allowed
    - No mutations (INSERT, UPDATE, DELETE)
    - Parameterized queries supported
    
    Examples:
    - "SELECT COUNT(*) FROM metrics WHERE timestamp > '2024-01-01'"
    - "SELECT category, AVG(value) FROM metrics GROUP BY category"
    """
    args_schema: Type[BaseModel] = RawSQLInput
    
    def _run(self, **kwargs) -> str:
        """Run the raw SQL tool synchronously."""
        import asyncio
        return asyncio.run(self._arun(**kwargs))
    
    async def _arun(self, **kwargs) -> str:
        """Execute raw SQL queries."""
        try:
            db = await get_metrics_database()
            
            results = await db.execute_raw_sql(
                sql=kwargs['sql'],
                params=kwargs.get('params')
            )
            
            if not results:
                return "SQL query executed successfully but returned no results."
            
            # Format results
            output = f"SQL query returned {len(results)} rows:\n\n"
            
            if results:
                headers = list(results[0].keys())
                output += " | ".join(headers) + "\n"
                output += "-" * (len(" | ".join(headers))) + "\n"
                
                for row in results[:15]:  # Show first 15 rows
                    values = [str(row.get(h, "")) for h in headers]
                    output += " | ".join(values) + "\n"
                
                if len(results) > 15:
                    output += f"\n... and {len(results) - 15} more rows"
            
            return output
            
        except Exception as e:
            return f"Error executing SQL: {str(e)}"


class DatabaseSchemaInfoTool(BaseTool):
    """Tool for getting database schema information."""
    
    name: str = "get_database_schema"
    description: str = """
    Get information about database tables, columns, indexes, and structure.
    
    Use this tool to:
    - Discover available tables and their columns
    - Check data types and constraints
    - View indexes and performance optimizations
    - Understand the database schema before querying
    
    Provides detailed information including:
    - Table names and column definitions
    - Data types and constraints
    - Primary keys and indexes
    - Table statistics (for PostgreSQL)
    """
    args_schema: Type[BaseModel] = SchemaInfoInput
    
    def _run(self, **kwargs) -> str:
        """Run the schema info tool synchronously."""
        import asyncio
        return asyncio.run(self._arun(**kwargs))
    
    async def _arun(self, **kwargs) -> str:
        """Get database schema information."""
        try:
            db = await get_metrics_database()
            
            schema_info = await db.get_schema_info()
            
            if not schema_info:
                return "No schema information available."
            
            output = "Database Schema Information:\n\n"
            
            for table_name, table_info in schema_info.items():
                if kwargs.get('table_name') and table_name != kwargs['table_name']:
                    continue
                
                output += f"Table: {table_name}\n"
                output += "Columns:\n"
                
                for col in table_info.get('columns', []):
                    col_info = f"  - {col['name']} ({col['type']})"
                    if not col.get('nullable', True):
                        col_info += " NOT NULL"
                    if col.get('primary_key'):
                        col_info += " PRIMARY KEY"
                    output += col_info + "\n"
                
                if table_info.get('indexes'):
                    output += "Indexes:\n"
                    for idx in table_info['indexes']:
                        if isinstance(idx, dict):
                            output += f"  - {idx.get('name', 'Unknown')}\n"
                        else:
                            output += f"  - {idx}\n"
                
                if table_info.get('statistics'):
                    output += f"Statistics: {table_info['statistics']}\n"
                
                output += "\n"
            
            return output
            
        except Exception as e:
            return f"Error getting schema info: {str(e)}"


class QueryExplainTool(BaseTool):
    """Tool for explaining query execution plans."""
    
    name: str = "explain_query_plan"
    description: str = """
    Get query execution plans to understand performance and optimize queries.
    
    Use this tool to:
    - Analyze query performance
    - Identify slow operations
    - Optimize complex queries
    - Understand index usage
    
    Provides execution plans with:
    - Query costs and timing
    - Index usage information
    - Join strategies
    - Optimization suggestions
    """
    args_schema: Type[BaseModel] = ExplainQueryInput
    
    def _run(self, **kwargs) -> str:
        """Run the explain query tool synchronously."""
        import asyncio
        return asyncio.run(self._arun(**kwargs))
    
    async def _arun(self, **kwargs) -> str:
        """Explain query execution plan."""
        try:
            db = await get_metrics_database()
            
            explain_result = await db.explain_query(kwargs['query'])
            
            output = f"Query Execution Plan for:\n{kwargs['query']}\n\n"
            
            if 'execution_plan' in explain_result:
                # SQLite format
                for step in explain_result['execution_plan']:
                    output += f"Step {step['id']}: {step['detail']}\n"
            elif 'postgresql_execution_plans' in explain_result:
                # PostgreSQL format
                import json
                for plan_name, plan_data in explain_result['postgresql_execution_plans'].items():
                    if plan_data:
                        output += f"\n{plan_name.upper()}:\n"
                        output += json.dumps(plan_data, indent=2)
            else:
                output += str(explain_result)
            
            return output
            
        except Exception as e:
            return f"Error explaining query: {str(e)}"


class DatabaseHealthTool(BaseTool):
    """Tool for checking database health and connection status."""
    
    name: str = "check_database_health"
    description: str = """
    Check the health and status of the metrics database connection.
    
    Use this tool to:
    - Verify database connectivity
    - Check connection pool status
    - Monitor database performance metrics
    - Troubleshoot connection issues
    
    Provides information about:
    - Connection status
    - Database size and statistics
    - Performance metrics
    - System health indicators
    """
    
    def _run(self) -> str:
        """Run the database health tool synchronously."""
        import asyncio
        return asyncio.run(self._arun())
    
    async def _arun(self) -> str:
        """Check database health."""
        try:
            db = await get_metrics_database()
            
            is_healthy = await db.health_check()
            
            if is_healthy:
                return f"✅ Database is healthy and connected. Type: {db.config.database_type.value}"
            else:
                return "❌ Database health check failed. Connection may be down."
            
        except Exception as e:
            return f"❌ Database health check error: {str(e)}"


# Convenience functions for programmatic access
async def query_metrics_data(filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Query metrics data programmatically."""
    db = await get_metrics_database()
    
    # Convert dict filters to QueryFilter
    query_filter = QueryFilter(**filters)
    results = await db.query_metrics(query_filter)
    
    return [
        {
            "attributes": r.attributes,
            "values": r.values,
            "timestamp": r.timestamp.isoformat()
        }
        for r in results
    ]


async def execute_sql_query(sql: str, params: Optional[List] = None) -> List[Dict[str, Any]]:
    """Execute SQL query programmatically."""
    db = await get_metrics_database()
    return await db.execute_raw_sql(sql, params)


async def get_database_schema() -> Dict[str, Any]:
    """Get database schema programmatically."""
    db = await get_metrics_database()
    return await db.get_schema_info()


# Export all tools for LangChain integration
METRICS_QUERY_TOOLS = [
    QueryMetricsTool(),
    ComplexQueryTool(),
    AggregateMetricsTool(),
    RawSQLTool(),
    DatabaseSchemaInfoTool(),
    QueryExplainTool(),
    DatabaseHealthTool()
] 