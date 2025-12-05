"""
Retriever - Retrieve relevant document chunks from vector store
"""
from typing import List, Dict, Optional
from app.rag.vector_store import VectorStore

class Retriever:
    """Retrieves relevant document chunks using semantic search"""
    
    def __init__(self, vector_store: VectorStore):
        """
        Initialize retriever
        
        Args:
            vector_store: VectorStore instance
        """
        self.vector_store = vector_store
    
    def retrieve(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict] = None,
        min_similarity: float = 0.0
    ) -> List[Dict]:
        """
        Retrieve relevant chunks for a query
        
        Args:
            query: Query string
            n_results: Number of results to return
            filter_metadata: Optional metadata filters
            min_similarity: Minimum similarity threshold (0.0 to 1.0)
            
        Returns:
            List of result dictionaries with content, metadata, and similarity
        """
        # Query vector store
        raw_results = self.vector_store.query(
            query_text=query,
            n_results=n_results,
            filter_metadata=filter_metadata
        )
        
        # Format results
        formatted_results = []
        
        documents = raw_results.get('documents', [])
        distances = raw_results.get('distances', [])
        metadatas = raw_results.get('metadatas', [])
        
        # Check if we got results
        if not documents:
            return []
        
        for i in range(len(documents)):
            distance = distances[i] if i < len(distances) else float('inf')
            
            # With cosine distance, convert to similarity
            # Cosine distance range: 0 (identical) to 2 (opposite)
            # Similarity = 1 - (distance / 2)
            similarity = 1.0 - (distance / 2.0)
            
            # Apply similarity threshold
            if similarity < min_similarity:
                continue
            
            formatted_results.append({
                'content': documents[i],
                'metadata': metadatas[i] if i < len(metadatas) else {},
                'similarity': similarity,
                'distance': distance
            })
        
        # Sort by similarity (highest first)
        formatted_results.sort(key=lambda x: x['similarity'], reverse=True)
        
        return formatted_results

# """
# Retriever - Retrieve relevant document chunks from vector store
# """
# from typing import List, Dict, Optional
# from app.rag.vector_store import VectorStore
# import math

# # Import global config
# from app.config import (
#     VECTOR_STORE_COLLECTION
# )


# class Retriever:
#     """Retrieves relevant document chunks using semantic search"""
    
#     def __init__(self, vector_store: VectorStore):
#         """
#         Initialize retriever
        
#         Args:
#             vector_store: VectorStore instance
#         """
#         self.vector_store = vector_store

#         # Get or create collection with cosine distance
#         self.collection = self.client.get_or_create_collection(
#             name=VECTOR_STORE_COLLECTION,
#             metadata={
#                 "description": "Historical earthing reports and standards",
#                 "hnsw:space": "cosine"  # Use cosine distance instead of L2
#             }
#         )
    
#     def retrieve(
#         self,
#         query: str,
#         n_results: int = 5,
#         filter_metadata: Optional[Dict] = None,
#         min_similarity: float = 0.0  # Don't filter by default
#     ) -> List[Dict]:
#         """
#         Retrieve relevant chunks for a query
        
#         Args:
#             query: Query string
#             n_results: Number of results to return
#             filter_metadata: Optional metadata filters
#             min_similarity: Minimum similarity threshold (0.0 to 1.0)
            
#         Returns:
#             List of result dictionaries with content, metadata, and similarity
#         """
#         # Query vector store
#         raw_results = self.vector_store.query(
#             query_text=query,
#             n_results=n_results,
#             filter_metadata=filter_metadata
#         )
        
#         # Format results
#         formatted_results = []
        
#         documents = raw_results.get('documents', [])
#         distances = raw_results.get('distances', [])
#         metadatas = raw_results.get('metadatas', [])
        
#         # Check if we got results
#         if not documents:
#             return []
        
#         for i in range(len(documents)):
#             distance = distances[i] if i < len(distances) else float('inf')
            
#             # Convert L2 distance to similarity score (0-1 range)
#             # L2 distance can be any positive number, so we use exponential decay
#             # Lower distance = higher similarity
#             # similarity = e^(-distance)
#             # Or use: similarity = 1 / (1 + distance)
#             similarity = 1.0 / (1.0 + distance)
            
#             # Apply similarity threshold
#             if similarity < min_similarity:
#                 continue
            
#             formatted_results.append({
#                 'content': documents[i],
#                 'metadata': metadatas[i] if i < len(metadatas) else {},
#                 'similarity': similarity,
#                 'distance': distance
#             })
        
#         # Sort by similarity (highest first)
#         formatted_results.sort(key=lambda x: x['similarity'], reverse=True)
        
#         return formatted_results
    
#     def retrieve_with_context(
#         self,
#         query: str,
#         n_results: int = 5,
#         context_window: int = 1
#     ) -> List[Dict]:
#         """
#         Retrieve chunks with surrounding context
        
#         Args:
#             query: Query string
#             n_results: Number of results to return
#             context_window: Number of chunks before/after to include
            
#         Returns:
#             List of results with expanded context
#         """
#         # Get initial results
#         results = self.retrieve(query, n_results)
        
#         # TODO: Implement context expansion by fetching neighboring chunks
#         # This would require storing chunk sequence information in metadata
        
#         return results

# """
# Retriever - Retrieve relevant context from the vector store
# """
# from typing import List, Dict, Optional
# from .vector_store import VectorStore

# class Retriever:
#     """Retrieves relevant documents from the vector store"""
    
#     def __init__(self, vector_store: VectorStore):
#         """
#         Initialize the retriever
        
#         Args:
#             vector_store: VectorStore instance
#         """
#         self.vector_store = vector_store
    
#     def retrieve(
#         self,
#         query: str,
#         n_results: int = 5,
#         min_similarity: float = 0.5,
#         filter_metadata: Optional[Dict] = None
#     ) -> List[Dict]:
#         """
#         Retrieve relevant documents for a query
        
#         Args:
#             query: Query string
#             n_results: Number of results to return
#             min_similarity: Minimum similarity threshold (0-1)
#             filter_metadata: Optional metadata filters
            
#         Returns:
#             List of relevant documents with metadata
#         """
#         # Query vector store
#         results = self.vector_store.query(
#             query_text=query,
#             n_results=n_results,
#             filter_metadata=filter_metadata
#         )
        
#         # Convert distances to similarities (cosine distance to similarity)
#         documents = []
#         for i, (doc, distance, metadata) in enumerate(zip(
#             results['documents'],
#             results['distances'],
#             results['metadatas']
#         )):
#             similarity = 1 - distance  # Convert distance to similarity
            
#             if similarity >= min_similarity:
#                 documents.append({
#                     'content': doc,
#                     'similarity': similarity,
#                     'metadata': metadata or {},
#                     'rank': i + 1
#                 })
        
#         return documents
    
#     def retrieve_by_type(
#         self,
#         query: str,
#         doc_type: str,
#         n_results: int = 3
#     ) -> List[Dict]:
#         """
#         Retrieve documents filtered by type
        
#         Args:
#             query: Query string
#             doc_type: Document type filter (e.g., 'standard', 'report')
#             n_results: Number of results
            
#         Returns:
#             Filtered documents
#         """
#         return self.retrieve(
#             query=query,
#             n_results=n_results,
#             filter_metadata={'type': doc_type}
#         )