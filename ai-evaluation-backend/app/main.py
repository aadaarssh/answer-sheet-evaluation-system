from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager

from .config import settings
from .database import connect_to_mongo, close_mongo_connection
from .routers import auth, schemes, sessions, scripts, evaluations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle app startup and shutdown events."""
    # Startup
    try:
        await connect_to_mongo()
        logger.info("Application startup completed")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    try:
        await close_mongo_connection()
        logger.info("Application shutdown completed")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")

# Create FastAPI application
app = FastAPI(
    title="AI Answer Sheet Evaluation System",
    description="Intelligent evaluation system for handwritten answer sheets using AI",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add trusted host middleware for security
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "0.0.0.0"]
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": "An internal server error occurred", "detail": str(exc)}
    )

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(schemes.router, prefix="/api")
app.include_router(sessions.router, prefix="/api")
app.include_router(scripts.router, prefix="/api")
app.include_router(evaluations.router, prefix="/api")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "AI Answer Sheet Evaluation System",
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "AI Answer Sheet Evaluation System API",
        "version": "1.0.0",
        "documentation": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )