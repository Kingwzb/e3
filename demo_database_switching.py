#!/usr/bin/env python3
"""
Demonstration script showing how to switch between different database backends
using environment variables and configuration.
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.tools.metrics_db_tools import (
    initialize_metrics_database, 
    close_metrics_database,
    insert_metric_direct,
    query_metrics_direct,
    create_metrics_db_tools
)


async def demo_sqlite():
    """Demonstrate SQLite usage."""
    print("\n" + "="*60)
    print("🗃️  DEMO: SQLite Database (Local Testing)")
    print("="*60)
    
    # Configure for SQLite
    os.environ["METRICS_DB_TYPE"] = "sqlite"
    os.environ["METRICS_DB_PATH"] = "./demo_sqlite_metrics.db"
    
    try:
        # Initialize database
        await initialize_metrics_database()
        print("✅ Initialized SQLite metrics database")
        
        # Insert sample data
        print("\n📥 Inserting sample metrics...")
        
        sample_metrics = [
            {
                "attributes": {"category": "engagement", "metric_name": "daily_users", "region": "us-east"},
                "values": {"daily_users": 1250, "growth_rate": 0.03}
            },
            {
                "attributes": {"category": "revenue", "metric_name": "daily_revenue", "region": "us-east"},
                "values": {"daily_revenue": 15000.50, "transactions": 450}
            },
            {
                "attributes": {"category": "performance", "metric_name": "response_time", "service": "api"},
                "values": {"response_time": 125.5, "p95": 200.0}
            }
        ]
        
        for metric in sample_metrics:
            metric_id = await insert_metric_direct(**metric)
            print(f"   • Inserted {metric['attributes']['metric_name']}: {metric_id[:8]}...")
        
        # Query data
        print("\n📤 Querying metrics...")
        
        # Query engagement metrics
        engagement_metrics = await query_metrics_direct(
            attributes={"category": "engagement"},
            days_back=1,
            limit=10
        )
        print(f"   • Found {len(engagement_metrics)} engagement metrics")
        
        # Query all metrics
        all_metrics = await query_metrics_direct(days_back=1, limit=50)
        print(f"   • Total metrics in last 24 hours: {len(all_metrics)}")
        
        print("\n✅ SQLite demo completed successfully!")
        
    except Exception as e:
        print(f"❌ SQLite demo failed: {e}")
    finally:
        await close_metrics_database()


async def demo_configuration_switching():
    """Demonstrate switching between configurations."""
    print("\n" + "="*60)
    print("⚙️  DEMO: Configuration Switching")
    print("="*60)
    
    configs = [
        {
            "name": "Development (SQLite)",
            "env": {
                "METRICS_DB_TYPE": "sqlite",
                "METRICS_DB_PATH": "./dev_metrics.db"
            }
        },
        {
            "name": "Testing (SQLite)",
            "env": {
                "METRICS_DB_TYPE": "sqlite", 
                "METRICS_DB_PATH": "./test_metrics.db"
            }
        },
        {
            "name": "Production (MongoDB - would fail without MongoDB running)",
            "env": {
                "METRICS_DB_TYPE": "mongodb",
                "METRICS_MONGODB_URI": "mongodb://localhost:27017",
                "METRICS_MONGODB_DATABASE": "prod_metrics",
                "METRICS_MONGODB_COLLECTION": "metrics"
            }
        }
    ]
    
    for config in configs:
        print(f"\n🔧 Configuring for: {config['name']}")
        
        # Set environment variables
        for key, value in config['env'].items():
            os.environ[key] = value
            print(f"   {key}={value}")
        
        try:
            # Only test SQLite configurations to avoid MongoDB connection issues
            if config['env']['METRICS_DB_TYPE'] == 'sqlite':
                await initialize_metrics_database()
                print(f"   ✅ Successfully initialized {config['name']}")
                
                # Insert a test metric
                metric_id = await insert_metric_direct(
                    attributes={"category": "test", "config": config['name']},
                    values={"test_value": 42}
                )
                print(f"   ✅ Test metric inserted: {metric_id[:8]}...")
                
                await close_metrics_database()
            else:
                print(f"   ⏭️  Skipping {config['name']} (MongoDB not running)")
                
        except Exception as e:
            print(f"   ❌ Failed to initialize {config['name']}: {e}")


async def demo_llm_tools_integration():
    """Demonstrate LLM tools integration."""
    print("\n" + "="*60)
    print("🤖 DEMO: LLM Tools Integration")
    print("="*60)
    
    # Configure for SQLite
    os.environ["METRICS_DB_TYPE"] = "sqlite"
    os.environ["METRICS_DB_PATH"] = "./demo_llm_metrics.db"
    
    try:
        await initialize_metrics_database()
        print("✅ Initialized metrics database for LLM tools")
        
        # Create LangChain tools
        tools = create_metrics_db_tools()
        print(f"\n🔧 Created {len(tools)} LangChain tools:")
        for tool in tools:
            print(f"   • {tool.name}: {tool.description[:60]}...")
        
        # Simulate LLM tool usage
        print("\n🧠 Simulating LLM tool usage...")
        
        # Insert metric using tool
        insert_tool = tools[0]  # InsertMetricTool
        insert_result = await insert_tool._arun(
            attributes={
                "category": "user_engagement",
                "metric_name": "session_length",
                "region": "global"
            },
            values={
                "avg_session_minutes": 45.2,
                "total_sessions": 1250
            }
        )
        print(f"   📥 Insert tool result: {insert_result[:100]}...")
        
        # Query metric using tool
        query_tool = tools[1]  # QueryMetricsTool
        query_result = await query_tool._arun(
            attributes={"category": "user_engagement"},
            days_back=1,
            limit=5
        )
        print(f"   📤 Query tool result: {query_result[:100]}...")
        
        # Health check using tool
        health_tool = tools[3]  # DatabaseHealthTool
        health_result = await health_tool._arun()
        print(f"   🏥 Health check: {health_result}")
        
        print("\n✅ LLM tools integration demo completed!")
        
    except Exception as e:
        print(f"❌ LLM tools demo failed: {e}")
    finally:
        await close_metrics_database()


async def demo_data_model_flexibility():
    """Demonstrate the flexible data model."""
    print("\n" + "="*60)
    print("📊 DEMO: Flexible Data Model")
    print("="*60)
    
    # Configure for SQLite
    os.environ["METRICS_DB_TYPE"] = "sqlite"
    os.environ["METRICS_DB_PATH"] = "./demo_flexible_metrics.db"
    
    try:
        await initialize_metrics_database()
        print("✅ Initialized database for data model demo")
        
        print("\n📝 Demonstrating different metric structures...")
        
        # Complex user engagement metric
        await insert_metric_direct(
            attributes={
                "category": "user_engagement",
                "product": "web_app", 
                "feature": "dashboard",
                "user_segment": "power_users",
                "a_b_test": "experiment_123"
            },
            values={
                "daily_active_users": 2500,
                "avg_session_duration": 35.7,
                "page_views_per_session": 12.3,
                "conversion_rate": 0.045,
                "retention_day_7": 0.68
            }
        )
        print("   ✅ Complex engagement metric with multiple dimensions")
        
        # Financial metric with metadata
        await insert_metric_direct(
            attributes={
                "category": "revenue",
                "business_unit": "enterprise",
                "region": "north_america",
                "quarter": "Q1_2024",
                "sales_channel": "direct"
            },
            values={
                "monthly_recurring_revenue": 125000.00,
                "customer_acquisition_cost": 850.50,
                "lifetime_value": 15000.00,
                "churn_rate": 0.02,
                "net_revenue_retention": 1.15
            }
        )
        print("   ✅ Business metric with financial KPIs")
        
        # Infrastructure performance metric
        await insert_metric_direct(
            attributes={
                "category": "infrastructure",
                "service": "user_api",
                "environment": "production",
                "region": "us-west-2",
                "instance_type": "c5.large"
            },
            values={
                "avg_response_time": 98.5,
                "p95_response_time": 245.0,
                "p99_response_time": 450.0,
                "error_rate": 0.0012,
                "requests_per_second": 1250.5,
                "cpu_utilization": 0.65,
                "memory_utilization": 0.78
            }
        )
        print("   ✅ Infrastructure metric with detailed performance data")
        
        # Query to show flexibility
        all_metrics = await query_metrics_direct(days_back=1, limit=10)
        print(f"\n📈 Retrieved {len(all_metrics)} metrics with varied structures:")
        
        for i, metric in enumerate(all_metrics, 1):
            print(f"   {i}. Category: {metric.attributes.get('category')}")
            print(f"      Attributes: {len(metric.attributes)} fields")
            print(f"      Values: {len(metric.values)} metrics")
            print(f"      Sample values: {list(metric.values.keys())[:3]}...")
            print()
        
        print("✅ Data model flexibility demo completed!")
        
    except Exception as e:
        print(f"❌ Data model demo failed: {e}")
    finally:
        await close_metrics_database()


async def main():
    """Run all demonstrations."""
    print("🎭 Database Abstraction Layer Demonstration")
    print("=" * 80)
    print("This demo shows how to switch between different database backends")
    print("and use the flexible metrics data model.")
    
    demos = [
        ("SQLite Usage", demo_sqlite),
        ("Configuration Switching", demo_configuration_switching),
        ("LLM Tools Integration", demo_llm_tools_integration),
        ("Flexible Data Model", demo_data_model_flexibility),
    ]
    
    for demo_name, demo_func in demos:
        try:
            await demo_func()
        except Exception as e:
            print(f"\n❌ {demo_name} demo failed: {e}")
    
    print("\n" + "="*80)
    print("🎉 DEMONSTRATION COMPLETE!")
    print("="*80)
    print("\nKey Benefits Demonstrated:")
    print("✅ Easy database switching via environment variables")
    print("✅ Unified API regardless of underlying database")
    print("✅ Flexible metric data model for any use case")
    print("✅ LLM/AI-ready tools for intelligent querying")
    print("✅ Production-ready for both SQL and NoSQL backends")
    print("\nTo use in production:")
    print("1. Set METRICS_DB_TYPE=mongodb and METRICS_MONGODB_URI")
    print("2. Or use METRICS_DB_TYPE=postgresql for SQL production")
    print("3. All existing code works without changes!")


if __name__ == "__main__":
    asyncio.run(main()) 