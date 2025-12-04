#!/usr/bin/env python3
"""
Quick Start Script - Test the earthing report generator MVP
"""
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

def check_environment():
    """Check if environment is set up correctly"""
    print("Checking environment...")
    
    # Check for .env file
    env_file = backend_path / ".env"
    if not env_file.exists():
        print("❌ .env file not found!")
        print("   Copy .env.example to .env and add your Anthropic API key")
        return False
    
    # Check for API key
    from dotenv import load_dotenv
    load_dotenv(env_file)
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        print("❌ Anthropic API key not set!")
        print("   Edit .env and add your API key: ANTHROPIC_API_KEY=sk-ant-...")
        return False
    
    print("✅ Environment configured")
    return True

def check_vector_store():
    """Check if vector store has data"""
    print("\nChecking vector store...")
    
    from app.rag.vector_store import VectorStore
    vector_store = VectorStore()
    stats = vector_store.get_stats()
    
    chunk_count = stats.get("total_chunks", 0)
    if chunk_count == 0:
        print(f"❌ Vector store is empty (0 chunks)")
        print("   Add reports to backend/data/historical_reports/")
        print("   Then run: python -m app.ingestion.ingest_all")
        return False
    
    print(f"✅ Vector store ready ({chunk_count} chunks)")
    print(f"   Project types: {stats.get('project_types', {})}")
    print(f"   Voltage levels: {stats.get('voltage_levels', {})}")
    return True

def test_retrieval():
    """Test RAG retrieval"""
    print("\nTesting RAG retrieval...")
    
    from app.rag.retriever import Retriever
    retriever = Retriever()
    
    test_query = "touch potential calculations for substation"
    results = retriever.retrieve(test_query, n_results=3)
    
    if not results:
        print("❌ No results found")
        return False
    
    print(f"✅ Found {len(results)} relevant chunks")
    print(f"\nTop result (similarity: {results[0]['similarity_score']:.3f}):")
    print(f"   {results[0]['text'][:150]}...")
    return True

def test_validation():
    """Test input validation"""
    print("\nTesting input validation...")
    
    from app.generation.validator import InputValidator
    import json
    
    # Load example input
    example_file = Path(__file__).parent / "examples" / "input_data.json"
    if not example_file.exists():
        print("❌ Example input file not found")
        return False
    
    with open(example_file) as f:
        test_data = json.load(f)
    
    validator = InputValidator()
    result = validator.validate(test_data)
    
    print(f"✅ Validation status: {result['validation_status']}")
    print(f"   Completeness: {result['completeness_score']:.1%}")
    
    if result['errors']:
        print(f"   Errors: {len(result['errors'])}")
    if result['warnings']:
        print(f"   Warnings: {len(result['warnings'])}")
    
    return True

def show_next_steps():
    """Show what to do next"""
    print("\n" + "="*60)
    print("NEXT STEPS TO COMPLETE MVP:")
    print("="*60)
    print("\n1. BUILD CALCULATION ENGINE")
    print("   Create: backend/app/calculations/earthing_calculations.py")
    print("   Implement: grid resistance, touch/step potentials, conductor sizing")
    
    print("\n2. BUILD LLM INTEGRATION")
    print("   Create: backend/app/generation/llm_client.py")
    print("   Create: backend/app/generation/prompt_builder.py")
    print("   Test: Generate one section (executive summary)")
    
    print("\n3. BUILD REPORT GENERATOR")
    print("   Create: backend/app/generation/report_generator.py")
    print("   Orchestrate: validation → calculations → RAG → LLM → output")
    
    print("\n4. BUILD DOCX FORMATTER")
    print("   Create: backend/app/formatting/docx_builder.py")
    print("   Format: Generated text → professional DOCX report")
    
    print("\n5. TEST END-TO-END")
    print("   Run: curl -X POST http://localhost:8000/api/v1/generate-report \\")
    print("        -H 'Content-Type: application/json' \\")
    print("        -d @examples/input_data.json")
    
    print("\nSee MVP_STATUS.md for detailed implementation guide!")
    print("="*60 + "\n")

def main():
    print("="*60)
    print("EARTHING REPORT GENERATOR - MVP QUICK START")
    print("="*60 + "\n")
    
    # Run checks
    checks = [
        check_environment(),
        check_vector_store(),
        test_retrieval(),
        test_validation()
    ]
    
    # Show status
    passed = sum(checks)
    total = len(checks)
    
    print("\n" + "="*60)
    print(f"STATUS: {passed}/{total} checks passed")
    print("="*60 + "\n")
    
    if passed == total:
        print("✅ All systems ready! Core infrastructure is working.")
        print("\nYou can now start building the report generation components.")
    else:
        print("⚠️  Some components need attention (see above)")
        print("\nFix the issues above before proceeding.")
    
    show_next_steps()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you've installed dependencies:")
        print("  cd backend && pip install -r requirements.txt")
        sys.exit(1)