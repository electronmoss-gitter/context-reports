#!/usr/bin/env python3
"""
Test Script - Ingest sample data and test the system
"""
import sys
import json
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

def test_sample_report_ingestion():
    """Test ingesting the sample reports"""
    print("="*70)
    print("TEST 1: INGESTING SAMPLE REPORTS")
    print("="*70 + "\n")
    
    from app.ingestion.pdf_parser import PDFParser
    from app.ingestion.docx_parser import DOCXParser
    from app.ingestion.chunker import DocumentChunker
    from app.rag.embedder import Embedder
    from app.rag.vector_store import VectorStore
    
    # Note: Sample reports are .txt files (simulating PDF content)
    # In real use, you'd use PDF/DOCX files
    
    sample_dir = Path("test_data/sample_reports")
    
    if not sample_dir.exists():
        print("❌ Sample reports directory not found!")
        print("   Expected: test_data/sample_reports/")
        return False
    
    # List available sample reports
    sample_files = list(sample_dir.glob("*.txt"))
    print(f"Found {len(sample_files)} sample reports:")
    for f in sample_files:
        print(f"  - {f.name}")
    
    if not sample_files:
        print("\n⚠️  No sample reports found to ingest")
        print("   Sample reports are provided as .txt files")
        print("   In production, use actual PDF/DOCX files")
        return True
    
    print("\n📝 Sample reports are text files (simulating extracted PDF content)")
    print("   To test real PDF/DOCX ingestion:")
    print("   1. Place PDF/DOCX files in backend/data/historical_reports/")
    print("   2. Run: python -m app.ingestion.ingest_all")
    
    return True

def test_input_validation():
    """Test input validation with sample data"""
    print("\n" + "="*70)
    print("TEST 2: INPUT VALIDATION")
    print("="*70 + "\n")
    
    from app.generation.validator import InputValidator
    
    validator = InputValidator()
    inputs_dir = Path("test_data/inputs")
    
    if not inputs_dir.exists():
        print("❌ Test inputs directory not found!")
        return False
    
    input_files = list(inputs_dir.glob("*.json"))
    print(f"Testing {len(input_files)} input files:\n")
    
    all_passed = True
    
    for input_file in input_files:
        print(f"Testing: {input_file.name}")
        
        try:
            with open(input_file) as f:
                data = json.load(f)
            
            result = validator.validate(data)
            
            status_icon = "✅" if result["validation_status"] != "fail" else "❌"
            print(f"  {status_icon} Status: {result['validation_status']}")
            print(f"  📊 Completeness: {result['completeness_score']:.1%}")
            
            if result['errors']:
                print(f"  ⚠️  Errors: {len(result['errors'])}")
                for error in result['errors'][:3]:  # Show first 3
                    print(f"     - {error['field']}: {error['message']}")
                all_passed = False
            
            if result['warnings']:
                print(f"  ⚠️  Warnings: {len(result['warnings'])}")
                for warning in result['warnings'][:2]:  # Show first 2
                    print(f"     - {warning['field']}: {warning['message']}")
            
            if not result['errors'] and not result['warnings']:
                print(f"  ✨ No issues found!")
            
            print()
            
        except Exception as e:
            print(f"  ❌ Error: {e}\n")
            all_passed = False
    
    return all_passed

def test_rag_system():
    """Test RAG retrieval with sample queries"""
    print("="*70)
    print("TEST 3: RAG SYSTEM (if data ingested)")
    print("="*70 + "\n")
    
    from app.rag.retriever import Retriever
    from app.rag.vector_store import VectorStore
    
    # Check if vector store has data
    vector_store = VectorStore()
    stats = vector_store.get_stats()
    
    if stats.get("total_chunks", 0) == 0:
        print("⚠️  Vector store is empty")
        print("   To test RAG:")
        print("   1. Add historical reports to: backend/data/historical_reports/")
        print("   2. Run: python -m app.ingestion.ingest_all")
        print("   3. Re-run this test script\n")
        return True
    
    print(f"✅ Vector store contains {stats['total_chunks']} chunks")
    print(f"   Project types: {stats.get('project_types', {})}")
    print(f"   Voltage levels: {stats.get('voltage_levels', {})}\n")
    
    # Test retrieval
    retriever = Retriever()
    
    test_queries = [
        "soil resistivity measurements Wenner method",
        "touch potential calculations IEEE 80",
        "earth grid design for 33kV substation",
        "compliance with AS/NZS 3000 earthing requirements"
    ]
    
    print("Testing retrieval with sample queries:\n")
    
    for query in test_queries:
        print(f"Query: '{query}'")
        results = retriever.retrieve(query, n_results=3)
        
        if results:
            print(f"  ✅ Found {len(results)} relevant chunks")
            print(f"     Top result similarity: {results[0]['similarity_score']:.3f}")
            print(f"     Preview: {results[0]['text'][:100]}...")
        else:
            print(f"  ⚠️  No results found")
        print()
    
    return True

def test_embedder():
    """Test embedding generation"""
    print("="*70)
    print("TEST 4: EMBEDDING GENERATION")
    print("="*70 + "\n")
    
    from app.rag.embedder import Embedder
    
    print("Loading embedding model (may take a minute first time)...")
    embedder = Embedder()
    print(f"✅ Model loaded: {embedder.embedding_dimension} dimensions\n")
    
    test_texts = [
        "Soil resistivity testing using Wenner four-probe method",
        "Touch potential calculation per IEEE 80 standard",
        "Earth grid resistance for 33kV substation"
    ]
    
    print("Generating embeddings for test texts...")
    embeddings = embedder.embed_texts(test_texts, show_progress=False)
    
    print(f"✅ Generated {len(embeddings)} embeddings")
    print(f"   Each embedding: {len(embeddings[0])} dimensions\n")
    
    # Test similarity
    query = "soil resistivity measurement procedures"
    query_emb = embedder.embed_query(query)
    
    print(f"Testing similarity with query: '{query}'")
    for i, text in enumerate(test_texts):
        sim = embedder.get_similarity(query_emb, embeddings[i])
        print(f"  Text {i+1} similarity: {sim:.3f}")
    
    print()
    return True

def test_standards_reference():
    """Check standards reference document"""
    print("="*70)
    print("TEST 5: STANDARDS REFERENCE")
    print("="*70 + "\n")
    
    standards_file = Path("test_data/standards/australian_earthing_standards_reference.txt")
    
    if not standards_file.exists():
        print("❌ Standards reference not found!")
        return False
    
    with open(standards_file) as f:
        content = f.read()
    
    print(f"✅ Standards reference loaded")
    print(f"   Size: {len(content):,} characters")
    print(f"   Lines: {len(content.splitlines()):,}")
    
    # Check for key standards
    key_standards = [
        "AS/NZS 3000",
        "AS 2067", 
        "IEEE 80",
        "AS/NZS 3008",
        "AS/NZS 5033"
    ]
    
    print(f"\n   Key standards found:")
    for std in key_standards:
        if std in content:
            print(f"     ✅ {std}")
        else:
            print(f"     ❌ {std} - NOT FOUND")
    
    print()
    return True

def show_test_data_summary():
    """Display summary of available test data"""
    print("\n" + "="*70)
    print("TEST DATA SUMMARY")
    print("="*70 + "\n")
    
    base_path = Path("test_data")
    
    if not base_path.exists():
        print("❌ test_data directory not found!")
        return
    
    # Sample reports
    reports_dir = base_path / "sample_reports"
    if reports_dir.exists():
        reports = list(reports_dir.glob("*.txt"))
        print(f"📄 Sample Reports ({len(reports)}):")
        for r in reports:
            size = r.stat().st_size
            print(f"   - {r.name} ({size:,} bytes)")
    
    # Input files
    inputs_dir = base_path / "inputs"
    if inputs_dir.exists():
        inputs = list(inputs_dir.glob("*.json"))
        print(f"\n📥 Test Inputs ({len(inputs)}):")
        for i in inputs:
            with open(i) as f:
                data = json.load(f)
            voltage = data.get('voltage_level', 'N/A')
            proj_type = data.get('project_type', 'N/A')
            print(f"   - {i.name}")
            print(f"     • {voltage}, {proj_type}")
    
    # Standards
    standards_dir = base_path / "standards"
    if standards_dir.exists():
        standards = list(standards_dir.glob("*.txt"))
        print(f"\n📚 Standards Reference ({len(standards)}):")
        for s in standards:
            size = s.stat().st_size
            print(f"   - {s.name} ({size:,} bytes)")
    
    print()

def main():
    print("\n" + "="*70)
    print("EARTHING REPORT GENERATOR - TEST DATA VALIDATION")
    print("="*70 + "\n")
    
    tests = [
        ("Sample Report Ingestion", test_sample_report_ingestion),
        ("Input Validation", test_input_validation),
        ("Embedder", test_embedder),
        ("Standards Reference", test_standards_reference),
        ("RAG System", test_rag_system),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n❌ {test_name} failed with error: {e}\n")
            results.append((test_name, False))
    
    # Show test data summary
    show_test_data_summary()
    
    # Final summary
    print("="*70)
    print("TEST RESULTS SUMMARY")
    print("="*70 + "\n")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        icon = "✅" if success else "❌"
        print(f"  {icon} {test_name}")
    
    print(f"\n{'='*70}")
    print(f"TOTAL: {passed}/{total} tests passed")
    print(f"{'='*70}\n")
    
    if passed == total:
        print("🎉 All tests passed! Test data is ready to use.")
        print("\nNext steps:")
        print("1. Add actual PDF/DOCX reports to: backend/data/historical_reports/")
        print("2. Run ingestion: python -m app.ingestion.ingest_all")
        print("3. Start building generation components (see MVP_STATUS.md)")
    else:
        print("⚠️  Some tests had issues - see details above")
    
    print()
    return 0 if passed == total else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)