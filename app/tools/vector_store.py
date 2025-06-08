"""FAISS vector store operations for RAG functionality."""

import os
import pickle
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import faiss
from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.models.state import RAGResult
from app.utils.logging import logger


class VectorStore:
    """FAISS vector store for document retrieval."""
    
    def __init__(self):
        self.index_path = settings.faiss_index_path
        self.embeddings_model_name = settings.embeddings_model
        self.embeddings_model = None
        self.index = None
        self.documents = []
        self.metadata = []
        self.dimension = 384  # Default for all-MiniLM-L6-v2
        
        # Ensure directory exists
        os.makedirs(self.index_path, exist_ok=True)
        
        # Initialize embeddings model
        self._initialize_embeddings_model()
        
        # Load existing index if available
        self._load_index()
    
    def _initialize_embeddings_model(self):
        """Initialize the sentence transformer model."""
        try:
            self.embeddings_model = SentenceTransformer(self.embeddings_model_name)
            self.dimension = self.embeddings_model.get_sentence_embedding_dimension()
            logger.info(f"Initialized embeddings model: {self.embeddings_model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize embeddings model: {str(e)}")
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
            
            # Generate embeddings
            logger.info(f"Generating embeddings for {len(doc_texts)} documents")
            embeddings = self.embeddings_model.encode(doc_texts, show_progress_bar=True)
            
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
            logger.error(f"Failed to add documents: {str(e)}")
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
            
            # Generate query embedding
            query_embedding = self.embeddings_model.encode([query])
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
            for score, idx in valid_results:
                contexts.append(self.documents[idx])
                source_info = self.metadata[idx] if idx < len(self.metadata) else {"source": f"doc_{idx}"}
                sources.append(f"{source_info.get('source', f'doc_{idx}')} (score: {score:.3f})")
            
            # Combine contexts
            combined_context = "\n\n---\n\n".join(contexts)
            
            # Calculate average confidence score
            avg_confidence = sum(score for score, _ in valid_results) / len(valid_results)
            
            return RAGResult(
                context=combined_context,
                sources=sources,
                confidence_score=float(avg_confidence)
            )
            
        except Exception as e:
            logger.error(f"Failed to search vector store: {str(e)}")
            return RAGResult(
                context="Error occurred while searching the knowledge base.",
                sources=[],
                confidence_score=0.0
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics."""
        return {
            "total_documents": len(self.documents),
            "index_size": self.index.ntotal if self.index else 0,
            "dimension": self.dimension,
            "model": self.embeddings_model_name
        }
    
    def clear(self):
        """Clear all documents from the vector store."""
        try:
            self.index = faiss.IndexFlatIP(self.dimension)
            self.documents = []
            self.metadata = []
            self._save_index()
            logger.info("Cleared vector store")
        except Exception as e:
            logger.error(f"Failed to clear vector store: {str(e)}")
            raise
    
    def clear_documents(self):
        """Alias for clear() method for compatibility."""
        self.clear()


# Global vector store instance
vector_store = VectorStore()


def initialize_sample_documents():
    """Initialize vector store with sample documents for demonstration."""
    sample_docs = [
        "User engagement metrics show a 15% increase in daily active users over the past month. This growth is primarily driven by new feature adoption and improved user experience.",
        "Revenue metrics indicate strong performance with a 22% quarter-over-quarter growth. Key contributors include subscription renewals and new customer acquisitions.",
        "System performance metrics show 99.9% uptime with average response times under 200ms. Infrastructure optimizations have improved overall system reliability.",
        "Customer satisfaction scores have improved to 4.8/5.0 based on recent surveys. Users particularly appreciate the new dashboard interface and faster loading times.",
        "Marketing campaign effectiveness shows a 30% improvement in conversion rates. Social media campaigns and email marketing have been the most successful channels.",
        "Product usage analytics reveal that users spend an average of 45 minutes per session. Feature adoption rates are highest for analytics dashboards and reporting tools.",
        "Security metrics show zero critical incidents in the past quarter. Enhanced monitoring and automated threat detection have strengthened our security posture.",
        "API performance metrics indicate stable usage with 99.95% success rates. Rate limiting and caching optimizations have improved API reliability.",
        "Mobile app metrics show 40% of traffic comes from mobile devices. User retention on mobile is 20% higher than web platform users.",
        "Database performance metrics show optimized query times with average execution under 50ms. Recent indexing improvements have enhanced data retrieval efficiency."
    ]
    
    sample_metadata = [
        {"source": "user_engagement_report", "category": "engagement", "date": "2024-01"},
        {"source": "revenue_analysis", "category": "revenue", "date": "2024-01"},
        {"source": "system_performance", "category": "infrastructure", "date": "2024-01"},
        {"source": "customer_satisfaction", "category": "customer", "date": "2024-01"},
        {"source": "marketing_report", "category": "marketing", "date": "2024-01"},
        {"source": "product_analytics", "category": "product", "date": "2024-01"},
        {"source": "security_report", "category": "security", "date": "2024-01"},
        {"source": "api_metrics", "category": "api", "date": "2024-01"},
        {"source": "mobile_analytics", "category": "mobile", "date": "2024-01"},
        {"source": "database_performance", "category": "database", "date": "2024-01"}
    ]
    
    if vector_store.get_stats()["total_documents"] == 0:
        logger.info("Initializing vector store with sample documents")
        vector_store.add_documents(sample_docs, sample_metadata)
    else:
        logger.info("Vector store already contains documents") 