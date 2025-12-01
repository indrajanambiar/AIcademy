# 🎓 Adaptive AI Learning Coach and Assistant

An intelligent, conversational AI tutor that adapts to each learner's pace, tracks progress, and provides personalized learning experiences through multi-agent workflows.

## 🌟 Features

### Core Learning Features
- **Adaptive Learning**: Dynamically adjusts difficulty based on user performance
- **Personalized Roadmaps**: Creates custom learning paths based on available time and skill level
- **Progress Tracking**: Comprehensive tracking across multiple subjects
- **Interactive Quizzes**: Adaptive testing with detailed feedback
- **Conversational Interface**: Friendly, motivating coaching style
- **📚 Course Discovery**: Automatically discovers courses from PDF folders and generates comprehensive learning materials
- **🎯 Adaptive Assessment**: Diagnostic quizzes that evaluate skill level and generate personalized study plans based on your performance

### Technical Features
- **LLM-First Architecture**: Uses local LLM with confidence-based fallback to RAG
- **Multi-Agent System**: LangGraph-powered workflow with specialized agents
- **RAG Integration**: ChromaDB vector store for knowledge retrieval
- **Confidence Evaluation**: Self-assessment mechanism to ensure answer quality
- **Missing Knowledge Logging**: Tracks gaps for continuous improvement
- **Multi-Platform**: Web UI, API, and extensible to mobile/Telegram/CLI
- **🎯 Intelligent Material Generation**: Auto-generates syllabus, roadmaps, quizzes, notes, lectures, and assignments from course PDFs

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Layer                              │
│  Web UI │ Mobile │ Telegram Bot │ CLI                       │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Backend (Auth, REST)                    │
│  Auth │ Conversation │ Agent Orchestrator │ Upload │ Admin  │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│         LangGraph Workflow Engine (10 Agents)                │
│  Intent │ Assessment │ Planning │ Teaching │ Quiz            │
│  Adaptive │ Memory │ Knowledge Validation │ Acquisition      │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              LLM Layer + Confidence Critic                   │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│         RAG & Storage (ChromaDB, SQL, Files)                 │
└─────────────────────────────────────────────────────────────┘
```

## 📊 Data Model

- **Users**: Authentication and preferences
- **Courses**: Learning topics and syllabi
- **User Courses**: Enrollment and progress
- **Roadmaps**: Personalized learning paths
- **Quiz Results**: Assessment history
- **Conversations**: Chat history
- **Missing Knowledge**: Identified knowledge gaps

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+ (for frontend)
- Docker (optional)

### Installation

1. **Clone and setup backend**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your settings
```

3. **Initialize database**:
```bash
python -m app.core.init_db
```

4. **Run backend**:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5. **Setup frontend** (in new terminal):
```bash
cd frontend
npm install
npm run dev
```

6. **Access the application**:
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs
- Admin Dashboard: http://localhost:8000/admin

## 🧠 Knowledge Access Strategy

The system follows a confidence-based approach:

1. **LLM First**: Answer using internal knowledge
2. **Self-Evaluate**: Calculate confidence (0-100)
3. **RAG Fallback**: If confidence < 70, retrieve from vector store
4. **Re-Evaluate**: Improve answer with retrieved context
5. **Log Gaps**: If still < 70, log missing knowledge for admin review

## 🎯 Answer Format

Every response includes:
- 💬 **Answer**: Clear, concise explanation
- 📘 **Simple Example**: Practical demonstration
- 🧠 **Why This Matters**: Real-world relevance
- 🎯 **Optional Next Step**: Guided learning progression

## 🛠️ Technology Stack

### Backend
- **FastAPI**: High-performance async API
- **LangGraph**: Multi-agent orchestration
- **LangChain**: LLM interaction and RAG
- **ChromaDB**: Vector database
- **SQLAlchemy**: ORM for SQL database
- **Pydantic**: Data validation
- **JWT**: Authentication

### Frontend
- **React/Vite**: Modern UI framework
- **TypeScript**: Type-safe development
- **TailwindCSS**: Utility-first styling
- **shadcn/ui**: Beautiful components
- **Zustand**: State management
- **React Query**: Data fetching

### LLM & Embeddings
- **Primary LLM**: Ollama (llama3.2/mistral) or OpenAI
- **Embeddings**: all-MiniLM-L6-v2 or bge-small-en-v1.5

## 📁 Project Structure

```
The_AI_tutor/
├── backend/
│   ├── app/
│   │   ├── agents/          # LangGraph agents
│   │   ├── api/             # API routes
│   │   ├── core/            # Config, auth, database
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   └── main.py          # FastAPI app
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/           # Page components
│   │   ├── hooks/           # Custom hooks
│   │   ├── services/        # API clients
│   │   └── App.tsx
│   └── package.json
├── data/                    # File storage
├── docs/                    # Documentation
└── docker-compose.yml
```

## 🔐 Authentication

- JWT-based authentication
- Secure password hashing with bcrypt
- Token refresh mechanism
- Role-based access control (user/admin)

## 📈 Monitoring & Logging

- Structured logging with timestamps
- Performance metrics
- Error tracking
- Admin dashboard for system health

## 📚 Course Discovery & Material Generation

The AI Tutor includes an intelligent **Course Discovery System** that automatically processes your PDF library and generates comprehensive learning materials.

### Quick Start

1. **Organize PDFs** in `backend/pdfs/`:
```
backend/pdfs/
├── python/
│   ├── pythonTutorial.pdf
│   └── ...
├── ML/
│   ├── intro_to_ml.pdf
│   └── ...
└── deeplearning/
    └── ...
```

2. **Access Course Discovery**: Navigate to `http://localhost:5173/courses`

3. **Process & Generate**:
   - Click "Process PDFs" to add course content to RAG
   - Click "Generate" to create all learning materials
   - View materials in the tabbed interface

### Generated Materials

For each course, the system generates:
- ✅ **Syllabus**: Structured course outline with modules and topics
- ✅ **Roadmap**: Day-by-day learning plan with activities
- ✅ **Quizzes**: Multiple-choice questions with explanations
- ✅ **Notes**: Comprehensive study notes in Markdown
- ✅ **Lecture Flow**: Time-structured teaching guide
- ✅ **Assignments**: Practical exercises with evaluation criteria
- ✅ **Explanations**: On-demand concept explanations

### How It Works

```
User Query → Intent Detection → Subject Selection → 
RAG Fetch → LLM Generation Layer → UI Output
```

1. **Discover**: Scans PDF folders to identify courses
2. **Process**: Extracts and chunks PDF content
3. **Store**: Adds to ChromaDB vector store
4. **Retrieve**: Fetches relevant context via RAG
5. **Generate**: Creates materials using LLM + RAG context

📖 **[Full Documentation](COURSE_DISCOVERY.md)** - Detailed guide with API endpoints, examples, and best practices


## 🤝 Contributing

Contributions are welcome! Please read the contributing guidelines.

## 📄 License

MIT License - See LICENSE file for details

## 🙋 Support

For issues and questions, please open a GitHub issue or contact the maintainers.

---

**Built with ❤️ for adaptive learning**
