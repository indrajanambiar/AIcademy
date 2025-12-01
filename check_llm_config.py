import sys
import os
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.core.config import settings

print("🔍 Current LLM Configuration:")
print(f"   Provider: {settings.LLM_PROVIDER}")
print(f"   Model: {settings.LLM_MODEL}")
print(f"   Temperature: {settings.LLM_TEMPERATURE}")

if settings.LLM_PROVIDER == "ollama":
    print(f"   Ollama URL: {settings.OLLAMA_BASE_URL}")
elif settings.LLM_PROVIDER == "openai":
    print(f"   OpenAI Key: {'Set' if settings.OPENAI_API_KEY else 'Not Set'}")
elif settings.LLM_PROVIDER == "gemini":
    print(f"   Google Key: {'Set' if settings.GOOGLE_API_KEY else 'Not Set'}")
