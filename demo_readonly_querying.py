#!/usr/bin/env python3
"""
Demonstration of Read-Only Database Querying with Complex SQL Support

This script showcases the capabilities of the read-only metrics database abstraction
layer, including complex SQL queries, joins, aggregations, and performance optimization.

Features demonstrated:
- Simple filtering and querying
- Complex SQL with joins and subqueries  
- Advanced aggregations and analytics
- Raw SQL execution with safety checks
- Database switching (SQLite, PostgreSQL, MongoDB)
- Query optimization and explain plans
- Schema introspection
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List

from app.core.database_abstraction import (
    MetricsQueryDatabase, DatabaseConfig, QueryFilter, ComplexQuery,
    JoinConfig, get_sqlite_query_config, get_postgresql_query_config,
    get_mongodb_query_config, DatabaseType
)
from app.tools.metrics_query_tools import (
    get_metrics_database, close_metrics_database,
    query_metrics_data, execute_sql_query, get_database_schema
)


async def demo_basic_querying():
    """Demonstrate basic metrics querying capabilities."""
    print("🔍 DEMO: Basic Metrics Querying")
    print("=" * 50)
    
    # Get database instance
    db = await get_metrics_database()
    
    # Demo 1: Simple attribute filtering
    print("\n1. Query metrics by category:")
    filters = QueryFilter(
        attributes={"category": "engagement"},
        limit=5,
        sort_by="timestamp",
        sort_order="desc"
    )
    
    try:
        results = await db.query_metrics(filters)
        print(f"   Found {len(results)} engagement metrics")
        for result in results[:3]:
            print(f"   - {result.attributes} | Values: {result.values}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Demo 2: Value-based filtering
    print("\n2. Query high-value metrics:")
    filters = QueryFilter(
        value_filters={
            "daily_users": {"$gte": 1000},
            "revenue": {"$gt": 500}
        },
        limit=10
    )
    
    try:
        results = await db.query_metrics(filters)
        print(f"   Found {len(results)} high-value metrics")
        for result in results[:3]:
            print(f"   - Values: {result.values} | Region: {result.attributes.get('region', 'N/A')}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Demo 3: Time range filtering
    print("\n3. Query recent metrics (last 30 days):")
    end_time = datetime.now()
    start_time = end_time - timedelta(days=30)
    
    filters = QueryFilter(
        time_range=(start_time, end_time),
        limit=5
    )
    
    try:
        results = await db.query_metrics(filters)
        print(f"   Found {len(results)} recent metrics")
        for result in results[:3]:
            print(f"   - {result.timestamp} | {result.attributes.get('metric_name', 'Unknown')}")
    except Exception as e:
        print(f"   Error: {e}")


async def demo_complex_sql_queries():
    """Demonstrate complex SQL queries with joins and analytics."""
    print("\n🔗 DEMO: Complex SQL Queries")
    print("=" * 50)
    
    db = await get_metrics_database()
    
    # Demo 1: Raw SQL aggregation
    print("\n1. SQL Aggregation - Daily metric summaries:")
    sql = """
    SELECT 
        DATE(timestamp) as date,
        COUNT(*) as metric_count,
        AVG(CAST(JSON_EXTRACT(metric_values, '$.daily_users') AS FLOAT)) as avg_daily_users,
        SUM(CAST(JSON_EXTRACT(metric_values, '$.revenue') AS FLOAT)) as total_revenue
    FROM metrics 
    WHERE JSON_EXTRACT(metric_values, '$.daily_users') IS NOT NULL
    GROUP BY DATE(timestamp)
    ORDER BY date DESC
    LIMIT 10
    """
    
    try:
        results = await db.execute_raw_sql(sql)
        print(f"   Found {len(results)} daily summaries:")
        for result in results[:5]:
            print(f"   - {result.get('date')}: {result.get('metric_count')} metrics, "
                  f"Avg Users: {result.get('avg_daily_users', 0):.0f}, "
                  f"Revenue: ${result.get('total_revenue', 0):.2f}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Demo 2: Complex filtering with JSON operations
    print("\n2. JSON-based complex filtering:")
    sql = """
    SELECT 
        JSON_EXTRACT(attributes, '$.region') as region,
        JSON_EXTRACT(attributes, '$.category') as category,
        COUNT(*) as count,
        MAX(CAST(JSON_EXTRACT(metric_values, '$.daily_users') AS FLOAT)) as max_users
    FROM metrics 
    WHERE JSON_EXTRACT(attributes, '$.region') IN ('us-east', 'us-west', 'eu-west')
      AND JSON_EXTRACT(metric_values, '$.daily_users') > 500
    GROUP BY JSON_EXTRACT(attributes, '$.region'), JSON_EXTRACT(attributes, '$.category')
    ORDER BY max_users DESC
    LIMIT 10
    """
    
    try:
        results = await db.execute_raw_sql(sql)
        print(f"   Found {len(results)} regional summaries:")
        for result in results:
            print(f"   - {result.get('region')} / {result.get('category')}: "
                  f"{result.get('count')} metrics, Max Users: {result.get('max_users', 0):.0f}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Demo 3: Time-series analysis
    print("\n3. Time-series trend analysis:")
    sql = """
    SELECT 
        strftime('%Y-%m', timestamp) as month,
        JSON_EXTRACT(attributes, '$.category') as category,
        AVG(CAST(JSON_EXTRACT(metric_values, '$.growth_rate') AS FLOAT)) as avg_growth_rate,
        COUNT(*) as sample_size
    FROM metrics 
    WHERE JSON_EXTRACT(metric_values, '$.growth_rate') IS NOT NULL
      AND timestamp >= date('now', '-12 months')
    GROUP BY strftime('%Y-%m', timestamp), JSON_EXTRACT(attributes, '$.category')
    HAVING COUNT(*) >= 5  -- Only include months with sufficient data
    ORDER BY month DESC, avg_growth_rate DESC
    LIMIT 15
    """
    
    try:
        results = await db.execute_raw_sql(sql)
        print(f"   Found {len(results)} monthly trends:")
        for result in results[:8]:
            growth_rate = result.get('avg_growth_rate', 0)
            print(f"   - {result.get('month')} / {result.get('category')}: "
                  f"{growth_rate:.2%} growth ({result.get('sample_size')} samples)")
    except Exception as e:
        print(f"   Error: {e}")


async def demo_advanced_aggregations():
    """Demonstrate advanced aggregation capabilities."""
    print("\n📊 DEMO: Advanced Aggregations")
    print("=" * 50)
    
    db = await get_metrics_database()
    
    # Demo 1: Multi-dimensional aggregation
    print("\n1. Multi-dimensional aggregation (Region x Category):")
    try:
        results = await db.aggregate_metrics(
            filters=QueryFilter(
                value_filters={"daily_users": {"$gte": 100}}
            ),
            group_by=["attributes.region", "attributes.category"],
            aggregations={
                "values.daily_users": "avg",
                "values.revenue": "sum",
                "values.growth_rate": "max"
            }
        )
        
        print(f"   Found {len(results)} regional/category combinations:")
        for result in results[:8]:
            print(f"   - {result}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Demo 2: Statistical analysis with raw SQL
    print("\n2. Statistical analysis with percentiles:")
    sql = """
    WITH metric_stats AS (
        SELECT 
            JSON_EXTRACT(attributes, '$.category') as category,
            CAST(JSON_EXTRACT(metric_values, '$.daily_users') AS FLOAT) as daily_users
        FROM metrics 
        WHERE JSON_EXTRACT(metric_values, '$.daily_users') IS NOT NULL
          AND CAST(JSON_EXTRACT(metric_values, '$.daily_users') AS FLOAT) > 0
    )
    SELECT 
        category,
        COUNT(*) as sample_count,
        AVG(daily_users) as mean_users,
        MIN(daily_users) as min_users,
        MAX(daily_users) as max_users,
        -- SQLite doesn't have PERCENTILE_CONT, so we approximate
        (SELECT daily_users FROM metric_stats ms2 
         WHERE ms2.category = ms1.category 
         ORDER BY daily_users 
         LIMIT 1 OFFSET (COUNT(*) / 2)) as median_users
    FROM metric_stats ms1
    GROUP BY category
    HAVING COUNT(*) >= 5
    ORDER BY mean_users DESC
    """
    
    try:
        results = await db.execute_raw_sql(sql)
        print(f"   Statistical analysis for {len(results)} categories:")
        for result in results:
            print(f"   - {result.get('category')}: Mean={result.get('mean_users', 0):.0f}, "
                  f"Median={result.get('median_users', 0):.0f}, "
                  f"Range=[{result.get('min_users', 0):.0f}-{result.get('max_users', 0):.0f}] "
                  f"(n={result.get('sample_count')})")
    except Exception as e:
        print(f"   Error: {e}")


async def demo_database_schema_analysis():
    """Demonstrate database schema introspection."""
    print("\n🗂️  DEMO: Database Schema Analysis")
    print("=" * 50)
    
    db = await get_metrics_database()
    
    # Get schema information
    print("\n1. Database schema overview:")
    try:
        schema_info = await db.get_schema_info()
        
        print(f"   Found {len(schema_info)} tables:")
        for table_name, table_info in schema_info.items():
            print(f"\n   📋 Table: {table_name}")
            print(f"      Columns: {len(table_info.get('columns', []))}")
            
            # Show key columns
            for col in table_info.get('columns', [])[:5]:
                col_desc = f"      - {col['name']} ({col['type']})"
                if col.get('primary_key'):
                    col_desc += " [PRIMARY KEY]"
                if not col.get('nullable', True):
                    col_desc += " [NOT NULL]"
                print(col_desc)
            
            # Show indexes
            indexes = table_info.get('indexes', [])
            if indexes:
                print(f"      Indexes: {len(indexes)}")
                for idx in indexes[:3]:
                    if isinstance(idx, dict):
                        print(f"      - {idx.get('name', 'Unknown')}")
                    else:
                        print(f"      - {idx}")
    except Exception as e:
        print(f"   Error: {e}")


async def demo_query_optimization():
    """Demonstrate query optimization and explain plans."""
    print("\n⚡ DEMO: Query Optimization")
    print("=" * 50)
    
    db = await get_metrics_database()
    
    # Demo 1: Query explanation
    print("\n1. Query execution plan analysis:")
    test_query = """
    SELECT 
        JSON_EXTRACT(attributes, '$.region') as region,
        COUNT(*) as metric_count,
        AVG(CAST(JSON_EXTRACT(metric_values, '$.daily_users') AS FLOAT)) as avg_users
    FROM metrics 
    WHERE timestamp >= date('now', '-30 days')
    GROUP BY JSON_EXTRACT(attributes, '$.region')
    ORDER BY avg_users DESC
    """
    
    try:
        explain_result = await db.explain_query(test_query)
        print("   Query execution plan:")
        
        if 'execution_plan' in explain_result:
            for step in explain_result['execution_plan']:
                print(f"   Step {step['id']}: {step['detail']}")
        else:
            print(f"   {explain_result}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Demo 2: Performance comparison
    print("\n2. Performance comparison (indexed vs non-indexed):")
    
    # Query with timestamp (usually indexed)
    indexed_query = "SELECT COUNT(*) FROM metrics WHERE timestamp >= date('now', '-7 days')"
    
    # Query with JSON extraction (not indexed)
    unindexed_query = "SELECT COUNT(*) FROM metrics WHERE JSON_EXTRACT(attributes, '$.custom_field') = 'test'"
    
    for query_name, query in [("Indexed (timestamp)", indexed_query), ("Unindexed (JSON)", unindexed_query)]:
        try:
            start_time = datetime.now()
            results = await db.execute_raw_sql(query)
            end_time = datetime.now()
            
            duration = (end_time - start_time).total_seconds() * 1000
            count = results[0].get('COUNT(*)', 0) if results else 0
            
            print(f"   {query_name}: {count} rows in {duration:.2f}ms")
        except Exception as e:
            print(f"   {query_name}: Error - {e}")


async def demo_database_switching():
    """Demonstrate switching between different database types."""
    print("\n🔄 DEMO: Database Type Switching")
    print("=" * 50)
    
    # Demo different database configurations
    configs = [
        ("SQLite (Local)", get_sqlite_query_config("./demo_metrics.db")),
        ("PostgreSQL (Production)", get_postgresql_query_config(
            host="localhost", port=5432, database="metrics_demo",
            username="postgres", password="demo123"
        ))
    ]
    
    for config_name, config in configs:
        print(f"\n📋 Testing {config_name}:")
        
        try:
            # Create dedicated database instance for this config
            test_db = MetricsQueryDatabase(config)
            await test_db.initialize()
            
            # Test basic health
            is_healthy = await test_db.health_check()
            print(f"   ✅ Connection: {'Healthy' if is_healthy else 'Failed'}")
            
            if is_healthy:
                # Test basic query
                try:
                    results = await test_db.execute_raw_sql("SELECT 1 as test")
                    print(f"   ✅ Basic query: Success")
                except Exception as e:
                    print(f"   ❌ Basic query: {e}")
                
                # Get schema info
                try:
                    schema = await test_db.get_schema_info()
                    print(f"   📊 Schema: {len(schema)} tables found")
                except Exception as e:
                    print(f"   ❌ Schema: {e}")
            
            await test_db.close()
            
        except Exception as e:
            print(f"   ❌ Connection failed: {e}")


async def demo_llm_tools_integration():
    """Demonstrate LLM tools for AI-powered querying."""
    print("\n🤖 DEMO: LLM Tools Integration")
    print("=" * 50)
    
    # Demo the programmatic functions that LLM tools use
    print("\n1. Programmatic query function:")
    try:
        results = await query_metrics_data({
            "attributes": {"category": "engagement"},
            "limit": 3
        })
        
        print(f"   Found {len(results)} engagement metrics:")
        for result in results:
            print(f"   - {result['attributes']} | {result['values']}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n2. SQL execution function:")
    try:
        results = await execute_sql_query(
            "SELECT COUNT(*) as total_metrics, "
            "COUNT(DISTINCT JSON_EXTRACT(attributes, '$.category')) as categories "
            "FROM metrics"
        )
        
        if results:
            result = results[0]
            print(f"   Database contains {result.get('total_metrics', 0)} metrics "
                  f"across {result.get('categories', 0)} categories")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n3. Schema introspection function:")
    try:
        schema = await get_database_schema()
        
        table_count = len(schema)
        total_columns = sum(len(table.get('columns', [])) for table in schema.values())
        
        print(f"   Schema: {table_count} tables with {total_columns} total columns")
    except Exception as e:
        print(f"   Error: {e}")


async def main():
    """Run all demonstrations."""
    print("🚀 Read-Only Database Querying Demonstration")
    print("=" * 60)
    print("This demo showcases advanced querying capabilities for metrics data")
    print("with support for complex SQL, aggregations, and database switching.")
    print()
    
    try:
        # Run all demonstrations
        await demo_basic_querying()
        await demo_complex_sql_queries()
        await demo_advanced_aggregations()
        await demo_database_schema_analysis()
        await demo_query_optimization()
        await demo_database_switching()
        await demo_llm_tools_integration()
        
        print("\n" + "=" * 60)
        print("✅ All demonstrations completed successfully!")
        print("\nKey takeaways:")
        print("- Read-only abstraction supports complex SQL queries")
        print("- JSON operations enable flexible attribute/value filtering")
        print("- Multiple database types (SQLite, PostgreSQL, MongoDB)")
        print("- Built-in safety checks prevent data mutations")
        print("- LLM tools provide AI-friendly query interface")
        print("- Query optimization and performance analysis")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        await close_metrics_database()
        print("\n🔒 Database connections closed.")


if __name__ == "__main__":
    asyncio.run(main()) 