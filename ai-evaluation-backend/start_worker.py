#!/usr/bin/env python3
"""
Startup script for Celery Worker
"""

import sys
import os
import logging
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent))

from app.workers.celery_app import celery_app
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("worker.log")
    ]
)

logger = logging.getLogger(__name__)

def print_banner():
    """Print worker startup banner."""
    banner = """
    ╔═══════════════════════════════════════════════╗
    ║     AI Evaluation System - Celery Worker     ║
    ║            Async Task Processor               ║
    ╚═══════════════════════════════════════════════╝
    
    🔄 Starting worker...
    📋 Processing evaluation tasks
    """
    print(banner)

def check_redis_connection():
    """Check Redis connection."""
    try:
        import redis
        r = redis.Redis.from_url(settings.redis_url)
        r.ping()
        logger.info("✓ Redis connection successful")
        return True
    except Exception as e:
        logger.error(f"✗ Redis connection failed: {e}")
        return False

def print_worker_info():
    """Print worker configuration."""
    info = f"""
    Worker Configuration:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    🔗 Broker URL:       {settings.redis_url}
    📋 Available Queues: evaluation, batch
    🏭 Worker Type:      Async Task Processor
    
    Available Tasks:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    📄 process_answer_script     - Single script processing
    📦 batch_process_session     - Batch session processing  
    🧹 cleanup_old_tasks         - System maintenance
    
    Features:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    🤖 OCR Processing:   {'✓ Enabled' if settings.openai_api_key else '⚠ Mock Mode'}
    🔍 AI Verification:  {'✓ Enabled' if settings.gemini_api_key else '⚠ Fallback Mode'}
    📧 Notifications:    {'✓ Enabled' if settings.email_user else '✗ Disabled'}
    
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """
    print(info)

def main():
    """Main worker startup function."""
    print_banner()
    
    # Check Redis connection
    if not check_redis_connection():
        logger.error("❌ Cannot start worker without Redis connection")
        sys.exit(1)
    
    print_worker_info()
    
    logger.info("🎯 Starting Celery worker...")
    
    # Start worker with configuration
    celery_app.worker_main([
        'worker',
        '--loglevel=info',
        '--queues=evaluation,batch',
        '--concurrency=4',
        '--prefetch-multiplier=1',
        '--max-tasks-per-child=1000',
        '--time-limit=1800',  # 30 minutes
        '--soft-time-limit=1500'  # 25 minutes
    ])

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("🛑 Worker shutdown by user")
        print("\n👋 Celery worker stopped!")
    except Exception as e:
        logger.error(f"💥 Worker startup failed: {e}")
        sys.exit(1)