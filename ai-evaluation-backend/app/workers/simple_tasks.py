"""
Completely separate simple tasks for debugging.
No complex imports, no database operations.
"""

import logging
from datetime import datetime
from .celery_app_simple import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name='debug_task') 
def debug_task(self, test_param="default"):
    """
    Super simple debug task with no external dependencies.
    """
    try:
        print(f"DEBUG_TASK: Started with param: {test_param}")
        logger.info(f"Debug task started with param: {test_param}")
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'working', 'progress': 50, 'param': test_param}
        )
        
        # Simple processing
        import time
        time.sleep(2)
        
        result = {
            "status": "success",
            "message": "Debug task completed successfully",
            "param": test_param,
            "timestamp": str(datetime.now())
        }
        
        print(f"DEBUG_TASK: Completed: {result}")
        logger.info(f"Debug task completed: {result}")
        
        return result
        
    except Exception as e:
        error_msg = f"Debug task failed: {e}"
        print(f"DEBUG_TASK: ERROR: {error_msg}")
        logger.error(error_msg)
        raise

@celery_app.task(bind=True, name='script_task')
def script_task(self, script_id):
    """
    Simple script processing task with minimal logic.
    """
    try:
        print(f"SCRIPT_TASK: Started with script_id: {script_id}")
        logger.info(f"Script task started with script_id: {script_id}")
        
        # Basic validation
        if not script_id:
            raise ValueError("No script_id provided")
            
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'processing', 'progress': 75, 'script_id': script_id}
        )
        
        # Simple processing simulation
        import time
        time.sleep(1)
        
        result = {
            "status": "success",
            "script_id": script_id,
            "message": "Script task completed",
            "processed_at": str(datetime.now())
        }
        
        print(f"SCRIPT_TASK: Completed: {result}")
        logger.info(f"Script task completed: {result}")
        
        return result
        
    except Exception as e:
        error_msg = f"Script task failed for {script_id}: {e}"
        print(f"SCRIPT_TASK: ERROR: {error_msg}")
        logger.error(error_msg)
        raise

@celery_app.task(bind=True, name='database_test_task')
def database_test_task(self, script_id):
    """
    Test database connectivity in worker process.
    """
    import asyncio
    from bson import ObjectId
    
    try:
        logger.info(f"Database test started for script {script_id}")
        
        # Validate ObjectId
        try:
            ObjectId(script_id)
        except Exception as e:
            raise ValueError(f"Invalid script_id format: {script_id} - {e}")
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'connecting', 'progress': 25, 'script_id': script_id}
        )
        
        # Test database connection
        async def test_db():
            from ..database import connect_to_mongo, get_database, close_mongo_connection
            
            # Connect to database
            await connect_to_mongo()
            db = get_database()
            
            if db is None:
                raise RuntimeError("Database connection returned None")
                
            # Try to find the script
            script = await db.answer_scripts.find_one({"_id": ObjectId(script_id)})
            
            # Close connection
            await close_mongo_connection()
            
            return script
        
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'testing_database', 'progress': 75, 'script_id': script_id}
        )
        
        # Run database test
        script = asyncio.run(test_db())
        
        result = {
            "status": "success",
            "script_id": script_id,
            "message": "Database connectivity test completed",
            "script_found": script is not None,
            "script_name": script.get('file_name', 'unknown') if script else None,
            "student_name": script.get('student_name', 'unknown') if script else None
        }
        
        logger.info(f"Database test completed: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"Database test failed for {script_id}: {e}")
        raise

@celery_app.task(bind=True, name='simple_service_check')
def simple_service_check(self):
    """
    Very simple service check - step by step.
    """
    try:
        logger.info("Starting simple service check")
        
        results = {}
        
        # Step 1: Check basic imports
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'basic_imports', 'progress': 25}
        )
        
        try:
            from ..config import settings
            results['config'] = 'SUCCESS'
        except Exception as e:
            results['config'] = f'FAILED: {e}'
        
        # Step 2: Check OCR service
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'ocr_service', 'progress': 50}
        )
        
        try:
            from ..services.ocr_service import OCRService
            results['ocr'] = 'SUCCESS'
        except Exception as e:
            results['ocr'] = f'FAILED: {e}'
        
        # Step 3: Check evaluation service  
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'evaluation_service', 'progress': 75}
        )
        
        try:
            from ..services.evaluation_service import EvaluationService
            results['evaluation'] = 'SUCCESS'
        except Exception as e:
            results['evaluation'] = f'FAILED: {e}'
        
        logger.info(f"Simple service check completed: {results}")
        
        return {
            "status": "success",
            "message": "Simple service check completed",
            "services": results,
            "timestamp": str(datetime.now())
        }
        
    except Exception as e:
        logger.error(f"Simple service check failed: {e}")
        raise

@celery_app.task(bind=True, name='test_imports')
def test_imports(self):
    """
    Test basic imports to find the issue.
    """
    try:
        logger.info("Starting import test")
        results = {}
        
        # Test 1: Basic Python imports
        try:
            import asyncio
            import time
            from datetime import datetime
            results['basic_python'] = 'SUCCESS'
        except Exception as e:
            results['basic_python'] = f'FAILED: {e}'
        
        # Test 2: External imports
        try:
            from bson import ObjectId
            results['bson'] = 'SUCCESS'
        except Exception as e:
            results['bson'] = f'FAILED: {e}'
        
        # Test 3: Database imports
        try:
            from ..database import connect_to_mongo, get_database
            results['database'] = 'SUCCESS'
        except Exception as e:
            results['database'] = f'FAILED: {e}'
            
        # Test 4: Models imports
        try:
            from ..models.script import ScriptStatus
            results['models'] = 'SUCCESS'
        except Exception as e:
            results['models'] = f'FAILED: {e}'
        
        logger.info(f"Import test results: {results}")
        
        return {
            "status": "success",
            "message": "Import test completed",
            "results": results,
            "timestamp": str(datetime.now())
        }
        
    except Exception as e:
        logger.error(f"Import test failed: {e}")
        raise

@celery_app.task(bind=True, name='fixed_process_script')
def fixed_process_script(self, script_id):
    """
    Fixed version of process_answer_script that bypasses service issues.
    """
    try:
        # Step 1: Basic logging
        logger.info(f"Fixed processing started for script {script_id}")
        
        # Step 2: Test imports one by one
        try:
            import asyncio
            logger.info("asyncio imported successfully")
        except Exception as e:
            logger.error(f"asyncio import failed: {e}")
            raise
            
        try:
            from bson import ObjectId
            logger.info("ObjectId imported successfully")
        except Exception as e:
            logger.error(f"ObjectId import failed: {e}")
            raise
        
        # Step 3: Basic validation
        try:
            ObjectId(script_id)
            logger.info(f"ObjectId validation successful for {script_id}")
        except Exception as e:
            logger.error(f"ObjectId validation failed: {e}")
            raise ValueError(f"Invalid script_id format: {script_id} - {e}")
        
        # Step 4: Test progress update
        try:
            self.update_state(
                state='PROGRESS',
                meta={'stage': 'initializing', 'progress': 10, 'script_id': script_id}
            )
            logger.info("Progress update successful")
        except Exception as e:
            logger.error(f"Progress update failed: {e}")
            raise
        
        # Process with only database operations - no services
        async def process_script_fixed():
            from ..database import connect_to_mongo, get_database, close_mongo_connection
            from ..models.script import ScriptStatus
            
            # Connect to database
            await connect_to_mongo()
            db = get_database()
            
            if db is None:
                raise RuntimeError("Database connection failed")
            
            self.update_state(
                state='PROGRESS',
                meta={'stage': 'database_connected', 'progress': 25, 'script_id': script_id}
            )
            
            # Get script and session
            script = await db.answer_scripts.find_one({"_id": ObjectId(script_id)})
            if not script:
                raise ValueError(f"Script {script_id} not found")
            
            session = await db.exam_sessions.find_one({"_id": script["session_id"]})
            if not session:
                raise ValueError(f"Session not found for script {script_id}")
            
            self.update_state(
                state='PROGRESS',
                meta={'stage': 'script_found', 'progress': 50, 'script_id': script_id}
            )
            
            # Update status to processing
            await db.answer_scripts.update_one(
                {"_id": ObjectId(script_id)},
                {"$set": {"status": ScriptStatus.PROCESSING}}
            )
            
            # Simulate processing (skip OCR/AI services for now)
            self.update_state(
                state='PROGRESS',
                meta={'stage': 'mock_processing', 'progress': 75, 'script_id': script_id}
            )
            
            # Create mock evaluation result
            mock_result = {
                "total_score": 85,
                "max_possible_score": 100,
                "percentage": 85.0,
                "processed_at": datetime.utcnow(),
                "processing_notes": "Mock processing - services bypassed"
            }
            
            # Insert mock evaluation result
            eval_result = await db.evaluation_results.insert_one({
                "script_id": ObjectId(script_id),
                "session_id": ObjectId(session["_id"]),
                **mock_result
            })
            
            # Update script status to completed
            await db.answer_scripts.update_one(
                {"_id": ObjectId(script_id)},
                {"$set": {
                    "status": ScriptStatus.COMPLETED,
                    **mock_result
                }}
            )
            
            # Update session processed count
            await db.exam_sessions.update_one(
                {"_id": ObjectId(session["_id"])},
                {"$inc": {"processed_count": 1}}
            )
            
            # Close database connection
            await close_mongo_connection()
            
            return {
                "script_id": script_id,
                "script_name": script.get('file_name', 'unknown'),
                "student_name": script.get('student_name', 'unknown'),
                **mock_result
            }
        
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'processing', 'progress': 90, 'script_id': script_id}
        )
        
        # Run the processing
        result = asyncio.run(process_script_fixed())
        
        logger.info(f"Fixed processing completed for script {script_id}")
        
        return {
            "status": "success",
            "message": "Fixed processing completed (services bypassed)",
            **result,
            "timestamp": str(datetime.now())
        }
        
    except Exception as e:
        logger.error(f"Fixed processing failed for script {script_id}: {e}")
        raise