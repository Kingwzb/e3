#!/usr/bin/env python3
"""
MongoDB Schema Extractor and Updater

This script connects to MongoDB, extracts the actual collections and their schemas,
generates a unified schema file, and updates the Python schema file.
"""

import asyncio
import sys
import os
from extract_mongodb_schema import MongoDBSchemaExtractor
from update_schema_from_file import update_python_schema_file


async def extract_and_update_schema(connection_string: str, database_name: str, 
                                  text_output: str = "schemas/unified_schema.txt",
                                  python_output: str = "schemas/unified_schema.py",
                                  sample_size: int = 100) -> bool:
    """Extract schema from MongoDB and update both text and Python files."""
    try:
        print("🚀 Starting MongoDB schema extraction and update process...")
        
        # Step 1: Extract schema from MongoDB
        print(f"\n📊 Step 1: Extracting schema from MongoDB database '{database_name}'")
        extractor = MongoDBSchemaExtractor(connection_string, database_name)
        
        # Connect to database
        if not await extractor.connect():
            return False
        
        # Generate unified schema text file
        success = await extractor.generate_unified_schema(text_output)
        if not success:
            await extractor.close()
            return False
        
        await extractor.close()
        
        # Step 2: Update Python schema file
        print(f"\n📝 Step 2: Updating Python schema file")
        success = update_python_schema_file(text_output, python_output)
        if not success:
            return False
        
        print(f"\n🎉 Complete! Schema extraction and update completed successfully!")
        print(f"📁 Text schema file: {text_output}")
        print(f"📁 Python schema file: {python_output}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to extract and update schema: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract MongoDB schema and update schema files')
    parser.add_argument('--connection-string', required=True, 
                       help='MongoDB connection string')
    parser.add_argument('--database', required=True,
                       help='Database name')
    parser.add_argument('--text-output', default='schemas/unified_schema.txt',
                       help='Text schema output file (default: schemas/unified_schema.txt)')
    parser.add_argument('--python-output', default='schemas/unified_schema.py',
                       help='Python schema output file (default: schemas/unified_schema.py)')
    parser.add_argument('--sample-size', type=int, default=100,
                       help='Number of documents to sample per collection (default: 100)')
    
    args = parser.parse_args()
    
    success = await extract_and_update_schema(
        args.connection_string,
        args.database,
        args.text_output,
        args.python_output,
        args.sample_size
    )
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 