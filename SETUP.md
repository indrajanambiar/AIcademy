# 🎓 Adaptive AI Learning Coach - Setup Guide

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Ollama (for local LLM) or OpenAI API key

### Backend Setup

1. **Navigate to backend directory**:
```bash
cd backend
```

2. **Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure environment**:
```bash
cp .env.example .env
# Edit .env file with your settings
```

5. **Initialize database**:
```bash
python -c "from app.core.database import init_db; init_db()"
```

6. **Run the backend**:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: http://localhost:8000
API Documentation: http://localhost:8000/docs

### Frontend Setup

1. **Navigate to frontend directory**:
```bash
cd frontend
```

2. **Install dependencies**:
```bash
npm install
```

3. **Run development server**:
```bash
npm run dev
```

The frontend will be available at: http://localhost:5173

## 🔧 Configuration

### LLM Setup

#### Option 1: Ollama (Local LLM - Recommended for Development)

1. Install Ollama from https://ollama.ai
2. Pull a model:
```bash
ollama pull llama3.2
# or
ollama pull mistral
```
3. In `.env`, set:
```
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434
```

#### Option 2: OpenAI

In `.env`, set:
```
LLM_PROVIDER=openai
LLM_MODEL=gpt-4
OPENAI_API_KEY=your-api-key-here
```

### Database

By default, SQLite is used. For production, use PostgreSQL:
```
DATABASE_URL=postgresql://user:password@localhost:5432/learningcoach
```

## 📁 Project Structure

```
The_AI_tutor/
├── backend/
│   ├── app/
│   │   ├── agents/          # LangGraph agents
│   │   ├── api/             # FastAPI routes
│   │   ├── core/            # Config, auth, database
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # LLM, RAG, knowledge services
│   │   └── main.py          # FastAPI app
│   ├── data/                # SQLite DB, uploads, ChromaDB
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/           # React pages (Login, Register, Chat)
│   │   ├── services/        # API client
│   │   ├── store/           # Zustand state management
│   │   └── App.tsx
│   └── package.json
└── README.md
```

## 🎯 Features

### Implemented
✅ Multi-agent workflow with LangGraph
✅ LLM-first with RAG fallback
✅ Confidence-based answer evaluation
✅ Intent detection (Learn, Quiz, Roadmap, etc.)
✅ Personalized learning roadmaps
✅ Adaptive quiz generation
✅ Missing knowledge logging
✅ User authentication (JWT)
✅ Beautiful modern UI with glassmorphism
✅ Real-time chat interface
✅ File upload for knowledge base
✅ Admin dashboard for system stats

### Agents
1. **Intent Agent** - Detects user intent
2. **Teaching Agent** - Answers questions
3. **Quiz Agent** - Generates adaptive quizzes
4. **Planning Agent** - Creates learning roadmaps
5. **Memory Agent** - Tracks progress (planned)
6. **Assessment Agent** - Skill evaluation (planned)
7. **Adaptive Agent** - Adjusts difficulty (planned)

## 🧪 Testing

### Create a test user

1. Visit http://localhost:5173/register
2. Create an account
3. Login and start chatting!

### Try these commands:
- "Teach me about Python programming"
- "Create a roadmap for learning AI in 30 days"
- "Quiz me on machine learning"
- "Explain neural networks"

## 🔐 Security

- JWT-based authentication
- Password hashing with bcrypt
- CORS protection
- Input validation with Pydantic
- SQL injection protection with SQLAlchemy ORM

## 📊 Monitoring

View system statistics (admin only):
- Total users
- Total conversations
- Pending knowledge gaps
- RAG document count

Access at: http://localhost:8000/api/admin/stats

## 🐛 Troubleshooting

### Backend won't start
- Check Python version (3.10+)
- Ensure all dependencies are installed
- Check .env configuration
- Verify Ollama is running (if using local LLM)

### Frontend won't build
- Check Node.js version (18+)
- Clear node_modules and reinstall: `rm -rf node_modules && npm install`
- Check for port conflicts

### LLM not responding
- Verify Ollama is running: `ollama list`
- Check OLLAMA_BASE_URL in .env
- Try pulling the model again: `ollama pull llama3.2`

## 📚 Next Steps

1. **Add more agents**: Assessment, Memory, Adaptive, Notification
2. **Enhance RAG**: Better chunking, metadata filtering
3. **Add features**: Progress tracking, achievements, social learning
4. **Deploy**: Docker, Kubernetes, cloud hosting
5. **Mobile**: React Native app
6. **Integrations**: Telegram bot, Discord bot

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License - See LICENSE file

---

**Built with ❤️ for adaptive learning**

For questions or issues, please create a GitHub issue.
