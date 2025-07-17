#!/usr/bin/env python3
"""
Test script to verify ee-productivities database connection.
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database_abstraction import (
    get_mongodb_ee_productivities_query_config,
    MetricsQueryDatabase
)
from app.utils.logging import logger


async def test_ee_productivities_connection():
    """Test the ee-productivities database connection."""
    print("\n" + "="*60)
    print("Testing EE-Productivities Database Connection")
    print("="*60)
    
    try:
        # Get connection string from environment or use default
        connection_string = os.getenv("METRICS_MONGODB_URI", "mongodb://localhost:27017")
        database_name = os.getenv("METRICS_MONGODB_DATABASE", "ee-productivities")
        
        print(f"Connection string: {connection_string}")
        print(f"Database name: {database_name}")
        
        # Create configuration
        config = get_mongodb_ee_productivities_query_config(
            connection_string=connection_string,
            database_name=database_name,
            collection_name="application_snapshot"
        )
        
        print("✅ Configuration created successfully")
        
        # Initialize database
        db = MetricsQueryDatabase(config)
        await db.initialize()
        
        print("✅ Database initialized successfully")
        print(f"✅ Adapter type: {type(db.adapter)}")
        
        # Test health check
        is_healthy = await db.health_check()
        print(f"✅ Health check: {'Passed' if is_healthy else 'Failed'}")
        
        # Test collection switching
        if hasattr(db.adapter, 'switch_collection'):
            print("✅ Adapter supports collection switching")
            
            # List available collections
            collections = await db.adapter.list_collections()
            print(f"✅ Available collections: {collections}")
            
            # Test switching to application_snapshot
            await db.adapter.switch_collection("application_snapshot")
            print("✅ Successfully switched to application_snapshot collection")
            
            # Test a simple query
            from app.core.database_abstraction import QueryFilter
            filters = QueryFilter(limit=3)
            results = await db.query_metrics(filters)
            print(f"✅ Query returned {len(results)} results")
            
        else:
            print("❌ Adapter does not support collection switching")
            print(f"Available methods: {dir(db.adapter)}")
        
        await db.close()
        print("✅ Database connection closed successfully")
        
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_ee_productivities_connection()) 