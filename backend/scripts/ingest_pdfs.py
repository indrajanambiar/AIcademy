import os
import sys
from pathlib import Path
import PyPDF2

# Add backend to path so we can import app modules
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.services.rag_service import rag_service
from app.core.logging import get_logger

logger = get_logger(__name__)

PDF_DIR = Path(__file__).parent.parent / "pdfs"

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        logger.error(f"Failed to read {pdf_path}: {e}")
    return text

def ingest_pdfs():
    if not PDF_DIR.exists():
        logger.error(f"PDF directory not found: {PDF_DIR}")
        return

    logger.info(f"Scanning for PDFs in {PDF_DIR}")
    total_files = 0
    total_chunks = 0
    
    for root, dirs, files in os.walk(PDF_DIR):
        for file in files:
            if file.lower().endswith('.pdf'):
                file_path = Path(root) / file
                # Topic is the parent directory name, unless it's the root pdfs dir
                topic = file_path.parent.name
                if file_path.parent == PDF_DIR:
                    topic = "general"
                
                logger.info(f"Processing {file} (Topic: {topic})")
                
                text = extract_text_from_pdf(file_path)
                if not text.strip():
                    logger.warning(f"No text found in {file}")
                    continue
                
                # Simple chunking
                chunk_size = 1000
                overlap = 200
                chunks = []
                metadatas = []
                
                for i in range(0, len(text), chunk_size - overlap):
                    chunk = text[i:i + chunk_size]
                    if len(chunk) < 50: # Skip very small chunks
                        continue
                    chunks.append(chunk)
                    metadatas.append({
                        "source": file,
                        "topic": topic,
                        "filename": file
                    })
                
                if chunks:
                    rag_service.add_documents(chunks, metadatas)
                    total_files += 1
                    total_chunks += len(chunks)
                    logger.info(f"Added {len(chunks)} chunks from {file}")

    logger.info(f"Ingestion complete. Processed {total_files} files and added {total_chunks} chunks.")

if __name__ == "__main__":
    ingest_pdfs()
