#!/usr/bin/env python3
"""
Simple Celery Worker startup script to fix unpacking errors.
"""

import sys
import os
import logging
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent))

from app.workers.celery_app_simple import celery_app
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("simple_worker.log")
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main worker startup function."""
    print("""
    +===============================================+
    |     AI Evaluation System - Simple Worker     |
    |         Fixed Unpacking Error Version        |
    +===============================================+
    
    >> Starting simple worker...
    >> Using minimal Celery configuration
    """)
    
    # Check Redis connection
    try:
        import redis
        r = redis.Redis.from_url(settings.redis_url)
        r.ping()
        logger.info("[OK] Redis connection successful")
    except Exception as e:
        logger.error(f"[ERROR] Redis connection failed: {e}")
        sys.exit(1)
    
    logger.info(">> Starting Simple Celery worker...")
    
    # Start worker with minimal configuration
    celery_app.worker_main([
        'worker',
        '--loglevel=info',
        '--concurrency=2',  # Reduced concurrency
        '--pool=solo'       # Use solo pool to avoid multiprocessing issues
    ])

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Worker shutdown by user")
        print("\nSimple worker stopped!")
    except Exception as e:
        logger.error(f"Worker startup failed: {e}")
        sys.exit(1)