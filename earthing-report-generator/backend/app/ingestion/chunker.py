"""
Document Chunker - Split documents into chunks for embedding and retrieval
"""
from typing import List, Dict
import re

class DocumentChunker:
    """
    Chunk documents intelligently based on sections and content
    Preserves context while creating manageable chunks for embeddings
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Args:
            chunk_size: Target size for each chunk (characters)
            chunk_overlap: Overlap between chunks to preserve context
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_document(self, parsed_doc: Dict) -> List[Dict]:
        """
        Chunk a parsed document intelligently
        
        Args:
            parsed_doc: Output from PDFParser or DOCXParser
            
        Returns:
            List of chunks with metadata
        """
        chunks = []
        
        # If document has sections, chunk by section
        if "sections" in parsed_doc and parsed_doc["sections"]:
            chunks.extend(self._chunk_by_sections(parsed_doc))
        else:
            # Fallback to simple text chunking
            chunks.extend(self._chunk_by_text(parsed_doc["full_text"], parsed_doc["metadata"]))
        
        # Add global metadata to all chunks
        for i, chunk in enumerate(chunks):
            chunk["chunk_id"] = i
            chunk["total_chunks"] = len(chunks)
            chunk["source_file"] = parsed_doc.get("source_file", "unknown")
        
        return chunks
    
    def _chunk_by_sections(self, parsed_doc: Dict) -> List[Dict]:
        """Chunk document by sections, splitting large sections if needed"""
        chunks = []
        metadata = parsed_doc.get("metadata", {})
        
        for section_type, section_text in parsed_doc["sections"].items():
            # If section is small enough, keep it as one chunk
            if len(section_text) <= self.chunk_size:
                chunks.append({
                    "text": section_text,
                    "section_type": section_type,
                    "metadata": metadata.copy()
                })
            else:
                # Split large section into multiple chunks
                section_chunks = self._split_text(section_text, self.chunk_size, self.chunk_overlap)
                for i, chunk_text in enumerate(section_chunks):
                    chunks.append({
                        "text": chunk_text,
                        "section_type": section_type,
                        "section_chunk_index": i,
                        "metadata": metadata.copy()
                    })
        
        return chunks
    
    def _chunk_by_text(self, text: str, metadata: Dict) -> List[Dict]:
        """Simple text-based chunking fallback"""
        chunks = []
        text_chunks = self._split_text(text, self.chunk_size, self.chunk_overlap)
        
        for i, chunk_text in enumerate(text_chunks):
            chunks.append({
                "text": chunk_text,
                "section_type": "unknown",
                "metadata": metadata.copy()
            })
        
        return chunks
    
    def _split_text(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """
        Split text into overlapping chunks
        Try to split on sentence boundaries when possible
        """
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # If not at the end, try to find a good breaking point
            if end < len(text):
                # Try to break on sentence boundary (period followed by space)
                sentence_breaks = [m.end() for m in re.finditer(r'\.\s+', text[start:end])]
                if sentence_breaks:
                    end = start + sentence_breaks[-1]
                else:
                    # Fallback to breaking on newline
                    newline_breaks = [m.end() for m in re.finditer(r'\n', text[start:end])]
                    if newline_breaks:
                        end = start + newline_breaks[-1]
                    # else: keep the character-based split
            
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(chunk_text)
            
            # Move start position with overlap
            start = end - overlap if end < len(text) else end
        
        return chunks
    
    def chunk_with_context(self, parsed_doc: Dict, context_window: int = 2) -> List[Dict]:
        """
        Advanced chunking that includes surrounding context
        Useful for maintaining coherence in retrieval
        
        Args:
            parsed_doc: Parsed document
            context_window: Number of surrounding chunks to include as context
            
        Returns:
            Chunks with context metadata
        """
        base_chunks = self.chunk_document(parsed_doc)
        
        # Add context information
        for i, chunk in enumerate(base_chunks):
            # Previous context
            if i > 0:
                chunk["previous_chunks"] = [
                    base_chunks[j]["text"][:200]  # First 200 chars of previous chunks
                    for j in range(max(0, i - context_window), i)
                ]
            
            # Next context
            if i < len(base_chunks) - 1:
                chunk["next_chunks"] = [
                    base_chunks[j]["text"][:200]  # First 200 chars of next chunks
                    for j in range(i + 1, min(len(base_chunks), i + context_window + 1))
                ]
        
        return base_chunks


if __name__ == "__main__":
    # Test the chunker
    chunker = DocumentChunker(chunk_size=500, chunk_overlap=100)
    
    # Example document
    test_doc = {
        "full_text": "This is a test document. " * 100,
        "sections": {
            "executive_summary": "Summary text. " * 50,
            "calculations": "Calculation details. " * 100
        },
        "metadata": {
            "project_type": "substation",
            "voltage_level": "HV"
        },
        "source_file": "test.pdf"
    }
    
    chunks = chunker.chunk_document(test_doc)
    print(f"Created {len(chunks)} chunks")
    print(f"First chunk: {chunks[0]['text'][:100]}...")