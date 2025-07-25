"""RAG extraction node for LangGraph workflow."""

from typing import Dict, Any
from app.models.state import MultiHopState
from app.tools.vector_store import get_vector_store
from app.utils.logging import logger


async def rag_extraction_node(state: MultiHopState) -> Dict[str, Any]:
    """
    LangGraph node that performs RAG extraction.
    
    This node:
    1. Takes the current user query
    2. Searches the vector database for relevant context
    3. Returns the retrieved context
    """
    try:
        logger.info(f"RAG node processing query for session: {state['session_id']}")
        
        user_query = state["user_query"]
        
        # Get the vector store instance
        vector_store = get_vector_store()
        
        # Search vector database for relevant context
        rag_result = vector_store.search(
            query=user_query,
            k=5,  # Retrieve top 5 most relevant documents
            min_score=0.1  # Minimum similarity score
        )
        
        # Return only the keys this node modifies
        result = {"retrieved_docs": {"rag_context": rag_result.context}}
        
        logger.info(f"RAG extraction completed. Found {len(rag_result.sources)} relevant sources")
        logger.debug(f"RAG confidence score: {rag_result.confidence_score}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in RAG extraction node: {str(e)}")
        # Return only the keys this node modifies, even in error case
        return {
            "error": f"RAG extraction failed: {str(e)}",
            "retrieved_docs": {"rag_context": "No relevant context found in the knowledge base."}
        }


def create_rag_node_tools() -> Dict[str, Any]:
    """Create tools and utilities for the RAG node."""
    return {
        "vector_store": get_vector_store(),
        "search_params": {
            "default_k": 5,
            "default_min_score": 0.1,
            "max_context_length": 4000
        }
    } 