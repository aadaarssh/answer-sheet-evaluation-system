from celery import Celery
from ..config import settings
import logging

logger = logging.getLogger(__name__)

# Create Celery application
celery_app = Celery(
    "ai_evaluation_worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=['app.workers.evaluation_worker']
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Task routing
celery_app.conf.task_routes = {
    'app.workers.evaluation_worker.process_answer_script': {'queue': 'evaluation'},
    'app.workers.evaluation_worker.batch_process_session': {'queue': 'batch'},
}

logger.info("Celery application configured")