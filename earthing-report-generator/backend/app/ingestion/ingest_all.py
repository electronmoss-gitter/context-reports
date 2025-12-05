"""
Complete document ingestion pipeline
Processes historical reports and standards, stores them in vector database
"""
from pathlib import Path
from typing import List, Dict, Optional
import os
from tqdm import tqdm
import re
from app.ingestion.resource_util import check_system_resources, should_pause_ingestion
import time

from app.ingestion.pdf_parser import PDFParser
from app.ingestion.docx_parser import DOCXParser
from app.ingestion.chunker import DocumentChunker
from app.rag.embedder import Embedder
from app.rag.vector_store import VectorStore

from app.config import (
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    EMBEDDING_BATCH_SIZE,
    HISTORICAL_REPORTS_PATH
)

def ingest_documents(specific_file: Optional[str] = None) -> Dict:
    """
    Ingest historical reports from data/historical_reports directory
    
    Args:
        specific_file: Optional path to a specific file to ingest
        
    Returns:
        Dict with ingestion statistics
    """
    # Initialize components
    pdf_parser = PDFParser()
    docx_parser = DOCXParser()
    chunker = DocumentChunker(
        chunk_size=int(os.getenv("CHUNK_SIZE", "1000")),
        chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "200"))
    )
    embedder = Embedder()
    vector_store = VectorStore()

    # Use config values
    chunker = DocumentChunker(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    
    # Get list of files to process
    if specific_file:
        files_to_process = [Path(specific_file)]
    else:
        reports_dir = Path(HISTORICAL_REPORTS_PATH)
        if not reports_dir.exists():
            reports_dir.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {reports_dir}")
            print("Please add PDF/DOCX reports to this directory and run ingestion again")
            return {
                "documents_processed": 0,
                "chunks_created": 0,
                "message": "No documents found"
            }
        
        # Find all PDF and DOCX files
        pdf_files = list(reports_dir.glob("*.pdf"))
        docx_files = list(reports_dir.glob("*.docx"))
        txt_files = list(reports_dir.glob("*.txt"))
        files_to_process = pdf_files + docx_files + txt_files
    
    if not files_to_process:
        print("No documents found to process")
        return {
            "documents_processed": 0,
            "chunks_created": 0,
            "message": "No documents found"
        }
    
    print(f"Found {len(files_to_process)} documents to ingest")
    
    # Process each document
    total_chunks = 0
    documents_processed = 0

    # MEMORY FIX: Process in batches
    BATCH_SIZE = EMBEDDING_BATCH_SIZE
    
    for file_path in tqdm(files_to_process, desc="Ingesting documents"):
        try:
            # RESOURCE CHECK: Pause if memory too high
            if should_pause_ingestion(memory_threshold=75.0):
                print("   Pausing for 30 seconds to release memory...")
                import gc
                gc.collect()
                time.sleep(30)
            
            # Show resources
            resources = check_system_resources()
            print(f"  [CPU: {resources['cpu_percent']:.0f}% | RAM: {resources['memory_percent']:.0f}%]")
            
            print(f"\nProcessing: {file_path.name}")
            
            # Parse document based on type
            if file_path.suffix.lower() == '.pdf':
                parsed_doc = pdf_parser.parse(str(file_path))
            elif file_path.suffix.lower() == '.docx':
                parsed_doc = docx_parser.parse(str(file_path))
            elif file_path.suffix.lower() == '.txt':
                parsed_doc = _parse_text_file(file_path)
            else:
                print(f"Skipping unsupported file type: {file_path.suffix}")
                continue
            
            print(f"  Extracted {len(parsed_doc['full_text'])} characters")
            print(f"  Found {len(parsed_doc.get('sections', {}))} sections")
            print(f"  Metadata: {parsed_doc['metadata']}")
            
            # Chunk document
            chunks = chunker.chunk_document(parsed_doc)
            print(f"  Created {len(chunks)} chunks")
            
            # MEMORY FIX: Process chunks in batches to avoid memory explosion
            for i in range(0, len(chunks), BATCH_SIZE):
                batch = chunks[i:i+BATCH_SIZE]
                texts = [chunk["text"] for chunk in batch]
                
                print(f"  Processing batch {i//BATCH_SIZE + 1}/{(len(chunks)-1)//BATCH_SIZE + 1}...")
                
                # Generate embeddings for batch
                embeddings = embedder.embed_texts(texts, show_progress=False)
                
                # Store batch in vector database
                vector_store.add_chunks(batch, embeddings)
                
                # MEMORY FIX: Force garbage collection after each batch
                import gc
                gc.collect()
            
            total_chunks += len(chunks)
            documents_processed += 1
            
        except Exception as e:
            print(f"Error processing {file_path.name}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Ingestion complete!")
    print(f"Documents processed: {documents_processed}")
    print(f"Total chunks created: {total_chunks}")
    print(f"{'='*60}\n")
    
    # Show vector store stats
    stats = vector_store.get_stats()
    print("Vector store statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    return {
        "documents_processed": documents_processed,
        "chunks_created": total_chunks,
        "vector_store_stats": stats
    }


def _parse_text_file(file_path: Path) -> Dict:
    """
    Parse plain text file
    
    Args:
        file_path: Path to text file
        
    Returns:
        Parsed document dictionary
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return {
        'full_text': content,
        'sections': {},
        'metadata': {
            'source': file_path.name,
            'file_type': 'text',
            'type': 'report'
        }
    }


def ingest_standards_documents() -> Dict:
    """
    Ingest standards documents (AS/NZS, IEEE, IEC)
    These are stored with special metadata for compliance checking
    
    Returns:
        Dict with ingestion statistics
    """
    # Initialize components
    pdf_parser = PDFParser()
    docx_parser = DOCXParser()
    chunker = DocumentChunker(
        chunk_size=int(os.getenv("CHUNK_SIZE", "1500")),  # Larger chunks for standards
        chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "300"))
    )
    embedder = Embedder()
    vector_store = VectorStore()
    
    standards_dir = Path(os.getenv("STANDARDS_PATH", "./data/standards"))
    
    if not standards_dir.exists():
        standards_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {standards_dir}")
        print("Add standards PDFs/DOCX to this directory")
        return {
            "standards_processed": 0,
            "standards_chunks": 0,
            "message": "No standards documents found"
        }
    
    # Find all standard documents
    pdf_files = list(standards_dir.glob("*.pdf"))
    docx_files = list(standards_dir.glob("*.docx"))
    txt_files = list(standards_dir.glob("*.txt"))
    files_to_process = pdf_files + docx_files + txt_files
    
    if not files_to_process:
        print("No standards documents found to process")
        print(f"Add standards PDFs/DOCX to: {standards_dir}")
        return {
            "standards_processed": 0,
            "standards_chunks": 0,
            "message": "No standards documents found"
        }
    
    print(f"\nIngesting {len(files_to_process)} standards documents...")
    
    total_chunks = 0
    standards_processed = 0
    clauses_extracted = 0
    
    for file_path in tqdm(files_to_process, desc="Ingesting standards"):
        try:
            print(f"\nProcessing standard: {file_path.name}")
            
            # Detect standard type from filename
            standard_type = _detect_standard_type(file_path.name)
            
            # Parse document
            if file_path.suffix.lower() == '.pdf':
                parsed_doc = pdf_parser.parse(str(file_path))
            elif file_path.suffix.lower() == '.docx':
                parsed_doc = docx_parser.parse(str(file_path))
            elif file_path.suffix.lower() == '.txt':
                parsed_doc = _parse_text_file(file_path)
            else:
                print(f"Skipping unsupported file type: {file_path.suffix}")
                continue
            
            print(f"  Extracted {len(parsed_doc['full_text'])} characters")
            
            # Extract clauses/sections from standard
            clauses = _extract_clauses(parsed_doc['full_text'], standard_type)
            print(f"  Extracted {len(clauses)} clauses")
            clauses_extracted += len(clauses)
            
            # Create chunks with clause metadata
            chunks = chunker.chunk_document(parsed_doc)
            
            # Enrich chunks with standards-specific metadata
            for chunk in chunks:
                chunk['metadata'].update({
                    'type': 'standard',
                    'standard_type': standard_type,
                    'document_type': 'electrical_standard',
                    'is_normative': _is_normative_clause(chunk['text']),
                    'compliance_relevant': True
                })
            
            # Map clauses to chunks for reference
            clause_mapping = _map_clauses_to_chunks(clauses, chunks)
            
            print(f"  Created {len(chunks)} chunks")
            
            # Generate embeddings
            texts = [chunk["text"] for chunk in chunks]
            print(f"  Generating embeddings...")
            embeddings = embedder.embed_texts(texts, show_progress=False)
            
            # Store in vector database
            vector_store.add_chunks(chunks, embeddings)
            
            total_chunks += len(chunks)
            standards_processed += 1
            
            # Store clause mapping as reference
            _store_clause_reference(standard_type, clause_mapping)
            
        except Exception as e:
            print(f"Error processing {file_path.name}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Standards ingestion complete!")
    print(f"Standards processed: {standards_processed}")
    print(f"Total chunks created: {total_chunks}")
    print(f"Clauses extracted: {clauses_extracted}")
    print(f"{'='*60}\n")
    
    # Show vector store stats
    stats = vector_store.get_stats()
    print("Vector store statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    return {
        "standards_processed": standards_processed,
        "standards_chunks": total_chunks,
        "clauses_extracted": clauses_extracted,
        "vector_store_stats": stats
    }


def _detect_standard_type(filename: str) -> str:
    """
    Detect standard type from filename
    
    Args:
        filename: Name of the standard document
        
    Returns:
        Standard type (AS/NZS, IEEE, IEC, etc.)
    """
    filename_upper = filename.upper()
    
    if 'AS/NZS' in filename_upper or 'ASNZS' in filename_upper:
        return 'AS/NZS'
    elif 'IEEE' in filename_upper:
        return 'IEEE'
    elif 'IEC' in filename_upper:
        return 'IEC'
    elif 'AS' in filename_upper:
        return 'AS'
    elif 'NZS' in filename_upper:
        return 'NZS'
    else:
        return 'UNKNOWN'


def _extract_clauses(text: str, standard_type: str) -> List[Dict]:
    """
    Extract clauses/sections from standard document
    
    Args:
        text: Full text of standard
        standard_type: Type of standard (AS/NZS, IEEE, etc.)
        
    Returns:
        List of extracted clauses with metadata
    """
    clauses = []
    
    if standard_type in ['AS/NZS', 'AS', 'NZS']:
        # Pattern for AS/NZS clause numbering (e.g., "3.2.1", "7.5")
        pattern = r'(\d+(?:\.\d+)+)\s+(.+?)(?=\n\d+(?:\.\d+)+\s+|$)'
    elif standard_type == 'IEEE':
        # Pattern for IEEE section numbering
        pattern = r'(Section\s+\d+(?:\.\d+)*)\s+(.+?)(?=Section\s+\d+|$)'
    elif standard_type == 'IEC':
        # Pattern for IEC clause numbering
        pattern = r'(\d+(?:\.\d+)+)\s+(.+?)(?=\n\d+(?:\.\d+)+\s+|$)'
    else:
        # Generic heading pattern
        pattern = r'([\d.]+)\s+(.+?)(?=[\n\d.]|$)'
    
    matches = re.finditer(pattern, text, re.MULTILINE | re.DOTALL)
    
    for match in matches:
        clause_num = match.group(1).strip()
        clause_title = match.group(2).strip()
        
        # Extract first 500 chars as preview
        clause_content = text[match.start():min(match.end(), match.start() + 500)]
        
        clauses.append({
            'clause_number': clause_num,
            'clause_title': clause_title,
            'content_preview': clause_content,
            'full_match_start': match.start(),
            'full_match_end': match.end()
        })
    
    return clauses


def _is_normative_clause(text: str) -> bool:
    """
    Determine if a clause is normative (prescriptive) or informative
    
    Args:
        text: Clause text
        
    Returns:
        True if normative, False if informative
    """
    normative_keywords = [
        'shall', 'must', 'required', 'shall not', 'must not',
        'shall be', 'is required', 'mandatory', 'requirement',
        'minimum', 'maximum', 'not permitted'
    ]
    
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in normative_keywords)


def _map_clauses_to_chunks(clauses: List[Dict], chunks: List[Dict]) -> Dict:
    """
    Map extracted clauses to vector chunks for reference
    
    Args:
        clauses: List of extracted clauses
        chunks: List of vector chunks
        
    Returns:
        Mapping of clause numbers to chunk indices
    """
    mapping = {}
    
    for clause in clauses:
        clause_num = clause['clause_number']
        
        # Find chunks that reference this clause
        matching_chunks = []
        for i, chunk in enumerate(chunks):
            if clause_num in chunk['text']:
                matching_chunks.append(i)
        
        if matching_chunks:
            mapping[clause_num] = {
                'title': clause['clause_title'],
                'chunk_indices': matching_chunks,
                'is_normative': _is_normative_clause(clause['content_preview'])
            }
    
    return mapping


def _store_clause_reference(standard_type: str, clause_mapping: Dict):
    """
    Store clause reference mapping for compliance checking
    
    Args:
        standard_type: Type of standard
        clause_mapping: Mapping of clauses to chunks
    """
    reference_dir = Path("./data/standards_reference")
    reference_dir.mkdir(parents=True, exist_ok=True)
    
    import json
    reference_file = reference_dir / f"{standard_type.replace('/', '_')}_clauses.json"
    
    with open(reference_file, 'w') as f:
        json.dump(clause_mapping, f, indent=2)
    
    print(f"  Stored clause reference: {reference_file}")


def clear_vector_store():
    """Clear all data from vector store (use with caution!)"""
    vector_store = VectorStore()
    confirm = input("Are you sure you want to clear the vector store? (yes/no): ")
    if confirm.lower() == 'yes':
        vector_store.clear_collection()
        print("Vector store cleared")
    else:
        print("Operation cancelled")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "clear":
            clear_vector_store()
        elif sys.argv[1] == "standards":
            ingest_standards_documents()
        elif sys.argv[1] == "all":
            print("Ingesting historical reports...")
            ingest_documents()
            print("\n" + "="*60)
            print("Ingesting standards documents...")
            ingest_standards_documents()
        else:
            # Ingest specific file
            ingest_documents(specific_file=sys.argv[1])
    else:
        # Default: ingest all documents in historical_reports directory
        ingest_documents()