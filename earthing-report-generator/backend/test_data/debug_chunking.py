"""
Debug chunking process
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ingestion.chunker import DocumentChunker
from app.ingestion.pdf_parser import PDFParser
from app.ingestion.docx_parser import DOCXParser
import time
import tracemalloc
import signal

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out!")

def debug_chunk_single_file(file_path: str):
    """Debug chunking for a single file"""
    print(f"\n{'='*60}")
    print(f"Debugging: {file_path}")
    print(f"{'='*60}\n")
    
    # Start memory tracking
    tracemalloc.start()
    
    # Parse file
    print("Step 1: Parsing file...")
    start_time = time.time()
    
    file_path = Path(file_path)
    if file_path.suffix.lower() == '.pdf':
        parser = PDFParser()
        parsed_doc = parser.parse(str(file_path))
    elif file_path.suffix.lower() == '.docx':
        parser = DOCXParser()
        parsed_doc = parser.parse(str(file_path))
    elif file_path.suffix.lower() == '.txt':
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        parsed_doc = {
            'full_text': content,
            'sections': {},
            'metadata': {'source': file_path.name, 'type': 'text'}
        }
    else:
        print(f"❌ Unsupported file type: {file_path.suffix}")
        return
    
    parse_time = time.time() - start_time
    current, peak = tracemalloc.get_traced_memory()
    
    print(f"✅ Parsing complete: {parse_time:.2f}s")
    print(f"   Text length: {len(parsed_doc.get('full_text', ''))} characters")
    print(f"   Sections: {len(parsed_doc.get('sections', {}))} found")
    print(f"   Memory: {current / 1024 / 1024:.1f} MB current, {peak / 1024 / 1024:.1f} MB peak")
    
    # Show first 500 chars of text to inspect
    print(f"\n   First 500 chars of text:")
    print(f"   {repr(parsed_doc['full_text'][:500])}")
    
    # Chunk document
    print("\nStep 2: Chunking document...")
    chunker = DocumentChunker(chunk_size=1000, chunk_overlap=200)
    
    start_time = time.time()
    tracemalloc.reset_peak()
    
    # Set 10 second timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(10)
    
    try:
        # Patch the chunker to add debug output
        original_split = chunker._split_text
        
        def debug_split(text, chunk_size, overlap):
            print(f"   _split_text called: text_len={len(text)}, chunk_size={chunk_size}, overlap={overlap}")
            
            if len(text) <= chunk_size:
                print(f"   → Returning single chunk")
                return [text]
            
            chunks = []
            start = 0
            iteration = 0
            max_iterations = len(text) // (chunk_size - overlap) + 10
            
            import re
            
            while start < len(text):
                iteration += 1
                
                if iteration % 10 == 0:
                    print(f"   → Iteration {iteration}/{max_iterations}, start={start}/{len(text)}")
                
                if iteration > max_iterations:
                    print(f"   ⚠️  INFINITE LOOP DETECTED at iteration {iteration}")
                    print(f"      start={start}, len(text)={len(text)}")
                    break
                
                end = start + chunk_size
                
                # Try to break on sentence boundary
                if end < len(text):
                    sentence_breaks = [m.end() for m in re.finditer(r'\.\s+', text[start:end])]
                    if sentence_breaks:
                        old_end = end
                        end = start + sentence_breaks[-1]
                        if iteration <= 3:
                            print(f"   → Found sentence break: end {old_end} → {end}")
                
                # CRITICAL FIX: Ensure we always advance
                if end <= start:
                    print(f"   ⚠️  WARNING: end ({end}) <= start ({start}), forcing advance")
                    end = start + 1
                
                chunk_text = text[start:end].strip()
                if chunk_text:
                    chunks.append(chunk_text)
                    if iteration <= 3:
                        print(f"   → Chunk {len(chunks)}: length={len(chunk_text)}, starts_with={repr(chunk_text[:50])}")
                
                # Calculate next start
                next_start = end - overlap if end < len(text) else end
                
                # CRITICAL FIX: Ensure minimum advance
                if next_start <= start:
                    print(f"   ⚠️  WARNING: next_start ({next_start}) <= start ({start}), forcing advance")
                    next_start = start + max(1, (chunk_size - overlap) // 2)
                
                start = next_start
            
            print(f"   → Returning {len(chunks)} chunks")
            return chunks
        
        chunker._split_text = debug_split
        
        chunks = chunker.chunk_document(parsed_doc)
        
        signal.alarm(0)  # Cancel alarm
        
        chunk_time = time.time() - start_time
        current, peak = tracemalloc.get_traced_memory()
        
        print(f"✅ Chunking complete: {chunk_time:.2f}s")
        print(f"   Chunks created: {len(chunks)}")
        print(f"   Memory: {current / 1024 / 1024:.1f} MB current, {peak / 1024 / 1024:.1f} MB peak")
        
        # Show sample chunks
        print("\nSample chunks:")
        for i, chunk in enumerate(chunks[:3]):
            print(f"\nChunk {i}:")
            print(f"  Length: {len(chunk['text'])} chars")
            print(f"  Section: {chunk.get('section_type', 'unknown')}")
            print(f"  Preview: {chunk['text'][:100]}...")
        
        # Check for problematic chunks
        print("\nChunk statistics:")
        lengths = [len(c['text']) for c in chunks]
        print(f"  Min length: {min(lengths)}")
        print(f"  Max length: {max(lengths)}")
        print(f"  Avg length: {sum(lengths) / len(lengths):.0f}")
        
        # Check for infinite loops (duplicate chunks)
        unique_texts = set(c['text'][:100] for c in chunks)
        if len(unique_texts) < len(chunks) * 0.8:
            print(f"  ⚠️  WARNING: Many duplicate chunks detected!")
            print(f"     Unique: {len(unique_texts)}, Total: {len(chunks)}")
        
        return chunks
        
    except TimeoutError:
        signal.alarm(0)
        print(f"❌ TIMEOUT: Chunking took more than 10 seconds!")
        print(f"   This confirms an infinite loop bug in the chunker")
        return None
    except Exception as e:
        signal.alarm(0)
        print(f"❌ Chunking failed: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        tracemalloc.stop()


def test_chunking_algorithm():
    """Test the chunking algorithm with known inputs"""
    print("\n" + "="*60)
    print("Testing chunking algorithm")
    print("="*60 + "\n")
    
    chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)
    
    # Test 1: Simple text
    print("Test 1: Simple text (no overlap needed)")
    text = "Short text."
    result = chunker._split_text(text, 100, 20)
    print(f"  Input: {len(text)} chars")
    print(f"  Output: {len(result)} chunks")
    assert len(result) == 1, "Should be 1 chunk"
    print("  ✅ PASS")
    
    # Test 2: Text requiring split
    print("\nTest 2: Text requiring split")
    text = "Sentence one. " * 20  # ~260 chars
    result = chunker._split_text(text, 100, 20)
    print(f"  Input: {len(text)} chars")
    print(f"  Output: {len(result)} chunks")
    print(f"  Chunk lengths: {[len(c) for c in result]}")
    assert len(result) >= 2, "Should be multiple chunks"
    print("  ✅ PASS")
    
    # Test 3: Very long text (potential infinite loop)
    print("\nTest 3: Very long text")
    text = "Word " * 5000  # ~25000 chars
    print(f"  Input: {len(text)} chars")
    
    start = time.time()
    result = chunker._split_text(text, 100, 20)
    elapsed = time.time() - start
    
    print(f"  Output: {len(result)} chunks")
    print(f"  Time: {elapsed:.2f}s")
    
    if elapsed > 2.0:
        print("  ⚠️  WARNING: Chunking is slow!")
    else:
        print("  ✅ PASS")
    
    # Check for infinite loop indicator
    expected_chunks = len(text) // (100 - 20) + 1
    if len(result) > expected_chunks * 2:
        print(f"  ❌ FAIL: Too many chunks! Expected ~{expected_chunks}, got {len(result)}")
        print(f"  This indicates an infinite loop bug!")
    
    # Test 4: Edge case - text with no sentence breaks
    print("\nTest 4: No sentence breaks")
    text = "a" * 500  # Long string with no breaks
    result = chunker._split_text(text, 100, 20)
    print(f"  Input: {len(text)} chars")
    print(f"  Output: {len(result)} chunks")
    print(f"  Chunk lengths: {[len(c) for c in result]}")
    print("  ✅ PASS")


if __name__ == "__main__":
    import sys
    
    # Test chunking algorithm first
    test_chunking_algorithm()
    
    # Then test real file if provided
    if len(sys.argv) > 1:
        debug_chunk_single_file(sys.argv[1])
    else:
        print("\n" + "="*60)
        print("File-specific debugging")
        print("="*60)
        print("\nUsage: python debug_chunking.py <path_to_file>")
        print("\nExample:")
        print("  python debug_chunking.py ../data/historical_reports/sample_33kV_substation_report.txt")

# """
# Debug chunking process
# """
# import sys
# from pathlib import Path
# sys.path.insert(0, str(Path(__file__).parent.parent))

# from app.ingestion.chunker import DocumentChunker
# from app.ingestion.pdf_parser import PDFParser
# from app.ingestion.docx_parser import DOCXParser
# import time
# import tracemalloc

# def debug_chunk_single_file(file_path: str):
#     """Debug chunking for a single file"""
#     print(f"\n{'='*60}")
#     print(f"Debugging: {file_path}")
#     print(f"{'='*60}\n")
    
#     # Start memory tracking
#     tracemalloc.start()
    
#     # Parse file
#     print("Step 1: Parsing file...")
#     start_time = time.time()
    
#     file_path = Path(file_path)
#     if file_path.suffix.lower() == '.pdf':
#         parser = PDFParser()
#         parsed_doc = parser.parse(str(file_path))
#     elif file_path.suffix.lower() == '.docx':
#         parser = DOCXParser()
#         parsed_doc = parser.parse(str(file_path))
#     elif file_path.suffix.lower() == '.txt':
#         with open(file_path, 'r', encoding='utf-8') as f:
#             content = f.read()
#         parsed_doc = {
#             'full_text': content,
#             'sections': {},
#             'metadata': {'source': file_path.name, 'type': 'text'}
#         }
#     else:
#         print(f"❌ Unsupported file type: {file_path.suffix}")
#         return
    
#     parse_time = time.time() - start_time
#     current, peak = tracemalloc.get_traced_memory()
    
#     print(f"✅ Parsing complete: {parse_time:.2f}s")
#     print(f"   Text length: {len(parsed_doc.get('full_text', ''))} characters")
#     print(f"   Sections: {len(parsed_doc.get('sections', {}))} found")
#     print(f"   Memory: {current / 1024 / 1024:.1f} MB current, {peak / 1024 / 1024:.1f} MB peak")
    
#     # Chunk document
#     print("\nStep 2: Chunking document...")
#     chunker = DocumentChunker(chunk_size=1000, chunk_overlap=200)
    
#     start_time = time.time()
#     tracemalloc.reset_peak()
    
#     try:
#         chunks = chunker.chunk_document(parsed_doc)
        
#         chunk_time = time.time() - start_time
#         current, peak = tracemalloc.get_traced_memory()
        
#         print(f"✅ Chunking complete: {chunk_time:.2f}s")
#         print(f"   Chunks created: {len(chunks)}")
#         print(f"   Memory: {current / 1024 / 1024:.1f} MB current, {peak / 1024 / 1024:.1f} MB peak")
        
#         # Show sample chunks
#         print("\nSample chunks:")
#         for i, chunk in enumerate(chunks[:3]):
#             print(f"\nChunk {i}:")
#             print(f"  Length: {len(chunk['text'])} chars")
#             print(f"  Section: {chunk.get('section_type', 'unknown')}")
#             print(f"  Preview: {chunk['text'][:100]}...")
        
#         # Check for problematic chunks
#         print("\nChunk statistics:")
#         lengths = [len(c['text']) for c in chunks]
#         print(f"  Min length: {min(lengths)}")
#         print(f"  Max length: {max(lengths)}")
#         print(f"  Avg length: {sum(lengths) / len(lengths):.0f}")
        
#         # Check for infinite loops (duplicate chunks)
#         unique_texts = set(c['text'][:100] for c in chunks)
#         if len(unique_texts) < len(chunks) * 0.8:
#             print(f"  ⚠️  WARNING: Many duplicate chunks detected!")
#             print(f"     Unique: {len(unique_texts)}, Total: {len(chunks)}")
        
#         return chunks
        
#     except Exception as e:
#         print(f"❌ Chunking failed: {e}")
#         traceback.print_exc()
#         return None
#     finally:
#         tracemalloc.stop()


# def test_chunking_algorithm():
#     """Test the chunking algorithm with known inputs"""
#     print("\n" + "="*60)
#     print("Testing chunking algorithm")
#     print("="*60 + "\n")
    
#     chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)
    
#     # Test 1: Simple text
#     print("Test 1: Simple text (no overlap needed)")
#     text = "Short text."
#     result = chunker._split_text(text, 100, 20)
#     print(f"  Input: {len(text)} chars")
#     print(f"  Output: {len(result)} chunks")
#     assert len(result) == 1, "Should be 1 chunk"
#     print("  ✅ PASS")
    
#     # Test 2: Text requiring split
#     print("\nTest 2: Text requiring split")
#     text = "Sentence one. " * 20  # ~260 chars
#     result = chunker._split_text(text, 100, 20)
#     print(f"  Input: {len(text)} chars")
#     print(f"  Output: {len(result)} chunks")
#     print(f"  Chunk lengths: {[len(c) for c in result]}")
#     assert len(result) >= 2, "Should be multiple chunks"
#     print("  ✅ PASS")
    
#     # Test 3: Very long text (potential infinite loop)
#     print("\nTest 3: Very long text")
#     text = "Word " * 5000  # ~25000 chars
#     print(f"  Input: {len(text)} chars")
    
#     start = time.time()
#     result = chunker._split_text(text, 100, 20)
#     elapsed = time.time() - start
    
#     print(f"  Output: {len(result)} chunks")
#     print(f"  Time: {elapsed:.2f}s")
    
#     if elapsed > 2.0:
#         print("  ⚠️  WARNING: Chunking is slow!")
#     else:
#         print("  ✅ PASS")
    
#     # Check for infinite loop indicator
#     expected_chunks = len(text) // (100 - 20) + 1
#     if len(result) > expected_chunks * 2:
#         print(f"  ❌ FAIL: Too many chunks! Expected ~{expected_chunks}, got {len(result)}")
#         print(f"  This indicates an infinite loop bug!")
    
#     # Test 4: Edge case - text with no sentence breaks
#     print("\nTest 4: No sentence breaks")
#     text = "a" * 500  # Long string with no breaks
#     result = chunker._split_text(text, 100, 20)
#     print(f"  Input: {len(text)} chars")
#     print(f"  Output: {len(result)} chunks")
#     print(f"  Chunk lengths: {[len(c) for c in result]}")
#     print("  ✅ PASS")


# if __name__ == "__main__":
#     import sys
    
#     # Test chunking algorithm first
#     test_chunking_algorithm()
    
#     # Then test real file if provided
#     if len(sys.argv) > 1:
#         debug_chunk_single_file(sys.argv[1])
#     else:
#         print("\n" + "="*60)
#         print("File-specific debugging")
#         print("="*60)
#         print("\nUsage: python debug_chunking.py <path_to_file>")
#         print("\nExample:")
#         print("  python debug_chunking.py data/historical_reports/sample_33kV_substation_report.txt")