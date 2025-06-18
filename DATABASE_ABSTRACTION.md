# Database Abstraction Layer for Metrics

This document describes the database abstraction layer that allows the application to seamlessly switch between different database backends for metrics storage.

## Overview

The database abstraction layer provides a unified interface for storing and querying metrics data across different database types:

- **SQLite** - For local development and testing
- **MongoDB** - For production NoSQL deployments  
- **PostgreSQL** - For production SQL deployments (extensible)

## Architecture

### Core Components

1. **MetricsAdapter** (Abstract Base Class)
   - Defines the interface all database adapters must implement
   - Provides methods for CRUD operations and aggregations

2. **Database Adapters**
   - `SQLiteMetricsAdapter` - SQLite implementation
   - `MongoDBMetricsAdapter` - MongoDB implementation
   - `PostgreSQLMetricsAdapter` - PostgreSQL implementation (extensible)

3. **MetricsDatabase** (Main Interface)
   - Factory class that manages different adapters
   - Provides unified API regardless of underlying database

4. **LLM Tools Layer**
   - LangChain tools that use the abstraction layer
   - Easy-to-use functions for AI/LLM integration

## Data Model

### MetricTuple

The core data structure represents a metric as a tuple with:

```python
class MetricTuple(BaseModel):
    attributes: Dict[str, Any]  # Key-value attributes (category, region, etc.)
    values: Dict[str, Union[float, int]]  # Metric values
    timestamp: datetime  # When the metric was recorded
```

**Example:**
```python
MetricTuple(
    attributes={
        "category": "engagement",
        "metric_name": "daily_active_users",
        "region": "us-east",
        "team": "product"
    },
    values={
        "daily_active_users": 1500,
        "sample_count": 100,
        "confidence": 0.95
    },
    timestamp=datetime.utcnow()
)
```

### QueryFilter

Flexible filtering for metric queries:

```python
class QueryFilter(BaseModel):
    attributes: Optional[Dict[str, Any]]  # Filter by attributes
    value_filters: Optional[Dict[str, Dict[str, Union[float, int]]]]  # Value filters with operators
    time_range: Optional[Tuple[datetime, datetime]]  # Time range
    limit: Optional[int]  # Result limit
    sort_by: Optional[str]  # Sort field
    sort_order: Optional[str]  # Sort order
```

**Example:**
```python
QueryFilter(
    attributes={"category": "performance"},
    value_filters={"response_time": {"$lte": 200}},
    time_range=(start_time, end_time),
    limit=50
)
```

## Configuration

### Environment Variables

```bash
# Metrics Database Type (sqlite, mongodb, postgresql)
METRICS_DB_TYPE=sqlite

# SQLite Configuration
METRICS_DB_PATH=./metrics.db

# MongoDB Configuration
METRICS_MONGODB_URI=mongodb://localhost:27017
METRICS_MONGODB_DATABASE=metrics_db
METRICS_MONGODB_COLLECTION=metrics
```

### Configuration in Code

```python
# SQLite for local development
config = get_sqlite_config("./metrics.db")

# MongoDB for production
config = get_mongodb_config(
    connection_string="mongodb://localhost:27017",
    database_name="metrics_db",
    collection_name="metrics"
)

# Initialize database
db = MetricsDatabase(config)
await db.initialize()
```

## Usage Examples

### Direct Database Usage

```python
from app.core.database_abstraction import MetricsDatabase, MetricTuple, QueryFilter
from app.core.database_abstraction import get_sqlite_config

# Initialize database
config = get_sqlite_config("./metrics.db")
db = MetricsDatabase(config)
await db.initialize()

# Insert a metric
metric = MetricTuple(
    attributes={"category": "engagement", "metric_name": "daily_users"},
    values={"daily_users": 1200, "growth_rate": 0.05},
    timestamp=datetime.utcnow()
)
metric_id = await db.insert_metric(metric)

# Query metrics
filters = QueryFilter(
    attributes={"category": "engagement"},
    time_range=(start_time, end_time),
    limit=100
)
results = await db.query_metrics(filters)

# Aggregate metrics
aggregation_results = await db.aggregate_metrics(
    filters=filters,
    group_by=["category", "region"],
    aggregations={"daily_users": "avg", "growth_rate": "sum"}
)

await db.close()
```

### Using LLM Tools

```python
from app.tools.metrics_db_tools import (
    initialize_metrics_database, 
    insert_metric_direct,
    query_metrics_direct,
    create_metrics_db_tools
)

# Initialize global database
await initialize_metrics_database()

# Direct insertion
metric_id = await insert_metric_direct(
    attributes={"category": "revenue", "region": "europe"},
    values={"daily_revenue": 15000.50}
)

# Direct querying
results = await query_metrics_direct(
    attributes={"category": "revenue"},
    days_back=7,
    limit=50
)

# Get LangChain tools for AI integration
tools = create_metrics_db_tools()
```

### LangChain Integration

```python
from app.tools.metrics_db_tools import create_metrics_db_tools

# Create tools for LangChain agents
tools = create_metrics_db_tools()

# Available tools:
# - insert_metric: Insert new metrics
# - query_metrics: Query metrics with filters
# - aggregate_metrics: Perform aggregations
# - check_database_health: Check database status

# Use with LangChain agents
from langchain.agents import initialize_agent
agent = initialize_agent(tools, llm, agent="zero-shot-react-description")

response = agent.run("Show me average daily users by region for the last 7 days")
```

## Database-Specific Features

### SQLite
- **Pros**: Zero setup, perfect for development and testing
- **Cons**: Limited concurrent access, not suitable for production scale
- **Use Cases**: Local development, automated testing, small deployments

### MongoDB
- **Pros**: Flexible schema, excellent for complex metrics, horizontal scaling
- **Cons**: Requires MongoDB setup and maintenance
- **Use Cases**: Production deployments, complex analytics, large scale

### PostgreSQL (Extensible)
- **Pros**: ACID compliance, mature ecosystem, powerful querying
- **Cons**: Requires PostgreSQL setup
- **Use Cases**: Enterprise deployments, complex relational queries

## Migration and Data Management

### Migrating from Legacy Schema

```python
from app.tools.data_migration import migrate_legacy_metrics_to_abstraction

# Migrate from old SQLAlchemy schema to new abstraction
stats = await migrate_legacy_metrics_to_abstraction()
print(f"Migrated {stats['migrated_records']} records")
```

### Generating Test Data

```python
from app.tools.data_migration import generate_sample_metrics_for_testing

# Generate sample metrics for testing
stats = await generate_sample_metrics_for_testing()
print(f"Generated {stats['generated_records']} test metrics")
```

### Data Verification

```python
from app.tools.data_migration import verify_data_consistency

# Verify data consistency between old and new formats
stats = await verify_data_consistency()
if stats['consistency_issues']:
    print("Issues found:", stats['consistency_issues'])
```

## Testing

Run the comprehensive test suite:

```bash
python test_metrics_abstraction.py
```

This will test:
- SQLite adapter functionality
- MongoDB adapter functionality (if available)
- LLM tools integration
- Data migration utilities

## Performance Considerations

### SQLite
- Use transactions for batch operations
- Consider WAL mode for better concurrency
- Regular VACUUM for maintenance

### MongoDB
- Proper indexing on frequently queried fields
- Use aggregation pipelines for complex queries
- Consider sharding for very large datasets

### General
- Use batch insertions for multiple metrics
- Implement connection pooling
- Monitor query performance and optimize filters

## Error Handling

The abstraction layer provides consistent error handling:

```python
try:
    await db.insert_metric(metric)
except Exception as e:
    logger.error(f"Failed to insert metric: {e}")
    # Handle error appropriately
```

## Extending the Abstraction

To add a new database adapter:

1. Implement the `MetricsAdapter` interface
2. Add configuration support
3. Register in `MetricsDatabase.initialize()`
4. Add tests and documentation

Example:
```python
class RedisMetricsAdapter(MetricsAdapter):
    async def connect(self) -> None:
        # Implementation
        pass
    
    async def insert_metric(self, metric: MetricTuple) -> str:
        # Implementation
        pass
    
    # ... implement all abstract methods
```

## Best Practices

1. **Always initialize the database** before use
2. **Use batch operations** for multiple metrics
3. **Implement proper error handling**
4. **Close connections** when done
5. **Use appropriate indexes** for your query patterns
6. **Monitor performance** and optimize as needed
7. **Test with realistic data volumes**

## Troubleshooting

### Common Issues

1. **Database not initialized**
   ```
   RuntimeError: Database not initialized. Call initialize() first.
   ```
   Solution: Call `await db.initialize()` or `await initialize_metrics_database()`

2. **MongoDB connection failed**
   ```
   Failed to connect to MongoDB: ...
   ```
   Solution: Ensure MongoDB is running and URI is correct

3. **SQLite locked**
   ```
   database is locked
   ```
   Solution: Ensure proper connection closing, consider WAL mode

### Debugging

Enable debug logging:
```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

Check database health:
```python
is_healthy = await db.health_check()
print(f"Database healthy: {is_healthy}")
``` 