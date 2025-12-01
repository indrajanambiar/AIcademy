"""
Application configuration management using Pydantic Settings.
"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "Aicademy"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = False
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: str = "sqlite:///./data/learningcoach.db"
    
    # LLM Configuration
    LLM_PROVIDER: str = "ollama"  # ollama or openai
    LLM_MODEL: str = "llama3.2"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2000
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OPENAI_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    
    # Embeddings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    # ChromaDB
    CHROMA_PERSIST_DIR: str = "./data/chroma"
    CHROMA_COLLECTION_NAME: str = "learning_knowledge"
    
    # RAG Configuration
    RAG_TOP_K: int = 5
    RAG_SIMILARITY_THRESHOLD: float = 0.7
    CONFIDENCE_THRESHOLD: int = 70
    
    # File Upload
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: str = ".pdf,.txt,.md,.docx,.pptx,.xlsx"
    UPLOAD_DIR: str = "./data/uploads"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    CORS_ALLOW_CREDENTIALS: bool = True
    
    # Admin
    ADMIN_EMAIL: str = "admin@example.com"
    ADMIN_PASSWORD: str = "changeme123"
    
    # Features
    ENABLE_QUIZ: bool = True
    ENABLE_ROADMAP: bool = True
    ENABLE_FILE_UPLOAD: bool = True
    ENABLE_NOTIFICATIONS: bool = False
    
    # Learning Defaults
    DEFAULT_LEARNING_DURATION_DAYS: int = 30
    DEFAULT_SKILL_LEVEL: str = "beginner"
    
    @field_validator("CORS_ORIGINS")
    @classmethod
    def parse_cors_origins(cls, v: str) -> List[str]:
        """Parse comma-separated CORS origins."""
        return [origin.strip() for origin in v.split(",")]
    
    @field_validator("ALLOWED_EXTENSIONS")
    @classmethod
    def parse_extensions(cls, v: str) -> List[str]:
        """Parse comma-separated file extensions."""
        return [ext.strip() for ext in v.split(",")]
    
    @property
    def max_file_size_bytes(self) -> int:
        """Convert MB to bytes."""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024
    
    @property
    def BASE_DIR(self) -> str:
        """Get the backend directory path."""
        from pathlib import Path
        return str(Path(__file__).parent.parent.parent)
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
