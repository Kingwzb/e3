"""LLM database tools built on top of the database abstraction layer.

This module provides tools that can be used by LLMs to interact with metrics data,
while abstracting away the underlying database implementation (SQL or NoSQL).
"""

import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from langchain.tools import BaseTool

from app.core.database_abstraction import (
    MetricsDatabase, MetricTuple, QueryFilter, DatabaseConfig, AggregationQuery,
    get_sqlite_config, get_mongodb_config, get_mongodb_ee_productivities_config
)
from app.core.config import settings
from app.utils.logging import logger


# Global database instance (will be initialized by the application)
_metrics_db: Optional[MetricsDatabase] = None


def get_metrics_database() -> MetricsDatabase:
    """Get the global metrics database instance."""
    global _metrics_db
    if _metrics_db is None:
        raise RuntimeError("Metrics database not initialized. Call initialize_metrics_database() first.")
    return _metrics_db


async def initialize_metrics_database() -> None:
    """Initialize the metrics database based on configuration."""
    global _metrics_db
    
    db_type = settings.metrics_db_type.lower()
    
    if db_type == "sqlite":
        config = get_sqlite_config(settings.metrics_db_path)
    elif db_type == "mongodb":
        if not settings.metrics_mongodb_uri:
            raise ValueError("MongoDB URI not configured. Set METRICS_MONGODB_URI environment variable.")
        config = get_mongodb_ee_productivities_config(
            settings.metrics_mongodb_uri,
            settings.metrics_mongodb_database,
            collection_name=None  # No default collection - tools will switch dynamically
        )
    else:
        raise ValueError(f"Unsupported metrics database type: {db_type}")
    
    _metrics_db = MetricsDatabase(config)
    await _metrics_db.initialize()
    logger.info(f"Initialized metrics database with {db_type} adapter")


async def close_metrics_database() -> None:
    """Close the metrics database connection."""
    global _metrics_db
    if _metrics_db:
        await _metrics_db.close()
        _metrics_db = None


# Pydantic models for tool inputs
class InsertMetricInput(BaseModel):
    """Input for inserting a single metric."""
    attributes: Dict[str, Any] = Field(..., description="Key-value attributes for the metric (e.g., category, metric_name, region)")
    values: Dict[str, Union[float, int, str, bool]] = Field(..., description="One or more metric values (e.g., {'value': 100, 'count': 5, 'status': 'active'})")
    timestamp: Optional[datetime] = Field(None, description="Optional timestamp (defaults to current time)")


class QueryMetricsInput(BaseModel):
    """Input for querying metrics."""
    attributes: Optional[Dict[str, Any]] = Field(None, description="Filter by attributes (e.g., {'category': 'engagement'})")
    value_filters: Optional[Dict[str, Dict[str, Union[float, int]]]] = Field(
        None, 
        description="Filter by values with operators (e.g., {'daily_users': {'$gte': 1000}})"
    )
    days_back: Optional[int] = Field(7, description="Number of days to look back (default: 7)")
    limit: Optional[int] = Field(50, description="Maximum number of results (default: 50)")
    sort_by: Optional[str] = Field("timestamp", description="Field to sort by (default: timestamp)")
    sort_order: Optional[str] = Field("desc", description="Sort order: 'asc' or 'desc' (default: desc)")


class AggregateMetricsInput(BaseModel):
    """Input for aggregating metrics."""
    group_by: List[str] = Field(..., description="Fields to group by (e.g., ['category', 'region'])")
    aggregations: Dict[str, str] = Field(..., description="Aggregation operations (e.g., {'daily_users': 'avg', 'revenue': 'sum'})")
    attributes: Optional[Dict[str, Any]] = Field(None, description="Filter by attributes")
    days_back: Optional[int] = Field(30, description="Number of days to look back (default: 30)")


# Tool implementations
class InsertMetricTool(BaseTool):
    """Tool for inserting metrics into the database."""
    
    name: str = "insert_metric"
    description: str = """Insert a single metric into the database. 
    
    Use this when you need to store new metric data. The metric should have:
    - attributes: Key-value pairs that describe the metric (category, metric_name, region, etc.)
    - values: The actual metric values (can be multiple values per metric)
    - timestamp: When the metric was recorded (optional, defaults to now)
    
    Example: Insert daily active users for the US region in the engagement category."""
    args_schema: type[BaseModel] = InsertMetricInput
    
    async def _arun(
        self, 
        attributes: Dict[str, Any], 
        values: Dict[str, Union[float, int, str, bool]], 
        timestamp: Optional[datetime] = None
    ) -> str:
        """Insert a metric asynchronously."""
        try:
            db = get_metrics_database()
            
            metric = MetricTuple(
                attributes=attributes,
                values=values,
                timestamp=timestamp or datetime.utcnow()
            )
            
            metric_id = await db.insert_metric(metric)
            
            result = {
                "success": True,
                "metric_id": metric_id,
                "attributes": attributes,
                "values": values,
                "timestamp": metric.timestamp.isoformat()
            }
            
            logger.info(f"Inserted metric with ID: {metric_id}")
            return f"Successfully inserted metric. ID: {metric_id}, Data: {json.dumps(result)}"
            
        except Exception as e:
            logger.error(f"Failed to insert metric: {e}")
            return f"Error inserting metric: {str(e)}"
    
    def _run(self, *args, **kwargs) -> str:
        """Synchronous version (not recommended for async operations)."""
        return "This tool requires async execution. Use _arun instead."


class QueryMetricsTool(BaseTool):
    """Tool for querying metrics from the database."""
    
    name: str = "query_metrics"
    description: str = """Query metrics from the database with flexible filtering.
    
    Use this to retrieve metric data based on various criteria:
    - attributes: Filter by metric attributes (category, metric_name, etc.)
    - value_filters: Filter by metric values using operators ($gte, $lte, $gt, $lt, $eq)
    - days_back: How many days back to look (default: 7)
    - limit: Maximum number of results (default: 50)
    - sort_by: Field to sort by (default: timestamp)
    - sort_order: 'asc' or 'desc' (default: desc)
    
    Example: Get all engagement metrics from the last 7 days with daily_users >= 1000."""
    args_schema: type[BaseModel] = QueryMetricsInput
    
    async def _arun(
        self,
        attributes: Optional[Dict[str, Any]] = None,
        value_filters: Optional[Dict[str, Dict[str, Union[float, int]]]] = None,
        days_back: int = 7,
        limit: int = 50,
        sort_by: str = "timestamp",
        sort_order: str = "desc"
    ) -> str:
        """Query metrics asynchronously."""
        try:
            db = get_metrics_database()
            
            # Build time range
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days_back)
            
            filters = QueryFilter(
                attributes=attributes,
                value_filters=value_filters,
                time_range=(start_time, end_time),
                limit=limit,
                sort_by=sort_by,
                sort_order=sort_order
            )
            
            metrics = await db.query_metrics(filters)
            
            # Convert to serializable format
            results = []
            for metric in metrics:
                results.append({
                    "attributes": metric.attributes,
                    "values": metric.values,
                    "timestamp": metric.timestamp.isoformat()
                })
            
            logger.info(f"Query returned {len(results)} metrics")
            return f"Found {len(results)} metrics:\n" + json.dumps(results[:10], indent=2)  # Show first 10
            
        except Exception as e:
            logger.error(f"Failed to query metrics: {e}")
            return f"Error querying metrics: {str(e)}"
    
    def _run(self, *args, **kwargs) -> str:
        """Synchronous version (not recommended for async operations)."""
        return "This tool requires async execution. Use _arun instead."


class AggregateMetricsTool(BaseTool):
    """Tool for aggregating metrics data."""
    
    name: str = "aggregate_metrics"
    description: str = """Perform aggregations on metrics data (sum, avg, count, max, min).
    
    Use this to get summarized insights from your metrics:
    - group_by: Fields to group by (e.g., ['category', 'region'])
    - aggregations: Operations to perform (e.g., {'daily_users': 'avg', 'revenue': 'sum'})
    - attributes: Filter by attributes before aggregating
    - days_back: Number of days to include in aggregation (default: 30)
    
    Example: Get average daily users and total revenue by category for the last 30 days."""
    args_schema: type[BaseModel] = AggregateMetricsInput
    
    async def _arun(
        self,
        group_by: List[str],
        aggregations: Dict[str, str],
        attributes: Optional[Dict[str, Any]] = None,
        days_back: int = 30
    ) -> str:
        """Aggregate metrics asynchronously."""
        try:
            db = get_metrics_database()
            
            # Build time range
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days_back)
            
            filters = QueryFilter(
                attributes=attributes,
                time_range=(start_time, end_time)
            )
            
            aggregation_query = AggregationQuery(
                group_by=group_by,
                aggregations=aggregations,
                filters=filters
            )
            
            results = await db.aggregate_metrics(aggregation_query)
            
            logger.info(f"Aggregation returned {len(results)} groups")
            return f"Aggregation results ({len(results)} groups):\n" + json.dumps(results, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to aggregate metrics: {e}")
            return f"Error aggregating metrics: {str(e)}"
    
    def _run(self, *args, **kwargs) -> str:
        """Synchronous version (not recommended for async operations)."""
        return "This tool requires async execution. Use _arun instead."


class DatabaseHealthTool(BaseTool):
    """Tool for checking database health."""
    
    name: str = "check_database_health"
    description: str = "Check if the metrics database connection is healthy and working properly."
    
    async def _arun(self) -> str:
        """Check database health asynchronously."""
        try:
            db = get_metrics_database()
            is_healthy = await db.health_check()
            
            if is_healthy:
                return "Database connection is healthy and working properly."
            else:
                return "Database connection appears to be unhealthy."
                
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return f"Database health check failed: {str(e)}"
    
    def _run(self) -> str:
        """Synchronous version (not recommended for async operations)."""
        return "This tool requires async execution. Use _arun instead."


def create_metrics_db_tools() -> List[BaseTool]:
    """Create a list of all metrics database tools."""
    return [
        InsertMetricTool(),
        QueryMetricsTool(),
        AggregateMetricsTool(),
        DatabaseHealthTool()
    ]


# Direct functions for programmatic use
async def insert_metric_direct(
    attributes: Dict[str, Any],
    values: Dict[str, Union[float, int, str, bool]],
    timestamp: Optional[datetime] = None
) -> str:
    """Insert a metric directly (for programmatic use)."""
    db = get_metrics_database()
    
    metric = MetricTuple(
        attributes=attributes,
        values=values,
        timestamp=timestamp or datetime.utcnow()
    )
    
    return await db.insert_metric(metric)


async def query_metrics_direct(
    attributes: Optional[Dict[str, Any]] = None,
    value_filters: Optional[Dict[str, Dict[str, Union[float, int]]]] = None,
    days_back: int = 7,
    limit: int = 50
) -> List[MetricTuple]:
    """Query metrics directly (for programmatic use)."""
    db = get_metrics_database()
    
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days_back)
    
    filters = QueryFilter(
        attributes=attributes,
        value_filters=value_filters,
        time_range=(start_time, end_time),
        limit=limit
    )
    
    return await db.query_metrics(filters) 