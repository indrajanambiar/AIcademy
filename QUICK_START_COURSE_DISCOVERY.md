# 🚀 Quick Start Guide - Course Discovery

This guide will help you get started with the Course Discovery and Material Generation system in under 5 minutes.

## Prerequisites

✅ Backend server running (`uvicorn app.main:app --reload`)  
✅ Frontend server running (`npm run dev`)  
✅ PDF files organized in `backend/pdfs/` folder

## Step 1: Organize Your PDFs (2 minutes)

Create course folders in `backend/pdfs/`:

```bash
cd backend/pdfs

# Example structure:
mkdir -p python ML deeplearning java AI

# Add your PDF files to each folder
# For example:
# cp ~/Downloads/python_tutorial.pdf python/
# cp ~/Downloads/ml_basics.pdf ML/
```

**Current Structure:**
```
backend/pdfs/
├── AI/
│   ├── AI.pdf
│   └── AI & ML DIGITAL NOTES.pdf
├── ML/
│   ├── Introduction to Machine Learning with Python.pdf
│   ├── Machine Learning For Absolute Beginners.pdf
│   └── advance_ml.pdf
├── deeplearning/
│   ├── d2l-en.pdf
│   ├── Deep-Learning-with-PyTorch.pdf
│   └── fundamentals-of-deep-learning-sampler.pdf
├── java/
│   ├── javabook.pdf
│   ├── thinkjava.pdf
│   ├── gsjava.pdf
│   ├── JavaNotesForProfessionals.pdf
│   └── javanotes5.pdf
└── python/
    ├── pythonTutorial.pdf
    ├── Introduction_to_Python_Programming_-_WEB.pdf
    └── PYTHON PROGRAMMING NOTES.pdf
```

## Step 2: Access the Course Discovery Page (30 seconds)

1. Open your browser
2. Navigate to: **http://localhost:5173/courses**
3. Login if prompted

You should see all discovered courses displayed as cards!

## Step 3: Configure Settings (30 seconds)

At the top of the page, set your preferences:

- **Skill Level**: Choose `beginner`, `intermediate`, or `advanced`
- **Roadmap Duration**: Set number of days (e.g., 30)

## Step 4: Process a Course (1-2 minutes)

For your first course:

1. Click **"Process PDFs"** button on any course card
2. Wait for processing to complete (you'll see a progress indicator)
3. Check the status - should show "success" with chunk count

**What's happening?**
- PDFs are being read
- Text is extracted and chunked
- Content is added to ChromaDB vector store

## Step 5: Generate Materials (1-2 minutes)

1. Click **"Generate"** button on the same course
2. Wait for generation (this takes ~1-2 minutes)
3. Materials will appear in a tabbed viewer below

**What's being generated?**
- Syllabus
- Roadmap
- Quiz
- Notes
- Lecture Flow
- Assignment

## Step 6: Explore Generated Materials (1 minute)

1. Click through the tabs to view different materials
2. Copy content for use in your learning
3. Generate materials for other courses as needed

## 🎯 Quick Commands

### Test the System

```bash
cd backend
python scripts/test_course_discovery.py
```

This will:
- ✅ Discover all courses
- ✅ Process sample PDFs
- ✅ Test RAG retrieval
- ✅ Generate sample materials

### Process All Courses at Once

1. Click **"Process All Courses"** button (top right)
2. Confirm the action
3. Wait for bulk processing to complete

⚠️ **Note**: This may take 10-30 minutes depending on PDF count and size.

## 📊 Understanding the Results

### Course Card Information

```
📚 Python
   3 PDFs • 15.5 MB
   
   [Status Badge]
   
   Processed: 3/3
   Chunks: 245
   
   [Process PDFs] [Generate]
```

- **PDFs**: Number of PDF files found
- **Size**: Total size of all PDFs
- **Status**: Current processing state
- **Chunks**: Number of text chunks added to RAG

### Generated Material Structure

#### Syllabus (JSON)
```json
{
  "title": "Python Programming Course",
  "description": "...",
  "modules": [...]
}
```

#### Roadmap (JSON)
```json
{
  "title": "30-Day Python Learning Roadmap",
  "days": [
    {
      "day": 1,
      "topic": "Python Basics",
      "activities": [...],
      "estimated_hours": 2
    }
  ]
}
```

#### Notes (Markdown)
```markdown
# Python Fundamentals

## Key Concepts
...

## Examples
...
```

## 🔧 Troubleshooting

### No Courses Found
- **Check**: PDFs exist in `backend/pdfs/` subdirectories
- **Fix**: Add PDF files to course folders

### Processing Failed
- **Check**: PDF files are not corrupted
- **Check**: Backend logs for specific errors
- **Try**: Process with `max_pages_per_pdf=10` first

### Generation Failed
- **Check**: LLM service is running (Ollama)
- **Check**: PDFs were processed successfully
- **Try**: Restart backend server

### No Context in Materials
- **Check**: ChromaDB has documents (`/api/upload/stats`)
- **Fix**: Re-process the course PDFs

## 💡 Tips for Best Results

1. **Start Small**: Process 1-2 courses first
2. **Test Generation**: Generate for one course before bulk processing
3. **Check Quality**: Review generated materials for accuracy
4. **Adjust Settings**: Try different skill levels and durations
5. **Monitor Logs**: Watch backend logs for any issues

## 🎓 Next Steps

Once you're comfortable with the basics:

1. **Explore API**: Check `/docs` for API endpoints
2. **Customize Prompts**: Modify generation prompts in `content_generation_service.py`
3. **Add More Courses**: Organize more PDFs
4. **Integrate with Chat**: Use generated materials in conversations
5. **Export Materials**: Copy/save generated content

## 📚 Additional Resources

- **[Full Documentation](COURSE_DISCOVERY.md)**: Complete guide with all features
- **[API Documentation](http://localhost:8000/docs)**: Interactive API explorer
- **[Main README](README.md)**: Project overview and architecture

## ⏱️ Expected Timings

| Operation | Time |
|-----------|------|
| Discover Courses | < 1 second |
| Process 1 PDF (50 pages) | 5-10 seconds |
| Process 1 PDF (200 pages) | 30-60 seconds |
| Generate All Materials | 1-2 minutes |
| Process All Courses | 10-30 minutes |

## 🎉 Success Checklist

- [ ] PDFs organized in course folders
- [ ] Course Discovery page accessible
- [ ] At least one course processed successfully
- [ ] Materials generated for one course
- [ ] Can view all generated material types
- [ ] RAG retrieval working (check with test script)

---

**Need Help?** Check the logs, review the documentation, or open an issue!

**Ready to Learn?** Start generating materials and enjoy your AI-powered learning experience! 🚀
