# AI Chat Agent with RAG and Metrics

A FastAPI-based conversational AI system that combines Retrieval Augmented Generation (RAG) with database metrics extraction using LangGraph orchestration.

## Tech Stack

- **FastAPI**: REST API endpoints
- **LLM Providers**: OpenAI GPT models and Google Vertex AI (Gemini)
- **FAISS**: Vector database for embeddings
- **LangChain & LangGraph**: Agent orchestration and workflow management
- **PostgreSQL**: Metrics database
- **SQLAlchemy**: Database ORM

## Project Structure

```
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── api/                    # API endpoints
│   │   ├── __init__.py
│   │   └── chat.py            # Chat endpoint implementation
│   ├── agents/                 # LangGraph nodes
│   │   ├── __init__.py
│   │   ├── rag_agent.py       # RAG extraction node
│   │   └── metrics_agent.py   # Database metrics extraction node
│   ├── workflows/              # LangGraph workflows
│   │   ├── __init__.py
│   │   └── chat_workflow.py   # Main conversation workflow
│   ├── tools/                  # Database and utility tools
│   │   ├── __init__.py
│   │   ├── langchain_db_tools.py  # LangChain database tools for metrics
│   │   ├── conversation_tools.py  # Database tools for conversation management
│   │   └── vector_store.py    # FAISS vector store operations
│   ├── models/                 # Pydantic models and schemas
│   │   ├── __init__.py
│   │   ├── chat.py            # Chat request/response models
│   │   └── state.py           # LangGraph state models
│   ├── core/                   # Core configuration and utilities
│   │   ├── __init__.py
│   │   ├── config.py          # Application configuration
│   │   ├── database.py        # Database connection
│   │   └── llm.py            # OpenAI client setup
│   └── utils/                  # Utility functions
│       ├── __init__.py
│       └── logging.py         # Logging configuration
├── data/                       # Data storage
│   ├── faiss_index/           # FAISS index files
│   └── docs/                  # Productivity Insights documentation
│       ├── system_overview.md # System overview and features
│       ├── metrics_data_schema.md # Database schema documentation
│       ├── conversation_history_schema.md # Conversation table schema
│       ├── api_usage_guide.md  # API usage and examples
│       ├── troubleshooting_guide.md # Common issues and solutions
│       └── getting_started.md  # User onboarding guide
├── scripts/                    # Utility scripts
│   ├── setup_sample_data.py   # Sample data generation
│   ├── run_tests.py           # Test runner
│   ├── verify_setup.py        # Installation verification
│   ├── update_vector_db.py    # Update RAG vector database with documentation
│   └── watch_docs.py          # Watch documentation files for changes
├── tests/                      # Test files
│   ├── __init__.py
│   ├── test_api.py
│   ├── test_agents.py
│   └── test_workflows.py
├── requirements.txt
├── env.example
└── README.md
```

## Team Collaboration Structure

The project is organized to allow different team members to work on specific components:

1. **API Team**: Work on `app/api/` and `app/models/`
2. **Agents Team**: Implement individual nodes in `app/agents/`
3. **Workflow Team**: Orchestrate agents in `app/workflows/`
4. **Database Team**: Implement tools in `app/tools/`
5. **Infrastructure Team**: Configure `app/core/` and deployment

## Quick Setup Instructions

### Option 1: Automated Setup (Recommended)

**Linux/macOS:**
```bash
./setup.sh
```

**Windows:**
```batch
setup.bat
```

**Using Make (Linux/macOS):**
```bash
make setup
```

### Option 2: Manual Setup

1. **Create Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/macOS
   # OR
   venv\Scripts\activate.bat  # Windows
   ```

2. **Install Dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Environment Configuration**:
   ```bash
   cp env.example .env
   # Edit .env with your actual configuration values
   ```

4. **Database Setup**:
   - Create PostgreSQL database
   - Update database credentials in `.env`

5. **Setup Sample Data**:
   ```bash
   python scripts/setup_sample_data.py
   ```

6. **Run the application**:
   ```bash
   python start.py
   # OR
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Virtual Environment Management

**Activate environment:**
```bash
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate.bat  # Windows
```

**Deactivate environment:**
```bash
deactivate
```

**Clean and rebuild environment:**
```bash
make clean && make setup  # Using Make
# OR manually:
rm -rf venv
./setup.sh
```

## LLM Provider Configuration

The system supports multiple LLM providers with flexible deployment options that can be configured via environment variables.

### Supported Providers

1. **OpenAI** (default)
2. **Google Vertex AI** with multiple deployment types

### Configuration

Set the `LLM_PROVIDER` environment variable to switch between providers:

```bash
# Use OpenAI (default)
LLM_PROVIDER=openai

# Use Google Vertex AI
LLM_PROVIDER=vertexai
```

### OpenAI Configuration

```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4
```

### Google Vertex AI Configuration

**Cloud Deployment (Default):**
```bash
LLM_PROVIDER=vertexai
VERTEXAI_PROJECT_ID=your_gcp_project_id
VERTEXAI_LOCATION=us-central1
VERTEXAI_MODEL=gemini-2.0-flash-lite-001
VERTEXAI_DEPLOYMENT_TYPE=cloud
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

**Corporate/On-Premise Deployment:**
```bash
LLM_PROVIDER=vertexai
VERTEXAI_PROJECT_ID=your_project_id
VERTEXAI_LOCATION=your_location
VERTEXAI_MODEL=gemini-2.0-flash-lite-001
VERTEXAI_DEPLOYMENT_TYPE=corporate  # or "on_premise"
VERTEXAI_ENDPOINT_URL=https://your-corporate-gemini-endpoint.com/v1
VERTEXAI_API_KEY=your_corporate_api_key
VERTEXAI_AUTH_METHOD=api_key
```

### Deployment Types

- **`cloud`** - Google Cloud Vertex AI (default)
- **`corporate`** - Corporate hosted Gemini models
- **`on_premise`** - On-premise Vertex AI deployment

### LLM Request Metadata

For in-house LLM services that require custom metadata headers (like authentication headers), you can configure metadata to be sent with every LLM request:

```bash
# Example: Pass user identification and API version headers
LLM_METADATA='{"x-r2d2-user": "user123", "x-api-version": "v1"}'

# Example: Multiple metadata fields
LLM_METADATA='{"x-r2d2-user": "user123", "x-api-version": "v1", "x-tenant-id": "org456"}'
```

**Key Features:**
- **JSON Format**: Metadata must be valid JSON object format
- **Global Configuration**: Set once in environment, applies to all LLM calls
- **Complete Coverage**: Works with both `generate_response` and `generate_embeddings` methods
- **Provider Support**: Works with both OpenAI-compatible and Vertex AI endpoints
- **Call-level Override**: Can be overridden per-call in code if needed
- **Validation**: Invalid JSON will prevent application startup with clear error message

**Usage Examples:**

```bash
# For in-house OpenAI-compatible services
LLM_PROVIDER=openai
OPENAI_BASE_URL=https://your-internal-llm.company.com/v1
LLM_METADATA='{"x-r2d2-user": "user123", "authorization": "Bearer token123"}'

# For corporate Vertex AI deployments
LLM_PROVIDER=vertexai
VERTEXAI_DEPLOYMENT_TYPE=corporate
VERTEXAI_ENDPOINT_URL=https://your-vertex-endpoint.company.com
LLM_METADATA='{"x-r2d2-user": "user123", "x-org-id": "org456"}'
```

📋 **For detailed setup instructions, see [VERTEX_AI_SETUP.md](VERTEX_AI_SETUP.md)**

### LLM Management API Endpoints

- `GET /api/llm/provider` - Get current provider information
- `POST /api/llm/test` - Test LLM connectivity
- `GET /api/llm/providers` - List available providers
- `GET /api/llm/config` - Get current configuration
- `GET /api/llm/health` - LLM service health check

### Testing LLM Connectivity

```bash
# Test current LLM provider
curl -X POST "http://localhost:8000/api/llm/test" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, test connectivity"}'

# Get provider information
curl "http://localhost:8000/api/llm/provider"
```

## API Usage

### Chat Endpoint

```bash
POST /api/chat
{
    "message": "What are the latest metrics for user engagement?",
    "conversation_id": "conv_123"
}
```

Response:
```json
{
    "response": "Based on the latest data...",
    "conversation_id": "conv_123"
}
```

## Development Guidelines

- Each agent/node should be independently testable
- Use dependency injection for database and external service connections
- Follow the established state management pattern for conversation history
- Add comprehensive logging for debugging and monitoring

## Development Commands

### Using Make (Recommended)
```bash
make help          # Show available commands
make setup         # Initial setup
make run           # Start the application
make dev           # Start in development mode with auto-reload
make test          # Run tests
make data          # Setup sample data
make update-docs   # Update RAG vector database with documentation changes
make rebuild-docs  # Rebuild RAG vector database from scratch
make watch-docs    # Watch documentation files for changes and auto-update
make docs-stats    # Show RAG vector database statistics
make clean         # Clean environment and cache
make check         # Check environment status
```

### Manual Commands
```bash
# Run tests
python scripts/run_tests.py
# OR
pytest tests/ -v

# Start application
python start.py

# Start with auto-reload for development
uvicorn app.main:app --reload

# Setup sample data
python scripts/setup_sample_data.py
```

## Documentation Management

The system includes comprehensive documentation about the "Productivity Insights" platform that powers the RAG (Retrieval-Augmented Generation) functionality.

### Documentation Files

The `data/docs/` directory contains markdown files that are automatically indexed into the vector database:

- **system_overview.md**: Overview of the Productivity Insights platform
- **metrics_data_schema.md**: Detailed schema documentation for the metrics_data table
- **conversation_history_schema.md**: Schema documentation for conversation storage
- **api_usage_guide.md**: API usage examples and best practices
- **troubleshooting_guide.md**: Common issues and solutions
- **getting_started.md**: User onboarding and quick start guide

### Managing Documentation

```bash
# Update vector database with any changed documentation files
make update-docs

# Rebuild the entire vector database from scratch
make rebuild-docs

# Watch for file changes and auto-update (useful during development)
make watch-docs

# Show statistics about the current vector database
make docs-stats
```

### Manual Documentation Management

```bash
# Update documentation
python scripts/update_vector_db.py

# Force rebuild
python scripts/update_vector_db.py --rebuild

# Watch for changes
python scripts/watch_docs.py

# Show stats
python scripts/update_vector_db.py --stats
```

### Adding New Documentation

1. Create new markdown files in `data/docs/`
2. Run `make update-docs` to index them into the vector database
3. The AI assistant will automatically have access to the new information

The documentation is automatically chunked by sections (headers) for optimal retrieval performance.

## Testing

```bash
# Using make
make test

# Manual
python scripts/run_tests.py
pytest tests/
``` 