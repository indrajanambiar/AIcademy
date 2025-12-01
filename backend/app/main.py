"""
FastAPI main application.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db
from app.core.logging import get_logger
from app.api import auth, conversation, courses, upload, admin, generation, course_discovery, assessment

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting AI Learning Coach application", version=settings.APP_VERSION)
    
    # Initialize database
    init_db()
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Adaptive AI Learning Coach and Assistant",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(conversation.router, prefix="/api/conversation", tags=["Conversation"])
app.include_router(courses.router, prefix="/api/courses", tags=["Courses"])
app.include_router(upload.router, prefix="/api/upload", tags=["Upload"])
app.include_router(generation.router, prefix="/api/generation", tags=["Generation"])
app.include_router(course_discovery.router, prefix="/api/course-discovery", tags=["Course Discovery"])
app.include_router(assessment.router, prefix="/api/assessment", tags=["Assessment"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AI Learning Coach API",
        "version": settings.APP_VERSION,
        "docs": "/docs" if settings.DEBUG else "Documentation not available in production",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
    )
