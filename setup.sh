#!/bin/bash

echo "🎓 AI Learning Coach - Quick Start Script"
echo "=========================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.10 or higher."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18 or higher."
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Backend setup
echo "📦 Setting up backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt --quiet

# Create data directories
mkdir -p data/uploads data/chroma

# Initialize database
echo "Initializing database..."
python scripts/init_db.py

echo "✅ Backend setup complete"
echo ""

# Frontend setup
echo "📦 Setting up frontend..."
cd ../frontend

# Install Node dependencies
echo "Installing Node dependencies..."
npm install --silent

echo "✅ Frontend setup complete"
echo ""

# Final instructions
echo "=========================================="
echo "🎉 Setup Complete!"
echo "=========================================="
echo ""
echo "To start the application:"
echo ""
echo "1. Start the backend (in backend directory):"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   uvicorn app.main:app --reload"
echo ""
echo "2. Start the frontend (in new terminal, in frontend directory):"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "3. Open http://localhost:5173 in your browser"
echo ""
echo "Admin credentials:"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
echo "📚 See SETUP.md for more details"
echo "=========================================="
