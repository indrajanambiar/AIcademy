# 📊 Understanding RAG vs LLM Logs

## How to Read the Logs

When you generate materials (syllabus, roadmap, quiz, notes, etc.), the system now provides **detailed logs** that clearly show whether content is being generated from:
- **RAG + LLM**: Using PDF knowledge (retrieved from vector store)
- **LLM Only**: Using the LLM's built-in knowledge

## Log Format

### 🎯 Generation Start
```json
{
  "event": "🎯 Starting syllabus generation",
  "subject": "python",
  "skill_level": "beginner",
  "material_type": "syllabus",
  "level": "info",
  "timestamp": "2025-11-27T16:00:00Z"
}
```

### 🔍 RAG Query
```json
{
  "event": "🔍 Querying RAG for context",
  "query": "python syllabus curriculum beginner",
  "top_k": 3,
  "level": "info",
  "timestamp": "2025-11-27T16:00:01Z"
}
```

### ✅ RAG Context Found (Using PDFs)
```json
{
  "event": "✅ RAG CONTEXT FOUND - Using PDF knowledge",
  "chunks_retrieved": 3,
  "total_context_length": 2847,
  "sources": ["pythonTutorial.pdf", "Introduction_to_Python_Programming.pdf", "PYTHON PROGRAMMING NOTES.pdf"],
  "distances": ["0.3245", "0.4123", "0.5678"],
  "mode": "RAG + LLM",
  "level": "info",
  "timestamp": "2025-11-27T16:00:02Z"
}
```

**This means:** ✅ Content is being generated using knowledge from your PDFs!

### ⚠️ No RAG Context (Using LLM Only)
```json
{
  "event": "⚠️ NO RAG CONTEXT - Using LLM knowledge only",
  "subject": "python",
  "mode": "LLM_ONLY",
  "reason": "No matching documents in vector store",
  "level": "warning",
  "timestamp": "2025-11-27T16:00:02Z"
}
```

**This means:** ⚠️ No PDFs were processed for this course, using LLM's general knowledge

### 🤖 LLM Generation
```json
{
  "event": "🤖 Generating with LLM",
  "has_context": true,
  "level": "info",
  "timestamp": "2025-11-27T16:00:03Z"
}
```

### ✅ Generation Complete
```json
{
  "event": "✅ Syllabus generation complete",
  "subject": "python",
  "response_length": 1234,
  "used_rag": true,
  "level": "info",
  "timestamp": "2025-11-27T16:00:15Z"
}
```

## Quick Reference

| Log Message | Meaning | Source |
|-------------|---------|--------|
| ✅ RAG CONTEXT FOUND | Using PDF knowledge | **PDFs + LLM** |
| ⚠️ NO RAG CONTEXT | No PDFs found | **LLM Only** |
| 📝 Using provided context | Custom context provided | **Custom + LLM** |
| `chunks_retrieved: 3` | Retrieved 3 chunks from PDFs | **RAG Active** |
| `sources: [...]` | PDF files used | **Shows which PDFs** |
| `distances: [...]` | Relevance scores (lower = better) | **Match quality** |
| `mode: "RAG + LLM"` | Using both RAG and LLM | **Best mode** |
| `mode: "LLM_ONLY"` | Using LLM knowledge only | **No PDFs** |

## Example Log Flow

### Scenario 1: PDFs Processed (GOOD ✅)

```
🎯 Starting syllabus generation
   subject: python
   skill_level: beginner

🔍 Querying RAG for context
   query: "python syllabus curriculum beginner"
   top_k: 3

✅ RAG CONTEXT FOUND - Using PDF knowledge
   chunks_retrieved: 3
   sources: ["pythonTutorial.pdf", "Introduction_to_Python_Programming.pdf"]
   distances: ["0.3245", "0.4123", "0.5678"]
   mode: "RAG + LLM"

🤖 Generating with LLM
   has_context: true

✅ Syllabus generation complete
   used_rag: true
```

**Result:** Content generated using your PDF knowledge! 🎉

### Scenario 2: PDFs NOT Processed (WARNING ⚠️)

```
🎯 Starting syllabus generation
   subject: python
   skill_level: beginner

🔍 Querying RAG for context
   query: "python syllabus curriculum beginner"
   top_k: 3

⚠️ NO RAG CONTEXT - Using LLM knowledge only
   subject: python
   mode: "LLM_ONLY"
   reason: "No matching documents in vector store"

🤖 Generating with LLM
   has_context: false

✅ Syllabus generation complete
   used_rag: false
```

**Result:** Content generated using LLM's general knowledge only

**Fix:** Click "Process PDFs" button for this course first!

## How to View Logs

### Option 1: Terminal Output
Watch the backend terminal where `uvicorn` is running. Logs appear in real-time:

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Option 2: Log File (if configured)
Check the log file in `backend/logs/` (if file logging is enabled)

### Option 3: Filter Logs
Use `grep` to filter specific events:

```bash
# Show only RAG-related logs
tail -f backend.log | grep "RAG"

# Show only generation starts
tail -f backend.log | grep "Starting.*generation"

# Show only warnings (no RAG context)
tail -f backend.log | grep "NO RAG CONTEXT"
```

## Understanding Distances

The `distances` field shows how relevant the retrieved chunks are:

- **0.0 - 0.3**: Excellent match (very relevant)
- **0.3 - 0.5**: Good match (relevant)
- **0.5 - 0.7**: Fair match (somewhat relevant)
- **0.7 - 1.0**: Poor match (less relevant)

Lower distances = better matches!

## Troubleshooting

### ⚠️ Always seeing "NO RAG CONTEXT"?

**Possible causes:**
1. PDFs not processed yet
2. ChromaDB empty
3. Query doesn't match PDF content

**Solutions:**
1. Click "Process PDFs" for the course
2. Check ChromaDB stats: `GET /api/upload/stats`
3. Try different search terms

### ✅ Seeing RAG context but content seems generic?

**Possible causes:**
1. Retrieved chunks not very relevant (high distances)
2. LLM not using context effectively

**Solutions:**
1. Check distance scores (should be < 0.5)
2. Process more PDFs for better coverage
3. Adjust chunk size in `course_discovery_service.py`

## Material-Specific Logging

Each material type has its own logging:

### Syllabus
```
🎯 Starting syllabus generation
🔍 Querying RAG: "python syllabus curriculum beginner"
```

### Roadmap
```
🎯 Starting roadmap generation
🔍 Querying RAG: "python learning path roadmap beginner"
```

### Quiz
```
🎯 Starting quiz generation
🔍 Querying RAG: "python fundamentals questions quiz"
```

### Notes
```
🎯 Starting notes generation
🔍 Querying RAG: "python Course Overview explanation concepts"
```

### Lecture Flow
```
🎯 Starting lecture flow generation
🔍 Querying RAG: "python Introduction teaching guide"
```

### Assignment
```
🎯 Starting assignment generation
🔍 Querying RAG: "python Practical Application exercises project"
```

### Explanation
```
🎯 Starting explanation generation
🔍 Querying RAG: "python list comprehensions definition explanation"
```

## Best Practices

1. **Always Process PDFs First**: Click "Process PDFs" before generating materials
2. **Check Logs**: Watch for ✅ or ⚠️ to know the source
3. **Monitor Distances**: Lower is better (< 0.5 is good)
4. **Review Sources**: Check which PDFs are being used
5. **Iterate**: If quality is low, add more PDFs or adjust queries

## Example: Complete Generation Flow

```json
{"event": "🎯 Starting syllabus generation", "subject": "python", "skill_level": "beginner", "material_type": "syllabus"}
{"event": "🔍 Querying RAG for context", "query": "python syllabus curriculum beginner", "top_k": 3}
{"event": "✅ RAG CONTEXT FOUND - Using PDF knowledge", "chunks_retrieved": 3, "total_context_length": 2847, "sources": ["pythonTutorial.pdf", "Introduction_to_Python_Programming.pdf", "PYTHON PROGRAMMING NOTES.pdf"], "distances": ["0.3245", "0.4123", "0.5678"], "mode": "RAG + LLM"}
{"event": "🤖 Generating with LLM", "has_context": true}
{"event": "✅ Syllabus generation complete", "subject": "python", "response_length": 1234, "used_rag": true}
```

**Summary:**
- ✅ PDFs were used
- ✅ 3 chunks retrieved
- ✅ Good relevance (distances < 0.6)
- ✅ Content based on your PDFs!

---

**Now you can easily tell if your generated content is coming from your PDFs or the LLM's general knowledge!** 🎉
