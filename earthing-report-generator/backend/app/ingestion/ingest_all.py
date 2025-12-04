"""
Complete document ingestion pipeline
Processes historical reports and stores them in vector database
"""
from pathlib import Path
from typing import List, Dict, Optional
import os
from tqdm import tqdm

from app.ingestion.pdf_parser import PDFParser
from app.ingestion.docx_parser import DOCXParser
from app.ingestion.chunker import DocumentChunker
from app.rag.embedder import Embedder
from app.rag.vector_store import VectorStore


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
    
    # Get list of files to process
    if specific_file:
        files_to_process = [Path(specific_file)]
    else:
        reports_dir = Path(os.getenv("HISTORICAL_REPORTS_PATH", "./data/historical_reports"))
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
        files_to_process = pdf_files + docx_files
    
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
    
    for file_path in tqdm(files_to_process, desc="Ingesting documents"):
        try:
            print(f"\nProcessing: {file_path.name}")
            
            # Parse document
            if file_path.suffix.lower() == '.pdf':
                parsed_doc = pdf_parser.parse(str(file_path))
            elif file_path.suffix.lower() == '.docx':
                parsed_doc = docx_parser.parse(str(file_path))
            else:
                print(f"Skipping unsupported file type: {file_path.suffix}")
                continue
            
            print(f"  Extracted {len(parsed_doc['full_text'])} characters")
            print(f"  Found {len(parsed_doc.get('sections', {}))} sections")
            print(f"  Metadata: {parsed_doc['metadata']}")
            
            # Chunk document
            chunks = chunker.chunk_document(parsed_doc)
            print(f"  Created {len(chunks)} chunks")
            
            # Generate embeddings
            texts = [chunk["text"] for chunk in chunks]
            print(f"  Generating embeddings...")
            embeddings = embedder.embed_texts(texts, show_progress=False)
            
            # Store in vector database
            vector_store.add_chunks(chunks, embeddings)
            
            total_chunks += len(chunks)
            documents_processed += 1
            
        except Exception as e:
            print(f"Error processing {file_path.name}: {e}")
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


def ingest_standards_documents():
    """
    Ingest standards documents (AS/NZS, IEEE, IEC)
    These are stored with special metadata for compliance checking
    """
    standards_dir = Path(os.getenv("STANDARDS_PATH", "./data/standards"))
    
    if not standards_dir.exists():
        standards_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {standards_dir}")
        print("Add standards PDFs to this directory")
        return
    
    # Process standards similar to reports but with special metadata
    # (Implementation similar to ingest_documents but with standards-specific metadata)
    print("Standards ingestion not yet implemented")
    # TODO: Implement standards-specific ingestion with clause extraction


def clear_vector_store():
    """Clear all data from vector store (use with caution!)"""
    vector_store = VectorStore()
    confirm = input("Are you sure you want to clear the vector store? (yes/no): ")
    if confirm.lower() == 'yes':
        vector_store.clear()
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
        else:
            # Ingest specific file
            ingest_documents(specific_file=sys.argv[1])
    else:
        # Ingest all documents in historical_reports directory
        ingest_documents()