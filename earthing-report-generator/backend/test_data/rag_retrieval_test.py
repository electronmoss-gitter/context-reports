"""Test RAG retrieval"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.rag.vector_store import VectorStore
from app.rag.retriever import Retriever


def test_retrieval():
    vector_store = VectorStore()
    
    # Check if vector store has data
    count = vector_store.get_collection_count()
    print(f"Vector store contains: {count} chunks\n")
    
    if count == 0:
        print("❌ Vector store is empty! Run ingestion first:")
        print("   python -m app.ingestion.ingest_all")
        return
    
    retriever = Retriever(vector_store)
    
    queries = [
        "touch potential calculations",
        "soil resistivity measurement",
        "grid conductor sizing",
        "step voltage requirements"
    ]
    
    print("=" * 60)
    print("Testing RAG Retrieval")
    print("=" * 60 + "\n")
    
    for query_num, query in enumerate(queries, 1):
        print(f"\nQuery {query_num}/{len(queries)}: {query}")
        print("-" * 60)
        sys.stdout.flush()
        
        try:
            results = retriever.retrieve(query, n_results=3)
            
            # Debug: show what we got
            print(f"   Retrieved: {len(results)} results (type: {type(results)})")
            sys.stdout.flush()
            
            # Check if results is empty list or None
            if results is None or len(results) == 0:
                print("   ⚠️  No results found")
                continue
            
            for i, result in enumerate(results, 1):
                similarity = result.get('similarity', 0)
                content = result.get('content', '')
                metadata = result.get('metadata', {})
                
                print(f"\n{i}. Similarity: {similarity:.3f}")
                print(f"   Source: {metadata.get('source', 'unknown')}")
                print(f"   Section: {metadata.get('section_type', 'unknown')[:30]}")
                print(f"   Preview: {content[:150]}...")
                sys.stdout.flush()
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            sys.stdout.flush()
    
    print("\n" + "=" * 60)


def test_direct_query():
    """Test by directly querying vector store to see raw results"""
    print("\n" + "=" * 60)
    print("Direct Vector Store Test")
    print("=" * 60 + "\n")
    
    vector_store = VectorStore()
    
    queries = [
        "touch potential calculations",
        "soil resistivity measurement", 
        "grid conductor sizing",
        "step voltage requirements"
    ]
    
    for query in queries:
        print(f"\nDirect query: {query}")
        print("-" * 60)
        sys.stdout.flush()
        
        try:
            raw_results = vector_store.query(query, n_results=3)
            
            documents = raw_results.get('documents', [])
            distances = raw_results.get('distances', [])
            metadatas = raw_results.get('metadatas', [])
            
            print(f"  Documents returned: {len(documents)}")
            print(f"  Distances: {[f'{d:.3f}' for d in distances]}")
            
            for i, doc in enumerate(documents):
                similarity = 1.0 - distances[i]  # Convert distance to similarity
                print(f"\n  {i+1}. Similarity: {similarity:.3f}")
                print(f"     Preview: {doc[:100]}...")
            
            sys.stdout.flush()
        
        except Exception as e:
            print(f"  ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            sys.stdout.flush()


if __name__ == "__main__":
    test_retrieval()
    test_direct_query()

# """Test RAG retrieval"""
# from app.rag.vector_store import VectorStore
# from app.rag.retriever import Retriever

# def test_retrieval():
#     vector_store = VectorStore()
#     retriever = Retriever(vector_store)
    
#     queries = [
#         "touch potential calculations",
#         "soil resistivity measurement",
#         "grid conductor sizing",
#         "step voltage requirements"
#     ]
    
#     print("\n" + "="*60)
#     print("Testing RAG Retrieval")
#     print("="*60 + "\n")
    
#     for query in queries:
#         print(f"\nQuery: {query}")
#         print("-" * 60)
        
#         results = retriever.retrieve(query, n_results=3)
        
#         for i, result in enumerate(results, 1):
#             print(f"\n{i}. Similarity: {result['similarity']:.3f}")
#             print(f"   Source: {result['metadata'].get('source', 'unknown')}")
#             print(f"   Preview: {result['content'][:150]}...")

# if __name__ == "__main__":
#     test_retrieval()