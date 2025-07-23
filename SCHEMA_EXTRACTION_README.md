# MongoDB Schema Extraction Tools

This directory contains tools to extract and analyze MongoDB database schemas and generate unified schema files for use with the dynamic database query tool.

## Overview

The schema extraction tools provide three main functionalities:

1. **Extract schema from MongoDB**: Connect to a MongoDB database and analyze the actual collections and their schemas
2. **Generate unified schema file**: Create a comprehensive text-based schema document
3. **Update Python schema file**: Convert the text schema to a Python module for import

## Files

### Core Scripts

- **`extract_mongodb_schema.py`**: Main schema extraction script
- **`update_schema_from_file.py`**: Updates Python schema file from text file
- **`extract_and_update_schema.py`**: Combined script that does both operations

### Generated Files

- **`schemas/unified_schema.txt`**: Text-based unified schema document
- **`schemas/unified_schema.py`**: Python module with the unified schema

## Usage

### Option 1: Complete Extraction and Update (Recommended)

Use the combined script to extract schema from MongoDB and update both files:

```bash
python extract_and_update_schema.py \
  --connection-string "mongodb://localhost:27017" \
  --database "your_database_name" \
  --sample-size 100
```

### Option 2: Step-by-Step Process

#### Step 1: Extract Schema from MongoDB

```bash
python extract_mongodb_schema.py \
  --connection-string "mongodb://localhost:27017" \
  --database "your_database_name" \
  --output "schemas/unified_schema.txt" \
  --sample-size 100
```

#### Step 2: Update Python Schema File

```bash
python update_schema_from_file.py schemas/unified_schema.txt
```

## Parameters

### Connection Parameters

- **`--connection-string`**: MongoDB connection string (required)
  - Example: `"mongodb://localhost:27017"`
  - Example: `"mongodb://username:password@host:port/database"`

- **`--database`**: Database name (required)
  - Example: `"ee-productivities"`

### Output Parameters

- **`--text-output`**: Text schema output file (default: `schemas/unified_schema.txt`)
- **`--python-output`**: Python schema output file (default: `schemas/unified_schema.py`)

### Analysis Parameters

- **`--sample-size`**: Number of documents to sample per collection (default: 100)
  - Higher values provide more accurate schema analysis but take longer
  - Recommended: 100-500 for most databases

## Examples

### Local MongoDB Instance

```bash
python extract_and_update_schema.py \
  --connection-string "mongodb://localhost:27017" \
  --database "ee-productivities"
```

### Remote MongoDB with Authentication

```bash
python extract_and_update_schema.py \
  --connection-string "mongodb://username:password@host:27017" \
  --database "production_db" \
  --sample-size 200
```

### Custom Output Files

```bash
python extract_and_update_schema.py \
  --connection-string "mongodb://localhost:27017" \
  --database "my_database" \
  --text-output "custom_schema.txt" \
  --python-output "custom_schema.py"
```

## What the Scripts Do

### Schema Analysis

The extraction process analyzes each collection by:

1. **Sampling documents**: Takes a sample of documents from each collection
2. **Analyzing field types**: Determines data types for each field
3. **Detecting relationships**: Identifies potential primary keys and relationships
4. **Generating descriptions**: Creates human-readable descriptions of collections and fields
5. **Inferring constraints**: Detects enums, required fields, and value patterns

### Output Format

The generated schema includes:

- **Database overview**: Summary of collections and document counts
- **Collection details**: Purpose, document count, and relationships for each collection
- **Field schemas**: JSON schema for each collection with field types and descriptions
- **Relationship table**: Mapping of relationships between collections
- **Usage notes**: Performance considerations and common query patterns

### Schema Features

- **Type inference**: Automatically detects field types from actual data
- **Enum detection**: Identifies fields with limited value sets
- **Relationship detection**: Finds potential foreign key relationships
- **Nested object support**: Handles complex nested document structures
- **Array analysis**: Analyzes array contents and element types

## Integration with Dynamic DB Tool

After running the schema extraction, the generated Python schema file can be imported and used with the dynamic database query tool:

```python
from schemas.unified_schema import UNIFIED_SCHEMA

# Use in dynamic DB tool
tool = create_dynamic_db_tool()
query_dict = await tool._generate_mongodb_query(
    user_prompt="Find high criticality applications",
    unified_schema=UNIFIED_SCHEMA,
    limit=10
)
```

## Troubleshooting

### Connection Issues

- **Authentication failed**: Check username/password in connection string
- **Connection refused**: Verify MongoDB is running and accessible
- **Network timeout**: Check firewall settings and network connectivity

### Analysis Issues

- **Empty collections**: Collections with no documents will show minimal schema
- **Large collections**: Use smaller sample sizes for very large collections
- **Complex schemas**: Very complex nested structures may not be fully captured

### Output Issues

- **Permission denied**: Ensure write permissions for output directories
- **Encoding issues**: Files are written in UTF-8 encoding
- **File size**: Large schemas may generate large files

## Performance Considerations

- **Sample size**: Larger samples provide better accuracy but take longer
- **Collection count**: More collections = longer processing time
- **Document size**: Large documents increase memory usage
- **Network latency**: Remote databases may be slower to analyze

## Best Practices

1. **Regular updates**: Re-run extraction when database schema changes
2. **Version control**: Track schema changes in version control
3. **Testing**: Test generated schemas with actual queries
4. **Documentation**: Keep notes about manual schema adjustments
5. **Backup**: Keep backups of important schema files

## Advanced Usage

### Custom Relationship Detection

You can modify the `_analyze_relationships` method in `extract_mongodb_schema.py` to add custom relationship detection logic.

### Custom Field Analysis

Extend the `_generate_field_description` method to add custom field descriptions based on your domain knowledge.

### Schema Validation

Add validation logic to ensure extracted schemas meet your requirements before updating the Python file.

## Support

For issues or questions about the schema extraction tools:

1. Check the troubleshooting section above
2. Review the generated schema files for accuracy
3. Test with a small sample size first
4. Verify MongoDB connection and permissions 