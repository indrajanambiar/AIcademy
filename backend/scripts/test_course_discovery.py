"""
Test script for Course Discovery functionality.
Run this to verify the course discovery system is working correctly.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.course_discovery_service import course_discovery_service
from app.services.rag_service import rag_service
from app.core.logging import get_logger

logger = get_logger(__name__)


async def test_discovery():
    """Test course discovery."""
    print("\n" + "="*60)
    print("Testing Course Discovery")
    print("="*60 + "\n")
    
    courses = course_discovery_service.discover_courses()
    
    if not courses:
        print("❌ No courses found!")
        print("   Make sure you have PDF folders in backend/pdfs/")
        return False
    
    print(f"✅ Found {len(courses)} courses:\n")
    for course in courses:
        print(f"  📚 {course['display_name']}")
        print(f"     - PDFs: {course['pdf_count']}")
        print(f"     - Size: {course['total_size_mb']:.1f} MB")
        print(f"     - Path: {course['path']}")
        print()
    
    return True


async def test_processing():
    """Test PDF processing for a single course."""
    print("\n" + "="*60)
    print("Testing PDF Processing")
    print("="*60 + "\n")
    
    courses = course_discovery_service.discover_courses()
    
    if not courses:
        print("❌ No courses to process")
        return False
    
    # Process the first course with limited pages
    test_course = courses[0]
    print(f"Processing course: {test_course['display_name']}")
    print(f"Limiting to 1 PDF, 10 pages for testing...\n")
    
    try:
        result = await course_discovery_service.process_course_pdfs(
            course_name=test_course['name'],
            max_pdfs=1,
            max_pages_per_pdf=10
        )
        
        print("✅ Processing completed:")
        print(f"   - Processed: {result['processed_files']}/{result['total_files']} files")
        print(f"   - Total chunks: {result['total_chunks']}")
        
        if result['failed_files']:
            print(f"   - Failed files: {result['failed_files']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Processing failed: {e}")
        return False


async def test_rag_retrieval():
    """Test RAG retrieval."""
    print("\n" + "="*60)
    print("Testing RAG Retrieval")
    print("="*60 + "\n")
    
    # Get collection stats
    stats = rag_service.get_collection_stats()
    print(f"ChromaDB Stats:")
    print(f"  - Documents: {stats['document_count']}")
    print(f"  - Collection: {stats['collection_name']}")
    print(f"  - Embedding Model: {stats['embedding_model']}\n")
    
    if stats['document_count'] == 0:
        print("⚠️  No documents in RAG. Run test_processing first.")
        return False
    
    # Test retrieval
    test_query = "python programming basics"
    print(f"Testing query: '{test_query}'")
    
    results = rag_service.retrieve(test_query, top_k=3)
    
    if results:
        print(f"✅ Retrieved {len(results)} results:\n")
        for i, doc in enumerate(results, 1):
            print(f"  {i}. Source: {doc['metadata'].get('source', 'unknown')}")
            print(f"     Distance: {doc['distance']:.4f}")
            print(f"     Preview: {doc['text'][:100]}...")
            print()
        return True
    else:
        print("❌ No results retrieved")
        return False


async def test_material_generation():
    """Test material generation."""
    print("\n" + "="*60)
    print("Testing Material Generation")
    print("="*60 + "\n")
    
    courses = course_discovery_service.discover_courses()
    
    if not courses:
        print("❌ No courses available")
        return False
    
    test_course = courses[0]
    print(f"Generating materials for: {test_course['display_name']}")
    print("This may take 1-2 minutes...\n")
    
    try:
        materials = await course_discovery_service.generate_all_materials(
            course_name=test_course['name'],
            skill_level='beginner',
            duration_days=7  # Shorter for testing
        )
        
        if 'error' in materials:
            print(f"❌ Generation failed: {materials['error']}")
            return False
        
        print("✅ Materials generated successfully:\n")
        for material_type, content in materials.items():
            if isinstance(content, dict):
                print(f"  ✓ {material_type}: {len(str(content))} chars (JSON)")
            else:
                print(f"  ✓ {material_type}: {len(content)} chars (Text)")
        
        # Show a sample
        print("\n📝 Sample Syllabus:")
        if 'syllabus' in materials and isinstance(materials['syllabus'], dict):
            print(f"   Title: {materials['syllabus'].get('title', 'N/A')}")
            print(f"   Modules: {len(materials['syllabus'].get('modules', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("🎓 COURSE DISCOVERY SYSTEM TEST SUITE")
    print("="*60)
    
    results = {
        "Discovery": await test_discovery(),
        "Processing": await test_processing(),
        "RAG Retrieval": await test_rag_retrieval(),
        "Material Generation": await test_material_generation(),
    }
    
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60 + "\n")
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! System is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")


if __name__ == "__main__":
    asyncio.run(main())
