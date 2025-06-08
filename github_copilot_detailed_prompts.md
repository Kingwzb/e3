# Detailed Implementation Prompts for Complex Components

This document provides specific, detailed prompts for implementing the most complex parts of the AI chat agent system.

## 1. LangGraph Workflow Implementation

### Complete Chat Workflow Prompt
```python
# Create app/workflows/chat_workflow.py
# Implement a LangGraph StateGraph workflow with these specifications:

from langgraph.graph import StateGraph, END
from typing import Dict, Any
from app.models.state import WorkflowState
from app.workflows.nodes.rag_node import rag_extraction_node
from app.workflows.nodes.metrics_node import metrics_extraction_node
from app.workflows.nodes.response_node import response_generation_node
from app.workflows.nodes.conversation_node import conversation_history_node

# Create workflow with these nodes and edges:
# 1. START -> conversation_history_node (load conversation context)
# 2. conversation_history_node -> rag_extraction_node (parallel with metrics)
# 3. conversation_history_node -> metrics_extraction_node (parallel with RAG)
# 4. Both rag_extraction_node and metrics_extraction_node -> response_generation_node
# 5. response_generation_node -> END

# Include conditional logic:
# - Skip metrics extraction if message doesn't require data analysis
# - Skip RAG if message is purely conversational
# - Handle error states and recovery

# Add workflow configuration:
# - Parallel execution for RAG and metrics when both needed
# - Timeout handling for long-running operations
# - State validation between nodes
# - Comprehensive logging and monitoring

def create_chat_workflow() -> StateGraph:
    # Implementation here with proper node connections and conditional edges
    pass

async def run_chat_workflow(initial_state: WorkflowState) -> WorkflowState:
    # Execute workflow with error handling and monitoring
    pass
```

### Metrics Node with LLM Tool Selection
```python
# Create app/workflows/nodes/metrics_node.py
# Implement intelligent tool selection using LLM analysis

import json
from typing import Dict, Any, List
from langchain.tools import BaseTool
from app.core.llm import llm_client
from app.tools.langchain_db_tools import create_langchain_db_tools, create_tool_config_for_environment
from app.core.database import get_db
from app.models.state import WorkflowState

async def metrics_extraction_node(state: WorkflowState) -> WorkflowState:
    """
    Analyze user message to determine if metrics data is needed.
    If needed, use LLM to select appropriate tools and parameters.
    Execute tools and format results.
    
    Tool selection logic:
    - Analyze message for metrics keywords (engagement, performance, revenue, satisfaction)
    - Determine specific metrics needed (daily_active_users, response_time, etc.)
    - Choose between get_metrics_by_category vs get_top_metrics
    - Extract parameters (date ranges, limits, categories)
    - Execute tools in optimal order
    - Aggregate and format results
    
    Error handling:
    - Tool execution failures
    - Invalid parameters
    - Database connection issues
    - LLM analysis errors
    """
    
    # 1. Analyze message intent using LLM
    # 2. Determine if metrics are needed
    # 3. Select appropriate tools and parameters
    # 4. Execute tools with error handling
    # 5. Format results for response generation
    # 6. Update state with metrics_data
    
    pass

def analyze_metrics_intent(message: str) -> Dict[str, Any]:
    """Use LLM to analyze message and determine metrics requirements"""
    pass

async def execute_metrics_tools(tools: List[BaseTool], tool_calls: List[Dict]) -> Dict[str, Any]:
    """Execute selected tools with proper error handling"""
    pass
```

## 2. Advanced Vector Store Implementation

### FAISS Vector Store with Metadata
```python
# Create app/tools/vector_store.py
# Implement advanced FAISS vector store with metadata support

import faiss
import numpy as np
import pickle
import json
from typing import List, Dict, Any, Optional, Tuple
from sentence_transformers import SentenceTransformer
from pathlib import Path

class VectorStore:
    """
    Advanced FAISS vector store with:
    - Metadata support for document tracking
    - Incremental updates with change detection
    - Batch processing for large document sets
    - Multiple search strategies (similarity, hybrid)
    - Index persistence and versioning
    - Performance optimization
    """
    
    def __init__(self, 
                 model_name: str = "all-MiniLM-L6-v2",
                 index_path: str = "data/faiss_index",
                 dimension: int = 384):
        # Initialize sentence transformer
        # Create FAISS index (IndexFlatIP for cosine similarity)
        # Setup metadata storage
        # Configure persistence paths
        pass
    
    async def add_documents(self, 
                          documents: List[Dict[str, Any]], 
                          batch_size: int = 100) -> None:
        """
        Add documents with metadata support.
        Documents format: [{"content": str, "metadata": dict}, ...]
        
        Features:
        - Batch processing for memory efficiency
        - Duplicate detection and handling
        - Metadata indexing for filtering
        - Progress tracking for large datasets
        """
        pass
    
    async def search(self, 
                    query: str, 
                    k: int = 5, 
                    score_threshold: float = 0.0,
                    metadata_filter: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Semantic search with metadata filtering.
        
        Returns: [{"content": str, "metadata": dict, "score": float}, ...]
        
        Features:
        - Configurable similarity threshold
        - Metadata-based filtering
        - Score normalization
        - Result ranking and deduplication
        """
        pass
    
    def save_index(self) -> None:
        """Persist index and metadata to disk with versioning"""
        pass
    
    def load_index(self) -> bool:
        """Load index and metadata from disk with validation"""
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Return index statistics and health metrics"""
        pass
    
    async def update_documents(self, 
                             document_hashes: Dict[str, str],
                             changed_documents: List[Dict[str, Any]]) -> None:
        """Incremental update with change detection"""
        pass
```

## 3. Comprehensive Database Tools

### LangChain Database Tools with Security
```python
# Create app/tools/langchain_db_tools.py
# Implement secure, configurable database tools

from typing import Dict, Any, List, Optional, Type
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from pydantic import BaseModel, Field, validator
from langchain.tools import BaseTool
import re
import time

class GetMetricsByCategoryTool(BaseTool):
    """
    Retrieve metrics by category with advanced filtering.
    
    Features:
    - Date range filtering with validation
    - Category validation against allowed list
    - Performance optimization with query limits
    - Result aggregation and statistics
    - Comprehensive error handling
    """
    
    name: str = "get_metrics_by_category"
    description: str = "Get metrics data by category with date filtering and aggregation"
    
    class InputSchema(BaseModel):
        category: str = Field(description="Metric category (engagement, performance, revenue, satisfaction)")
        days_back: int = Field(default=7, ge=1, le=90, description="Days to look back")
        aggregation: Optional[str] = Field(default=None, description="Aggregation method (avg, sum, max, min)")
        department: Optional[str] = Field(default=None, description="Filter by department")
        
        @validator('category')
        def validate_category(cls, v):
            allowed = ['engagement', 'performance', 'revenue', 'satisfaction']
            if v not in allowed:
                raise ValueError(f"Category must be one of: {allowed}")
            return v
    
    args_schema: Type[BaseModel] = InputSchema
    
    async def _arun(self, **kwargs) -> str:
        """
        Execute tool with:
        - Input validation and sanitization
        - SQL injection prevention
        - Performance monitoring
        - Result formatting and aggregation
        - Comprehensive error handling
        """
        pass

class ExecuteCustomQueryTool(BaseTool):
    """
    Safe SQL query execution with security measures.
    
    Security features:
    - Whitelist of allowed SQL keywords
    - Query complexity analysis
    - Result size limits
    - Execution timeout
    - Audit logging
    """
    
    name: str = "execute_custom_query"
    description: str = "Execute safe SELECT queries with security validation"
    
    def validate_query_security(self, query: str) -> Tuple[bool, str]:
        """
        Comprehensive SQL security validation:
        - Only SELECT statements allowed
        - No dangerous keywords (DROP, DELETE, etc.)
        - No nested queries beyond certain depth
        - No system table access
        - Query complexity limits
        """
        pass
    
    async def _arun(self, sql_query: str) -> str:
        """Execute query with security validation and monitoring"""
        pass

def create_tool_config_for_environment(environment: str) -> 'DatabaseToolsConfig':
    """
    Create environment-specific configurations:
    
    Development:
    - Custom queries enabled
    - Higher limits for testing
    - Detailed logging
    
    Production:
    - Custom queries disabled
    - Conservative limits
    - Security-focused settings
    
    Testing:
    - Limited data access
    - Fast execution timeouts
    - Minimal logging
    """
    pass
```

## 4. Response Generation with Context Management

### Advanced Response Node
```python
# Create app/workflows/nodes/response_node.py
# Implement intelligent response generation with context management

from typing import Dict, Any, List
import json
from app.models.state import WorkflowState
from app.core.llm import llm_client
from app.utils.logging import logger

async def response_generation_node(state: WorkflowState) -> WorkflowState:
    """
    Generate contextual responses combining:
    - Conversation history with relevance scoring
    - RAG context with source attribution
    - Metrics data with human-readable formatting
    - Error handling and fallback responses
    
    Features:
    - Token management and response length control
    - Context prioritization based on relevance
    - Multi-turn conversation continuity
    - Response quality assessment
    - Streaming support for long responses
    """
    
    # 1. Analyze available context sources
    # 2. Prioritize context based on relevance and recency
    # 3. Format metrics data for human consumption
    # 4. Construct optimized prompt for LLM
    # 5. Generate response with error handling
    # 6. Validate and post-process response
    # 7. Update conversation state
    
    pass

def format_metrics_for_llm(metrics_data: Dict[str, Any]) -> str:
    """
    Format metrics data for LLM consumption:
    - Convert raw data to human-readable format
    - Add context and explanations
    - Highlight key insights and trends
    - Structure for easy parsing
    """
    pass

def prioritize_context_sources(
    conversation_history: List[Dict],
    rag_context: str,
    metrics_data: Dict[str, Any],
    current_message: str
) -> Dict[str, Any]:
    """
    Intelligently prioritize context sources:
    - Analyze relevance to current message
    - Consider conversation flow and continuity
    - Balance between different data sources
    - Optimize for token limits
    """
    pass

def construct_llm_prompt(
    system_message: str,
    prioritized_context: Dict[str, Any],
    current_message: str
) -> List[Dict[str, str]]:
    """
    Construct optimized prompt for LLM:
    - System message with role definition
    - Context integration with clear boundaries
    - Conversation history with relevance weighting
    - Current message with intent preservation
    """
    pass
```

## 5. Conversation Management System

### Advanced Conversation Tools
```python
# Create app/tools/conversation_tools.py
# Implement comprehensive conversation management

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from app.core.database import ConversationHistory
from app.models.chat import Message, ConversationSummary

class ConversationManager:
    """
    Advanced conversation management with:
    - Efficient history retrieval with pagination
    - Conversation summarization and insights
    - Privacy and data retention compliance
    - Performance optimization for large histories
    - Search and filtering capabilities
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
    
    async def get_conversation_history(
        self,
        conversation_id: str,
        limit: int = 50,
        before_timestamp: Optional[datetime] = None,
        message_types: Optional[List[str]] = None
    ) -> List[Message]:
        """
        Retrieve conversation history with:
        - Pagination support for large conversations
        - Filtering by message type and timestamp
        - Relevance scoring for context prioritization
        - Memory-efficient loading
        """
        pass
    
    async def summarize_conversation(
        self,
        conversation_id: str,
        summary_length: str = "medium"
    ) -> ConversationSummary:
        """
        Generate conversation summary with:
        - Key topics and themes extraction
        - Participant analysis and engagement metrics
        - Timeline and activity patterns
        - Action items and decisions tracking
        """
        pass
    
    async def search_conversations(
        self,
        query: str,
        conversation_ids: Optional[List[str]] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search across conversations with:
        - Full-text search capabilities
        - Semantic similarity matching
        - Metadata filtering and sorting
        - Result ranking and relevance scoring
        """
        pass
    
    async def cleanup_old_conversations(
        self,
        retention_days: int = 90,
        preserve_important: bool = True
    ) -> Dict[str, int]:
        """
        Data retention management with:
        - Configurable retention policies
        - Important conversation preservation
        - Audit logging for compliance
        - Batch processing for performance
        """
        pass
```

## 6. Documentation Processing System

### Advanced Documentation Indexing
```python
# Create scripts/update_vector_db.py
# Implement intelligent documentation processing

import hashlib
import json
import re
from typing import Dict, List, Any, Tuple
from pathlib import Path
import argparse
from app.tools.vector_store import VectorStore

class DocumentProcessor:
    """
    Advanced document processing with:
    - Section-based chunking by headers
    - Hash-based change detection
    - Metadata extraction and enrichment
    - Cross-reference resolution
    - Content quality validation
    """
    
    def __init__(self, docs_dir: str, vector_store: VectorStore):
        self.docs_dir = Path(docs_dir)
        self.vector_store = vector_store
        self.metadata_file = self.docs_dir / ".document_metadata.json"
    
    def extract_sections_from_markdown(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract sections from markdown with:
        - Header-based chunking (H1, H2, H3)
        - Code block preservation
        - Table and list handling
        - Cross-reference extraction
        - Metadata enrichment (file path, section hierarchy)
        """
        pass
    
    def detect_changes(self, file_path: str, content: str) -> bool:
        """
        Efficient change detection using:
        - Content hashing (SHA-256)
        - Metadata comparison
        - Timestamp validation
        - Incremental update optimization
        """
        pass
    
    def enrich_metadata(self, section: Dict[str, Any], file_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich section metadata with:
        - Document hierarchy and relationships
        - Content type classification
        - Keyword extraction
        - Relevance scoring
        - Update timestamps
        """
        pass
    
    async def process_all_documents(self, force_rebuild: bool = False) -> Dict[str, Any]:
        """
        Process all documentation with:
        - Incremental updates for efficiency
        - Parallel processing for large document sets
        - Progress tracking and reporting
        - Error handling and recovery
        - Statistics and metrics collection
        """
        pass
    
    def validate_content_quality(self, content: str) -> Tuple[bool, List[str]]:
        """
        Validate document quality:
        - Minimum content length
        - Proper markdown formatting
        - Link validation
        - Code block syntax checking
        - Completeness assessment
        """
        pass

def main():
    """
    Command-line interface with options:
    --rebuild: Force complete rebuild
    --stats: Show index statistics
    --verbose: Detailed logging
    --docs-dir: Custom documentation directory
    --validate: Validate content quality
    --watch: Watch for changes (development mode)
    """
    pass
```

## Usage Instructions

1. **Use these prompts sequentially** - Each builds on previous components
2. **Customize for your needs** - Adjust parameters and configurations
3. **Test incrementally** - Implement and test each component separately
4. **Add error handling** - Each prompt includes comprehensive error handling patterns
5. **Monitor performance** - Built-in logging and metrics collection
6. **Security first** - Security considerations built into each component

These detailed prompts provide the specific implementation patterns and architectural decisions used in the original project, ensuring consistency and completeness when recreating the system. 