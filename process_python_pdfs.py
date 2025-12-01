
import asyncio
import sys
import os
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.services.course_discovery_service import course_discovery_service

async def process_python():
    print("🔄 Processing Python PDFs...")
    result = await course_discovery_service.process_course_pdfs("python")
    print(f"✅ Done!")
    print(f"   Processed: {result['processed_files']}/{result['total_files']} files")
    print(f"   Total chunks: {result['total_chunks']}")
    if result['failed_files']:
        print(f"   Failed: {result['failed_files']}")

if __name__ == "__main__":
    asyncio.run(process_python())
