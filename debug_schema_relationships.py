#!/usr/bin/env python3
"""
Debug script to check actual database structure and relationships.
"""

import asyncio
from pymongo import MongoClient
import json


async def debug_database_structure():
    """Debug the actual database structure and relationships."""
    
    # Connect to MongoDB
    client = MongoClient("mongodb://localhost:27017")
    db = client["ee-productivities"]
    
    print("🔍 Debugging Database Structure")
    print("=" * 40)
    
    # Check all collections
    collections = db.list_collection_names()
    print(f"📊 Collections: {collections}")
    
    # Sample documents from each collection
    for collection_name in collections:
        print(f"\n📋 Collection: {collection_name}")
        collection = db[collection_name]
        
        # Get sample document
        sample = collection.find_one()
        if sample:
            print(f"   Document count: {collection.count_documents({})}")
            print(f"   Sample fields: {list(sample.keys())}")
            
            # Check for potential relationship fields
            potential_keys = ['csiId', 'soeId', 'soeld', 'nativeID', 'id']
            found_keys = []
            for key in potential_keys:
                if key in sample:
                    found_keys.append(key)
                    print(f"   Found key: {key} = {sample[key]}")
            
            if not found_keys:
                print("   No common relationship fields found")
        else:
            print("   Empty collection")
    
    # Check for actual relationships by looking at field values
    print(f"\n🔗 Checking for actual relationships...")
    
    # Get some csiId values from application_snapshot
    app_sample = db.application_snapshot.find_one()
    if app_sample and 'application' in app_sample and 'csiId' in app_sample['application']:
        csi_id = app_sample['application']['csiId']
        print(f"   Sample csiId from application_snapshot: {csi_id}")
        
        # Check if this csiId exists in employee_ratio
        emp_ratio_sample = db.employee_ratio.find_one({"soeId": csi_id})
        if emp_ratio_sample:
            print(f"   ✅ Found matching record in employee_ratio with soeId: {csi_id}")
        else:
            print(f"   ❌ No matching record in employee_ratio with soeId: {csi_id}")
            
            # Check what soeId values exist in employee_ratio
            emp_ratio_ids = list(db.employee_ratio.distinct("soeId"))
            print(f"   Available soeId values in employee_ratio: {emp_ratio_ids[:5]}...")
    
    # Check application_snapshot csiId values
    app_csi_ids = list(db.application_snapshot.distinct("application.csiId"))
    print(f"   Available csiId values in application_snapshot: {app_csi_ids[:5]}...")
    
    # Check for any overlapping values
    emp_ratio_ids = list(db.employee_ratio.distinct("soeId"))
    overlapping = set(app_csi_ids) & set(emp_ratio_ids)
    print(f"   Overlapping IDs between collections: {len(overlapping)} values")
    if overlapping:
        print(f"   Sample overlapping IDs: {list(overlapping)[:3]}")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(debug_database_structure()) 