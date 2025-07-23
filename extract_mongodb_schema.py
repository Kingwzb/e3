#!/usr/bin/env python3
"""
MongoDB Schema Extractor

This script connects to MongoDB, extracts the actual collections and their schemas,
and generates a unified schema file based on the real database structure.

e.g. python extract_mongodb_schema.py \        
  --connection-string "mongodb://localhost:27017" \
  --database "ee-productivities" \
  --output "schemas/unified_schema.txt"
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
import argparse
import sys


class MongoDBSchemaExtractor:
    """Extracts and analyzes MongoDB collections and their schemas."""
    
    def __init__(self, connection_string: str, database_name: str):
        """Initialize the schema extractor."""
        self.connection_string = connection_string
        self.database_name = database_name
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        
    async def connect(self) -> bool:
        """Connect to MongoDB database."""
        try:
            print(f"🔌 Connecting to MongoDB...")
            print(f"   Database: {self.database_name}")
            
            self.client = MongoClient(self.connection_string)
            self.db = self.client[self.database_name]
            
            # Test connection
            await asyncio.get_event_loop().run_in_executor(
                None, self.client.admin.command, 'ping'
            )
            
            print("✅ Successfully connected to MongoDB")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            return False
    
    async def get_collections(self) -> List[str]:
        """Get list of all collections in the database."""
        try:
            collections = await asyncio.get_event_loop().run_in_executor(
                None, self.db.list_collection_names
            )
            return collections
        except Exception as e:
            print(f"❌ Failed to get collections: {e}")
            return []
    
    async def analyze_collection_schema(self, collection_name: str, sample_size: int = 100) -> Dict[str, Any]:
        """Analyze the schema of a collection based on sample documents."""
        try:
            collection = self.db[collection_name]
            
            # Get sample documents
            sample_docs = await asyncio.get_event_loop().run_in_executor(
                None, lambda: list(collection.find().limit(sample_size))
            )
            
            if not sample_docs:
                return {
                    "name": collection_name,
                    "document_count": 0,
                    "schema": {},
                    "relationships": [],
                    "field_values": {},  # Track field values for relationship detection
                    "description": "Empty collection"
                }
            
            # Analyze schema from sample documents
            try:
                schema = self._analyze_documents_schema(sample_docs)
                print(f"   📊 Schema analysis completed for {len(sample_docs)} documents")
            except Exception as e:
                print(f"   ⚠️  Schema analysis failed: {e}")
                schema = {"type": "object", "properties": {}, "error": str(e)}
            
            # Get collection stats using count_documents
            doc_count = await asyncio.get_event_loop().run_in_executor(
                None, collection.count_documents, {}
            )
            
            stats = {"count": doc_count}
            size_info = {"totalSize": 0}  # Size calculation is complex, skip for now
            
            # Analyze relationships (look for common field patterns)
            relationships = self._analyze_relationships(collection_name, sample_docs)
            
            # Extract field values for cross-collection relationship detection
            field_values = self._extract_field_values(sample_docs)
            
            return {
                "name": collection_name,
                "document_count": stats.get("count", 0),
                "schema": schema,
                "relationships": relationships,
                "field_values": field_values,
                "description": self._generate_collection_description(collection_name, schema, stats, size_info)
            }
            
        except Exception as e:
            print(f"❌ Failed to analyze collection {collection_name}: {e}")
            return {
                "name": collection_name,
                "document_count": 0,
                "schema": {},
                "relationships": [],
                "field_values": {},
                "description": f"Error analyzing collection: {e}"
            }
    
    def _analyze_documents_schema(self, documents: List[Dict]) -> Dict[str, Any]:
        """Analyze the schema of documents and infer types and patterns."""
        if not documents:
            return {}
        
        try:
            schema = {}
            field_types = {}
            field_values = {}
            field_required = {}
            
            for doc in documents:
                self._analyze_document_fields(doc, schema, field_types, field_values, field_required)
            
            # Generate schema with type information
            return self._generate_schema_from_analysis(schema, field_types, field_values, field_required, len(documents))
        except Exception as e:
            print(f"   ⚠️  Document analysis failed: {e}")
            return {"type": "object", "properties": {}, "error": str(e)}
    
    def _analyze_document_fields(self, doc: Dict, schema: Dict, field_types: Dict, 
                                field_values: Dict, field_required: Dict, prefix: str = ""):
        """Recursively analyze document fields."""
        try:
            for key, value in doc.items():
                full_key = f"{prefix}.{key}" if prefix else key
                
                if full_key not in field_types:
                    field_types[full_key] = set()
                    field_values[full_key] = set()
                    field_required[full_key] = 0
                
                # Track type
                if value is None:
                    field_types[full_key].add("null")
                elif isinstance(value, bool):
                    field_types[full_key].add("boolean")
                elif isinstance(value, int):
                    field_types[full_key].add("integer")
                elif isinstance(value, float):
                    field_types[full_key].add("number")
                elif isinstance(value, str):
                    field_types[full_key].add("string")
                elif isinstance(value, list):
                    field_types[full_key].add("array")
                elif isinstance(value, dict):
                    field_types[full_key].add("object")
                    # Recursively analyze nested object
                    self._analyze_document_fields(value, schema, field_types, field_values, field_required, full_key)
                else:
                    # Handle other types (like ObjectId, etc.)
                    field_types[full_key].add("string")
                
                # Track unique values (for enums)
                if isinstance(value, (str, int, bool)) and len(field_values[full_key]) < 50:
                    field_values[full_key].add(str(value))
                
                field_required[full_key] += 1
        except Exception as e:
            print(f"   ⚠️  Field analysis error: {e}")
            # Continue with other fields
    
    def _generate_schema_from_analysis(self, schema: Dict, field_types: Dict, 
                                     field_values: Dict, field_required: Dict, total_docs: int) -> Dict[str, Any]:
        """Generate JSON schema from field analysis."""
        properties = {}
        
        try:
            for field_path, types in field_types.items():
                field_schema = self._generate_field_schema(field_path, types, field_values[field_path], 
                                                         field_required[field_path], total_docs)
                if field_schema:
                    # Handle nested fields
                    parts = field_path.split('.')
                    current = properties
                    for part in parts[:-1]:
                        if part not in current:
                            current[part] = {"type": "object", "properties": {}}
                        elif "properties" not in current[part]:
                            current[part]["properties"] = {}
                        current = current[part]["properties"]
                    current[parts[-1]] = field_schema
            
            return {
                "type": "object",
                "properties": properties
            }
        except Exception as e:
            print(f"⚠️  Warning: Error generating schema: {e}")
            # Return a basic schema if there's an error
            return {
                "type": "object",
                "properties": {},
                "error": f"Schema generation failed: {e}"
            }
    
    def _generate_field_schema(self, field_path: str, types: set, values: set, 
                             required_count: int, total_docs: int) -> Optional[Dict[str, Any]]:
        """Generate schema for a single field."""
        if not types:
            return None
        
        # Determine primary type
        if "object" in types:
            primary_type = "object"
        elif "array" in types:
            primary_type = "array"
        elif "string" in types:
            primary_type = "string"
        elif "number" in types:
            primary_type = "number"
        elif "integer" in types:
            primary_type = "integer"
        elif "boolean" in types:
            primary_type = "boolean"
        else:
            primary_type = "string"
        
        schema = {
            "type": primary_type,
            "description": self._generate_field_description(field_path, types, values, required_count, total_docs)
        }
        
        # Add enum if we have a limited set of values
        if len(values) <= 20 and primary_type in ["string", "integer"]:
            enum_values = []
            for val in values:
                if val != "null":
                    try:
                        if primary_type == "integer":
                            enum_values.append(int(val))
                        else:
                            enum_values.append(val)
                    except ValueError:
                        pass
            
            if enum_values:
                schema["enum"] = enum_values
        
        # Add required status
        if required_count == total_docs:
            schema["required"] = True
        
        return schema
    
    def _generate_field_description(self, field_path: str, types: set, values: set, 
                                 required_count: int, total_docs: int) -> str:
        """Generate description for a field."""
        parts = field_path.split('.')
        field_name = parts[-1]
        
        description = f"{field_name} field"
        
        if len(types) > 1:
            description += f" (types: {', '.join(types)})"
        
        if len(values) <= 10 and values:
            description += f" (values: {', '.join(sorted(values))})"
        
        if required_count == total_docs:
            description += " (required)"
        elif required_count > 0:
            description += f" (present in {required_count}/{total_docs} documents)"
        
        return description
    
    def _analyze_relationships(self, collection_name: str, documents: List[Dict]) -> List[Dict[str, str]]:
        """Analyze potential relationships between collections."""
        relationships = []
        seen_fields = set()
        
        # Look for common relationship patterns (exclude _id as it's the default MongoDB primary key)
        common_id_fields = ['id', 'csiId', 'soeld', 'nativeID', 'snapshotId']
        
        # Track field frequency to identify potential foreign keys
        field_frequency = {}
        
        for doc in documents:
            for field, value in doc.items():
                # Count field occurrences
                if field not in field_frequency:
                    field_frequency[field] = 0
                field_frequency[field] += 1
                
                # Check for potential primary keys
                if field in common_id_fields and value and field not in seen_fields:
                    relationships.append({
                        "field": field,
                        "type": "primary_key",
                        "description": f"Potential primary key field: {field}"
                    })
                    seen_fields.add(field)
        
        # Look for potential foreign key relationships
        # Fields that appear frequently and have consistent values might be foreign keys
        for field, count in field_frequency.items():
            if count > len(documents) * 0.8 and field not in seen_fields:  # Field appears in >80% of documents
                if field in ['csiId', 'soeld', 'nativeID']:  # Known foreign key patterns
                    relationships.append({
                        "field": field,
                        "type": "foreign_key",
                        "description": f"Potential foreign key field: {field}"
                    })
        
        return relationships
    
    def _extract_field_values(self, documents: List[Dict]) -> Dict[str, set]:
        """Extract field values for cross-collection relationship detection."""
        field_values = {}
        linking_fields = ['csiId', 'soeld', 'nativeID', 'snapshotId', 'level3', 'name']
        
        for doc in documents:
            for field, value in doc.items():
                if field in linking_fields and value is not None:
                    if field not in field_values:
                        field_values[field] = set()
                    field_values[field].add(str(value))
        
        return field_values
    
    def _generate_collection_description(self, collection_name: str, schema: Dict, stats: Dict, size_info: Dict) -> str:
        """Generate a description for the collection."""
        doc_count = stats.get("count", 0)
        size_bytes = size_info.get("totalSize", 0)
        
        description = f"Collection '{collection_name}' with {doc_count} documents"
        
        if size_bytes > 0:
            size_mb = size_bytes / (1024 * 1024)
            description += f" ({size_mb:.2f} MB)"
        
        # Add schema info
        if schema and "properties" in schema:
            try:
                prop_count = len(schema["properties"])
                description += f". Contains {prop_count} main fields."
            except Exception as e:
                description += f". Schema analysis completed with warnings."
        elif schema and "error" in schema:
            description += f". Schema analysis had issues: {schema['error']}"
        
        return description
    
    async def generate_unified_schema(self, output_file: str = "schemas/unified_schema.txt") -> bool:
        """Generate unified schema file from actual database structure."""
        try:
            print(f"\n🔍 Analyzing database structure...")
            
            # Get all collections
            collections = await self.get_collections()
            if not collections:
                print("❌ No collections found in database")
                return False
            
            print(f"📊 Found {len(collections)} collections: {', '.join(collections)}")
            
            # Analyze each collection
            collection_schemas = []
            for collection_name in collections:
                print(f"\n📋 Analyzing collection: {collection_name}")
                schema_info = await self.analyze_collection_schema(collection_name)
                collection_schemas.append(schema_info)
                print(f"   ✅ Analyzed {schema_info['document_count']} documents")
            
            # Generate unified schema document
            unified_schema = self._generate_unified_schema_document(collection_schemas)
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            # Write to file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(unified_schema)
            
            print(f"\n✅ Unified schema written to: {output_file}")
            print(f"📄 File size: {len(unified_schema)} characters")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to generate unified schema: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _generate_unified_schema_document(self, collection_schemas: List[Dict]) -> str:
        """Generate the unified schema document."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Generate database overview
        total_docs = sum(schema['document_count'] for schema in collection_schemas)
        total_collections = len(collection_schemas)
        
        schema_doc = f"""# Unified Database Schema Document
# Generated on: {timestamp}
# Database: {self.database_name}
# Total Collections: {total_collections}
# Total Documents: {total_docs:,}

This document provides a comprehensive schema for the {self.database_name} MongoDB database, including all collections, their relationships, field definitions, and supplementary explanations.

## Database Overview

The {self.database_name} database contains {total_collections} collections with a total of {total_docs:,} documents. This schema was automatically generated from the actual database structure.

## Collections and Relationships

"""
        
        # Add each collection
        for schema_info in collection_schemas:
            schema_doc += self._format_collection_schema(schema_info)
        
        # Add relationships table
        schema_doc += self._generate_relationships_table(collection_schemas)
        
        # Add common patterns and usage notes
        schema_doc += self._generate_usage_notes(collection_schemas)
        
        return schema_doc
    
    def _format_collection_schema(self, schema_info: Dict) -> str:
        """Format a collection's schema information."""
        collection_name = schema_info['name']
        doc_count = schema_info['document_count']
        description = schema_info['description']
        schema = schema_info['schema']
        relationships = schema_info['relationships']
        
        output = f"""### {collection_name} Collection

**Purpose**: {description}

**Document Count**: {doc_count:,} documents

**Key Relationships**:
"""
        
        if relationships:
            # Remove duplicates from relationships
            unique_relationships = []
            seen_descriptions = set()
            for rel in relationships:
                if rel['description'] not in seen_descriptions:
                    unique_relationships.append(rel)
                    seen_descriptions.add(rel['description'])
            
            for rel in unique_relationships:
                output += f"- {rel['description']}\n"
        else:
            output += "- No explicit relationships identified\n"
        
        output += f"""
**Schema**:
```json
{json.dumps(schema, indent=2, default=str)}
```

"""
        
        return output
    
    def _generate_relationships_table(self, collection_schemas: List[Dict]) -> str:
        """Generate a relationships table."""
        # Collect all relationships first
        all_relationships = []
        seen_relationships = set()
        
        # First, add primary keys
        for schema_info in collection_schemas:
            collection_name = schema_info['name']
            relationships = schema_info['relationships']
            
            for rel in relationships:
                if rel['type'] == 'primary_key':
                    # Create unique key for this relationship
                    rel_key = f"{collection_name}:{rel['field']}"
                    if rel_key not in seen_relationships:
                        all_relationships.append({
                            'from_collection': collection_name,
                            'from_field': rel['field'],
                            'to_collection': '-',
                            'to_field': '-',
                            'type': 'Primary Key'
                        })
                        seen_relationships.add(rel_key)
        
        # Then, add cross-collection relationships
        cross_collection_relationships = self._detect_cross_collection_relationships(collection_schemas)
        for rel in cross_collection_relationships:
            rel_key = f"{rel['from_collection']}:{rel['from_field']}:{rel['to_collection']}:{rel['to_field']}"
            if rel_key not in seen_relationships:
                all_relationships.append({
                    'from_collection': rel['from_collection'],
                    'from_field': rel['from_field'],
                    'to_collection': rel['to_collection'],
                    'to_field': rel['to_field'],
                    'type': rel['type']
                })
                seen_relationships.add(rel_key)
        
        # Calculate column widths based on content
        if all_relationships:
            max_from_collection = max(len(rel['from_collection']) for rel in all_relationships)
            max_from_field = max(len(rel['from_field']) for rel in all_relationships)
            max_to_collection = max(len(rel['to_collection']) for rel in all_relationships)
            max_to_field = max(len(rel['to_field']) for rel in all_relationships)
            max_type = max(len(rel['type']) for rel in all_relationships)
        else:
            max_from_collection = 15
            max_from_field = 10
            max_to_collection = 15
            max_to_field = 10
            max_type = 15
        
        # Ensure minimum widths and account for header text
        max_from_collection = max(max_from_collection, len("From Collection"))
        max_from_field = max(max_from_field, len("From Field"))
        max_to_collection = max(max_to_collection, len("To Collection"))
        max_to_field = max(max_to_field, len("To Field"))
        max_type = max(max_type, len("Relationship Type"))
        
        # Generate table
        output = """
## Key Field Relationships

"""
        
        # Header
        output += f"| {'From Collection':<{max_from_collection}} | {'From Field':<{max_from_field}} | {'To Collection':<{max_to_collection}} | {'To Field':<{max_to_field}} | {'Relationship Type':<{max_type}} |\n"
        
        # Separator - each column needs at least 3 dashes (for the spaces and content)
        output += f"|{'-' * (max_from_collection + 2)}|{'-' * (max_from_field + 2)}|{'-' * (max_to_collection + 2)}|{'-' * (max_to_field + 2)}|{'-' * (max_type + 2)}|\n"
        
        # Rows
        for rel in all_relationships:
            output += f"| {rel['from_collection']:<{max_from_collection}} | {rel['from_field']:<{max_from_field}} | {rel['to_collection']:<{max_to_collection}} | {rel['to_field']:<{max_to_field}} | {rel['type']:<{max_type}} |\n"
        
        output += "\n"
        return output
    
    def _detect_cross_collection_relationships(self, collection_schemas: List[Dict]) -> List[Dict]:
        """Detect relationships between different collections."""
        relationships = []
        
        # Common field patterns that might link collections
        linking_fields = ['csiId', 'soeld', 'nativeID', 'snapshotId', 'level3', 'name']
        
        # Build a map of field values to collections
        field_collections = {}
        
        for schema_info in collection_schemas:
            collection_name = schema_info['name']
            field_values = schema_info.get('field_values', {})
            
            for field, values in field_values.items():
                if field in linking_fields and values:
                    if field not in field_collections:
                        field_collections[field] = {}
                    
                    # Store which collection has which values for this field
                    for value in values:
                        if value not in field_collections[field]:
                            field_collections[field][value] = []
                        field_collections[field][value].append(collection_name)
        
        # Find actual relationships based on shared values
        for field, value_collections in field_collections.items():
            # Find values that appear in multiple collections
            for value, collections in value_collections.items():
                if len(collections) > 1:
                    # This value appears in multiple collections - actual relationship
                    for i, from_collection in enumerate(collections):
                        for to_collection in collections[i+1:]:
                            relationships.append({
                                'from_collection': from_collection,
                                'from_field': field,
                                'to_collection': to_collection,
                                'to_field': field,
                                'type': 'Foreign Key'
                            })
        
        return relationships
    
    def _generate_usage_notes(self, collection_schemas: List[Dict]) -> str:
        """Generate usage notes and common patterns."""
        output = """
## Data Types and Constraints

### Common Field Types
- **ObjectId**: MongoDB document identifiers
- **String**: Text fields, often with enumerated values
- **Number**: Numeric values (integers and floats)
- **Boolean**: True/false values
- **Array**: Lists of values
- **Object**: Nested document structures
- **Date**: Timestamp fields

## Performance Considerations

1. **Indexing**: Primary key fields and frequently queried fields should be indexed
2. **Aggregation Limits**: Use `$limit` in aggregation pipelines to prevent large result sets
3. **Join Order**: Start with the smallest collection when possible to optimize join performance
4. **Projection**: Use projection to limit returned fields and improve performance

## Common Query Patterns

### 1. Document Retrieval
- **Find by ID**: Use `_id` field for direct document lookup
- **Find by field**: Use specific field names for filtering
- **Aggregation**: Use `$lookup` for joining collections

### 2. Data Analysis
- **Group by field**: Use `$group` for aggregating data
- **Sort results**: Use `$sort` for ordering results
- **Limit results**: Use `$limit` to control result set size

This unified schema provides a comprehensive view of the database structure, relationships, and common query patterns for the {self.database_name} MongoDB database.
"""
        
        return output
    
    async def close(self):
        """Close the MongoDB connection."""
        if self.client:
            self.client.close()
            print("🔌 MongoDB connection closed")


async def main():
    """Main function to run the schema extractor."""
    parser = argparse.ArgumentParser(description='Extract MongoDB schema to unified schema file')
    parser.add_argument('--connection-string', required=True, 
                       help='MongoDB connection string')
    parser.add_argument('--database', required=True,
                       help='Database name')
    parser.add_argument('--output', default='schemas/unified_schema.txt',
                       help='Output file path (default: schemas/unified_schema.txt)')
    parser.add_argument('--sample-size', type=int, default=100,
                       help='Number of documents to sample per collection (default: 100)')
    
    args = parser.parse_args()
    
    # Create extractor
    extractor = MongoDBSchemaExtractor(args.connection_string, args.database)
    
    try:
        # Connect to database
        if not await extractor.connect():
            sys.exit(1)
        
        # Generate unified schema
        success = await extractor.generate_unified_schema(args.output)
        
        if success:
            print(f"\n🎉 Schema extraction completed successfully!")
            print(f"📁 Output file: {args.output}")
        else:
            print(f"\n❌ Schema extraction failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await extractor.close()


if __name__ == "__main__":
    asyncio.run(main()) 