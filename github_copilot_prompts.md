# GitHub Copilot Prompts for AI Chat Agent with RAG and Metrics

This document contains detailed prompts for GitHub Copilot to generate a complete AI chat agent project with RAG (Retrieval Augmented Generation) and database metrics integration using LangGraph orchestration.

## Project Overview Prompt

```
Create a FastAPI-based conversational AI system that combines:
1. Retrieval Augmented Generation (RAG) using FAISS vector database
2. Database metrics extraction using LangChain tools
3. LangGraph workflow orchestration for multi-step conversations
4. OpenAI LLM integration for natural language processing
5. SQLAlchemy with async PostgreSQL for metrics storage
6. Conversation history management
7. Comprehensive documentation system with auto-indexing

Tech Stack: FastAPI, OpenAI, FAISS, LangChain, LangGraph, PostgreSQL, SQLAlchemy, Pydantic

Project Structure:
- app/ (main application)
- data/docs/ (documentation for RAG)
- scripts/ (utility scripts)
- tests/ (test files)
```

## 1. Project Structure and Dependencies

### Requirements.txt Prompt
```
Create a requirements.txt file for an AI chat agent with these dependencies:
- FastAPI >=0.104.0 and uvicorn for web framework
- OpenAI >=1.3.0 for LLM integration
- LangChain >=0.1.0 and LangGraph >=0.0.40 for agent orchestration
- sentence-transformers >=2.2.0 for embeddings
- faiss-cpu >=1.7.0 and numpy for vector database
- pydantic >=2.5.0 for data validation
- python-dotenv for environment management
- sqlalchemy >=2.0.20 with aiosqlite and asyncpg for async database
- httpx for HTTP client
- watchdog >=3.0.0 for file watching
- pytest and pytest-asyncio for testing
```

### Project Structure Prompt
```
Create a Python project structure for an AI chat agent with:

app/
├── __init__.py
├── main.py (FastAPI app entry point)
├── api/
│   ├── __init__.py
│   └── chat.py (chat endpoints)
├── core/
│   ├── __init__.py
│   ├── config.py (settings with pydantic-settings)
│   ├── database.py (async SQLAlchemy setup)
│   └── llm.py (OpenAI client)
├── models/
│   ├── __init__.py
│   ├── chat.py (request/response models)
│   └── state.py (LangGraph state models)
├── workflows/
│   ├── __init__.py
│   ├── chat_workflow.py (main LangGraph workflow)
│   ├── workflow_factory.py
│   └── nodes/
│       ├── __init__.py
│       ├── rag_node.py (RAG extraction)
│       ├── metrics_node.py (database metrics)
│       ├── response_node.py (LLM response generation)
│       ├── conversation_node.py (history management)
│       └── orchestration_node.py (workflow control)
├── tools/
│   ├── __init__.py
│   ├── vector_store.py (FAISS operations)
│   ├── langchain_db_tools.py (LangChain database tools)
│   └── conversation_tools.py (conversation management)
└── utils/
    ├── __init__.py
    └── logging.py

data/docs/ (markdown documentation for RAG)
scripts/ (utility scripts)
tests/ (test files)
```

## 2. Core Configuration and Database

### Config.py Prompt
```
Create app/core/config.py with pydantic-settings for:
- OpenAI API key and model configuration
- Database URL for async PostgreSQL
- FAISS index path configuration
- Logging level settings
- CORS origins
- Environment-specific settings (development, testing, production)
- Vector store configuration (embedding model, index parameters)
- LangGraph workflow settings
- Conversation history limits

Use BaseSettings with env_file support and validation.
```

### Database.py Prompt
```
Create app/core/database.py with:
- Async SQLAlchemy engine and session factory
- Database models for:
  * MetricsData (id, metric_name, metric_value, timestamp, category, meta_data)
  * ConversationHistory (id, conversation_id, message_type, content, timestamp)
- Async session dependency for FastAPI
- Database initialization and table creation
- Connection pooling configuration
- Proper async context management
```

### LLM.py Prompt
```
Create app/core/llm.py with:
- OpenAI async client setup
- Chat completion wrapper with error handling
- Token counting and rate limiting
- Temperature and model configuration
- Streaming response support
- Retry logic with exponential backoff
- Response validation and parsing
```

## 3. Data Models

### State.py Prompt
```
Create app/models/state.py with LangGraph state models:
- WorkflowState TypedDict with:
  * conversation_id: str
  * current_message: str
  * messages: List[Dict[str, str]] (conversation history)
  * rag_context: Optional[str]
  * metrics_data: Optional[Dict[str, Any]]
  * final_response: Optional[str]
  * error: Optional[str]
  * configuration parameters (history_limit, metrics_environment, etc.)
- RAGResult Pydantic model (context, sources, confidence_score)
- MetricsResult Pydantic model (data, query_used, execution_time)
```

### Chat.py Prompt
```
Create app/models/chat.py with Pydantic models:
- ChatRequest (message: str, conversation_id: str, optional parameters)
- ChatResponse (response: str, conversation_id: str, timestamp: datetime)
- Message (role: str, content: str, timestamp: datetime)
- ConversationSummary (id, participant_count, message_count, last_activity)
- Proper validation, examples, and field descriptions
```

## 4. Vector Store and RAG

### Vector Store Prompt
```
Create app/tools/vector_store.py with FAISS vector store:
- VectorStore class with sentence-transformers embeddings
- Methods: add_documents, search, clear, save_index, load_index
- Support for both string documents and dict documents with metadata
- Batch processing for large document sets
- Similarity search with configurable k and score threshold
- Index persistence and loading
- Document metadata tracking
- Error handling and logging
```

### RAG Node Prompt
```
Create app/workflows/nodes/rag_node.py with:
- Async function rag_extraction_node(state: WorkflowState) -> WorkflowState
- Extract relevant context from vector store based on current message
- Use semantic search with configurable similarity threshold
- Combine multiple document sources intelligently
- Add source tracking and confidence scoring
- Handle empty results gracefully
- Update state with rag_context
- Comprehensive logging
```

## 5. Database Tools and Metrics

### LangChain DB Tools Prompt
```
Create app/tools/langchain_db_tools.py with LangChain tools:
- GetMetricsByCategoryTool: retrieve metrics by category with date filtering
- GetTopMetricsTool: get top N metrics by value for specific metric names
- ExecuteCustomQueryTool: safe SQL query execution (SELECT only)
- Pydantic input schemas for each tool
- DatabaseToolsConfig class for environment-specific settings
- Factory functions: create_langchain_db_tools, create_tool_config_for_environment
- Comprehensive error handling and validation
- Security measures (SQL injection prevention)
- Performance optimization with query limits
```

### Metrics Node Prompt
```
Create app/workflows/nodes/metrics_node.py with:
- Async function metrics_extraction_node(state: WorkflowState) -> WorkflowState
- LLM-powered tool selection based on user query intent
- Integration with LangChain database tools
- Support for multiple tool execution in single request
- Tool result aggregation and formatting
- Error handling for failed tool executions
- Metrics about tool usage and performance
- Update state with metrics_data
```

## 6. Workflow Orchestration

### Chat Workflow Prompt
```
Create app/workflows/chat_workflow.py with LangGraph workflow:
- StateGraph with WorkflowState
- Nodes: rag_extraction, metrics_extraction, response_generation
- Conditional edges based on message content and context
- Parallel execution where possible (RAG + metrics)
- Error handling and recovery paths
- Conversation history integration
- Workflow configuration and customization
- Proper state transitions and validation
```

### Response Node Prompt
```
Create app/workflows/nodes/response_node.py with:
- Async function response_generation_node(state: WorkflowState) -> WorkflowState
- Combine conversation history, RAG context, and metrics data
- Generate contextual LLM responses using OpenAI
- Handle different response types (informational, analytical, error)
- Maintain conversation continuity
- Format metrics data for human readability
- Token management and response length control
- Update state with final_response
```

## 7. API Endpoints

### Chat API Prompt
```
Create app/api/chat.py with FastAPI endpoints:
- POST /api/chat for main chat functionality
- GET /api/chat/health for health checks
- GET /api/chat/conversations for conversation listing
- Integration with LangGraph workflow
- Async request handling
- Proper error responses and status codes
- Request validation and sanitization
- Response streaming support (optional)
- Rate limiting and authentication (basic)
- Comprehensive logging and monitoring
```

### Main App Prompt
```
Create app/main.py with FastAPI application:
- FastAPI app initialization with metadata
- CORS middleware configuration
- Include API routers
- Startup and shutdown event handlers
- Database connection management
- Vector store initialization
- Global exception handling
- Health check endpoints
- Proper logging setup
```

## 8. Documentation System

### Documentation Files Prompt
```
Create comprehensive markdown documentation in data/docs/:
- system_overview.md: Platform features, architecture, data sources
- metrics_data_schema.md: Database schema, metric categories, queries
- api_usage_guide.md: Authentication, endpoints, SDKs, examples
- conversation_history_schema.md: Conversation table structure, patterns
- troubleshooting_guide.md: Common issues, solutions, monitoring
- getting_started.md: User onboarding, setup, use cases

Each file should be detailed, well-structured, and include practical examples.
```

### Documentation Indexing Prompt
```
Create scripts/update_vector_db.py for RAG documentation management:
- Load markdown files from data/docs/
- Process documents with section-based chunking (by headers)
- Hash-based change detection for incremental updates
- Metadata tracking in JSON file
- Command-line interface with options: --rebuild, --stats, --verbose
- Integration with FAISS vector store
- Support for file watching and auto-updates
- Comprehensive logging and error handling
```

## 9. Utility Scripts

### Mock Data Generation Prompt
```
Create scripts/insert_mock_metrics.py for testing:
- Generate realistic mock metrics across categories:
  * Engagement: daily_active_users, session_duration, feature_usage_rate
  * Performance: response_time, uptime_percentage, error_rate
  * Revenue: daily_revenue, conversion_rate, customer_lifetime_value
  * Satisfaction: nps_score, customer_satisfaction, support_rating
- 30 days of historical data with realistic trends
- Department and user-specific metadata
- Async database insertion with proper error handling
- Command-line interface for data volume control
```

### Setup and Verification Prompts
```
Create setup scripts:
- setup.sh: Automated Linux/macOS setup with virtual environment
- setup.bat: Windows batch file for setup
- verify_setup.py: Installation verification with component testing
- Makefile: Development commands (setup, run, test, clean, docs management)

Each script should handle dependencies, environment setup, and provide clear feedback.
```

## 10. Testing Framework

### Test Structure Prompt
```
Create comprehensive tests in tests/:
- test_api.py: FastAPI endpoint testing with async client
- test_workflows.py: LangGraph workflow testing with mock data
- test_agents.py: Individual node testing (RAG, metrics, response)
- Fixtures for database, vector store, and LLM mocking
- Integration tests for end-to-end workflows
- Performance tests for vector search and database queries
- Error handling and edge case testing
```

### Test Utilities Prompt
```
Create test utilities:
- Mock OpenAI responses for consistent testing
- Test database with sample data
- Vector store testing with known documents
- Conversation flow testing with multiple turns
- Tool execution verification
- Response quality assessment helpers
```

## 11. Advanced Features

### File Watching Prompt
```
Create scripts/watch_docs.py for development:
- Monitor data/docs/ for file changes using watchdog
- Automatic vector database updates on file modifications
- Debouncing to prevent rapid successive updates
- Background process management
- Integration with development workflow
- Proper error handling and logging
```

### Conversation Management Prompt
```
Create app/tools/conversation_tools.py:
- Async functions for conversation CRUD operations
- Conversation history retrieval with pagination
- Message filtering and search capabilities
- Conversation summarization
- Privacy and data retention management
- Performance optimization for large conversation histories
```

## 12. Production Considerations

### Deployment Prompt
```
Create production-ready configuration:
- Environment-specific settings (dev, staging, prod)
- Docker containerization with multi-stage builds
- Database migration scripts
- Health check endpoints for load balancers
- Logging configuration for production monitoring
- Security headers and CORS configuration
- Rate limiting and authentication middleware
- Performance monitoring and metrics collection
```

### Monitoring and Logging Prompt
```
Create app/utils/logging.py with:
- Structured logging with JSON format
- Different log levels for different components
- Request/response logging for API endpoints
- Performance metrics logging
- Error tracking and alerting
- Log rotation and retention policies
- Integration with monitoring systems
- Privacy-aware logging (no sensitive data)
```

## Usage Instructions for Copilot

1. **Start with Project Structure**: Use the project structure prompt to create the directory layout
2. **Dependencies First**: Generate requirements.txt and setup scripts
3. **Core Components**: Create config, database, and LLM modules
4. **Data Models**: Generate Pydantic models for API and state management
5. **Tools and Utilities**: Implement vector store and database tools
6. **Workflow Nodes**: Create individual LangGraph nodes
7. **Orchestration**: Build the main workflow and API endpoints
8. **Documentation**: Generate comprehensive documentation files
9. **Testing**: Create test suite with proper fixtures
10. **Scripts and Utilities**: Add development and deployment scripts

Each prompt is designed to be self-contained while maintaining consistency with the overall architecture. Use them sequentially for best results, and customize based on specific requirements. 