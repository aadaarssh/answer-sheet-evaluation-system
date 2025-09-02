#!/usr/bin/env python3
"""
Startup script for AI Evaluation System Backend
"""

import asyncio
import sys
import os
import logging
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent))

from app.main import app
from app.config import settings
from app.database import connect_to_mongo
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("server.log")
    ]
)

logger = logging.getLogger(__name__)

async def check_dependencies():
    """Check if all required services are available."""
    logger.info("Checking system dependencies...")
    
    # Check MongoDB connection
    try:
        await connect_to_mongo()
        logger.info("[OK] MongoDB connection successful")
    except Exception as e:
        logger.error(f"[ERROR] MongoDB connection failed: {e}")
        return False
    
    # Check Redis connection (for Celery)
    try:
        import redis
        r = redis.Redis.from_url(settings.redis_url)
        r.ping()
        logger.info("[OK] Redis connection successful")
    except Exception as e:
        logger.error(f"[ERROR] Redis connection failed: {e}")
        logger.warning("Redis is required for async processing. Some features may not work.")
    
    # Check API keys
    if not settings.openai_api_key:
        logger.warning("[WARNING] OpenAI API key not configured - OCR will use mock responses")
    else:
        logger.info("[OK] OpenAI API key configured")
    
    if not settings.gemini_api_key:
        logger.warning("[WARNING] Gemini API key not configured - verification will use fallback logic")
    else:
        logger.info("[OK] Gemini API key configured")
    
    # Check upload directory
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    if upload_dir.exists() and upload_dir.is_dir():
        logger.info("[OK] Upload directory ready")
    else:
        logger.error("[ERROR] Upload directory not accessible")
        return False
    
    return True

def print_banner():
    """Print startup banner."""
    banner = """
    ===============================================
       AI Answer Sheet Evaluation System
                Backend Server
    ===============================================
    
    Starting server...
    FastAPI + MongoDB + AI Integration
    Environment: Development
    """
    print(banner)

def print_startup_info():
    """Print startup information."""
    info = f"""
    Server Configuration:
    ============================================
    Server URL:         http://localhost:8000
    API Documentation:  http://localhost:8000/docs
    Alternative Docs:   http://localhost:8000/redoc
    Health Check:       http://localhost:8000/health
    
    Database:
    ============================================
    MongoDB:           {settings.mongodb_url}
    Database:          {settings.database_name}
    
    Features:
    ============================================
    OCR Processing:    {'Enabled' if settings.openai_api_key else 'Mock Mode'}
    AI Verification:   {'Enabled' if settings.gemini_api_key else 'Fallback Mode'}
    Email Notifications: {'Enabled' if settings.email_user else 'Disabled'}
    Async Processing:  {'Ready' if settings.redis_url else 'Limited'}
    
    To start Celery worker (for async processing):
    celery -A app.workers.celery_app worker --loglevel=info
    
    ============================================
    """
    print(info)

async def main():
    """Main startup function."""
    print_banner()
    
    # Check dependencies
    dependencies_ok = await check_dependencies()
    
    if not dependencies_ok:
        logger.error("[ERROR] Dependency check failed. Please resolve issues before starting.")
        sys.exit(1)
    
    print_startup_info()
    
    logger.info("All systems ready. Starting FastAPI server...")
    
    # Start the server
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )
    
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server shutdown by user")
        print("\nThanks for using AI Evaluation System!")
    except Exception as e:
        logger.error(f"Server startup failed: {e}")
        sys.exit(1)