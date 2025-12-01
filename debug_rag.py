
import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.services.rag_service import rag_service
from app.core.database import init_db

async def check_rag(topic):
    print(f"🔍 Checking RAG for topic: '{topic}'")
    
    # 1. Check collection stats if possible (rag_service doesn't expose this directly, but we can try a broad query)
    
    # 2. Try retrieval
    query = f"{topic} fundamentals concepts"
    print(f"   Querying: '{query}'")
    
    results = rag_service.retrieve(query, top_k=5)
    
    if results:
        print(f"✅ Found {len(results)} chunks")
        for i, res in enumerate(results):
            meta = res.get("metadata", {})
            print(f"   [{i+1}] Source: {meta.get('source', 'unknown')} | Score: {res.get('score', 'N/A')}")
            print(f"       Preview: {res.get('text', '')[:100]}...")
    else:
        print("❌ No results found. RAG is returning empty.")
        print("   Possible reasons:")
        print("   1. No PDFs processed for this topic.")
        print("   2. ChromaDB persistence issue.")
        print("   3. Embedding model mismatch.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        topic = sys.argv[1]
    else:
        topic = "Python"
        
    asyncio.run(check_rag(topic))
