#!/usr/bin/env python3
"""
Verify all required files are present in the project
"""
from pathlib import Path
import sys

def check_files():
    """Check if all required files exist"""
    
    base_path = Path(__file__).parent

    print(f"Checking files in project at: {base_path}\n")
    
    required_files = {
        "Documentation": [
            "README.md",
            "MVP_STATUS.md",
            "GETTING_STARTED.md",
            "quickstart.py",
        ],
        "Backend Core": [
            "backend/requirements.txt",
            "backend/.env.example",
            "backend/app/__init__.py",
            "backend/app/main.py",
        ],
        "Ingestion": [
            "backend/app/ingestion/__init__.py",
            "backend/app/ingestion/pdf_parser.py",
            "backend/app/ingestion/docx_parser.py",
            "backend/app/ingestion/chunker.py",
            "backend/app/ingestion/ingest_all.py",
        ],
        "RAG System": [
            "backend/app/rag/__init__.py",
            "backend/app/rag/embedder.py",
            "backend/app/rag/vector_store.py",
            "backend/app/rag/retriever.py",
        ],
        "Generation": [
            "backend/app/generation/__init__.py",
            "backend/app/generation/validator.py",
        ],
        "Docker (Optional)": [
            "backend/Dockerfile",
            "docker-compose.yml",
        ]
    }
    
    print("="*60)
    print("FILE VERIFICATION")
    print("="*60 + "\n")
    
    all_present = True
    
    for category, files in required_files.items():
        print(f"\n{category}:")
        category_ok = True
        
        for file_path in files:
            full_path = base_path / file_path
            exists = full_path.exists()
            
            if exists:
                size = full_path.stat().st_size
                status = f"✅ {file_path} ({size:,} bytes)"
            else:
                status = f"❌ {file_path} - MISSING!"
                category_ok = False
                all_present = False
            
            print(f"  {status}")
        
        if category_ok:
            print(f"  → All {category} files present")
    
    print("\n" + "="*60)
    if all_present:
        print("✅ ALL FILES PRESENT - Project is complete!")
        print("="*60 + "\n")
        print("Next steps:")
        print("1. cd backend")
        print("2. pip install -r requirements.txt")
        print("3. cp .env.example .env")
        print("4. Add your ANTHROPIC_API_KEY to .env")
        print("5. Run: python ../quickstart.py")
        return 0
    else:
        print("❌ SOME FILES MISSING - See above")
        print("="*60 + "\n")
        return 1

if __name__ == "__main__":
    sys.exit(check_files())