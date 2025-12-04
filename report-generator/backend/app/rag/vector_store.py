"""
Vector Store - Store and retrieve document embeddings using ChromaDB
"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
from pathlib import Path
import os
import json

class VectorStore:
    """
    Manage document embeddings in ChromaDB (local, persistent vector database)
    """
    
    def __init__(self, persist_directory: str = None, collection_name: str = "earthing_reports"):
        """
        Initialize vector store
        
        Args:
            persist_directory: Directory to store the database
            collection_name: Name of the collection
        """
        if persist_directory is None:
            persist_directory = os.getenv("VECTOR_DB_PATH", "./data/vector_db")
        
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection
        self.collection_name = collection_name
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Electrical earthing study reports and standards"}
        )
        
        print(f"Vector store initialized at: {self.persist_directory}")
        print(f"Collection '{collection_name}' contains {self.collection.count()} documents")
    
    def add_chunks(self, chunks: List[Dict], embeddings: List[List[float]]):
        """
        Add document chunks with their embeddings to the vector store
        
        Args:
            chunks: List of chunk dicts (must have 'text' and 'metadata')
            embeddings: Corresponding embeddings for each chunk
        """
        if len(chunks) != len(embeddings):
            raise ValueError(f"Number of chunks ({len(chunks)}) must match embeddings ({len(embeddings)})")
        
        # Prepare data for ChromaDB
        ids = []
        documents = []
        metadatas = []
        embeddings_list = []
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            # Generate unique ID
            source_file = chunk.get("source_file", "unknown")
            chunk_id = chunk.get("chunk_id", i)
            doc_id = f"{Path(source_file).stem}_chunk_{chunk_id}"
            
            ids.append(doc_id)
            documents.append(chunk["text"])
            
            # Prepare metadata (ChromaDB requires flat dict with string/int/float values)
            metadata = self._flatten_metadata(chunk.get("metadata", {}))
            metadata["section_type"] = chunk.get("section_type", "unknown")
            metadata["source_file"] = source_file
            metadata["chunk_id"] = chunk_id
            
            metadatas.append(metadata)
            embeddings_list.append(embedding)
        
        # Add to collection
        self.collection.add(
            ids=ids,
            embeddings=embeddings_list,
            documents=documents,
            metadatas=metadatas
        )
        
        print(f"Added {len(chunks)} chunks to vector store")
    
    def search(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Search for similar chunks using query embedding
        
        Args:
            query_embedding: Query embedding vector
            n_results: Number of results to return
            filter_metadata: Optional metadata filters (e.g., {"project_type": "substation"})
            
        Returns:
            List of matching chunks with similarity scores
        """
        where_clause = filter_metadata if filter_metadata else None
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_clause,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                "id": results['ids'][0][i],
                "text": results['documents'][0][i],
                "metadata": results['metadatas'][0][i],
                "similarity_score": 1 - results['distances'][0][i],  # Convert distance to similarity
                "distance": results['distances'][0][i]
            })
        
        return formatted_results
    
    def get_by_metadata(self, filter_metadata: Dict, limit: int = 10) -> List[Dict]:
        """
        Retrieve chunks by metadata filters
        
        Args:
            filter_metadata: Metadata to filter by
            limit: Maximum number of results
            
        Returns:
            List of matching chunks
        """
        results = self.collection.get(
            where=filter_metadata,
            limit=limit,
            include=["documents", "metadatas"]
        )
        
        formatted_results = []
        for i in range(len(results['ids'])):
            formatted_results.append({
                "id": results['ids'][i],
                "text": results['documents'][i],
                "metadata": results['metadatas'][i]
            })
        
        return formatted_results
    
    def delete_by_source(self, source_file: str):
        """
        Delete all chunks from a specific source file
        
        Args:
            source_file: Source filename to delete
        """
        self.collection.delete(
            where={"source_file": source_file}
        )
        print(f"Deleted chunks from: {source_file}")
    
    def clear(self):
        """Clear all data from the collection"""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"description": "Electrical earthing study reports and standards"}
        )
        print(f"Cleared collection '{self.collection_name}'")
    
    def get_stats(self) -> Dict:
        """Get statistics about the vector store"""
        count = self.collection.count()
        
        # Get sample of metadata to understand what's stored
        if count > 0:
            sample = self.collection.get(limit=min(100, count), include=["metadatas"])
            
            # Aggregate metadata
            project_types = {}
            voltage_levels = {}
            section_types = {}
            
            for metadata in sample['metadatas']:
                pt = metadata.get('project_type', 'unknown')
                project_types[pt] = project_types.get(pt, 0) + 1
                
                vl = metadata.get('voltage_level', 'unknown')
                voltage_levels[vl] = voltage_levels.get(vl, 0) + 1
                
                st = metadata.get('section_type', 'unknown')
                section_types[st] = section_types.get(st, 0) + 1
            
            return {
                "total_chunks": count,
                "project_types": project_types,
                "voltage_levels": voltage_levels,
                "section_types": section_types
            }
        else:
            return {
                "total_chunks": 0,
                "message": "No documents in collection"
            }
    
    def _flatten_metadata(self, metadata: Dict) -> Dict:
        """
        Flatten metadata dict to only include string/int/float values
        (ChromaDB requirement)
        """
        flattened = {}
        
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)):
                flattened[key] = value
            elif isinstance(value, list):
                # Convert lists to comma-separated strings
                flattened[key] = ",".join(str(v) for v in value)
            elif isinstance(value, dict):
                # Skip nested dicts
                continue
            else:
                flattened[key] = str(value)
        
        return flattened


if __name__ == "__main__":
    # Test the vector store
    from app.rag.embedder import Embedder
    
    embedder = Embedder()
    vector_store = VectorStore()
    
    # Test data
    test_chunks = [
        {
            "text": "Soil resistivity was measured using the Wenner four-probe method at depths of 1m, 3m, and 5m.",
            "metadata": {"project_type": "substation", "voltage_level": "HV"},
            "section_type": "soil_resistivity",
            "source_file": "test_report.pdf",
            "chunk_id": 0
        },
        {
            "text": "Touch potential calculations were performed according to IEEE 80-2013 standards.",
            "metadata": {"project_type": "substation", "voltage_level": "HV"},
            "section_type": "calculations",
            "source_file": "test_report.pdf",
            "chunk_id": 1
        }
    ]
    
    # Generate embeddings
    texts = [chunk["text"] for chunk in test_chunks]
    embeddings = embedder.embed_texts(texts, show_progress=False)
    
    # Add to vector store
    vector_store.add_chunks(test_chunks, embeddings)
    
    # Search
    query = "How was soil resistivity measured?"
    query_embedding = embedder.embed_query(query)
    results = vector_store.search(query_embedding, n_results=2)
    
    print(f"\nSearch results for: '{query}'")
    for result in results:
        print(f"- Similarity: {result['similarity_score']:.3f}")
        print(f"  Text: {result['text'][:100]}...")
    
    # Stats
    stats = vector_store.get_stats()
    print(f"\nVector store stats: {stats}")