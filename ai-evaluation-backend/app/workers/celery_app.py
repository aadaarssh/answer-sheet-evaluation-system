from celery import Celery
from ..config import settings
import logging

logger = logging.getLogger(__name__)

# Create Celery application with minimal, working configuration
celery_app = Celery(
    'ai_evaluation_worker',
    broker=settings.redis_url,
    backend=settings.redis_url
)

# Basic configuration that works
celery_app.conf.update(
    # Serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Timezone
    timezone='UTC',
    enable_utc=True,
    
    # Task configuration
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Worker configuration  
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=True,
    
    # Result backend settings
    result_expires=3600,
    result_persistent=True,
    
    # Import tasks
    imports=['app.workers.evaluation_worker']
)

# Force import of tasks to ensure registration
try:
    from . import evaluation_worker
    logger.info("Tasks imported successfully")
except Exception as e:
    logger.warning(f"Could not import tasks: {e}")

logger.info("Celery application configured successfully")