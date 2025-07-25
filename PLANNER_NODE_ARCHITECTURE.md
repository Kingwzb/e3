# Planner Node Architecture

## Overview

The new planner node architecture separates intent detection from metrics extraction, providing a cleaner and more intelligent workflow. The planner node analyzes user messages and database schema to determine if a database query is needed, then routes to the appropriate node.

## Architecture Components

### 1. Planner Node (`app/workflows/nodes/planner_node.py`)

**Purpose**: Analyzes user messages and determines if database queries are needed.

**Key Features**:
- **LLM-based Analysis**: Uses Vertex AI to intelligently analyze user intent
- **Schema Awareness**: Reviews database schema to understand available data
- **Confidence Scoring**: Provides confidence levels for decisions
- **Fallback Detection**: Uses keyword-based detection when LLM fails
- **Routing Logic**: Determines next node (metrics or RAG)

**Input**:
- User message
- Database schema
- Conversation context

**Output**:
```json
{
    "planning_data": {
        "needs_database_query": true/false,
        "reasoning": "Explanation of decision",
        "relevant_collections": ["list", "of", "collections"],
        "query_type": "find|aggregate|count|analysis",
        "confidence": 0.0-1.0,
        "user_message": "original message",
        "schema_used": "unified_schema.txt"
    },
    "next_node": "metrics_extraction_node|rag_node",
    "trigger_metrics": true/false
}
```

### 2. Updated Metrics Node (`app/workflows/nodes/metrics_node.py`)

**Purpose**: Executes database queries when triggered by planner node.

**Key Changes**:
- **Removed Keyword Detection**: No longer uses `_should_extract_metrics()` with keywords
- **Planner-Driven**: Uses planner node's decision (`trigger_metrics`)
- **Simplified Logic**: Focuses only on query execution
- **Better Integration**: Receives planning data from previous node

**Decision Logic**:
```python
def _should_extract_metrics(state: WorkflowState) -> bool:
    planning_data = state.get("planning_data", {})
    return planning_data.get("trigger_metrics", False)
```

## Workflow Flow

### 1. User Input
```
User: "Show me applications with high criticality"
```

### 2. Planner Node Analysis
```
Input: User message + Database schema
Process: LLM analysis with planning prompt
Output: {
    "needs_database_query": true,
    "reasoning": "User is asking for application data with specific criteria",
    "confidence": 0.95,
    "next_node": "metrics_extraction_node",
    "trigger_metrics": true
}
```

### 3. Metrics Node Execution
```
Input: Planning decision + User message
Process: Dynamic database query execution
Output: Query results and metrics data
```

### 4. RAG Node (if no database query needed)
```
Input: User message
Process: Vector search and response generation
Output: General knowledge response
```

## Benefits

### 1. **Intelligent Decision Making**
- LLM-based analysis instead of keyword matching
- Context-aware decisions
- Confidence scoring for better routing

### 2. **Cleaner Separation of Concerns**
- Planner: Intent detection and routing
- Metrics: Database query execution
- RAG: General knowledge responses

### 3. **Better Error Handling**
- Fallback to keyword detection when LLM fails
- Graceful degradation
- Detailed error reporting

### 4. **Enhanced Flexibility**
- Easy to add new decision criteria
- Configurable confidence thresholds
- Extensible planning logic

## Configuration

### Planner Node Configuration
```python
{
    "confidence_threshold": 0.5,
    "schema_file": "schemas/unified_schema.txt",
    "planning_method": "llm_analysis"
}
```

### Metrics Node Configuration
```python
{
    "metrics_limit": 100,
    "metrics_context_limit": 3,
    "include_aggregation": True,
    "join_strategy": "lookup"
}
```

## Testing

### Test Files
- `test_planner_node.py`: Tests planner node functionality
- `test_dynamic_db_workflow_integration.py`: Tests full workflow integration

### Test Cases
1. **Database Query Messages**:
   - "Show me applications with high criticality"
   - "How many employees are there?"
   - "Find applications in the finance sector"

2. **Non-Database Messages**:
   - "What's the weather like?"
   - "Tell me a joke"
   - "What is the capital of France?"

3. **Integration Tests**:
   - Planner → Metrics node routing
   - Planner → RAG node routing
   - Error handling and fallbacks

## Migration from Old Architecture

### Before (Keyword-Based)
```python
# In metrics_node.py
def _should_extract_metrics(message: str) -> bool:
    database_keywords = ["application", "employee", ...]
    return any(keyword in message.lower() for keyword in database_keywords)
```

### After (Planner-Based)
```python
# In planner_node.py
async def planner_node(state: WorkflowState) -> Dict[str, Any]:
    # LLM-based analysis with schema awareness
    # Returns intelligent decision with confidence

# In metrics_node.py
def _should_extract_metrics(state: WorkflowState) -> bool:
    planning_data = state.get("planning_data", {})
    return planning_data.get("trigger_metrics", False)
```

## Future Enhancements

### 1. **Advanced Planning**
- Multi-step query planning
- Query optimization suggestions
- Performance analysis

### 2. **Enhanced Routing**
- Multiple specialized nodes
- Conditional routing based on query type
- Load balancing between nodes

### 3. **Better Context**
- Conversation history analysis
- User preference learning
- Adaptive confidence thresholds

### 4. **Monitoring and Analytics**
- Planning decision tracking
- Performance metrics
- User satisfaction feedback

## Usage Examples

### Basic Usage
```python
from app.workflows.nodes.planner_node import planner_node
from app.workflows.nodes.metrics_node import metrics_extraction_node

# Create workflow state
state = WorkflowState(
    conversation_id="test-123",
    current_message="Show me high criticality applications",
    messages=[]
)

# Run planner node
planner_result = await planner_node(state)
state.update(planner_result)

# Run metrics node if needed
if state.get("trigger_metrics", False):
    metrics_result = await metrics_extraction_node(state)
    state.update(metrics_result)
```

### Testing
```bash
# Test planner node
python test_planner_node.py

# Test full workflow integration
python test_dynamic_db_workflow_integration.py
```

This architecture provides a more intelligent, maintainable, and scalable approach to database query planning and execution. 