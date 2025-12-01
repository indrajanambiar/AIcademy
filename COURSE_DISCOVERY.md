# 🎓 Course Discovery & Material Generation System

## Overview

The AI Tutor now includes an intelligent **Course Discovery System** that automatically:
- 📂 Scans PDF folders to identify courses
- 📚 Processes course materials and adds them to the RAG knowledge base
- 🎯 Generates comprehensive learning materials using LLM + RAG
- 🤖 Creates personalized content based on skill level and duration

## Architecture Flow

```
User Query → Intent Detection → Subject Selection → 
RAG Fetch → LLM Generation Layer → UI Output

✔ Identify the subject (Python, ML, DS, etc.)
✔ Retrieve relevant materials from PDFs
✔ Use LLMs to generate:
  • Syllabus
  • Roadmap
  • Quizzes
  • Notes
  • Lecture Flow
  • Assignments
  • Explanations
```

## Features

### 1. **Automatic Course Discovery**
- Scans `backend/pdfs/` folder structure
- Identifies courses from folder names (e.g., `python`, `ML`, `deeplearning`)
- Displays course metadata (PDF count, total size, file list)

### 2. **PDF Processing**
- Extracts text from all PDFs in a course folder
- Chunks content intelligently for optimal RAG retrieval
- Adds to ChromaDB vector store with metadata
- Supports batch processing of all courses

### 3. **Comprehensive Material Generation**
Generates all learning materials in one click:

#### **Syllabus**
```json
{
  "title": "Course Title",
  "description": "Course description",
  "modules": [
    {
      "title": "Module 1",
      "description": "Module description",
      "topics": ["Topic 1", "Topic 2"]
    }
  ]
}
```

#### **Roadmap**
```json
{
  "title": "Learning Roadmap",
  "days": [
    {
      "day": 1,
      "topic": "Introduction",
      "activities": ["Read chapter 1", "Practice exercises"],
      "estimated_hours": 2
    }
  ]
}
```

#### **Quiz**
```json
{
  "title": "Quiz Title",
  "questions": [
    {
      "id": 1,
      "question": "Question text",
      "options": {
        "A": "Option A",
        "B": "Option B",
        "C": "Option C",
        "D": "Option D"
      },
      "correct_answer": "A",
      "explanation": "Why A is correct"
    }
  ]
}
```

#### **Notes** (Markdown)
- Key Concepts
- Detailed Explanations
- Examples (code or real-world)
- Summary/Key Takeaways

#### **Lecture Flow** (Markdown)
- Introduction & Hook (5-10%)
- Core Concepts (Teaching phase)
- Examples/Demonstrations
- Interactive Activity/Practice
- Conclusion & Q&A

#### **Assignment**
```json
{
  "title": "Assignment Title",
  "description": "Overview of the task",
  "instructions": ["Step 1", "Step 2"],
  "requirements": ["Requirement 1", "Requirement 2"],
  "evaluation_criteria": ["Criterion 1", "Criterion 2"],
  "estimated_time": "2 hours"
}
```

## API Endpoints

### Course Discovery

#### `GET /api/course-discovery/discover`
Discover all available courses from the PDFs folder.

**Response:**
```json
{
  "success": true,
  "total_courses": 5,
  "courses": [
    {
      "name": "python",
      "display_name": "Python",
      "path": "/path/to/pdfs/python",
      "pdf_count": 3,
      "pdf_files": ["pythonTutorial.pdf", "..."],
      "total_size_mb": 15.5
    }
  ]
}
```

#### `POST /api/course-discovery/process`
Process PDFs for a specific course and add to RAG.

**Request:**
```json
{
  "course_name": "python",
  "max_pdfs": 5,
  "max_pages_per_pdf": 100
}
```

**Response:**
```json
{
  "success": true,
  "course": "python",
  "processed_files": 3,
  "total_files": 3,
  "total_chunks": 245,
  "failed_files": []
}
```

#### `POST /api/course-discovery/generate-all`
Generate all learning materials for a course.

**Request:**
```json
{
  "course_name": "python",
  "skill_level": "beginner",
  "duration_days": 30
}
```

**Response:**
```json
{
  "success": true,
  "course": "python",
  "skill_level": "beginner",
  "materials": {
    "syllabus": {...},
    "roadmap": {...},
    "quiz": {...},
    "notes": "...",
    "lecture_flow": "...",
    "assignment": {...}
  }
}
```

#### `POST /api/course-discovery/explain`
Get an explanation for a specific concept.

**Request:**
```json
{
  "course_name": "python",
  "concept": "list comprehensions"
}
```

**Response:**
```json
{
  "success": true,
  "course": "python",
  "concept": "list comprehensions",
  "explanation": "..."
}
```

#### `POST /api/course-discovery/process-all`
Process all discovered courses (bulk operation).

**Request:**
```json
{
  "max_pdfs_per_course": 5,
  "max_pages_per_pdf": 100
}
```

## Frontend Usage

### Access the Course Discovery Page
Navigate to: `http://localhost:5173/courses`

### Features:
1. **View All Courses**: See all discovered courses with metadata
2. **Configure Settings**: Set skill level and roadmap duration
3. **Process PDFs**: Click "Process PDFs" to add course content to RAG
4. **Generate Materials**: Click "Generate" to create all learning materials
5. **View Materials**: Browse generated content in tabbed interface
6. **Bulk Processing**: Process all courses at once

## Setup Instructions

### 1. Organize Your PDFs

Create course folders in `backend/pdfs/`:

```
backend/pdfs/
├── python/
│   ├── pythonTutorial.pdf
│   ├── Introduction_to_Python_Programming.pdf
│   └── PYTHON PROGRAMMING NOTES.pdf
├── ML/
│   ├── Introduction to Machine Learning.pdf
│   ├── Machine Learning For Absolute Beginners.pdf
│   └── advance_ml.pdf
├── deeplearning/
│   ├── d2l-en.pdf
│   ├── Deep-Learning-with-PyTorch.pdf
│   └── fundamentals-of-deep-learning.pdf
├── java/
│   └── ...
└── AI/
    └── ...
```

### 2. Start the Backend

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Start the Frontend

```bash
cd frontend
npm run dev
```

### 4. Access the Application

- Frontend: http://localhost:5173
- Course Discovery: http://localhost:5173/courses
- API Docs: http://localhost:8000/docs

## How It Works

### 1. **Discovery Phase**
- Scans `backend/pdfs/` directory
- Identifies subdirectories as courses
- Counts PDFs and calculates total size

### 2. **Processing Phase**
- Extracts text from PDFs using PyPDF2
- Chunks text with intelligent overlap (1000 chars, 200 overlap)
- Generates embeddings using SentenceTransformer
- Stores in ChromaDB with metadata (course, source, chunk_index)

### 3. **Generation Phase**
- Retrieves relevant context from RAG based on course
- Uses LLM (Ollama/OpenAI) to generate materials
- Combines RAG context with LLM knowledge
- Returns structured JSON or Markdown

### 4. **RAG Strategy**
```python
# For each material type:
1. Query RAG: f"{course} {material_type} {skill_level}"
2. Retrieve top-k relevant chunks
3. Combine chunks as context
4. Generate with LLM using context
5. Parse and return structured output
```

## Configuration

### Environment Variables

```bash
# LLM Configuration
LLM_PROVIDER=ollama  # or openai
LLM_MODEL=llama3.2
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000

# Embeddings
EMBEDDING_MODEL=all-MiniLM-L6-v2

# RAG
RAG_TOP_K=5
RAG_SIMILARITY_THRESHOLD=0.7
CONFIDENCE_THRESHOLD=70

# ChromaDB
CHROMA_PERSIST_DIR=./data/chroma
CHROMA_COLLECTION_NAME=learning_knowledge
```

## Best Practices

### 1. **PDF Organization**
- Use clear folder names (e.g., `python`, `machine_learning`)
- Group related materials together
- Keep PDFs under 50MB for optimal processing

### 2. **Processing Strategy**
- Start with 1-2 courses to test
- Use `max_pages_per_pdf` to limit processing time
- Process all courses during off-peak hours

### 3. **Material Generation**
- Choose appropriate skill level
- Set realistic roadmap duration
- Review generated content before sharing

### 4. **RAG Optimization**
- Process PDFs before generating materials
- Ensure ChromaDB is properly initialized
- Monitor chunk count and quality

## Troubleshooting

### PDFs Not Processing
- Check file permissions
- Verify PDF is not corrupted
- Ensure PyPDF2 can extract text

### No Context in Generated Materials
- Verify PDFs were processed successfully
- Check ChromaDB collection stats
- Ensure RAG service is initialized

### Generation Fails
- Check LLM service is running (Ollama)
- Verify API keys (if using OpenAI)
- Review logs for specific errors

## Performance Considerations

### Processing Time
- **Small PDF (1MB, 50 pages)**: ~5-10 seconds
- **Medium PDF (5MB, 200 pages)**: ~30-60 seconds
- **Large PDF (20MB, 500 pages)**: ~2-5 minutes

### Generation Time
- **Single Material**: ~5-15 seconds
- **All Materials**: ~1-2 minutes
- **Depends on**: LLM speed, RAG retrieval, content complexity

## Future Enhancements

- [ ] Support for more file formats (PPTX, XLSX)
- [ ] Incremental PDF processing
- [ ] Course versioning and updates
- [ ] Material export (PDF, DOCX)
- [ ] Collaborative material editing
- [ ] Student progress tracking per course
- [ ] Automated quiz grading
- [ ] Interactive code examples

## Contributing

Contributions are welcome! Please:
1. Test with sample PDFs
2. Document new features
3. Add error handling
4. Update this README

## License

MIT License - See LICENSE file for details

---

**Built with ❤️ for adaptive learning**
