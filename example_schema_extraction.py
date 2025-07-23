#!/usr/bin/env python3
"""
Example: MongoDB Schema Extraction

This script demonstrates how to use the schema extraction tools
to extract and update schema files from a MongoDB database.
"""

import asyncio
import os
import sys
from extract_and_update_schema import extract_and_update_schema


async def example_extraction():
    """Example of extracting schema from MongoDB."""
    
    # Configuration - Update these values for your MongoDB instance
    CONNECTION_STRING = "mongodb://localhost:27017"  # Update with your connection string
    DATABASE_NAME = "ee-productivities"  # Update with your database name
    
    print("🔍 Example: MongoDB Schema Extraction")
    print("=" * 50)
    
    # Check if we can connect to MongoDB
    try:
        from pymongo import MongoClient
        client = MongoClient(CONNECTION_STRING)
        client.admin.command('ping')
        print("✅ MongoDB connection successful")
        client.close()
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        print("\nPlease update the CONNECTION_STRING and DATABASE_NAME variables")
        print("in this script with your actual MongoDB connection details.")
        return False
    
    # Extract and update schema
    print(f"\n📊 Extracting schema from database: {DATABASE_NAME}")
    print(f"🔌 Connection: {CONNECTION_STRING}")
    
    success = await extract_and_update_schema(
        connection_string=CONNECTION_STRING,
        database_name=DATABASE_NAME,
        text_output="schemas/unified_schema.txt",
        python_output="schemas/unified_schema.py",
        sample_size=50  # Smaller sample for faster processing
    )
    
    if success:
        print("\n🎉 Schema extraction completed successfully!")
        print("\n📁 Generated files:")
        print("   - schemas/unified_schema.txt (Text schema)")
        print("   - schemas/unified_schema.py (Python module)")
        
        # Show file sizes
        if os.path.exists("schemas/unified_schema.txt"):
            size = os.path.getsize("schemas/unified_schema.txt")
            print(f"   📄 Text file size: {size:,} bytes")
        
        if os.path.exists("schemas/unified_schema.py"):
            size = os.path.getsize("schemas/unified_schema.py")
            print(f"   📄 Python file size: {size:,} bytes")
        
        print("\n✅ You can now use the unified schema in your dynamic DB tool!")
        print("   Example:")
        print("   from schemas.unified_schema import UNIFIED_SCHEMA")
        print("   # Use UNIFIED_SCHEMA in your queries")
        
    else:
        print("\n❌ Schema extraction failed!")
        return False
    
    return True


def show_usage_examples():
    """Show usage examples for the schema extraction tools."""
    print("\n📚 Usage Examples:")
    print("=" * 30)
    
    print("\n1. Extract schema from local MongoDB:")
    print("   python extract_and_update_schema.py \\")
    print("     --connection-string 'mongodb://localhost:27017' \\")
    print("     --database 'ee-productivities'")
    
    print("\n2. Extract schema from remote MongoDB:")
    print("   python extract_and_update_schema.py \\")
    print("     --connection-string 'mongodb://user:pass@host:27017' \\")
    print("     --database 'production_db' \\")
    print("     --sample-size 200")
    
    print("\n3. Extract schema step by step:")
    print("   # Step 1: Extract to text file")
    print("   python extract_mongodb_schema.py \\")
    print("     --connection-string 'mongodb://localhost:27017' \\")
    print("     --database 'my_database' \\")
    print("     --output 'my_schema.txt'")
    print("   # Step 2: Update Python file")
    print("   python update_schema_from_file.py my_schema.txt")


async def main():
    """Main function."""
    print("🚀 MongoDB Schema Extraction Example")
    print("=" * 40)
    
    # Check if required files exist
    required_files = [
        "extract_mongodb_schema.py",
        "update_schema_from_file.py", 
        "extract_and_update_schema.py"
    ]
    
    missing_files = [f for f in required_files if not os.path.exists(f)]
    if missing_files:
        print(f"❌ Missing required files: {', '.join(missing_files)}")
        print("Please ensure all schema extraction scripts are in the current directory.")
        return False
    
    # Run example extraction
    success = await example_extraction()
    
    if success:
        show_usage_examples()
    
    return success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 