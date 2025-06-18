"""Database abstraction layer for metrics querying and writing.

This module provides a unified interface for querying and writing metrics data
across different database backends (SQL and NoSQL) with generic query capabilities.

The abstraction supports switching between:
- SQLite (for local testing and development)
- MongoDB (for production NoSQL)
- PostgreSQL (for production SQL with complex joins)

Key Design Principles:
1. Database-agnostic query interface
2. Generic filtering and aggregation
3. No SQL-specific concepts in the main interface
4. Adapter-specific optimizations under the hood
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from dataclasses import dataclass


class DatabaseType(str, Enum):
    """Supported database types."""
    SQLITE = "sqlite"
    MONGODB = "mongodb"
    POSTGRESQL = "postgresql"


class MetricTuple(BaseModel):
    """Represents a metric tuple with attributes and values."""
    attributes: Dict[str, Any] = Field(..., description="Key-value attributes for the metric")
    values: Dict[str, Union[float, int]] = Field(..., description="One or more metric values")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the metric was recorded")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class QueryFilter(BaseModel):
    """Generic filter criteria for querying metrics across different database types."""
    attributes: Optional[Dict[str, Any]] = Field(None, description="Attribute filters (key-value pairs)")
    value_filters: Optional[Dict[str, Dict[str, Union[float, int]]]] = Field(
        None, 
        description="Value filters with operators like {'metric_name': {'$gte': 100}}"
    )
    time_range: Optional[Tuple[datetime, datetime]] = Field(None, description="Start and end datetime")
    limit: Optional[int] = Field(None, description="Maximum number of results")
    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_order: Optional[str] = Field("desc", description="Sort order: 'asc' or 'desc'")
    
    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True


class AggregationQuery(BaseModel):
    """Generic aggregation query that works across different database types."""
    group_by: List[str] = Field(..., description="Fields to group by (e.g., ['category', 'region'])")
    aggregations: Dict[str, str] = Field(..., description="Aggregation operations (sum, avg, count, max, min)")
    filters: Optional[QueryFilter] = Field(None, description="Filters to apply before aggregation")
    having: Optional[Dict[str, Any]] = Field(None, description="Post-aggregation filters")


class DatabaseQuery(BaseModel):
    """Generic database query that abstracts away SQL vs NoSQL differences."""
    operation: str = Field(..., description="Query operation: 'find', 'aggregate', 'count', 'distinct'")
    collection_table: str = Field(..., description="Target collection/table name")
    filters: Optional[QueryFilter] = Field(None, description="Query filters")
    aggregation: Optional[AggregationQuery] = Field(None, description="Aggregation specification")
    projection: Optional[List[str]] = Field(None, description="Fields to include in results")
    native_query: Optional[Dict[str, Any]] = Field(None, description="Database-specific native query")


class MetricsAdapter(ABC):
    """Abstract base class for metrics database adapters with read and write capabilities."""
    
    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the database."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the database."""
        pass
    
    # Generic read operations
    @abstractmethod
    async def query_metrics(self, filters: QueryFilter) -> List[MetricTuple]:
        """Query metrics based on filter criteria."""
        pass
    
    @abstractmethod
    async def aggregate_metrics(
        self, 
        aggregation_query: AggregationQuery
    ) -> List[Dict[str, Any]]:
        """Perform aggregations on metrics data."""
        pass
    
    @abstractmethod
    async def count_metrics(self, filters: QueryFilter) -> int:
        """Count metrics matching the filter criteria."""
        pass
    
    @abstractmethod
    async def distinct_values(self, field: str, filters: Optional[QueryFilter] = None) -> List[Any]:
        """Get distinct values for a field."""
        pass
    
    @abstractmethod
    async def execute_native_query(self, query: DatabaseQuery) -> List[Dict[str, Any]]:
        """Execute database-specific native queries (SQL for SQL DBs, aggregation pipelines for MongoDB)."""
        pass
    
    @abstractmethod
    async def get_schema_info(self) -> Dict[str, Any]:
        """Get information about available tables/collections, fields, and their types."""
        pass
    
    @abstractmethod
    async def explain_query(self, query: DatabaseQuery) -> Dict[str, Any]:
        """Explain query execution plan for optimization."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the database connection is healthy."""
        pass
    
    # Write operations
    @abstractmethod
    async def insert_metric(self, metric: MetricTuple) -> str:
        """Insert a single metric and return its ID."""
        pass
    
    @abstractmethod
    async def insert_metrics_batch(self, metrics: List[MetricTuple]) -> List[str]:
        """Insert multiple metrics and return their IDs."""
        pass
    
    @abstractmethod
    async def update_metric(self, metric_id: str, updates: Dict[str, Any]) -> bool:
        """Update a metric by ID."""
        pass
    
    @abstractmethod
    async def delete_metric(self, metric_id: str) -> bool:
        """Delete a metric by ID."""
        pass
    
    @abstractmethod
    async def delete_metrics(self, filters: QueryFilter) -> int:
        """Delete metrics matching the filter criteria."""
        pass


class MetricsQueryAdapter(ABC):
    """Abstract base class for read-only metrics database adapters."""
    
    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the database."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the database."""
        pass
    
    @abstractmethod
    async def query_metrics(self, filters: QueryFilter) -> List[MetricTuple]:
        """Query metrics based on filter criteria."""
        pass
    
    @abstractmethod
    async def aggregate_metrics(
        self, 
        aggregation_query: AggregationQuery
    ) -> List[Dict[str, Any]]:
        """Perform aggregations on metrics data."""
        pass
    
    @abstractmethod
    async def count_metrics(self, filters: QueryFilter) -> int:
        """Count metrics matching the filter criteria."""
        pass
    
    @abstractmethod
    async def distinct_values(self, field: str, filters: Optional[QueryFilter] = None) -> List[Any]:
        """Get distinct values for a field."""
        pass
    
    @abstractmethod
    async def execute_native_query(self, query: DatabaseQuery) -> List[Dict[str, Any]]:
        """Execute database-specific native queries."""
        pass
    
    @abstractmethod
    async def get_schema_info(self) -> Dict[str, Any]:
        """Get information about available tables/collections, fields, and their types."""
        pass
    
    @abstractmethod
    async def explain_query(self, query: DatabaseQuery) -> Dict[str, Any]:
        """Explain query execution plan for optimization."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the database connection is healthy."""
        pass


@dataclass
class DatabaseConfig:
    """Configuration for database connections."""
    database_type: DatabaseType
    connection_params: Dict[str, Any]
    
    # Connection optimizations
    read_only: bool = False  # Changed default to False to support write operations
    connection_pool_size: int = 20
    query_timeout: int = 30
    enable_query_cache: bool = True
    
    # Query-specific configuration
    default_limit: int = 1000
    max_limit: int = 10000
    enable_explain: bool = True


class MetricsDatabase:
    """Main database abstraction for metrics with read and write capabilities."""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.adapter: Optional[MetricsAdapter] = None
        self._connected = False
    
    async def initialize(self) -> None:
        """Initialize the database adapter based on configuration."""
        if self.config.database_type == DatabaseType.SQLITE:
            from app.core.adapters.sqlite_adapter import SQLiteMetricsAdapter
            self.adapter = SQLiteMetricsAdapter(self.config)
        elif self.config.database_type == DatabaseType.MONGODB:
            from app.core.adapters.mongodb_adapter import MongoDBMetricsAdapter
            self.adapter = MongoDBMetricsAdapter(self.config)
        elif self.config.database_type == DatabaseType.POSTGRESQL:
            # PostgreSQL adapter not yet implemented for write operations
            raise ValueError("PostgreSQL adapter for write operations not yet implemented")
        else:
            raise ValueError(f"Unsupported database type: {self.config.database_type}")
        
        await self.adapter.connect()
        self._connected = True
    
    async def close(self) -> None:
        """Close the database connection."""
        if self.adapter and self._connected:
            await self.adapter.disconnect()
            self._connected = False
    
    def _ensure_connected(self) -> None:
        """Ensure the database is connected."""
        if not self._connected or not self.adapter:
            raise RuntimeError("Database not initialized. Call initialize() first.")
    
    # Generic read operations
    async def query_metrics(self, filters: QueryFilter) -> List[MetricTuple]:
        """Query metrics based on filter criteria."""
        self._ensure_connected()
        return await self.adapter.query_metrics(filters)
    
    async def aggregate_metrics(self, aggregation_query: AggregationQuery) -> List[Dict[str, Any]]:
        """Perform aggregations on metrics data."""
        self._ensure_connected()
        return await self.adapter.aggregate_metrics(aggregation_query)
    
    async def count_metrics(self, filters: QueryFilter) -> int:
        """Count metrics matching the filter criteria."""
        self._ensure_connected()
        return await self.adapter.count_metrics(filters)
    
    async def distinct_values(self, field: str, filters: Optional[QueryFilter] = None) -> List[Any]:
        """Get distinct values for a field."""
        self._ensure_connected()
        return await self.adapter.distinct_values(field, filters)
    
    async def execute_native_query(self, query: DatabaseQuery) -> List[Dict[str, Any]]:
        """Execute database-specific native queries."""
        self._ensure_connected()
        return await self.adapter.execute_native_query(query)
    
    async def get_schema_info(self) -> Dict[str, Any]:
        """Get database schema information."""
        self._ensure_connected()
        return await self.adapter.get_schema_info()
    
    async def explain_query(self, query: DatabaseQuery) -> Dict[str, Any]:
        """Explain query execution plan."""
        self._ensure_connected()
        return await self.adapter.explain_query(query)
    
    async def health_check(self) -> bool:
        """Check database health."""
        if not self._connected or not self.adapter:
            return False
        return await self.adapter.health_check()
    
    # Write operations
    async def insert_metric(self, metric: MetricTuple) -> str:
        """Insert a single metric and return its ID."""
        self._ensure_connected()
        return await self.adapter.insert_metric(metric)
    
    async def insert_metrics_batch(self, metrics: List[MetricTuple]) -> List[str]:
        """Insert multiple metrics and return their IDs."""
        self._ensure_connected()
        return await self.adapter.insert_metrics_batch(metrics)
    
    async def update_metric(self, metric_id: str, updates: Dict[str, Any]) -> bool:
        """Update a metric by ID."""
        self._ensure_connected()
        return await self.adapter.update_metric(metric_id, updates)
    
    async def delete_metric(self, metric_id: str) -> bool:
        """Delete a metric by ID."""
        self._ensure_connected()
        return await self.adapter.delete_metric(metric_id)
    
    async def delete_metrics(self, filters: QueryFilter) -> int:
        """Delete metrics matching the filter criteria."""
        self._ensure_connected()
        return await self.adapter.delete_metrics(filters)


class MetricsQueryDatabase:
    """Main database abstraction for read-only metric queries."""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.adapter: Optional[MetricsQueryAdapter] = None
        self._connected = False
    
    async def initialize(self) -> None:
        """Initialize the database adapter based on configuration."""
        if self.config.database_type == DatabaseType.SQLITE:
            from app.core.adapters.sqlite_query_adapter import SQLiteQueryAdapter
            self.adapter = SQLiteQueryAdapter(self.config)
        elif self.config.database_type == DatabaseType.MONGODB:
            from app.core.adapters.mongodb_query_adapter import MongoDBQueryAdapter
            self.adapter = MongoDBQueryAdapter(self.config)
        elif self.config.database_type == DatabaseType.POSTGRESQL:
            from app.core.adapters.postgresql_query_adapter import PostgreSQLQueryAdapter
            self.adapter = PostgreSQLQueryAdapter(self.config)
        else:
            raise ValueError(f"Unsupported database type: {self.config.database_type}")
        
        await self.adapter.connect()
        self._connected = True
    
    async def close(self) -> None:
        """Close the database connection."""
        if self.adapter and self._connected:
            await self.adapter.disconnect()
            self._connected = False
    
    def _ensure_connected(self) -> None:
        """Ensure the database is connected."""
        if not self._connected or not self.adapter:
            raise RuntimeError("Database not initialized. Call initialize() first.")
    
    async def query_metrics(self, filters: QueryFilter) -> List[MetricTuple]:
        """Query metrics based on filter criteria."""
        self._ensure_connected()
        return await self.adapter.query_metrics(filters)
    
    async def aggregate_metrics(self, aggregation_query: AggregationQuery) -> List[Dict[str, Any]]:
        """Perform aggregations on metrics data."""
        self._ensure_connected()
        return await self.adapter.aggregate_metrics(aggregation_query)
    
    async def count_metrics(self, filters: QueryFilter) -> int:
        """Count metrics matching the filter criteria."""
        self._ensure_connected()
        return await self.adapter.count_metrics(filters)
    
    async def distinct_values(self, field: str, filters: Optional[QueryFilter] = None) -> List[Any]:
        """Get distinct values for a field."""
        self._ensure_connected()
        return await self.adapter.distinct_values(field, filters)
    
    async def execute_native_query(self, query: DatabaseQuery) -> List[Dict[str, Any]]:
        """Execute database-specific native queries."""
        self._ensure_connected()
        return await self.adapter.execute_native_query(query)
    
    async def get_schema_info(self) -> Dict[str, Any]:
        """Get database schema information."""
        self._ensure_connected()
        return await self.adapter.get_schema_info()
    
    async def explain_query(self, query: DatabaseQuery) -> Dict[str, Any]:
        """Explain query execution plan."""
        self._ensure_connected()
        return await self.adapter.explain_query(query)
    
    async def health_check(self) -> bool:
        """Check database health."""
        if not self._connected or not self.adapter:
            return False
        return await self.adapter.health_check()


# Factory function for creating database configurations
def create_database_config(
    db_type: str,
    **connection_params
) -> DatabaseConfig:
    """Create a database configuration from string type and parameters."""
    return DatabaseConfig(
        database_type=DatabaseType(db_type.lower()),
        connection_params=connection_params
    )


# Configuration presets for read-write access
def get_sqlite_config(db_path: str = "./metrics.db") -> DatabaseConfig:
    """Get SQLite configuration for local development with read-write access."""
    return DatabaseConfig(
        database_type=DatabaseType.SQLITE,
        connection_params={"database_path": db_path},
        read_only=False,
        enable_query_cache=True
    )


def get_mongodb_config(
    connection_string: str,
    database_name: str = "metrics_db",
    collection_name: str = "metrics"
) -> DatabaseConfig:
    """Get MongoDB configuration for production with read-write access."""
    return DatabaseConfig(
        database_type=DatabaseType.MONGODB,
        connection_params={
            "connection_string": connection_string,
            "database_name": database_name,
            "collection_name": collection_name
        },
        read_only=False,
        connection_pool_size=30
    )


def get_postgresql_config(
    host: str,
    port: int,
    database: str,
    username: str,
    password: str
) -> DatabaseConfig:
    """Get PostgreSQL configuration for production with read-write access."""
    return DatabaseConfig(
        database_type=DatabaseType.POSTGRESQL,
        connection_params={
            "host": host,
            "port": port,
            "database": database,
            "username": username,
            "password": password
        },
        read_only=False,
        connection_pool_size=30,
        enable_explain=True
    )


# Configuration presets for read-only access
def get_sqlite_query_config(db_path: str = "./metrics.db") -> DatabaseConfig:
    """Get SQLite configuration for local querying."""
    return DatabaseConfig(
        database_type=DatabaseType.SQLITE,
        connection_params={"database_path": db_path},
        read_only=True,
        enable_query_cache=True
    )


def get_mongodb_query_config(
    connection_string: str,
    database_name: str = "metrics_db",
    collection_name: str = "metrics"
) -> DatabaseConfig:
    """Get MongoDB configuration for production querying."""
    return DatabaseConfig(
        database_type=DatabaseType.MONGODB,
        connection_params={
            "connection_string": connection_string,
            "database_name": database_name,
            "collection_name": collection_name
        },
        read_only=True,
        connection_pool_size=50  # Higher for read-heavy workloads
    )


def get_postgresql_query_config(
    host: str,
    port: int,
    database: str,
    username: str,
    password: str
) -> DatabaseConfig:
    """Get PostgreSQL configuration for complex queries."""
    return DatabaseConfig(
        database_type=DatabaseType.POSTGRESQL,
        connection_params={
            "host": host,
            "port": port,
            "database": database,
            "username": username,
            "password": password
        },
        read_only=True,
        connection_pool_size=30,
        enable_explain=True  # PostgreSQL has excellent EXPLAIN capabilities
    ) 