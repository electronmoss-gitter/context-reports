"""Verify all dependencies are correctly installed"""
import sys

def check_imports():
    """Check all required imports"""
    errors = []
    
    packages = [
        ('fastapi', 'FastAPI'),
        ('uvicorn', 'Uvicorn'),
        ('pydantic', 'Pydantic'),
        ('anthropic', 'Anthropic'),
        ('chromadb', 'ChromaDB'),
        ('sentence_transformers', 'Sentence Transformers'),
        ('numpy', 'NumPy'),
        ('pandas', 'Pandas'),
        ('scipy', 'SciPy'),
        ('docx', 'python-docx'),
        ('PyPDF2', 'PyPDF2'),
        ('pdfplumber', 'pdfplumber'),
    ]
    
    print("Checking dependencies...\n")
    
    for module, name in packages:
        try:
            mod = __import__(module)
            version = getattr(mod, '__version__', 'unknown')
            print(f"✓ {name:25} {version}")
        except ImportError as e:
            error = f"✗ {name:25} NOT INSTALLED"
            print(error)
            errors.append((name, str(e)))
    
    # Check NumPy version specifically
    try:
        import numpy as np
        version = tuple(map(int, np.__version__.split('.')[:2]))
        if version >= (2, 0):
            errors.append(('NumPy', f'Version {np.__version__} may cause compatibility issues. Recommended: 1.24.4'))
            print(f"\n⚠ Warning: NumPy {np.__version__} detected. Recommended version: 1.24.4")
    except:
        pass
    
    if errors:
        print(f"\n❌ Found {len(errors)} issue(s):")
        for pkg, err in errors:
            print(f"   - {pkg}: {err}")
        return False
    else:
        print(f"\n✅ All dependencies installed correctly!")
        return True

if __name__ == "__main__":
    success = check_imports()
    sys.exit(0 if success else 1)