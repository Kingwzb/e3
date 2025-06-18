# Read-Only Database Abstraction Layer

## Overview

This abstraction layer provides a **read-only interface** for querying metrics data across different database backends with support for **complex SQL queries, joins, and advanced analytics**. It's optimized for data analysis, reporting, and AI-powered querying without the risk of data mutations.

## Key Features

### 🔒 **Read-Only Safety**
- Only SELECT operations allowed
- Built-in safety checks prevent mutations
- Connection pooling optimized for read-heavy workloads
- Query timeout and resource management

### 🗄️ **Multi-Database Support**
- **SQLite**: Local development and testing
- **MongoDB**: NoSQL document-based analytics
- **PostgreSQL**: Advanced SQL features and analytics

### 🔍 **Advanced Querying**
- Complex SQL with JOINs and subqueries
- JSON path operations for flexible schemas
- Aggregations with GROUP BY and HAVING
- Raw SQL execution with safety checks
- Query optimization and explain plans

### 🤖 **AI Integration**
- LangChain tools for LLM-powered queries
- Programmatic query functions
- Natural language to SQL capabilities
- Structured query building

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        LLM Tools Layer                         │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐  │
│  │ QueryMetricsTool│ │   RawSQLTool    │ │DatabaseHealthTool│  │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                  MetricsQueryDatabase                           │
│              (Main Abstraction Layer)                          │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                 MetricsQueryAdapter                             │
│                  (Abstract Interface)                          │
└─────────────────────────────────────────────────────────────────┘
                                │
   ┌────────────────────────────┼────────────────────────────┐
   │                            │                            │
┌──▼──────────────┐   ┌────────▼─────────┐   ┌─────────▼────────┐
│SQLiteQueryAdapter│   │MongoDBQueryAdapter│   │PostgreSQLQueryAdapter│
│                 │   │                  │   │                  │
│ • JSON ops      │   │ • Aggregation    │   │ • Advanced SQL   │
│ • Connection    │   │   pipelines      │   │ • Window funcs   │
│   pooling       │   │ • Native queries │   │ • CTEs          │
│ • Query cache   │   │ • Index hints    │   │ • Explain plans │
└─────────────────┘   └──────────────────┘   └──────────────────┘
```

## Configuration

### Environment Variables

```bash
# Database Type Selection
METRICS_DB_TYPE=sqlite  # sqlite, mongodb, postgresql

# SQLite Configuration
METRICS_DB_PATH=./metrics.db

# MongoDB Configuration  
METRICS_MONGODB_URI=mongodb://localhost:27017
METRICS_MONGODB_DATABASE=metrics_db
METRICS_MONGODB_COLLECTION=metrics

# PostgreSQL Configuration
METRICS_PG_HOST=localhost
METRICS_PG_PORT=5432
METRICS_PG_DATABASE=metrics
METRICS_PG_USERNAME=postgres
METRICS_PG_PASSWORD=your_password

# Query Optimization
METRICS_QUERY_TIMEOUT=30
METRICS_CONNECTION_POOL_SIZE=20
METRICS_ENABLE_QUERY_CACHE=true
METRICS_DEFAULT_LIMIT=1000
METRICS_MAX_LIMIT=10000
```

### Programmatic Configuration

```python
from app.core.database_abstraction import (
    get_sqlite_query_config, 
    get_postgresql_query_config,
    MetricsQueryDatabase
)

# SQLite for local development
config = get_sqlite_query_config("./analytics.db")

# PostgreSQL for production analytics
config = get_postgresql_query_config(
    host="analytics-db.company.com",
    port=5432,
    database="metrics_warehouse",
    username="readonly_user",
    password="secure_password"
)

# Initialize database
db = MetricsQueryDatabase(config)
await db.initialize()
```

## Usage Examples

### Basic Querying

```python
from app.core.database_abstraction import QueryFilter
from datetime import datetime, timedelta

# Query by attributes
filters = QueryFilter(
    attributes={"category": "engagement", "region": "us-east"},
    limit=100,
    sort_by="timestamp",
    sort_order="desc"
)
results = await db.query_metrics(filters)

# Query by value ranges
filters = QueryFilter(
    value_filters={
        "daily_users": {"$gte": 1000, "$lte": 10000},
        "revenue": {"$gt": 500}
    },
    time_range=(
        datetime.now() - timedelta(days=30),
        datetime.now()
    )
)
results = await db.query_metrics(filters)
```

### Complex SQL Queries

```python
# Advanced analytics with JSON operations
sql = """
SELECT 
    JSON_EXTRACT(attributes, '$.region') as region,
    JSON_EXTRACT(attributes, '$.category') as category,
    COUNT(*) as metric_count,
    AVG(CAST(JSON_EXTRACT(metric_values, '$.daily_users') AS FLOAT)) as avg_users,
    SUM(CAST(JSON_EXTRACT(metric_values, '$.revenue') AS FLOAT)) as total_revenue,
    MAX(timestamp) as latest_update
FROM metrics 
WHERE timestamp >= date('now', '-90 days')
  AND JSON_EXTRACT(metric_values, '$.daily_users') > 100
GROUP BY 
    JSON_EXTRACT(attributes, '$.region'),
    JSON_EXTRACT(attributes, '$.category')
HAVING COUNT(*) >= 5
ORDER BY total_revenue DESC
LIMIT 20
"""

results = await db.execute_raw_sql(sql)
```

### Complex Query Builder

```python
from app.core.database_abstraction import ComplexQuery, JoinConfig

# Build complex query with joins
query = ComplexQuery(
    base_table="metrics",
    joins=[
        JoinConfig(
            join_type="left",
            tables=["metrics", "user_segments"],
            on_fields={"metrics.user_id": "user_segments.user_id"},
            select_fields=["metrics.*", "user_segments.segment"]
        )
    ],
    group_by=["attributes.region", "user_segments.segment"],
    aggregations={
        "values.daily_users": "avg",
        "values.revenue": "sum"
    },
    filters=QueryFilter(
        time_range=(datetime.now() - timedelta(days=30), datetime.now())
    )
)

results = await db.execute_complex_query(query)
```

### Aggregations

```python
# Multi-dimensional aggregation
results = await db.aggregate_metrics(
    filters=QueryFilter(
        attributes={"category": "engagement"},
        value_filters={"daily_users": {"$gte": 100}}
    ),
    group_by=["attributes.region", "attributes.platform"],
    aggregations={
        "values.daily_users": "avg",
        "values.session_duration": "max", 
        "values.bounce_rate": "min"
    }
)
```

## LLM Tools Integration

### Available Tools

1. **QueryMetricsTool**: Flexible filtering and sorting
2. **RawSQLTool**: Execute complex SQL queries
3. **DatabaseHealthTool**: Check connection status

### Usage in LangChain

```python
from app.tools.metrics_query_tools import METRICS_QUERY_TOOLS
from langchain.agents import initialize_agent

# Add tools to LangChain agent
agent = initialize_agent(
    tools=METRICS_QUERY_TOOLS,
    llm=your_llm,
    agent_type="openai-functions"
)

# Natural language querying
response = agent.run(
    "Show me the top 5 regions by average daily users for engagement metrics in the last 30 days"
)
```

### Programmatic Functions

```python
from app.tools.metrics_query_tools import (
    query_metrics_data,
    execute_sql_query,
    get_database_schema
)

# Direct function calls
results = await query_metrics_data({
    "attributes": {"category": "revenue"},
    "value_filters": {"amount": {"$gte": 1000}},
    "limit": 50
})

# Execute custom SQL
results = await execute_sql_query("""
    SELECT region, AVG(daily_users) as avg_users
    FROM metrics_view 
    WHERE date >= '2024-01-01'
    GROUP BY region
""")

# Get schema information
schema = await get_database_schema()
```

## Database-Specific Features

### SQLite Optimizations
- WAL mode for concurrent reads
- Memory-mapped I/O for performance
- JSON1 extension for JSON operations
- Connection pooling for scalability

```python
# SQLite-specific JSON queries
sql = """
SELECT 
    json_extract(attributes, '$.category') as category,
    avg(json_extract(metric_values, '$.score')) as avg_score
FROM metrics 
WHERE json_extract(attributes, '$.region') = 'us-east'
GROUP BY json_extract(attributes, '$.category')
"""
```

### PostgreSQL Advanced Features
- JSONB operations and indexing
- Window functions and CTEs
- Advanced aggregations (percentiles, etc.)
- Sophisticated query optimization

```python
# PostgreSQL-specific features
sql = """
WITH monthly_trends AS (
    SELECT 
        date_trunc('month', timestamp) as month,
        attributes->>'category' as category,
        avg((metric_values->>'daily_users')::numeric) as avg_users,
        lag(avg((metric_values->>'daily_users')::numeric)) 
            OVER (PARTITION BY attributes->>'category' ORDER BY date_trunc('month', timestamp)) as prev_month
    FROM metrics 
    WHERE timestamp >= now() - interval '12 months'
    GROUP BY date_trunc('month', timestamp), attributes->>'category'
)
SELECT 
    month,
    category,
    avg_users,
    ((avg_users - prev_month) / prev_month * 100) as growth_rate
FROM monthly_trends
WHERE prev_month IS NOT NULL
ORDER BY month DESC, growth_rate DESC
"""
```

### MongoDB Aggregation Pipelines
- Native document operations
- Powerful aggregation framework
- Flexible schema handling

```python
# MongoDB aggregation pipeline
pipeline = [
    {"$match": {"timestamp": {"$gte": datetime.now() - timedelta(days=30)}}},
    {"$group": {
        "_id": {
            "region": "$attributes.region",
            "category": "$attributes.category"
        },
        "avg_users": {"$avg": "$values.daily_users"},
        "total_revenue": {"$sum": "$values.revenue"},
        "count": {"$sum": 1}
    }},
    {"$sort": {"total_revenue": -1}},
    {"$limit": 20}
]
```

## Performance Optimization

### Query Optimization
- Automatic query plan analysis
- Index usage recommendations
- Connection pooling
- Query result caching

```python
# Get query execution plan
explain_result = await db.explain_query("""
    SELECT region, COUNT(*) 
    FROM metrics 
    WHERE timestamp >= '2024-01-01'
    GROUP BY region
""")

print("Execution plan:", explain_result)
```

### Best Practices
1. **Use appropriate indexes** on timestamp and frequently queried JSON fields
2. **Limit result sets** to avoid memory issues
3. **Use parameterized queries** for repeated operations
4. **Monitor query performance** with explain plans
5. **Implement connection pooling** for concurrent access

## Safety Features

### Read-Only Enforcement
- SQL parsing to block mutations
- Whitelist of allowed operations
- Connection-level read-only settings
- Query timeout protection

```python
# These will be blocked automatically:
# await db.execute_raw_sql("DELETE FROM metrics")  # ❌ Blocked
# await db.execute_raw_sql("UPDATE metrics SET ...")  # ❌ Blocked
# await db.execute_raw_sql("DROP TABLE metrics")  # ❌ Blocked

# This is allowed:
await db.execute_raw_sql("SELECT * FROM metrics LIMIT 10")  # ✅ Allowed
```

### Resource Management
- Query timeouts prevent runaway queries
- Connection limits prevent resource exhaustion
- Result set size limits prevent memory issues
- Automatic connection cleanup

## Error Handling

```python
try:
    results = await db.execute_raw_sql("SELECT * FROM non_existent_table")
except Exception as e:
    if "not found" in str(e).lower():
        print("Table doesn't exist")
    elif "timeout" in str(e).lower():
        print("Query timed out")
    else:
        print(f"Database error: {e}")
```

## Migration from Write-Enabled System

If you're migrating from a write-enabled metrics system:

1. **Update imports**: Change from `metrics_db_tools` to `metrics_query_tools`
2. **Remove mutation calls**: Replace `insert_metric` calls with data ingestion pipelines
3. **Update query patterns**: Use new filtering and aggregation methods
4. **Add safety checks**: Implement read-only connection validation

## Conclusion

This read-only database abstraction provides:

- **Safety**: No risk of accidental data mutations
- **Performance**: Optimized for read-heavy analytical workloads
- **Flexibility**: Support for simple filters to complex SQL analytics
- **Portability**: Easy switching between database types
- **AI Integration**: Native support for LLM-powered querying

Perfect for analytics dashboards, reporting systems, and AI-powered data exploration where you need powerful querying without the risk of data corruption. 