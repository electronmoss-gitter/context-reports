"""
Document Chunker - Split documents into overlapping chunks
"""
import re
from typing import List, Dict


class DocumentChunker:
    """Splits documents into semantically meaningful chunks"""
    
    def __init__(self, chunk_size: int = 1500, chunk_overlap: int = 300):
        """
        Initialize the chunker
        
        Args:
            chunk_size: Target size of each chunk in characters
            chunk_overlap: Number of overlapping characters between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_document(self, document: Dict) -> List[Dict]:
        """
        Split document into chunks while preserving semantic structure
        
        Args:
            document: Parsed document dictionary
            
        Returns:
            List of chunk dictionaries
        """
        text = document.get('full_text', '')
        chunks = []
        
        # Try to split on section boundaries first
        sections = self._split_by_sections(text)
        
        for section_text, section_name in sections:
            # Further split large sections by paragraphs
            section_chunks = self._chunk_text(section_text, section_name)
            chunks.extend(section_chunks)
        
        # Add metadata to each chunk
        for i, chunk in enumerate(chunks):
            chunk['metadata'] = {
                **document.get('metadata', {}),
                'chunk_index': i,
                'total_chunks': len(chunks)
            }
        
        return chunks
    
    def _split_by_sections(self, text: str) -> List[tuple]:
        """
        Split text by section headers
        
        Returns:
            List of (section_text, section_name) tuples
        """
        # Look for common section headers (ALL CAPS, numbered, etc)
        section_pattern = r'^([A-Z][A-Z\s\d\.]*)\s*$'
        
        lines = text.split('\n')
        sections = []
        current_section = ""
        current_section_name = "Introduction"
        
        for line in lines:
            # Check if line looks like a section header
            if re.match(section_pattern, line.strip()) and len(line.strip()) > 3:
                # Save previous section
                if current_section.strip():
                    sections.append((current_section, current_section_name))
                
                current_section_name = line.strip()
                current_section = line + "\n"
            else:
                current_section += line + "\n"
        
        # Add final section
        if current_section.strip():
            sections.append((current_section, current_section_name))
        
        return sections if sections else [(text, "Document")]
    
    def _chunk_text(self, text: str, section_name: str = "") -> List[Dict]:
        """
        Split text into chunks with smart boundaries
        
        Args:
            text: Text to chunk
            section_name: Name of the section
            
        Returns:
            List of chunk dictionaries
        """
        if len(text) <= self.chunk_size:
            return [{
                'text': text.strip(),
                'section_type': section_name,
                'metadata': {}
            }]
        
        chunks = []
        start = 0
        iteration = 0
        max_iterations = (len(text) // (self.chunk_size - self.chunk_overlap)) + 10
        
        while start < len(text):
            iteration += 1
            
            # Safety check
            if iteration > max_iterations:
                print(f"⚠️  Breaking out of potential infinite loop")
                break
            
            end = start + self.chunk_size
            
            # Try to break at smart boundaries in order of preference:
            # 1. Paragraph break (double newline)
            # 2. Sentence boundary (period + space)
            # 3. Line break (single newline)
            # 4. Word boundary (space)
            
            if end < len(text):
                # 1. Try paragraph break
                paragraph_breaks = [m.end() for m in re.finditer(r'\n\n+', text[start:end])]
                if paragraph_breaks:
                    end = start + paragraph_breaks[-1]
                else:
                    # 2. Try sentence boundary
                    sentence_breaks = [m.end() for m in re.finditer(r'\.\s+', text[start:end])]
                    if sentence_breaks:
                        end = start + sentence_breaks[-1]
                    else:
                        # 3. Try line break
                        newline_breaks = [m.end() for m in re.finditer(r'\n', text[start:end])]
                        if newline_breaks:
                            end = start + newline_breaks[-1]
                        else:
                            # 4. Try word boundary
                            word_breaks = [m.end() for m in re.finditer(r'\s', text[start:end])]
                            if word_breaks:
                                end = start + word_breaks[-1]
            
            # Safety: ensure we always advance
            if end <= start:
                end = start + 1
            
            chunk_text = text[start:end].strip()
            if chunk_text and len(chunk_text) > 50:  # Only keep substantial chunks
                chunks.append({
                    'text': chunk_text,
                    'section_type': section_name,
                    'metadata': {}
                })
            
            # Calculate next start with overlap
            next_start = end - self.chunk_overlap if end < len(text) else end
            
            # Ensure minimum advance
            if next_start <= start:
                next_start = start + max(1, (self.chunk_size - self.chunk_overlap) // 2)
            
            start = next_start
        
        return chunks

# """
# Document Chunker - Split documents into chunks for embedding and retrieval
# """
# from typing import List, Dict
# import re

# class DocumentChunker:
#     """
#     Chunk documents intelligently based on sections and content
#     Preserves context while creating manageable chunks for embeddings
#     """
    
#     def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
#         """
#         Args:
#             chunk_size: Target size for each chunk (characters)
#             chunk_overlap: Overlap between chunks to preserve context
#         """
#         self.chunk_size = chunk_size
#         self.chunk_overlap = chunk_overlap
    
#     def chunk_document(self, parsed_doc: Dict) -> List[Dict]:
#         """
#         Chunk a parsed document intelligently
        
#         Args:
#             parsed_doc: Output from PDFParser or DOCXParser
            
#         Returns:
#             List of chunks with metadata
#         """
#         chunks = []
        
#         # If document has sections, chunk by section
#         if "sections" in parsed_doc and parsed_doc["sections"]:
#             chunks.extend(self._chunk_by_sections(parsed_doc))
#         else:
#             # Fallback to simple text chunking
#             chunks.extend(self._chunk_by_text(parsed_doc["full_text"], parsed_doc["metadata"]))
        
#         # Add global metadata to all chunks
#         for i, chunk in enumerate(chunks):
#             chunk["chunk_id"] = i
#             chunk["total_chunks"] = len(chunks)
#             chunk["source_file"] = parsed_doc.get("source_file", "unknown")
        
#         return chunks
    
#     def _chunk_by_sections(self, parsed_doc: Dict) -> List[Dict]:
#         """Chunk document by sections, splitting large sections if needed"""
#         chunks = []
#         metadata = parsed_doc.get("metadata", {})
        
#         for section_type, section_text in parsed_doc["sections"].items():
#             # If section is small enough, keep it as one chunk
#             if len(section_text) <= self.chunk_size:
#                 chunks.append({
#                     "text": section_text,
#                     "section_type": section_type,
#                     "metadata": metadata.copy()
#                 })
#             else:
#                 # Split large section into multiple chunks
#                 section_chunks = self._split_text(section_text, self.chunk_size, self.chunk_overlap)
#                 for i, chunk_text in enumerate(section_chunks):
#                     chunks.append({
#                         "text": chunk_text,
#                         "section_type": section_type,
#                         "section_chunk_index": i,
#                         "metadata": metadata.copy()
#                     })
        
#         return chunks
    
#     def _chunk_by_text(self, text: str, metadata: Dict) -> List[Dict]:
#         """Simple text-based chunking fallback"""
#         chunks = []
#         text_chunks = self._split_text(text, self.chunk_size, self.chunk_overlap)
        
#         for i, chunk_text in enumerate(text_chunks):
#             chunks.append({
#                 "text": chunk_text,
#                 "section_type": "unknown",
#                 "metadata": metadata.copy()
#             })
        
#         return chunks
    
#     def _split_text(self, text: str, chunk_size: int, overlap: int) -> List[str]:
#         """
#         Split text into overlapping chunks
#         Try to split on sentence boundaries when possible
#         """
#         if len(text) <= chunk_size:
#             return [text]
        
#         chunks = []
#         start = 0
#         iteration = 0
        
#         # Safety limit to prevent infinite loops
#         max_iterations = (len(text) // (chunk_size - overlap)) + 10
        
#         while start < len(text):
#             iteration += 1
            
#             # Safety check for infinite loops
#             if iteration > max_iterations:
#                 print(f"⚠️  WARNING: Breaking out of potential infinite loop at position {start}/{len(text)}")
#                 break
            
#             end = start + chunk_size
            
#             # Try to break on sentence boundary (period followed by space)
#             if end < len(text):
#                 sentence_breaks = [m.end() for m in re.finditer(r'\.\s+', text[start:end])]
#                 if sentence_breaks:
#                     end = start + sentence_breaks[-1]
#                 else:
#                     # Fallback: try to break on newline
#                     newline_breaks = [m.end() for m in re.finditer(r'\n', text[start:end])]
#                     if newline_breaks:
#                         end = start + newline_breaks[-1]
            
#             # CRITICAL FIX: Ensure we always advance at least 1 character
#             if end <= start:
#                 end = start + 1
            
#             chunk_text = text[start:end].strip()
#             if chunk_text:
#                 chunks.append(chunk_text)
            
#             # Calculate next start position with overlap
#             next_start = end - overlap if end < len(text) else end
            
#             # CRITICAL FIX: Ensure minimum advance to prevent infinite loops
#             # If overlap is too large or sentence break puts us back, force advance
#             if next_start <= start:
#                 # Force advance by at least half the chunk size to avoid getting stuck
#                 next_start = start + max(1, (chunk_size - overlap) // 2)
            
#             start = next_start
        
#         return chunks
    
#     def chunk_with_context(self, parsed_doc: Dict, context_window: int = 2) -> List[Dict]:
#         """
#         Advanced chunking that includes surrounding context
#         Useful for maintaining coherence in retrieval
        
#         Args:
#             parsed_doc: Parsed document
#             context_window: Number of surrounding chunks to include as context
            
#         Returns:
#             Chunks with context metadata
#         """
#         base_chunks = self.chunk_document(parsed_doc)
        
#         # Add context information
#         for i, chunk in enumerate(base_chunks):
#             # Previous context
#             if i > 0:
#                 chunk["previous_chunks"] = [
#                     base_chunks[j]["text"][:200]  # First 200 chars of previous chunks
#                     for j in range(max(0, i - context_window), i)
#                 ]
            
#             # Next context
#             if i < len(base_chunks) - 1:
#                 chunk["next_chunks"] = [
#                     base_chunks[j]["text"][:200]  # First 200 chars of next chunks
#                     for j in range(i + 1, min(len(base_chunks), i + context_window + 1))
#                 ]
        
#         return base_chunks


# if __name__ == "__main__":
#     # Test the chunker
#     chunker = DocumentChunker(chunk_size=500, chunk_overlap=100)
    
#     # Example document
#     test_doc = {
#         "full_text": "This is a test document. " * 100,
#         "sections": {
#             "executive_summary": "Summary text. " * 50,
#             "calculations": "Calculation details. " * 100
#         },
#         "metadata": {
#             "project_type": "substation",
#             "voltage_level": "HV"
#         },
#         "source_file": "test.pdf"
#     }
    
#     chunks = chunker.chunk_document(test_doc)
#     print(f"Created {len(chunks)} chunks")
#     print(f"First chunk: {chunks[0]['text'][:100]}...")