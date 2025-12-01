"""
RAG (Retrieval Augmented Generation) service using ChromaDB.
"""
from typing import List, Dict, Any, Optional
import os
import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from pathlib import Path

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class RAGService:
    """Service for RAG functionality using ChromaDB vector store."""
    
    def __init__(self):
        """Initialize ChromaDB and embedding model."""
        # Create persist directory if it doesn't exist
        persist_dir = Path(settings.CHROMA_PERSIST_DIR)
        persist_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            )
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION_NAME,
            metadata={"description": "Learning knowledge base"}
        )
        
        # Initialize embedding model lazily
        self._embedding_model = None
        
        logger.info(
            "RAG service initialized",
            collection=settings.CHROMA_COLLECTION_NAME,
            persist_dir=str(persist_dir),
        )
    
    @property
    def embedding_model(self):
        """Lazy load the embedding model."""
        if self._embedding_model is None:
            logger.info("Loading embedding model...", model=settings.EMBEDDING_MODEL)
            self._embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info("Embedding model loaded successfully")
        return self._embedding_model
    
    def add_documents(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> None:
        """
        Add documents to the vector store.
        
        Args:
            texts: List of text chunks to add
            metadatas: Optional metadata for each chunk
            ids: Optional IDs for each chunk (generated if not provided)
        """
        if not texts:
            return
        
        # Generate IDs if not provided
        if ids is None:
            import uuid
            ids = [str(uuid.uuid4()) for _ in texts]
        
        # Generate embeddings
        embeddings = self.embedding_model.encode(texts, convert_to_tensor=False).tolist()
        
        # Add to collection
        self.collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas or [{} for _ in texts],
            ids=ids,
        )
        
        logger.info("Added documents to RAG", count=len(texts))
    
    def retrieve(
        self,
        query: str,
        top_k: int = None,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: Search query
            top_k: Number of results to return (defaults to RAG_TOP_K setting)
            filter_metadata: Optional metadata filter
            
        Returns:
            List of retrieved documents with metadata and scores
        """
        if top_k is None:
            top_k = settings.RAG_TOP_K
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query], convert_to_tensor=False).tolist()[0]
        
        # Query the collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter_metadata,
        )
        
        # Format results
        documents = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                documents.append({
                    "text": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 0,
                    "id": results["ids"][0][i] if results["ids"] else None,
                })
        
        logger.info(
            "RAG retrieval completed",
            query=query[:50],
            results_count=len(documents),
        )
        
        return documents
    
    def delete_documents(self, ids: List[str]) -> None:
        """
        Delete documents by ID.
        
        Args:
            ids: List of document IDs to delete
        """
        self.collection.delete(ids=ids)
        logger.info("Deleted documents from RAG", count=len(ids))
    
    def clear_collection(self) -> None:
        """Clear all documents from the collection."""
        self.client.delete_collection(settings.CHROMA_COLLECTION_NAME)
        self.collection = self.client.create_collection(
            name=settings.CHROMA_COLLECTION_NAME,
            metadata={"description": "Learning knowledge base"}
        )
        logger.warning("RAG collection cleared")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection."""
        count = self.collection.count()
        return {
            "document_count": count,
            "collection_name": settings.CHROMA_COLLECTION_NAME,
            "embedding_model": settings.EMBEDDING_MODEL,
        }


# Global instance
rag_service = RAGService()
