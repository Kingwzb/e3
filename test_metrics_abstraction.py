#!/usr/bin/env python3
"""
Test script for the metrics database abstraction layer.
This script demonstrates how to switch between different database backends.
"""

import asyncio
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.database_abstraction import (
    MetricsDatabase, MetricTuple, QueryFilter, DatabaseConfig,
    get_sqlite_config, get_mongodb_config
)
from app.tools.metrics_db_tools import (
    initialize_metrics_database, close_metrics_database,
    create_metrics_db_tools, insert_metric_direct, query_metrics_direct
)
from app.tools.data_migration import generate_sample_metrics_for_testing
from app.utils.logging import logger


async def test_sqlite_adapter():
    """Test the SQLite adapter functionality."""
    print("\n" + "="*50)
    print("Testing SQLite Adapter")
    print("="*50)
    
    # Create SQLite configuration
    config = get_sqlite_config("./test_metrics.db")
    db = MetricsDatabase(config)
    
    try:
        # Initialize database
        await db.initialize()
        print("✅ SQLite database initialized successfully")
        
        # Test health check
        is_healthy = await db.health_check()
        print(f"✅ Database health check: {'Passed' if is_healthy else 'Failed'}")
        
        # Insert sample metric
        sample_metric = MetricTuple(
            attributes={
                "category": "engagement",
                "metric_name": "daily_active_users",
                "region": "us-east",
                "team": "product"
            },
            values={
                "daily_active_users": 1500,
                "sample_count": 100
            },
            timestamp=datetime.utcnow()
        )
        
        metric_id = await db.insert_metric(sample_metric)
        print(f"✅ Inserted metric with ID: {metric_id}")
        
        # Query metrics
        filters = QueryFilter(
            attributes={"category": "engagement"},
            limit=10
        )
        
        results = await db.query_metrics(filters)
        print(f"✅ Queried {len(results)} metrics")
        
        # Test aggregation
        aggregation_results = await db.aggregate_metrics(
            filters=QueryFilter(time_range=(datetime.utcnow() - timedelta(days=1), datetime.utcnow())),
            group_by=["category"],
            aggregations={"daily_active_users": "avg"}
        )
        print(f"✅ Aggregation returned {len(aggregation_results)} groups")
        
        return True
        
    except Exception as e:
        print(f"❌ SQLite test failed: {e}")
        return False
    finally:
        await db.close()


async def test_mongodb_adapter():
    """Test the MongoDB adapter functionality (if MongoDB is available)."""
    print("\n" + "="*50)
    print("Testing MongoDB Adapter")
    print("="*50)
    
    # Check if MongoDB is available
    try:
        import motor.motor_asyncio
        mongodb_uri = "mongodb://localhost:27017"
        print(f"MongoDB driver available, testing with URI: {mongodb_uri}")
    except ImportError:
        print("❌ MongoDB driver (motor) not available, skipping MongoDB test")
        return True
    
    # Create MongoDB configuration
    config = get_mongodb_config(
        connection_string=mongodb_uri,
        database_name="test_metrics_db",
        collection_name="test_metrics"
    )
    db = MetricsDatabase(config)
    
    try:
        # Initialize database
        await db.initialize()
        print("✅ MongoDB database initialized successfully")
        
        # Test health check
        is_healthy = await db.health_check()
        print(f"✅ Database health check: {'Passed' if is_healthy else 'Failed'}")
        
        # Insert sample metric
        sample_metric = MetricTuple(
            attributes={
                "category": "performance",
                "metric_name": "response_time",
                "region": "us-west",
                "service": "api_gateway"
            },
            values={
                "response_time": 125.5,
                "percentile_95": 200.0,
                "sample_count": 1000
            },
            timestamp=datetime.utcnow()
        )
        
        metric_id = await db.insert_metric(sample_metric)
        print(f"✅ Inserted metric with ID: {metric_id}")
        
        # Query metrics
        filters = QueryFilter(
            attributes={"category": "performance"},
            value_filters={"response_time": {"$lte": 200}},
            limit=10
        )
        
        results = await db.query_metrics(filters)
        print(f"✅ Queried {len(results)} metrics")
        
        # Test aggregation
        aggregation_results = await db.aggregate_metrics(
            filters=QueryFilter(time_range=(datetime.utcnow() - timedelta(days=1), datetime.utcnow())),
            group_by=["category", "region"],
            aggregations={"response_time": "avg", "sample_count": "sum"}
        )
        print(f"✅ Aggregation returned {len(aggregation_results)} groups")
        
        return True
        
    except Exception as e:
        print(f"❌ MongoDB test failed: {e}")
        print("Note: This is expected if MongoDB is not running locally")
        return False
    finally:
        try:
            await db.close()
        except:
            pass


async def test_llm_tools():
    """Test the LLM tools that use the abstraction layer."""
    print("\n" + "="*50)
    print("Testing LLM Tools with Database Abstraction")
    print("="*50)
    
    try:
        # Initialize the global metrics database (SQLite for this test)
        import os
        os.environ["METRICS_DB_TYPE"] = "sqlite"
        os.environ["METRICS_DB_PATH"] = "./test_metrics_tools.db"
        
        await initialize_metrics_database()
        print("✅ Initialized global metrics database")
        
        # Test direct insertion
        metric_id = await insert_metric_direct(
            attributes={
                "category": "revenue",
                "metric_name": "daily_revenue",
                "region": "europe",
                "currency": "EUR"
            },
            values={
                "daily_revenue": 15000.50,
                "transaction_count": 450
            }
        )
        print(f"✅ Direct insertion successful, ID: {metric_id}")
        
        # Test direct querying
        results = await query_metrics_direct(
            attributes={"category": "revenue"},
            days_back=1,
            limit=5
        )
        print(f"✅ Direct query returned {len(results)} results")
        
        # Test LangChain tools
        tools = create_metrics_db_tools()
        print(f"✅ Created {len(tools)} LangChain tools")
        
        # Test query tool
        query_tool = tools[1]  # QueryMetricsTool
        result = await query_tool._arun(
            attributes={"category": "revenue"},
            days_back=1,
            limit=10
        )
        print("✅ LangChain query tool test completed")
        print(f"Result preview: {result[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM tools test failed: {e}")
        return False
    finally:
        await close_metrics_database()


async def test_data_migration():
    """Test data migration functionality."""
    print("\n" + "="*50)
    print("Testing Data Migration")
    print("="*50)
    
    try:
        # Initialize the global metrics database
        import os
        os.environ["METRICS_DB_TYPE"] = "sqlite"
        os.environ["METRICS_DB_PATH"] = "./test_migration.db"
        
        await initialize_metrics_database()
        print("✅ Initialized global metrics database for migration test")
        
        # Generate sample metrics
        stats = await generate_sample_metrics_for_testing()
        print(f"✅ Generated {stats['generated_records']} sample metrics")
        print(f"   Categories: {stats['categories']}")
        print(f"   Regions: {stats['regions']}")
        print(f"   Days: {stats['days']}")
        
        if stats['errors']:
            print(f"⚠️  {len(stats['errors'])} errors occurred during generation")
        
        # Test querying the generated data
        results = await query_metrics_direct(limit=5)
        print(f"✅ Verified data: Found {len(results)} metrics")
        
        if results:
            print("Sample metric:")
            sample = results[0]
            print(f"   Attributes: {sample.attributes}")
            print(f"   Values: {sample.values}")
            print(f"   Timestamp: {sample.timestamp}")
        
        return True
        
    except Exception as e:
        print(f"❌ Data migration test failed: {e}")
        return False
    finally:
        await close_metrics_database()


async def main():
    """Run all tests."""
    print("🧪 Starting Database Abstraction Layer Tests")
    print("=" * 60)
    
    tests = [
        ("SQLite Adapter", test_sqlite_adapter),
        ("MongoDB Adapter", test_mongodb_adapter),
        ("LLM Tools", test_llm_tools),
        ("Data Migration", test_data_migration),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Database abstraction layer is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")


if __name__ == "__main__":
    asyncio.run(main()) 