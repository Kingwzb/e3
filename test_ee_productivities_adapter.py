#!/usr/bin/env python3
"""
Test script for the ee-productivities MongoDB adapters.
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database_abstraction import (
    MetricsDatabase, MetricsQueryDatabase, QueryFilter, MetricTuple,
    get_mongodb_ee_productivities_config, get_mongodb_ee_productivities_query_config
)
from datetime import datetime
from app.utils.logging import logger


async def test_ee_productivities_adapters():
    """Test the ee-productivities MongoDB adapters."""
    print("\n" + "="*60)
    print("Testing EE-Productivities MongoDB Adapters")
    print("="*60)
    
    # Test configuration
    connection_string = "mongodb://localhost:27017"
    
    try:
        # Test write adapter
        print("\n📝 Testing Write Adapter...")
        write_config = get_mongodb_ee_productivities_config(
            connection_string=connection_string,
            database_name="ee-productivities",
            collection_name="application_snapshot"
        )
        
        write_db = MetricsDatabase(write_config)
        await write_db.initialize()
        print("✅ Write adapter initialized successfully")
        
        # Test health check
        is_healthy = await write_db.health_check()
        print(f"✅ Health check: {'Passed' if is_healthy else 'Failed'}")
        
        # Test querying existing data
        filters = QueryFilter(
            attributes={"status": "Active"},
            limit=5
        )
        
        results = await write_db.query_metrics(filters)
        print(f"✅ Query returned {len(results)} application snapshots")
        
        # Test aggregation
        from app.core.database_abstraction import AggregationQuery
        agg_query = AggregationQuery(
            group_by=["sector"],
            aggregations={"count": "count"},
            filters=QueryFilter(attributes={"status": "Active"})
        )
        
        agg_results = await write_db.aggregate_metrics(agg_query)
        print(f"✅ Aggregation returned {len(agg_results)} sector groups")
        
        await write_db.close()
        
        # Test query adapter
        print("\n📊 Testing Query Adapter...")
        query_config = get_mongodb_ee_productivities_query_config(
            connection_string=connection_string,
            database_name="ee-productivities",
            collection_name="application_snapshot"
        )
        
        query_db = MetricsQueryDatabase(query_config)
        await query_db.initialize()
        print("✅ Query adapter initialized successfully")
        
        # Test health check
        is_healthy = await query_db.health_check()
        print(f"✅ Health check: {'Passed' if is_healthy else 'Failed'}")
        
        # Test querying existing data
        filters = QueryFilter(
            attributes={"status": "Active"},
            limit=5
        )
        
        results = await query_db.query_metrics(filters)
        print(f"✅ Query returned {len(results)} application snapshots")
        
        # Test native query
        from app.core.database_abstraction import DatabaseQuery
        native_query = DatabaseQuery(
            native_query={
                "filter": {"status": "Active"},
                "pipeline": [
                    {"$match": {"status": "Active"}},
                    {"$group": {"_id": "$sector", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}},
                    {"$limit": 5}
                ]
            },
            limit=5
        )
        
        native_results = await query_db.execute_native_query(native_query)
        print(f"✅ Native query returned {len(native_results)} results")
        
        # Test schema info
        schema_info = await query_db.get_schema_info()
        print(f"✅ Schema info retrieved for {schema_info['collection_name']}")
        print(f"   Document count: {schema_info['document_count']}")
        print(f"   Storage size: {schema_info['storage_size']} bytes")
        
        await query_db.close()
        
        # Test collection switching
        print("\n🔄 Testing Collection Switching...")
        query_db = MetricsQueryDatabase(query_config)
        await query_db.initialize()
        
        # Switch to different collections
        collections_to_test = ["employeed_ratio", "employee_tree_archived", "statistic"]
        
        for collection_name in collections_to_test:
            try:
                await query_db.adapter.switch_collection(collection_name)
                print(f"✅ Switched to collection: {collection_name}")
                
                # Test a simple query
                filters = QueryFilter(limit=3)
                results = await query_db.query_metrics(filters)
                print(f"   Query returned {len(results)} documents")
                
            except Exception as e:
                print(f"❌ Failed to test collection {collection_name}: {e}")
        
        await query_db.close()
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


async def test_collection_specific_queries():
    """Test queries specific to each collection."""
    print("\n" + "="*60)
    print("Testing Collection-Specific Queries")
    print("="*60)
    
    connection_string = "mongodb://localhost:27017"
    
    try:
        # Test application_snapshot collection
        print("\n📋 Testing application_snapshot collection...")
        config = get_mongodb_ee_productivities_query_config(
            connection_string=connection_string,
            collection_name="application_snapshot"
        )
        
        db = MetricsQueryDatabase(config)
        await db.initialize()
        
        # Test filtering by criticality
        filters = QueryFilter(
            attributes={"application.criticality": "High"},
            limit=5
        )
        results = await db.query_metrics(filters)
        print(f"✅ High criticality applications: {len(results)}")
        
        # Test filtering by sector
        filters = QueryFilter(
            attributes={"sector": "Technology"},
            limit=5
        )
        results = await db.query_metrics(filters)
        print(f"✅ Technology sector applications: {len(results)}")
        
        await db.close()
        
        # Test employeed_ratio collection
        print("\n👥 Testing employeed_ratio collection...")
        config = get_mongodb_ee_productivities_query_config(
            connection_string=connection_string,
            collection_name="employeed_ratio"
        )
        
        db = MetricsQueryDatabase(config)
        await db.initialize()
        
        # Test querying employee ratios
        filters = QueryFilter(limit=3)
        results = await db.query_metrics(filters)
        print(f"✅ Employee ratio records: {len(results)}")
        
        if results:
            sample = results[0]
            print(f"   Sample SOE ID: {sample.attributes.get('soeId')}")
            print(f"   Employee ratio snapshots: {len(sample.values.get('employeeRatioSnapshot', []))}")
            print(f"   Tools adoption snapshots: {len(sample.values.get('toolsAdoptionRatioSnapshot', []))}")
        
        await db.close()
        
        # Test employee_tree_archived collection
        print("\n🌳 Testing employee_tree_archived collection...")
        config = get_mongodb_ee_productivities_query_config(
            connection_string=connection_string,
            collection_name="employee_tree_archived"
        )
        
        db = MetricsQueryDatabase(config)
        await db.initialize()
        
        # Test querying employee trees
        filters = QueryFilter(
            attributes={"hierarchy": 1},
            limit=3
        )
        results = await db.query_metrics(filters)
        print(f"✅ Top-level employee trees: {len(results)}")
        
        if results:
            sample = results[0]
            print(f"   Sample SOE ID: {sample.attributes.get('soeId')}")
            print(f"   Total employees: {sample.values.get('totalNum')}")
            print(f"   Engineers: {sample.values.get('engineerNum')}")
        
        await db.close()
        
        # Test statistic collection
        print("\n📊 Testing statistic collection...")
        config = get_mongodb_ee_productivities_query_config(
            connection_string=connection_string,
            collection_name="statistic"
        )
        
        db = MetricsQueryDatabase(config)
        await db.initialize()
        
        # Test querying statistics
        filters = QueryFilter(limit=3)
        results = await db.query_metrics(filters)
        print(f"✅ Statistic records: {len(results)}")
        
        if results:
            sample = results[0]
            print(f"   Sample Native ID: {sample.attributes.get('nativeID')}")
            print(f"   Native ID Type: {sample.attributes.get('nativeIDType')}")
            print(f"   Statistics snapshots: {len(sample.values.get('statistics', []))}")
        
        await db.close()
        
        print("\n✅ All collection-specific tests completed!")
        
    except Exception as e:
        print(f"❌ Collection-specific tests failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main test function."""
    print("🚀 Starting EE-Productivities MongoDB Adapter Tests")
    
    await test_ee_productivities_adapters()
    await test_collection_specific_queries()
    
    print("\n🎉 All tests completed!")


if __name__ == "__main__":
    asyncio.run(main()) 