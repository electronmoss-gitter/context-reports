"""
Vector Store - Store and retrieve document embeddings using ChromaDB
"""
import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY"] = "False"

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
import time

# Import global config
from app.config import (
    EMBEDDING_MODEL,
    VECTOR_STORE_PATH,
    VECTOR_STORE_COLLECTION
)


class VectorStore:
    """Manages document embeddings and retrieval using ChromaDB"""
    
    def __init__(self, persist_directory: str = None):
        """
        Initialize the vector store with ChromaDB
        
        Args:
            persist_directory: Directory to persist the database (uses config if None)
        """
        if persist_directory is None:
            persist_directory = VECTOR_STORE_PATH
        
        self.persist_directory = os.path.abspath(persist_directory)
        os.makedirs(self.persist_directory, exist_ok=True)
        
        print(f"Initializing ChromaDB at: {self.persist_directory}")
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Lazy load embedding model
        self._embedding_model = None
        self.model_name = EMBEDDING_MODEL
        
        # Get or create collection with COSINE distance metric
        self.collection = self.client.get_or_create_collection(
            name=VECTOR_STORE_COLLECTION,
            metadata={
                "description": "Historical earthing reports and standards",
                "hnsw:space": "cosine"  # ✅ Use cosine distance for better similarity scores
            }
        )
        
        print(f"Collection '{VECTOR_STORE_COLLECTION}' ready. Current count: {self.collection.count()}")
    
    @property
    def embedding_model(self):
        """Lazy load the embedding model"""
        if self._embedding_model is None:
            print(f"Loading embedding model: {self.model_name}")
            self._embedding_model = SentenceTransformer(self.model_name)
            dim = self._embedding_model.get_sentence_embedding_dimension()
            print(f"✅ Model loaded. Embedding dimension: {dim}")
        return self._embedding_model
    
    def add_documents(
        self, 
        documents: List[str], 
        metadatas: Optional[List[Dict]] = None,
        ids: Optional[List[str]] = None
    ):
        """
        Add documents to the vector store
        
        Args:
            documents: List of text documents
            metadatas: Optional metadata for each document
            ids: Optional IDs for documents
        """
        if not documents:
            return
        
        # Generate embeddings
        embeddings = self.embedding_model.encode(documents).tolist()
        
        # Generate IDs if not provided
        if ids is None:
            timestamp = int(time.time() * 1000)
            ids = [f"doc_{timestamp}_{i}" for i in range(len(documents))]
        
        # Add to collection
        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"Added {len(documents)} documents. Total: {self.collection.count()}")
    
    def add_chunks(self, chunks: List[Dict], embeddings: List) -> None:
        """
        Add pre-computed chunks and embeddings to vector store
        
        Args:
            chunks: List of chunk dictionaries with 'text' and 'metadata'
            embeddings: Pre-computed embeddings (from Embedder)
        """
        if not chunks or len(chunks) == 0:
            return
        
        # Extract text and metadata from chunks
        documents = [chunk['text'] for chunk in chunks]
        metadatas = [chunk.get('metadata', {}) for chunk in chunks]
        
        # Generate unique IDs
        timestamp = int(time.time() * 1000)
        ids = [f"chunk_{timestamp}_{i}" for i in range(len(chunks))]
        
        # Convert embeddings to list if numpy array
        if hasattr(embeddings, 'tolist'):
            embeddings = embeddings.tolist()
        
        # Add to collection
        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"  Stored {len(chunks)} chunks in vector DB. Total: {self.collection.count()}")
    
    def query(
        self, 
        query_text: str, 
        n_results: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Query the vector store for similar documents
        
        Args:
            query_text: Query string
            n_results: Number of results to return
            filter_metadata: Optional metadata filters
            
        Returns:
            Dictionary with documents, distances, and metadatas
        """
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query_text]).tolist()
        
        # Query collection
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=n_results,
            where=filter_metadata
        )
        
        return {
            'documents': results['documents'][0] if results['documents'] else [],
            'distances': results['distances'][0] if results['distances'] else [],
            'metadatas': results['metadatas'][0] if results['metadatas'] else []
        }
    
    def get_collection_count(self) -> int:
        """Get the number of documents in the collection"""
        return self.collection.count()
    
    def get_stats(self) -> Dict:
        """
        Get statistics about the vector store
        
        Returns:
            Dictionary with statistics
        """
        count = self.get_collection_count()
        
        if count == 0:
            return {
                "total_chunks": 0,
                "message": "Vector store is empty. Run ingestion to add documents."
            }
        
        # Get sample metadata to analyze
        try:
            sample = self.collection.get(
                limit=min(100, count),
                include=["metadatas"]
            )
            
            # Aggregate metadata statistics
            project_types = {}
            voltage_levels = {}
            doc_types = {}
            
            for metadata in sample.get('metadatas', []):
                if metadata:
                    # Count project types
                    pt = metadata.get('project_type', 'unknown')
                    project_types[pt] = project_types.get(pt, 0) + 1
                    
                    # Count voltage levels
                    vl = metadata.get('voltage_level', 'unknown')
                    voltage_levels[vl] = voltage_levels.get(vl, 0) + 1
                    
                    # Count document types
                    dt = metadata.get('type', 'unknown')
                    doc_types[dt] = doc_types.get(dt, 0) + 1
            
            return {
                "total_chunks": count,
                "project_types": project_types,
                "voltage_levels": voltage_levels,
                "doc_types": doc_types,
                "model_loaded": self._embedding_model is not None
            }
        except Exception as e:
            return {
                "total_chunks": count,
                "error": f"Could not retrieve detailed stats: {str(e)}"
            }
    
    def clear_collection(self):
        """Clear all documents from the collection"""
        try:
            self.client.delete_collection(VECTOR_STORE_COLLECTION)
            self.collection = self.client.get_or_create_collection(
                name=VECTOR_STORE_COLLECTION,
                metadata={
                    "description": "Historical earthing reports and standards",
                    "hnsw:space": "cosine"
                }
            )
            print("✅ Collection cleared")
        except Exception as e:
            print(f"⚠️  Error clearing collection: {e}")