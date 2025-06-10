"""FAISS vector store operations for RAG functionality."""

import os
import pickle
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import faiss
import asyncio

from app.core.config import settings
from app.core.llm import LLMClientFactory
from app.models.state import RAGResult
from app.utils.logging import logger


class VectorStore:
    """FAISS vector store for document retrieval using Vertex AI embeddings."""
    
    def __init__(self):
        self.index_path = settings.faiss_index_path
        self.embeddings_model_name = settings.embeddings_model
        self.llm_client = None
        self.index = None
        self.documents = []
        self.metadata = []
        self.dimension = 768  # Default for Vertex AI text-embedding models
        
        # Ensure directory exists
        os.makedirs(self.index_path, exist_ok=True)
        
        # Initialize embeddings model
        self._initialize_embeddings_model()
        
        # Load existing index if available
        self._load_index()
    
    def _initialize_embeddings_model(self):
        """Initialize the Vertex AI embedding model."""
        try:
            # Create LLM client for embeddings
            self.llm_client = LLMClientFactory.create_from_settings()
            
            # Set dimension based on model
            if "text-embedding-005" in self.embeddings_model_name:
                self.dimension = 768
            elif "text-embedding-004" in self.embeddings_model_name:
                self.dimension = 768
            elif "gemini-embedding-001" in self.embeddings_model_name:
                self.dimension = 768
            elif "text-multilingual-embedding-002" in self.embeddings_model_name:
                self.dimension = 768
            else:
                # Default dimension for Vertex AI models
                self.dimension = 768
                
            logger.info(f"Initialized Vertex AI embeddings model: {self.embeddings_model_name} with dimension {self.dimension}")
        except Exception as e:
            logger.error(f"Failed to initialize embeddings model: {str(e)}")
            raise
    
    async def _generate_embeddings(self, texts: List[str], metadata: Optional[Dict[str, Any]] = None) -> np.ndarray:
        """Generate embeddings using Vertex AI."""
        try:
            # Use the LLM client to generate embeddings with metadata
            embeddings = await self.llm_client.generate_embeddings(texts, metadata=metadata)
            return np.array(embeddings, dtype=np.float32)
        except Exception as e:
            # Enhanced exception logging with traceback and input parameters
            logger.error(f"Failed to generate embeddings at line {e.__traceback__.tb_lineno if e.__traceback__ else 'unknown'}: {str(e)}")
            logger.error(f"Input parameters - texts: {len(texts)}, metadata: {list(metadata.keys()) if metadata else 'None'}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise
    
    def _generate_embeddings_sync(self, texts: List[str], metadata: Optional[Dict[str, Any]] = None) -> np.ndarray:
        """Synchronous wrapper for embedding generation."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, we need to handle this differently
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self._generate_embeddings(texts, metadata))
                    return future.result()
            else:
                return asyncio.run(self._generate_embeddings(texts, metadata))
        except Exception as e:
            # Enhanced exception logging with traceback and input parameters
            logger.error(f"Failed to generate embeddings synchronously at line {e.__traceback__.tb_lineno if e.__traceback__ else 'unknown'}: {str(e)}")
            logger.error(f"Input parameters - texts: {len(texts)}, metadata: {list(metadata.keys()) if metadata else 'None'}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise

    def _load_index(self):
        """Load existing FAISS index and metadata."""
        index_file = os.path.join(self.index_path, "index.faiss")
        docs_file = os.path.join(self.index_path, "documents.pkl")
        metadata_file = os.path.join(self.index_path, "metadata.pkl")
        
        try:
            if os.path.exists(index_file) and os.path.exists(docs_file):
                # Load FAISS index
                self.index = faiss.read_index(index_file)
                
                # Load documents
                with open(docs_file, 'rb') as f:
                    self.documents = pickle.load(f)
                
                # Load metadata
                if os.path.exists(metadata_file):
                    with open(metadata_file, 'rb') as f:
                        self.metadata = pickle.load(f)
                else:
                    self.metadata = [{"source": f"doc_{i}"} for i in range(len(self.documents))]
                
                logger.info(f"Loaded FAISS index with {len(self.documents)} documents")
            else:
                # Create new empty index
                self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for similarity
                self.documents = []
                self.metadata = []
                logger.info("Created new empty FAISS index")
                
        except Exception as e:
            logger.error(f"Failed to load FAISS index: {str(e)}")
            # Create new empty index as fallback
            self.index = faiss.IndexFlatIP(self.dimension)
            self.documents = []
            self.metadata = []
    
    def _save_index(self):
        """Save FAISS index and metadata to disk."""
        try:
            index_file = os.path.join(self.index_path, "index.faiss")
            docs_file = os.path.join(self.index_path, "documents.pkl")
            metadata_file = os.path.join(self.index_path, "metadata.pkl")
            
            # Save FAISS index
            faiss.write_index(self.index, index_file)
            
            # Save documents
            with open(docs_file, 'wb') as f:
                pickle.dump(self.documents, f)
            
            # Save metadata
            with open(metadata_file, 'wb') as f:
                pickle.dump(self.metadata, f)
            
            logger.info("Saved FAISS index to disk")
            
        except Exception as e:
            logger.error(f"Failed to save FAISS index: {str(e)}")
            raise
    
    def add_documents(
        self, 
        documents: List[Dict[str, Any]], 
        metadata: Optional[List[Dict[str, Any]]] = None
    ):
        """Add documents to the vector store.
        
        Args:
            documents: List of documents, each can be a string or dict with 'content' and 'metadata'
            metadata: Optional metadata list (deprecated, use documents with metadata)
        """
        try:
            if not documents:
                return
            
            # Handle both old format (list of strings) and new format (list of dicts)
            doc_texts = []
            doc_metadata = []
            
            for i, doc in enumerate(documents):
                if isinstance(doc, str):
                    # Old format: string document
                    doc_texts.append(doc)
                    if metadata and i < len(metadata):
                        doc_metadata.append(metadata[i])
                    else:
                        doc_metadata.append({"source": f"doc_{len(self.documents) + i}"})
                elif isinstance(doc, dict) and 'content' in doc:
                    # New format: dict with content and metadata
                    doc_texts.append(doc['content'])
                    doc_metadata.append(doc.get('metadata', {"source": f"doc_{len(self.documents) + i}"}))
                else:
                    logger.warning(f"Invalid document format at index {i}, skipping")
                    continue
            
            if not doc_texts:
                logger.warning("No valid documents to add")
                return
            
            # Generate embeddings using Vertex AI
            logger.info(f"Generating embeddings for {len(doc_texts)} documents using Vertex AI")
            embeddings = self._generate_embeddings_sync(doc_texts)
            
            # Normalize embeddings for cosine similarity
            embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
            
            # Add to FAISS index
            self.index.add(embeddings.astype('float32'))
            
            # Store documents and metadata
            self.documents.extend(doc_texts)
            self.metadata.extend(doc_metadata)
            
            # Save to disk
            self._save_index()
            
            logger.info(f"Added {len(doc_texts)} documents to vector store")
            
        except Exception as e:
            # Enhanced exception logging with traceback and input parameters
            logger.error(f"Failed to add documents at line {e.__traceback__.tb_lineno if e.__traceback__ else 'unknown'}: {str(e)}")
            logger.error(f"Input parameters - documents: {len(documents)} items, metadata: {len(metadata) if metadata else 'None'}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise
    
    def search(
        self, 
        query: str, 
        k: int = 5, 
        min_score: float = 0.1
    ) -> RAGResult:
        """Search for similar documents."""
        try:
            if self.index.ntotal == 0:
                logger.warning("Vector store is empty")
                return RAGResult(
                    context="No documents available in the knowledge base.",
                    sources=[],
                    confidence_score=0.0
                )
            
            # Generate query embedding using Vertex AI
            query_embedding = self._generate_embeddings_sync([query])
            query_embedding = query_embedding / np.linalg.norm(query_embedding, axis=1, keepdims=True)
            
            # Search in FAISS index
            scores, indices = self.index.search(query_embedding.astype('float32'), k)
            
            # Filter by minimum score
            valid_results = [(score, idx) for score, idx in zip(scores[0], indices[0]) 
                           if score >= min_score and idx < len(self.documents)]
            
            if not valid_results:
                return RAGResult(
                    context="No relevant information found for your query.",
                    sources=[],
                    confidence_score=0.0
                )
            
            # Build context and sources
            contexts = []
            sources = []
            total_score = 0.0
            
            for score, idx in valid_results:
                contexts.append(self.documents[idx])
                sources.append({
                    "content": self.documents[idx][:200] + "..." if len(self.documents[idx]) > 200 else self.documents[idx],
                    "metadata": self.metadata[idx] if idx < len(self.metadata) else {"source": f"doc_{idx}"},
                    "score": float(score)
                })
                total_score += score
            
            # Combine contexts
            combined_context = "\n\n".join(contexts)
            avg_confidence = total_score / len(valid_results) if valid_results else 0.0
            
            return RAGResult(
                context=combined_context,
                sources=sources,
                confidence_score=avg_confidence
            )
            
        except Exception as e:
            # Enhanced exception logging with traceback and input parameters
            logger.error(f"Search failed at line {e.__traceback__.tb_lineno if e.__traceback__ else 'unknown'}: {str(e)}")
            logger.error(f"Input parameters - query: '{query}', k: {k}, min_score: {min_score}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return RAGResult(
                context="An error occurred during search.",
                sources=[],
                confidence_score=0.0
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        return {
            "total_documents": len(self.documents),
            "index_size": self.index.ntotal if self.index else 0,
            "embedding_dimension": self.dimension,
            "model_name": self.embeddings_model_name
        }
    
    def clear(self):
        """Clear all documents and reset the index."""
        try:
            self.index = faiss.IndexFlatIP(self.dimension)
            self.documents = []
            self.metadata = []
            self._save_index()
            logger.info("Cleared vector store")
        except Exception as e:
            # Enhanced exception logging with traceback and input parameters
            logger.error(f"Failed to clear vector store at line {e.__traceback__.tb_lineno if e.__traceback__ else 'unknown'}: {str(e)}")
            logger.error(f"Input parameters - dimension: {self.dimension}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise
    
    def clear_documents(self):
        """Clear all documents but keep the index structure."""
        try:
            self.clear()  # Same as clear for now
        except Exception as e:
            # Enhanced exception logging with traceback and input parameters
            logger.error(f"Failed to clear documents at line {e.__traceback__.tb_lineno if e.__traceback__ else 'unknown'}: {str(e)}")
            logger.error(f"Input parameters - none")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise


# Global vector store instance for backward compatibility
# Initialize immediately to ensure it's available
vector_store = None

def get_vector_store():
    """Get or create the global vector store instance."""
    global vector_store
    if vector_store is None:
        vector_store = VectorStore()
    return vector_store


def initialize_sample_documents():
    """Initialize the vector store with actual documentation for testing."""
    import os
    global vector_store
    
    # Initialize the global vector store
    vector_store = get_vector_store()
    
    if vector_store.get_stats()["total_documents"] > 0:
        logger.info("Vector store already has documents, skipping initialization")
        return vector_store
    
    # Load actual documentation files
    docs_dir = "data/docs"
    sample_documents = []
    
    try:
        if os.path.exists(docs_dir):
            # Read each documentation file
            doc_files = [
                ("system_overview.md", "System overview and platform description"),
                ("metrics_data_schema.md", "Database schema and metric definitions"),
                ("api_usage_guide.md", "API usage and integration guide"),
                ("getting_started.md", "Getting started guide and setup instructions"),
                ("conversation_history_schema.md", "Conversation data structure and schema"),
                ("troubleshooting_guide.md", "Troubleshooting guide and common issues")
            ]
            
            for filename, description in doc_files:
                filepath = os.path.join(docs_dir, filename)
                if os.path.exists(filepath):
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            sample_documents.append({
                                "content": content,
                                "metadata": {
                                    "source": filename,
                                    "type": "documentation",
                                    "description": description
                                }
                            })
                    except Exception as e:
                        logger.warning(f"Failed to read {filename}: {str(e)}")
        
        # If no docs found, use fallback sample data
        if not sample_documents:
            logger.warning("No documentation files found, using fallback sample data")
            sample_documents = [
                {
                    "content": "Engagement metrics include daily active users (DAU), session duration, and feature usage rates. DAU measures unique users active in a day. Session duration tracks average time spent per session. Feature usage rate shows percentage of users using specific features.",
                    "metadata": {"source": "engagement_metrics", "topic": "metrics", "category": "engagement"}
                },
                {
                    "content": "Performance metrics track system and employee performance including response time, uptime percentage, error rate, task completion rate, and throughput. These metrics help identify bottlenecks and optimization opportunities.",
                    "metadata": {"source": "performance_metrics", "topic": "metrics", "category": "performance"}
                },
                {
                    "content": "Revenue metrics analyze financial performance including monthly revenue, conversion rate, customer lifetime value, revenue per employee, and churn rate. These metrics help measure business impact.",
                    "metadata": {"source": "revenue_metrics", "topic": "metrics", "category": "revenue"}
                },
                {
                    "content": "Satisfaction metrics monitor customer and employee satisfaction through NPS score, support ratings, employee satisfaction scores, customer satisfaction scores, and retention rates.",
                    "metadata": {"source": "satisfaction_metrics", "topic": "metrics", "category": "satisfaction"}
                },
                {
                    "content": "The metrics data table stores quantitative metrics with columns: id, metric_name, metric_value, timestamp, category, and meta_data. Categories include engagement, performance, revenue, and satisfaction.",
                    "metadata": {"source": "metrics_schema", "topic": "database", "category": "schema"}
                }
            ]
        
        vector_store.add_documents(sample_documents)
        logger.info(f"Initialized vector store with {len(sample_documents)} documents")
        
    except Exception as e:
        logger.error(f"Failed to initialize sample documents: {str(e)}")
    
    return vector_store 