# Dynamic Database Tool

The Dynamic Database Tool is a powerful feature that allows you to generate and execute MongoDB queries on the fly using natural language prompts and schema documents. This tool uses an LLM (Large Language Model) to interpret your requests and generate appropriate MongoDB queries.

## Overview

Unlike the predefined ee-productivities tools that have fixed query capabilities, the dynamic database tool can handle any query you describe in natural language, as long as you provide the appropriate schema document that describes the collection structure.

## Key Features

- **Natural Language Queries**: Describe what you want to find in plain English
- **Multi-Collection Support**: Query and join data across multiple MongoDB collections
- **Unified Schema Approach**: Uses a comprehensive schema document that includes all collections, relationships, and field definitions
- **Flexible Query Types**: Supports both simple find queries and complex aggregation pipelines
- **Automatic Query Generation**: LLM generates the appropriate MongoDB query based on your request
- **Advanced Joins**: Supports $lookup operations for joining collections
- **Complex Filtering**: Apply filters across multiple collections
- **Structured Results**: Returns results in a consistent JSON format with metadata
- **Relationship Awareness**: Understands relationships between collections and generates appropriate joins

## Usage

### Basic Usage

```python
from app.tools.dynamic_db_tool import create_dynamic_db_tool

# Create the tool
tool = create_dynamic_db_tool()

# Execute a query using unified schema
result = await tool._arun(
    user_prompt="Find all applications with high criticality",
    unified_schema=your_unified_schema_document,
    limit=10
)

# Execute a multi-collection query using unified schema
result = await tool._arun(
    user_prompt="Find high criticality applications with their employee ratio data",
    unified_schema=your_unified_schema_document,
    limit=10,
    include_aggregation=True
)
```

### Parameters

- **user_prompt** (str): Natural language description of what data to query
- **unified_schema** (str): Comprehensive schema document describing all collections, their relationships, and field definitions
- **limit** (int, optional): Maximum number of results to return (default: 100)
- **include_aggregation** (bool, optional): Whether to include aggregation pipeline (default: False)
- **join_strategy** (str, optional): Join strategy for multi-collection queries (default: "lookup")

### Unified Schema Document Format

The unified schema document should be a comprehensive document that describes all collections, their relationships, field definitions, and supplementary explanations. Here's an example structure:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "_id": {
      "type": "object",
      "properties": {
        "$oid": {
          "type": "string",
          "description": "Unique identifier for the document in MongoDB."
        }
      },
      "required": ["$oid"]
    },
    "snapshotId": {
      "type": "string",
      "description": "Unique identifier for the snapshot."
    },
    "application": {
      "type": "object",
      "properties": {
        "csiId": {
          "type": "integer",
          "description": "Unique identifier for the application in CSI."
        },
        "criticality": {
          "type": "string",
          "enum": ["LOW", "MEDIUM", "HIGH"],
          "description": "Criticality level of the application."
        }
      }
    }
  }
}
```

## Example Queries

### Single Collection Queries

```python
# Find high criticality applications
result = await tool._arun(
    user_prompt="Find all applications with high criticality level",
    collections_config={"application_snapshot": application_schema},
    limit=10
)

# Find applications by organization
result = await tool._arun(
    user_prompt="Find applications in the IT department",
    collections_config={"application_snapshot": application_schema},
    limit=5
)
```

### Multi-Collection Join Queries

```python
# Join applications with employee ratios
result = await tool._arun(
    user_prompt="Find high criticality applications and their associated employee ratio data",
    collections_config={
        "application_snapshot": application_schema,
        "employee_ratio": employee_schema
    },
    limit=10,
    include_aggregation=True
)

# Complex join with management segments
result = await tool._arun(
    user_prompt="Find applications by criticality level and join with their management segment information",
    collections_config={
        "application_snapshot": application_schema,
        "management_segment_tree": management_schema
    },
    limit=10,
    include_aggregation=True
)
```

### Complex Analytics Queries

```python
# Cross-collection analysis
result = await tool._arun(
    user_prompt="Analyze the relationship between application criticality and employee ratios, group by sector",
    collections_config={
        "application_snapshot": application_schema,
        "employee_ratio": employee_schema,
        "management_segment_tree": management_schema
    },
    limit=15,
    include_aggregation=True
)

# Performance metrics analysis
result = await tool._arun(
    user_prompt="Calculate average engineer ratio by application criticality and management segment",
    collections_config={
        "application_snapshot": application_schema,
        "employee_ratio": employee_schema,
        "management_segment_tree": management_schema
    },
    limit=10,
    include_aggregation=True
)
```

### Advanced Filtering and Sorting

```python
# Filtered joins
result = await tool._arun(
    user_prompt="Find active applications with high criticality that have employee ratios above 0.7",
    collections_config={
        "application_snapshot": application_schema,
        "employee_ratio": employee_schema
    },
    limit=10,
    include_aggregation=True
)

# Sorted multi-collection results
result = await tool._arun(
    user_prompt="Find applications sorted by criticality level and then by employee count in descending order",
    collections_config={
        "application_snapshot": application_schema,
        "employee_ratio": employee_schema
    },
    limit=10,
    include_aggregation=True
)
```

## Response Format

The tool returns results in a structured JSON format:

```json
{
  "query_info": {
    "primary_collection": "application_snapshot",
    "query_type": "aggregation",
    "limit": 10,
    "joins": [
      {
        "collection": "employee_ratio",
        "type": "lookup",
        "local_field": "application.csiId",
        "foreign_field": "csiId",
        "as": "employee_data"
      }
    ],
    "generated_query": {
      "primary_collection": "application_snapshot",
      "filter": {},
      "projection": {},
      "sort": {},
      "limit": 10,
      "aggregation": [
        {
          "$lookup": {
            "from": "employee_ratio",
            "localField": "application.csiId",
            "foreignField": "csiId",
            "as": "employee_data"
          }
        }
      ],
      "joins": [...]
    }
  },
  "results": {
    "total_count": 5,
    "data": [
      {
        "_id": {"$oid": "..."},
        "snapshotId": "...",
        "application": {
          "csiId": 12345,
          "criticality": "HIGH"
        },
        "employee_data": [...]
      }
    ]
  },
  "summary": {
    "execution_time": "2024-01-15T10:30:00",
    "result_count": 5,
    "collections_involved": ["application_snapshot", "employee_ratio"]
  }
}
```

## Best Practices

1. **Provide Clear Prompts**: Be specific about what you want to find and which collections to involve
2. **Use Accurate Schemas**: Ensure your schema documents accurately reflect the collection structures
3. **Set Appropriate Limits**: Use the limit parameter to prevent large result sets
4. **Use Aggregation for Multi-Collection Queries**: Set `include_aggregation=True` for joins and complex analytics
5. **Optimize Join Performance**: Limit the number of collections in a single query for better performance
6. **Use Meaningful Field Names**: Ensure your schemas have descriptive field names for better LLM understanding
7. **Handle Errors**: The tool returns error information in the response if something goes wrong

## Error Handling

The tool includes comprehensive error handling:

- **Schema Validation**: Ensures the schema document is valid JSON Schema
- **Query Generation**: Handles LLM generation errors gracefully
- **Database Errors**: Catches and reports database connection and query execution errors
- **Result Formatting**: Handles serialization issues with ObjectId and datetime fields

## Integration with Existing Tools

The dynamic database tool can be used alongside the existing ee-productivities tools:

```python
from app.tools.ee_productivities_tools import create_ee_productivities_tools
from app.tools.dynamic_db_tool import create_dynamic_db_tools

# Get all tools
all_tools = create_ee_productivities_tools() + create_dynamic_db_tools()
```

## Example Script

See `examples/dynamic_db_example.py` for a complete example showing how to use the dynamic database tool with the schema documents from the screenshots.

## Limitations

- Requires an LLM client to be properly configured
- Query generation depends on the quality of the schema document
- Complex queries may require multiple attempts or refinement
- Performance depends on the underlying database and LLM response times

## Troubleshooting

### Common Issues

1. **LLM Client Not Available**: Ensure your LLM provider is properly configured
2. **Invalid Schema**: Check that your schema document is valid JSON Schema
3. **Collection Not Found**: Verify the collection name exists in your database
4. **Query Generation Fails**: Try simplifying your prompt or providing more context

### Debug Information

The tool includes detailed logging that can help diagnose issues:

- Database connection status
- Collection switching operations
- Generated query structure
- Execution results and timing

Check the application logs for detailed information about query generation and execution. 