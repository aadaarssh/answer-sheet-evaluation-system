"""
Diagnostic tasks to identify service initialization issues.
"""

import logging
from datetime import datetime
from .celery_app_simple import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name='diagnose_services')
def diagnose_services(self):
    """
    Diagnose which services are causing initialization failures.
    """
    try:
        logger.info("Starting service diagnostics")
        
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'starting_diagnostics', 'progress': 10}
        )
        
        services_status = {}
        
        # Test 1: OCR Service
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'testing_ocr_service', 'progress': 20}
        )
        
        try:
            from ..services.ocr_service import OCRService
            ocr_service = OCRService()
            services_status['ocr_service'] = 'SUCCESS'
            logger.info("OCR Service initialized successfully")
        except Exception as e:
            services_status['ocr_service'] = f'FAILED: {e}'
            logger.error(f"OCR Service failed: {e}")
        
        # Test 2: Evaluation Service
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'testing_evaluation_service', 'progress': 40}
        )
        
        try:
            from ..services.evaluation_service import EvaluationService
            evaluation_service = EvaluationService()
            services_status['evaluation_service'] = 'SUCCESS'
            logger.info("Evaluation Service initialized successfully")
        except Exception as e:
            services_status['evaluation_service'] = f'FAILED: {e}'
            logger.error(f"Evaluation Service failed: {e}")
        
        # Test 3: Verification Service
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'testing_verification_service', 'progress': 60}
        )
        
        try:
            from ..services.verification_service import VerificationService
            verification_service = VerificationService()
            services_status['verification_service'] = 'SUCCESS'
            logger.info("Verification Service initialized successfully")
        except Exception as e:
            services_status['verification_service'] = f'FAILED: {e}'
            logger.error(f"Verification Service failed: {e}")
        
        # Test 4: Notification Service
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'testing_notification_service', 'progress': 80}
        )
        
        try:
            from ..services.notification_service import NotificationService
            notification_service = NotificationService()
            services_status['notification_service'] = 'SUCCESS'
            logger.info("Notification Service initialized successfully")
        except Exception as e:
            services_status['notification_service'] = f'FAILED: {e}'
            logger.error(f"Notification Service failed: {e}")
        
        # Test 5: Config and Environment
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'testing_config', 'progress': 90}
        )
        
        try:
            from ..config import settings
            config_status = {
                'openai_api_key': 'SET' if settings.openai_api_key else 'MISSING',
                'gemini_api_key': 'SET' if settings.gemini_api_key else 'MISSING',
                'redis_url': settings.redis_url,
                'mongodb_url': settings.mongodb_url
            }
            services_status['config'] = config_status
            logger.info("Config loaded successfully")
        except Exception as e:
            services_status['config'] = f'FAILED: {e}'
            logger.error(f"Config loading failed: {e}")
        
        result = {
            "status": "completed",
            "message": "Service diagnostics completed",
            "services": services_status,
            "timestamp": str(datetime.now())
        }
        
        logger.info(f"Service diagnostics completed: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"Service diagnostics failed: {e}")
        raise

@celery_app.task(bind=True, name='minimal_process_script')
def minimal_process_script(self, script_id):
    """
    Minimal version of process_answer_script that only uses working services.
    """
    import asyncio
    from bson import ObjectId
    
    try:
        logger.info(f"Minimal processing started for script {script_id}")
        
        # Validate ObjectId
        try:
            ObjectId(script_id)
        except Exception as e:
            raise ValueError(f"Invalid script_id format: {script_id} - {e}")
        
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'connecting_database', 'progress': 20, 'script_id': script_id}
        )
        
        # Database operations
        async def process_with_db():
            from ..database import connect_to_mongo, get_database, close_mongo_connection
            from ..models.script import ScriptStatus
            
            await connect_to_mongo()
            db = get_database()
            
            if db is None:
                raise RuntimeError("Database connection failed")
                
            # Get script
            script = await db.answer_scripts.find_one({"_id": ObjectId(script_id)})
            if not script:
                raise ValueError(f"Script {script_id} not found")
                
            # Update status to processing
            await db.answer_scripts.update_one(
                {"_id": ObjectId(script_id)},
                {"$set": {"status": ScriptStatus.PROCESSING}}
            )
            
            # Simulate minimal processing (skip OCR and AI for now)
            await db.answer_scripts.update_one(
                {"_id": ObjectId(script_id)},
                {"$set": {
                    "status": ScriptStatus.COMPLETED,
                    "processed_at": datetime.utcnow(),
                    "processing_notes": "Minimal processing - services test"
                }}
            )
            
            await close_mongo_connection()
            
            return {
                "script_id": script_id,
                "script_name": script.get('file_name', 'unknown'),
                "student_name": script.get('student_name', 'unknown'),
                "processing_type": "minimal"
            }
        
        self.update_state(
            state='PROGRESS', 
            meta={'stage': 'processing', 'progress': 75, 'script_id': script_id}
        )
        
        result = asyncio.run(process_with_db())
        
        logger.info(f"Minimal processing completed for script {script_id}")
        
        return {
            "status": "success",
            "message": "Minimal processing completed successfully",
            **result,
            "timestamp": str(datetime.now())
        }
        
    except Exception as e:
        logger.error(f"Minimal processing failed for script {script_id}: {e}")
        raise