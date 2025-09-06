"""
Simple, clean Celery configuration without complex settings.
This should resolve the unpacking error.
"""

from celery import Celery
from ..config import settings
import logging

logger = logging.getLogger(__name__)

# Create minimal Celery application
celery_app = Celery(
    'ai_evaluation_worker',
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        'app.workers.evaluation_worker',
        'app.workers.simple_tasks',
        'app.workers.diagnostic_tasks'
    ]
)

# Minimal configuration to avoid unpacking errors
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],  
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Force import of tasks to ensure registration
try:
    from . import evaluation_worker
    from . import simple_tasks
    from . import diagnostic_tasks
    logger.info("All task modules imported successfully")
except Exception as e:
    logger.warning(f"Could not import tasks: {e}")

logger.info("Simple Celery application configured successfully")