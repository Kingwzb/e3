# Dynamic DB Tool

A self-contained dynamic database tool that generates MongoDB queries on the fly using LLM. This implementation has minimal dependencies and can work with any MongoDB adapter and LLM client.

## 🎯 **Key Features**

- **Self-contained**: Only depends on generic MongoDB adapter and LLM client
- **Flexible**: Works with any MongoDB database and LLM service
- **Schema-aware**: Uses unified schema documents for accurate query generation
- **Error-resistant**: Handles missing relationships and invalid field references
- **Extensible**: Easy to customize with custom adapters and LLM clients

## 📦 **Dependencies**

### Required Dependencies
- `langchain` - For BaseTool functionality
- `pydantic` - For data validation
- `pymongo` - For MongoDB operations (optional, can use custom adapter)

### Optional Dependencies
- Any LLM client (Vertex AI, OpenAI, etc.)
- Any MongoDB adapter (custom implementations supported)

## 🚀 **Quick Start**

### Basic Usage

```python
from app.tools.dynamic_db_tool import create_dynamic_db_tool

# Create tool with default components
tool = create_dynamic_db_tool()

# Use the tool
result = await tool._arun(
    user_prompt="Find applications with high criticality",
    unified_schema=your_schema_document,
    limit=10
)
```

### With Custom Components

```python
# Create custom adapter
class CustomMongoAdapter:
    async def initialize(self):
        # Initialize your MongoDB connection
        pass
    
    async def switch_collection(self, collection_name: str):
        # Switch to collection
        pass
    
    async def execute_native_query(self, query):
        # Execute query and return results
        return results

# Create custom LLM client
class CustomLLMClient:
    async def generate_response(self, prompt: str) -> str:
        # Call your LLM service
        return "generated_query_json"

# Create tool with custom components
tool = create_dynamic_db_tool(
    adapter=CustomMongoAdapter(),
    llm_client=CustomLLMClient()
)
```

## 🔧 **Configuration**

### Environment Variables

```bash
# MongoDB Configuration
METRICS_MONGODB_URI=mongodb://localhost:27017
METRICS_MONGODB_DATABASE=your_database

# LLM Configuration
LLM_CLIENT_TYPE=vertex_ai  # or your custom type
```

### Default Behavior

- **MongoDB**: Uses `pymongo` with default connection string
- **LLM**: Uses placeholder client (replace with actual implementation)
- **Schema**: Loads from `schemas/unified_schema.txt` if available

## 📋 **API Reference**

### DynamicDBQueryTool

#### Constructor
```python
DynamicDBQueryTool(adapter=None, llm_client=None)
```

#### Methods

##### `_arun(**kwargs) -> str`
Main async execution method.

**Parameters:**
- `user_prompt` (str): Natural language query description
- `unified_schema` (str): Schema document
- `limit` (int, optional): Maximum results (default: 100)
- `include_aggregation` (bool, optional): Include aggregation (default: False)
- `join_strategy` (str, optional): Join strategy (default: "lookup")

**Returns:** JSON string with query results

##### `_generate_mongodb_query(...) -> Dict[str, Any]`
Generate MongoDB query using LLM.

##### `_execute_query(query_dict) -> List[Dict[str, Any]]`
Execute generated query against database.

##### `_format_results(results, query_dict) -> Dict[str, Any]`
Format query results into structured response.

## 🔌 **Adapter Interface**

Your MongoDB adapter must implement:

```python
class YourMongoAdapter:
    async def initialize(self):
        """Initialize database connection."""
        pass
    
    async def switch_collection(self, collection_name: str):
        """Switch to different collection."""
        pass
    
    async def execute_native_query(self, query: DatabaseQuery) -> List[Dict[str, Any]]:
        """Execute database query."""
        pass
```

## 🤖 **LLM Client Interface**

Your LLM client must implement:

```python
class YourLLMClient:
    async def generate_response(self, prompt: str) -> str:
        """Generate response from prompt string."""
        return "generated_query_json_string"
```

## 📊 **Query Generation**

The tool generates queries in this format:

```json
{
  "primary_collection": "collection_name",
  "filter": {},
  "projection": {},
  "sort": {},
  "limit": 100,
  "aggregation": [],
  "joins": []
}
```

### Supported Operations

- **Find queries**: Simple document retrieval
- **Aggregation pipelines**: Complex data processing
- **Joins**: Multi-collection queries (when relationships exist)
- **Filtering**: Field-based document filtering
- **Sorting**: Result ordering
- **Projection**: Field selection

## 🛡️ **Error Handling**

The tool includes robust error handling:

- **Schema validation**: Checks field existence before query generation
- **Relationship detection**: Avoids joins when no relationships exist
- **Field validation**: Ensures referenced fields exist in schema
- **Query validation**: Validates pipeline before execution
- **Graceful fallbacks**: Provides helpful error messages

## 🔍 **Schema Requirements**

Your schema document should include:

- Collection names and purposes
- Field definitions with types
- Relationship information
- Data constraints and enums
- Performance considerations

Example schema format:
```markdown
### collection_name Collection
**Purpose**: Description of collection purpose
**Schema**:
```json
{
  "properties": {
    "field_name": {
      "type": "string",
      "enum": ["value1", "value2"]
    }
  }
}
```
```

## 🧪 **Testing**

Run the standalone tests:

```bash
python test_standalone_tool.py
```

## 🔄 **Migration from Original**

The original implementation has been replaced with this self-contained version. The interface remains the same, but now supports dependency injection:

1. **Import remains the same**:
   ```python
   from app.tools.dynamic_db_tool import create_dynamic_db_tool
   ```

2. **Constructor now supports dependency injection**:
   ```python
   # Default behavior (same as before)
   tool = create_dynamic_db_tool()
   
   # With custom components
   tool = create_dynamic_db_tool(
       adapter=CustomMongoAdapter(),
       llm_client=CustomLLMClient()
   )
   ```

3. **Benefits**: Self-contained with fewer dependencies and better error handling

## 🎯 **Benefits**

- **Minimal dependencies**: Only core requirements
- **Easy deployment**: Self-contained implementation
- **Flexible integration**: Works with any MongoDB and LLM setup
- **Better error handling**: Robust validation and error messages
- **Schema-aware**: Prevents invalid queries
- **Extensible**: Easy to customize for specific needs

## 📝 **Example Usage**

```python
import asyncio
from app.tools.dynamic_db_tool import create_dynamic_db_tool

async def main():
    # Create tool
    tool = create_dynamic_db_tool()
    
    # Define schema
    schema = """
    ### users Collection
    **Schema**:
    ```json
    {
      "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"}
      }
    }
    ```
    """
    
    # Execute query
    result = await tool._arun(
        user_prompt="Find users older than 25",
        unified_schema=schema,
        limit=10
    )
    
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

This standalone implementation provides a clean, self-contained solution for dynamic database querying with minimal external dependencies. 