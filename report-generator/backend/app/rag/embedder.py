"""
Embedder - Generate embeddings for text chunks using sentence-transformers
"""
from sentence_transformers import SentenceTransformer
from typing import List, Union
import numpy as np
import os

class Embedder:
    """Generate embeddings using local sentence-transformers model"""
    
    def __init__(self, model_name: str = None):
        """
        Initialize embedder with specified model
        
        Args:
            model_name: Sentence-transformer model name
                       Default: 'sentence-transformers/all-mpnet-base-v2'
                       (384 dimensions, good balance of speed and quality)
        """
        if model_name is None:
            model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-mpnet-base-v2")
        
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.embedding_dimension = self.model.get_sentence_embedding_dimension()
        print(f"Model loaded. Embedding dimension: {self.embedding_dimension}")
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector as list of floats
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def embed_texts(self, texts: List[str], batch_size: int = 32, show_progress: bool = True) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batched for efficiency)
        
        Args:
            texts: List of input texts
            batch_size: Number of texts to process at once
            show_progress: Show progress bar
            
        Returns:
            List of embedding vectors
        """
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True
        )
        return embeddings.tolist()
    
    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a search query
        (Alias for embed_text, but semantically clearer)
        
        Args:
            query: Search query
            
        Returns:
            Query embedding vector
        """
        return self.embed_text(query)
    
    def get_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score (0 to 1, higher is more similar)
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Cosine similarity
        similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        
        return float(similarity)


if __name__ == "__main__":
    # Test the embedder
    embedder = Embedder()
    
    # Test single text
    text = "This is a test earthing study report for a 33kV substation."
    embedding = embedder.embed_text(text)
    print(f"Generated embedding of dimension: {len(embedding)}")
    
    # Test multiple texts
    texts = [
        "Soil resistivity measurements using Wenner method",
        "Touch and step potential calculations per IEEE 80",
        "Earth grid resistance design for substations"
    ]
    embeddings = embedder.embed_texts(texts, show_progress=False)
    print(f"Generated {len(embeddings)} embeddings")
    
    # Test similarity
    query_embedding = embedder.embed_query("soil resistivity testing")
    similarity = embedder.get_similarity(query_embedding, embeddings[0])
    print(f"Similarity between query and first text: {similarity:.3f}")