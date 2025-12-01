
import sys
import os
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.services.rag_service import rag_service

print("🔧 Clearing ChromaDB collection...")
try:
    rag_service.clear_collection()
    print("✅ ChromaDB collection cleared successfully")
    print("📊 Collection stats:", rag_service.get_collection_stats())
except Exception as e:
    print(f"❌ Error: {e}")
