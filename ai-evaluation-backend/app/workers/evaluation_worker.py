import logging
import asyncio
import os
from datetime import datetime
from bson import ObjectId

# Import Celery - use simple configuration to avoid unpacking errors
try:
    from .celery_app_simple import celery_app
    celery_config_type = "simple"
except ImportError:
    from .celery_app import celery_app
    celery_config_type = "standard"

# Database and services
from ..database import get_database
from ..models.script import ScriptStatus
from ..models.evaluation import ReviewReason, ManualReviewStatus, ManualReviewPriority  
from ..models.scheme import EvaluationScheme

logger = logging.getLogger(__name__)
logger.info(f"Using {celery_config_type} Celery configuration")

@celery_app.task(bind=True, name='test_task')
def test_task(self, test_param="default"):
    """
    Simple test task to validate Celery setup.
    
    Args:
        test_param (str): Simple parameter for testing
    """
    try:
        logger.info("Test task started")
        logger.info(f"Test parameter received: {test_param}")
        
        # Update task progress
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'testing', 'progress': 50, 'param': test_param}
        )
        
        # Simulate some work
        import time
        time.sleep(2)
        
        logger.info("Test task completed successfully")
        
        return {
            "status": "success",
            "message": "Test task executed successfully",
            "param_received": test_param,
            "timestamp": str(datetime.now())
        }
        
    except Exception as e:
        logger.error(f"Test task failed: {e}")
        raise

# Initialize services with error handling
ocr_service = None
evaluation_service = None
verification_service = None
notification_service = None

try:
    from ..services.ocr_service import OCRService
    from ..services.evaluation_service import EvaluationService
    from ..services.verification_service import VerificationService
    from ..services.notification_service import NotificationService
    
    ocr_service = OCRService()
    evaluation_service = EvaluationService()
    verification_service = VerificationService() 
    notification_service = NotificationService()
    logger.info("Worker services initialized successfully")
except Exception as e:
    logger.warning(f"Some services failed to initialize: {e}")

@celery_app.task(bind=True, name='process_answer_script_simple')  
def process_answer_script_simple(self, script_id):
    """
    Simplified version with database connection test.
    """
    import asyncio
    
    try:
        logger.info(f"Simple processing started for script {script_id}")
        
        # Basic validation
        if not script_id:
            raise ValueError("No script_id provided")
            
        # Validate ObjectId format
        try:
            ObjectId(script_id)
        except Exception as e:
            raise ValueError(f"Invalid script_id format: {script_id} - {e}")
        
        # Update task progress
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'validating', 'progress': 25, 'script_id': script_id}
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
            meta={'stage': 'testing_database', 'progress': 50, 'script_id': script_id}
        )
        
        # Run database test
        script = asyncio.run(test_db())
        
        if script:
            message = f"Found script: {script.get('file_name', 'unknown')}"
            logger.info(message)
        else:
            message = f"Script {script_id} not found in database"
            logger.warning(message)
            
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'completed', 'progress': 100, 'script_id': script_id}
        )
        
        return {
            "status": "success",
            "script_id": script_id,
            "message": "Simple processing with database test completed",
            "script_found": script is not None,
            "script_name": script.get('file_name', 'unknown') if script else None
        }
        
    except Exception as e:
        logger.error(f"Error in simple processing for script {script_id}: {e}")
        raise

@celery_app.task(bind=True, name='working_process_script')
def working_process_script(self, script_id):
    """
    Working version of process_answer_script - placed in evaluation_worker.py.
    """
    import asyncio
    
    try:
        logger.info(f"Working processing started for script {script_id}")
        
        # Validate ObjectId format
        try:
            ObjectId(script_id)
        except Exception as e:
            raise ValueError(f"Invalid script_id format: {script_id} - {e}")
        
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'initializing', 'progress': 20, 'script_id': script_id}
        )
        
        # Process with database operations only
        async def process_script_working():
            from ..database import connect_to_mongo, get_database, close_mongo_connection
            from ..models.script import ScriptStatus
            
            # Connect to database
            await connect_to_mongo()
            db = get_database()
            
            if db is None:
                raise RuntimeError("Database connection failed")
            
            # Get script and session
            script = await db.answer_scripts.find_one({"_id": ObjectId(script_id)})
            if not script:
                raise ValueError(f"Script {script_id} not found")
            
            session = await db.exam_sessions.find_one({"_id": script["session_id"]})
            if not session:
                raise ValueError(f"Session not found for script {script_id}")
            
            # Update status to processing
            await db.answer_scripts.update_one(
                {"_id": ObjectId(script_id)},
                {"$set": {"status": ScriptStatus.PROCESSING}}
            )
            
            # Create a working evaluation result (mock for now)
            mock_result = {
                "total_score": 75,
                "max_possible_score": 100, 
                "percentage": 75.0,
                "processed_at": datetime.now(),
                "processing_notes": "Working processing - core functionality only"
            }
            
            # Insert evaluation result
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
            meta={'stage': 'processing', 'progress': 75, 'script_id': script_id}
        )
        
        # Run the processing
        result = asyncio.run(process_script_working())
        
        logger.info(f"Working processing completed for script {script_id}")
        
        return {
            "status": "success", 
            "message": "Working processing completed successfully",
            **result
        }
        
    except Exception as e:
        logger.error(f"Working processing failed for script {script_id}: {e}")
        raise

@celery_app.task(bind=True, name='minimal_working_script')
def minimal_working_script(self, script_id):
    """
    Absolutely minimal version following database_test_task pattern exactly.
    """
    import asyncio
    
    try:
        logger.info(f"Minimal working processing started for script {script_id}")
        
        # Validate ObjectId format (same as database_test_task)
        try:
            ObjectId(script_id)
        except Exception as e:
            raise ValueError(f"Invalid script_id format: {script_id} - {e}")
        
        # Update progress (same as database_test_task)
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'connecting', 'progress': 25, 'script_id': script_id}
        )
        
        # Database test (exactly like database_test_task)
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
        
        # Run database test (same as database_test_task)
        script = asyncio.run(test_db())
        
        result = {
            "status": "success",
            "script_id": script_id,
            "message": "Minimal working processing completed",
            "script_found": script is not None,
            "script_name": script.get('file_name', 'unknown') if script else None,
            "student_name": script.get('student_name', 'unknown') if script else None
        }
        
        logger.info(f"Minimal working processing completed: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"Minimal working processing failed for {script_id}: {e}")
        raise

@celery_app.task(bind=True, name='step_by_step_script')
def step_by_step_script(self, script_id):
    """
    Step by step version - add one feature at a time.
    """
    import asyncio
    
    try:
        logger.info(f"Step by step processing started for script {script_id}")
        
        # Validate ObjectId format (working)
        try:
            ObjectId(script_id)
        except Exception as e:
            raise ValueError(f"Invalid script_id format: {script_id} - {e}")
        
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'connecting', 'progress': 25, 'script_id': script_id}
        )
        
        # Step by step database processing
        async def process_step_by_step():
            from ..database import connect_to_mongo, get_database, close_mongo_connection
            
            # Connect to database (working)
            await connect_to_mongo()
            db = get_database()
            
            if db is None:
                raise RuntimeError("Database connection returned None")
            
            # Get script (working)
            script = await db.answer_scripts.find_one({"_id": ObjectId(script_id)})
            if not script:
                raise ValueError(f"Script {script_id} not found")
            
            # NEW: Get session
            session = await db.exam_sessions.find_one({"_id": script["session_id"]})
            if not session:
                raise ValueError(f"Session not found for script {script_id}")
            
            # Close connection (working)
            await close_mongo_connection()
            
            return {
                "script_id": script_id,
                "script_name": script.get('file_name', 'unknown'),
                "student_name": script.get('student_name', 'unknown'),
                "session_id": str(session["_id"]),
                "session_name": session.get('name', 'unknown')
            }
        
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'testing_database', 'progress': 75, 'script_id': script_id}
        )
        
        # Run step by step processing
        result = asyncio.run(process_step_by_step())
        
        return {
            "status": "success",
            "message": "Step by step processing completed",
            **result
        }
        
    except Exception as e:
        logger.error(f"Step by step processing failed for script {script_id}: {e}")
        raise

@celery_app.task(bind=True, name='complete_working_script')
def complete_working_script(self, script_id):
    """
    Complete working version that processes scripts end-to-end.
    """
    import asyncio
    
    try:
        logger.info(f"Complete processing started for script {script_id}")
        
        # Validate ObjectId format
        try:
            ObjectId(script_id)
        except Exception as e:
            raise ValueError(f"Invalid script_id format: {script_id} - {e}")
        
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'initializing', 'progress': 10, 'script_id': script_id}
        )
        
        # Complete processing function
        async def process_complete():
            from ..database import connect_to_mongo, get_database, close_mongo_connection
            from ..models.script import ScriptStatus
            
            # Connect to database
            await connect_to_mongo()
            db = get_database()
            
            if db is None:
                raise RuntimeError("Database connection failed")
            
            self.update_state(
                state='PROGRESS',
                meta={'stage': 'database_connected', 'progress': 20, 'script_id': script_id}
            )
            
            # Get script and validate
            script = await db.answer_scripts.find_one({"_id": ObjectId(script_id)})
            if not script:
                raise ValueError(f"Script {script_id} not found")
            
            # Get session and scheme
            session = await db.exam_sessions.find_one({"_id": script["session_id"]})
            if not session:
                raise ValueError(f"Session not found for script {script_id}")
            
            scheme = await db.evaluation_schemes.find_one({"_id": session["scheme_id"]})
            if not scheme:
                raise ValueError(f"Scheme not found for session {session['_id']}")
            
            self.update_state(
                state='PROGRESS',
                meta={'stage': 'script_validation', 'progress': 30, 'script_id': script_id}
            )
            
            # Update status to processing
            await db.answer_scripts.update_one(
                {"_id": ObjectId(script_id)},
                {"$set": {"status": ScriptStatus.PROCESSING}}
            )
            
            # Step 1: Mock OCR Processing (skip actual OCR for now)
            self.update_state(
                state='PROGRESS',
                meta={'stage': 'ocr_processing', 'progress': 50, 'script_id': script_id}
            )
            
            # Create mock extracted questions
            mock_questions = [
                {
                    "question_number": 1,
                    "raw_text": "Sample answer text for question 1",
                    "confidence": 0.85
                },
                {
                    "question_number": 2, 
                    "raw_text": "Sample answer text for question 2",
                    "confidence": 0.90
                }
            ]
            
            # Step 2: Mock Evaluation (skip actual AI evaluation for now)
            self.update_state(
                state='PROGRESS',
                meta={'stage': 'evaluation', 'progress': 70, 'script_id': script_id}
            )
            
            # Create mock evaluation result
            total_score = 85
            max_score = 100
            evaluation_result = {
                "total_score": total_score,
                "max_possible_score": max_score,
                "percentage": (total_score / max_score) * 100,
                "questions_evaluated": mock_questions,
                "requires_manual_review": False,
                "processed_at": datetime.utcnow(),
                "processing_notes": "Mock evaluation - core pipeline working"
            }
            
            # Save evaluation result
            eval_result = await db.evaluation_results.insert_one({
                "script_id": ObjectId(script_id),
                "session_id": ObjectId(session["_id"]),
                **evaluation_result
            })
            
            self.update_state(
                state='PROGRESS',
                meta={'stage': 'finalizing', 'progress': 90, 'script_id': script_id}
            )
            
            # Update script with results
            await db.answer_scripts.update_one(
                {"_id": ObjectId(script_id)},
                {"$set": {
                    "status": ScriptStatus.COMPLETED,
                    "questions_extracted": mock_questions,
                    **evaluation_result
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
                "session_id": str(session["_id"]),
                "evaluation_id": str(eval_result.inserted_id),
                **evaluation_result
            }
        
        # Run the complete processing
        result = asyncio.run(process_complete())
        
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'completed', 'progress': 100, 'script_id': script_id}
        )
        
        logger.info(f"Complete processing finished for script {script_id}")
        
        return {
            "status": "success",
            "message": "Complete script processing successful",
            **result
        }
        
    except Exception as e:
        logger.error(f"Complete processing failed for script {script_id}: {e}")
        
        # Try to update script status to failed
        try:
            import asyncio
            from ..database import connect_to_mongo, get_database, close_mongo_connection
            from ..models.script import ScriptStatus
            
            async def update_failed_status():
                await connect_to_mongo()
                db = get_database()
                if db:
                    await db.answer_scripts.update_one(
                        {"_id": ObjectId(script_id)},
                        {"$set": {
                            "status": ScriptStatus.FAILED,
                            "processing_errors": [str(e)]
                        }}
                    )
                    await close_mongo_connection()
            
            asyncio.run(update_failed_status())
        except:
            pass  # Don't let error handling fail the main error
            
        raise

@celery_app.task(bind=True, name='process_answer_script')
def process_answer_script(self, script_id):
    """
    Process a single answer script - REAL AI PROCESSING VERSION.
    Uses actual OpenAI Vision API, AI evaluation, and Gemini verification.
    """
    import asyncio
    
    try:
        logger.info(f"🚀 STARTING REAL AI PROCESSING for script {script_id}")
        
        # Validate ObjectId format
        try:
            ObjectId(script_id)
        except Exception as e:
            raise ValueError(f"Invalid script_id format: {script_id} - {e}")
        
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'initializing', 'progress': 5, 'script_id': script_id}
        )
        
        # Real AI processing implementation
        result = asyncio.run(_real_ai_process_script(script_id, self))
        
        logger.info(f"✅ REAL AI PROCESSING COMPLETED for script {script_id}")
        
        return {
            "status": "success",
            "message": "Script processed successfully with REAL AI evaluation",
            **result
        }
        
    except Exception as e:
        logger.error(f"❌ REAL AI PROCESSING FAILED for script {script_id}: {e}")
        
        # Update script status to failed
        try:
            import asyncio
            from ..database import connect_to_mongo, get_database, close_mongo_connection
            from ..models.script import ScriptStatus
            
            async def update_failed():
                await connect_to_mongo()
                db = get_database()
                if db:
                    await db.answer_scripts.update_one(
                        {"_id": ObjectId(script_id)},
                        {"$set": {
                            "status": ScriptStatus.FAILED,
                            "processing_errors": [str(e)],
                            "failed_at": datetime.utcnow()
                        }}
                    )
                    await close_mongo_connection()
            
            asyncio.run(update_failed())
        except:
            logger.error("Could not update script status to failed")
            
        raise

async def _real_ai_process_script(script_id: str, task):
    """
    Real AI processing pipeline with 7 comprehensive steps:
    1. Database connection & data retrieval
    2. Image file validation  
    3. Real OCR processing with OpenAI Vision API
    4. Real AI evaluation with semantic similarity
    5. Gemini verification
    6. Manual review check
    7. Completion with results storage
    """
    try:
        logger.info(f"🔄 STEP 1: Database connection & data retrieval for script {script_id}")
        
        # Connect to database
        from ..database import connect_to_mongo, get_database, close_mongo_connection
        await connect_to_mongo()
        db = get_database()
        
        if db is None:
            raise RuntimeError("Failed to establish database connection")
        
        # Get script document
        script = await db.answer_scripts.find_one({"_id": ObjectId(script_id)})
        if not script:
            raise ValueError(f"Script {script_id} not found in database")
            
        logger.info(f"✅ Found script: {script.get('file_name', 'unknown')} for student: {script.get('student_name', 'unknown')}")
        
        # Get session and scheme  
        session = await db.exam_sessions.find_one({"_id": script["session_id"]})
        if not session:
            raise ValueError(f"Session not found for script {script_id}")
            
        scheme = await db.evaluation_schemes.find_one({"_id": session["scheme_id"]})
        if not scheme:
            raise ValueError(f"Evaluation scheme not found for session {session['_id']}")
            
        logger.info(f"✅ Session: {session.get('name', 'unknown')}, Scheme: {scheme.get('name', 'unknown')}")
        
        # Update script status to processing
        await db.answer_scripts.update_one(
            {"_id": ObjectId(script_id)},
            {"$set": {"status": ScriptStatus.PROCESSING, "started_at": datetime.utcnow()}}
        )
        
        task.update_state(
            state='PROGRESS',
            meta={'stage': 'database_connected', 'progress': 15, 'script_id': script_id}
        )
        
        # Broadcast WebSocket update
        try:
            from ..websockets import websocket_manager
            await websocket_manager.broadcast_processing_stage(
                script_id, "database_connected", 15, 
                estimated_time=45,
                details={"script_name": script.get('file_name', 'unknown')}
            )
        except Exception as e:
            logger.warning(f"Failed to broadcast WebSocket update: {e}")
        
        # ==================== STEP 2: Image file validation ====================
        logger.info(f"🔄 STEP 2: Image file validation for script {script_id}")
        
        image_path = script.get("image_path")
        if not image_path:
            raise ValueError(f"No image_path found for script {script_id}")
            
        if not os.path.exists(image_path):
            raise ValueError(f"Image file not found at path: {image_path}")
            
        # Get file info
        file_stats = os.stat(image_path)
        file_size_mb = file_stats.st_size / (1024 * 1024)
        
        logger.info(f"✅ Image validated: {os.path.basename(image_path)}, Size: {file_size_mb:.2f}MB")
        
        task.update_state(
            state='PROGRESS',
            meta={'stage': 'image_validated', 'progress': 25, 'script_id': script_id}
        )
        
        # Broadcast WebSocket update
        try:
            from ..websockets import websocket_manager
            await websocket_manager.broadcast_processing_stage(
                script_id, "image_validated", 25, 
                estimated_time=35,
                details={"file_size_mb": file_size_mb, "file_name": os.path.basename(image_path)}
            )
        except Exception as e:
            logger.warning(f"Failed to broadcast WebSocket update: {e}")
        
        # ==================== STEP 3: Real OCR processing with OpenAI Vision API ====================
        logger.info(f"🔄 STEP 3: Real OCR processing with OpenAI Vision API for script {script_id}")
        
        if not ocr_service:
            raise RuntimeError("OCR Service not initialized - check API keys")
            
        # Extract questions using real OpenAI Vision API
        start_time = datetime.utcnow()
        extracted_questions, ocr_confidence = await ocr_service.extract_and_segment_questions(image_path)
        ocr_duration = (datetime.utcnow() - start_time).total_seconds()
        
        logger.info(f"✅ OCR completed: {len(extracted_questions)} questions extracted")
        logger.info(f"✅ OCR confidence: {ocr_confidence}, Processing time: {ocr_duration:.2f}s")
        
        # Log OCR details
        for i, question in enumerate(extracted_questions):
            preview = question.raw_text[:100] + "..." if len(question.raw_text) > 100 else question.raw_text
            logger.info(f"   Q{question.question_number}: {preview} (confidence: {getattr(question, 'confidence', 'N/A')})")
            
        if ocr_confidence == 0:
            logger.error("❌ CRITICAL: OCR confidence is 0 - API issue or image processing failed")
            raise RuntimeError("OCR processing failed with 0 confidence")
            
        # Update script with OCR results
        questions_data = [q.dict() for q in extracted_questions]
        await db.answer_scripts.update_one(
            {"_id": ObjectId(script_id)},
            {
                "$set": {
                    "questions_extracted": questions_data,
                    "ocr_confidence": ocr_confidence,
                    "ocr_processing_time": ocr_duration,
                    "ocr_processed_at": datetime.utcnow()
                }
            }
        )
        
        task.update_state(
            state='PROGRESS',
            meta={'stage': 'ocr_completed', 'progress': 45, 'script_id': script_id}
        )
        
        # Broadcast WebSocket update
        try:
            from ..websockets import websocket_manager
            await websocket_manager.broadcast_processing_stage(
                script_id, "ocr_completed", 45, 
                estimated_time=25,
                details={
                    "questions_extracted": len(extracted_questions),
                    "ocr_confidence": ocr_confidence,
                    "ocr_duration": ocr_duration
                }
            )
        except Exception as e:
            logger.warning(f"Failed to broadcast WebSocket update: {e}")
        
        # ==================== STEP 4: Real AI evaluation with semantic similarity ====================
        logger.info(f"🔄 STEP 4: Real AI evaluation with semantic similarity for script {script_id}")
        
        if not evaluation_service:
            raise RuntimeError("Evaluation Service not initialized - check configuration")
            
        # Create evaluation scheme object
        from ..models.scheme import EvaluationScheme
        scheme_obj = EvaluationScheme(**scheme)
        
        # Perform real AI evaluation
        eval_start_time = datetime.utcnow()
        
        # Get evaluation result data (dict format)
        try:
            result_dict = await evaluation_service.evaluate_answer_script(extracted_questions, scheme_obj)
            eval_duration = (datetime.utcnow() - eval_start_time).total_seconds()
            
            # Add required IDs and metadata
            result_dict["script_id"] = ObjectId(script_id)
            result_dict["session_id"] = ObjectId(session["_id"])
            result_dict["processing_time"] = eval_duration
            
            # Create properly structured EvaluationResult
            from ..models.evaluation import EvaluationResult
            evaluation_result = EvaluationResult(**result_dict)
            
            logger.info(f"✅ AI Evaluation completed: {evaluation_result.total_score}/{evaluation_result.max_possible_score}")
            logger.info(f"✅ Percentage: {evaluation_result.percentage:.1f}%, Processing time: {eval_duration:.2f}s")
            logger.info(f"✅ Requires manual review: {evaluation_result.requires_manual_review}")
            
            # Log individual question scores
            if hasattr(evaluation_result, 'question_scores'):
                for qeval in evaluation_result.question_scores:
                    logger.info(f"   Q{qeval.question_number}: {qeval.score}/{qeval.max_score} pts")
                    
        except Exception as e:
            logger.error(f"❌ Evaluation failed: {e}")
            raise RuntimeError(f"AI evaluation failed: {e}")
        
        # Save evaluation result to database
        save_dict = evaluation_result.dict()
        save_dict["evaluated_at"] = datetime.utcnow()
        
        eval_result = await db.evaluation_results.insert_one(save_dict)
        logger.info(f"✅ Evaluation result saved with ID: {eval_result.inserted_id}")
        
        task.update_state(
            state='PROGRESS',
            meta={'stage': 'evaluation_completed', 'progress': 65, 'script_id': script_id}
        )
        
        # ==================== STEP 5: Gemini verification ====================
        logger.info(f"🔄 STEP 5: Gemini verification for script {script_id}")
        
        verification = None
        verification_confidence = 0.0
        
        if verification_service:
            try:
                # Prepare student answers for verification
                student_answers = {q.question_number: q.raw_text for q in extracted_questions}
                
                # Perform Gemini verification
                verify_start_time = datetime.utcnow()
                verification = await verification_service.verify_evaluation(
                    evaluation_result, scheme_obj, student_answers
                )
                verify_duration = (datetime.utcnow() - verify_start_time).total_seconds()
                
                verification_confidence = getattr(verification, 'confidence_score', 0.0)
                
                logger.info(f"✅ Gemini verification completed: confidence {verification_confidence}")
                logger.info(f"✅ Verification time: {verify_duration:.2f}s")
                logger.info(f"✅ Flagged for review: {getattr(verification, 'flagged_for_review', False)}")
                
                # Update evaluation result with verification
                await db.evaluation_results.update_one(
                    {"_id": eval_result.inserted_id},
                    {
                        "$set": {
                            "gemini_verification": verification.dict(),
                            "verification_confidence": verification_confidence,
                            "verified_at": datetime.utcnow()
                        }
                    }
                )
                
            except Exception as e:
                logger.warning(f"⚠️ Gemini verification failed: {e}")
                verification = None
        else:
            logger.warning("⚠️ Verification service not available")
            
        task.update_state(
            state='PROGRESS',
            meta={'stage': 'verification_completed', 'progress': 80, 'script_id': script_id}
        )
        
        # ==================== STEP 6: Manual review check ====================
        logger.info(f"🔄 STEP 6: Manual review check for script {script_id}")
        
        # Determine if manual review is needed
        needs_review = (
            evaluation_result.requires_manual_review or
            ocr_confidence < 0.6 or
            (verification and getattr(verification, 'flagged_for_review', False)) or
            evaluation_result.percentage < 30
        )
        
        review_reasons = []
        if evaluation_result.requires_manual_review:
            review_reasons.append("AI evaluation flagged")
        if ocr_confidence < 0.6:
            review_reasons.append(f"Low OCR confidence ({ocr_confidence:.2f})")
        if verification and getattr(verification, 'flagged_for_review', False):
            review_reasons.append("Gemini verification flagged")
        if evaluation_result.percentage < 30:
            review_reasons.append(f"Low score ({evaluation_result.percentage:.1f}%)")
            
        logger.info(f"✅ Manual review needed: {needs_review}")
        if needs_review:
            logger.info(f"✅ Review reasons: {', '.join(review_reasons)}")
            
        if needs_review:
            priority = ManualReviewPriority.HIGH if ocr_confidence < 0.4 else ManualReviewPriority.MEDIUM
            
            review_entry = {
                "script_id": ObjectId(script_id),
                "evaluation_id": eval_result.inserted_id,
                "reason": _determine_review_reason(evaluation_result, verification, ocr_confidence),
                "priority": priority,
                "status": ManualReviewStatus.PENDING,
                "original_score": evaluation_result.total_score,
                "review_reasons": review_reasons,
                "flagged_at": datetime.utcnow()
            }
            
            await db.manual_review_queue.insert_one(review_entry)
            logger.info(f"✅ Added to manual review queue with {priority} priority")
            
        task.update_state(
            state='PROGRESS',
            meta={'stage': 'review_check_completed', 'progress': 90, 'script_id': script_id}
        )
        
        # ==================== STEP 7: Completion with results storage ====================
        logger.info(f"🔄 STEP 7: Completion with results storage for script {script_id}")
        
        # Final script update with all results
        final_update = {
            "status": ScriptStatus.COMPLETED,
            "completed_at": datetime.utcnow(),
            "total_score": evaluation_result.total_score,
            "max_possible_score": evaluation_result.max_possible_score,
            "percentage": evaluation_result.percentage,
            "requires_manual_review": needs_review,
            "processing_summary": {
                "ocr_confidence": ocr_confidence,
                "questions_extracted": len(extracted_questions),
                "verification_confidence": verification_confidence,
                "total_processing_time": (datetime.utcnow() - start_time).total_seconds()
            }
        }
        
        await db.answer_scripts.update_one(
            {"_id": ObjectId(script_id)},
            {"$set": final_update}
        )
        
        # Update session processed count
        await db.exam_sessions.update_one(
            {"_id": ObjectId(session["_id"])},
            {"$inc": {"processed_count": 1}}
        )
        
        logger.info(f"✅ Script {script_id} processing completed successfully")
        logger.info(f"✅ Final score: {evaluation_result.total_score}/{evaluation_result.max_possible_score} ({evaluation_result.percentage:.1f}%)")
        
        # Close database connection
        await close_mongo_connection()
        
        task.update_state(
            state='PROGRESS',
            meta={'stage': 'completed', 'progress': 100, 'script_id': script_id}
        )
        
        # Prepare final result
        final_result = {
            "script_id": script_id,
            "script_name": script.get('file_name', 'unknown'),
            "student_name": script.get('student_name', 'unknown'),
            "total_score": evaluation_result.total_score,
            "max_score": evaluation_result.max_possible_score,
            "percentage": evaluation_result.percentage,
            "questions_extracted": len(extracted_questions),
            "ocr_confidence": ocr_confidence,
            "verification_confidence": verification_confidence,
            "requires_manual_review": needs_review,
            "evaluation_id": str(eval_result.inserted_id),
            "processing_time": (datetime.utcnow() - start_time).total_seconds()
        }
        
        # Broadcast completion WebSocket update
        try:
            from ..websockets import websocket_manager
            await websocket_manager.broadcast_processing_complete(script_id, final_result)
        except Exception as e:
            logger.warning(f"Failed to broadcast completion WebSocket update: {e}")
        
        return final_result
        
    except Exception as e:
        logger.error(f"❌ Real AI processing failed at step for script {script_id}: {e}")
        
        # Try to update script status to failed
        try:
            await db.answer_scripts.update_one(
                {"_id": ObjectId(script_id)},
                {"$set": {
                    "status": ScriptStatus.FAILED,
                    "processing_errors": [str(e)],
                    "failed_at": datetime.utcnow()
                }}
            )
            await close_mongo_connection()
        except:
            pass
            
        raise

async def _process_script_async(script_id: str, task):
    """Process script asynchronously."""
    try:
        # Ensure database connection is established in worker process
        from ..database import connect_to_mongo, get_database, close_mongo_connection
        
        # Connect to database
        await connect_to_mongo()
        db = get_database()
        
        if db is None:
            raise RuntimeError("Failed to establish database connection")
        
        # Get script
        script = await db.answer_scripts.find_one({"_id": ObjectId(script_id)})
        if not script:
            raise ValueError(f"Script {script_id} not found")
            
        # Get session and scheme
        session = await db.exam_sessions.find_one({"_id": script["session_id"]})
        if not session:
            raise ValueError(f"Session not found for script {script_id}")
            
        scheme = await db.evaluation_schemes.find_one({"_id": session["scheme_id"]})
        if not scheme:
            raise ValueError(f"Scheme not found for script {script_id}")
        
        # Update script status
        await db.answer_scripts.update_one(
            {"_id": ObjectId(script_id)},
            {"$set": {"status": ScriptStatus.PROCESSING}}
        )
        
        # Step 1: OCR Processing (20% progress)
        task.update_state(
            state='PROGRESS', 
            meta={'stage': 'ocr', 'progress': 20, 'script_id': script_id}
        )
        
        logger.info(f"Starting OCR for script {script_id}")
        
        # Check if image exists
        image_path = script["image_path"]
        if not os.path.exists(image_path):
            raise ValueError(f"Image file not found: {image_path}")
        
        extracted_questions, ocr_confidence = await ocr_service.extract_and_segment_questions(image_path)
        
        # Update script with OCR results
        await db.answer_scripts.update_one(
            {"_id": ObjectId(script_id)},
            {
                "$set": {
                    "questions_extracted": [q.dict() for q in extracted_questions],
                    "ocr_confidence": ocr_confidence,
                    "processed_at": datetime.utcnow()
                }
            }
        )
        
        # Step 2: Evaluation (60% progress)
        task.update_state(
            state='PROGRESS',
            meta={'stage': 'evaluation', 'progress': 60, 'script_id': script_id}
        )
        
        logger.info(f"Starting evaluation for script {script_id}")
        scheme_obj = EvaluationScheme(**scheme)
        
        evaluation_result = await evaluation_service.evaluate_answer_script(
            extracted_questions, scheme_obj
        )
        
        # Add IDs to evaluation result
        evaluation_result.script_id = ObjectId(script_id)
        evaluation_result.session_id = ObjectId(session["_id"])
        
        # Save evaluation result
        result_dict = evaluation_result.dict()
        result_dict["script_id"] = ObjectId(script_id)
        result_dict["session_id"] = ObjectId(session["_id"])
        
        eval_result = await db.evaluation_results.insert_one(result_dict)
        
        # Step 3: Verification (80% progress)
        task.update_state(
            state='PROGRESS',
            meta={'stage': 'verification', 'progress': 80, 'script_id': script_id}
        )
        
        logger.info(f"Starting verification for script {script_id}")
        student_answers = {q.question_number: q.raw_text for q in extracted_questions}
        
        verification = await verification_service.verify_evaluation(
            evaluation_result, scheme_obj, student_answers
        )
        
        # Update evaluation with verification
        await db.evaluation_results.update_one(
            {"_id": eval_result.inserted_id},
            {"$set": {"gemini_verification": verification.dict()}}
        )
        
        # Step 4: Manual review check (90% progress)
        task.update_state(
            state='PROGRESS',
            meta={'stage': 'review_check', 'progress': 90, 'script_id': script_id}
        )
        
        needs_review = (
            evaluation_result.requires_manual_review or
            getattr(verification, 'flagged_for_review', False) or
            ocr_confidence < 0.6
        )
        
        if needs_review:
            priority = ManualReviewPriority.HIGH if ocr_confidence < 0.4 else ManualReviewPriority.MEDIUM
            
            review_entry = {
                "script_id": ObjectId(script_id),
                "evaluation_id": eval_result.inserted_id,
                "reason": _determine_review_reason(evaluation_result, verification, ocr_confidence),
                "priority": priority,
                "status": ManualReviewStatus.PENDING,
                "original_score": evaluation_result.total_score,
                "flagged_at": datetime.utcnow()
            }
            
            await db.manual_review_queue.insert_one(review_entry)
            logger.info(f"Script {script_id} flagged for manual review")
        
        # Step 5: Completion (100% progress)
        task.update_state(
            state='PROGRESS',
            meta={'stage': 'completed', 'progress': 100, 'script_id': script_id}
        )
        
        # Update script status to completed
        await db.answer_scripts.update_one(
            {"_id": ObjectId(script_id)},
            {"$set": {"status": ScriptStatus.COMPLETED}}
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
            "total_score": evaluation_result.total_score,
            "max_score": evaluation_result.max_possible_score,
            "percentage": evaluation_result.percentage,
            "needs_manual_review": needs_review,
            "ocr_confidence": ocr_confidence,
            "verification_confidence": getattr(verification, 'confidence_score', 0.0)
        }
        
    except Exception as e:
        logger.error(f"Error in async processing for script {script_id}: {e}")
        # Try to close connection on error
        try:
            await close_mongo_connection()
        except:
            pass
        raise

@celery_app.task(bind=True, name='batch_process_session')
def batch_process_session(self, session_id):
    """
    Process all pending scripts in a session.
    
    Args:
        session_id (str): ID of the exam session to process
    """
    try:
        logger.info(f"Starting batch processing for session {session_id}")
        
        # Validate session_id
        if not session_id:
            raise ValueError("No session_id provided")
            
        try:
            ObjectId(session_id)
        except Exception:
            raise ValueError(f"Invalid session_id format: {session_id}")
        
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'initializing', 'progress': 0, 'session_id': session_id}
        )
        
        result = asyncio.run(_batch_process_session_async(session_id, self))
        
        logger.info(f"Successfully completed batch processing for session {session_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error in batch processing for session {session_id}: {e}")
        raise

async def _batch_process_session_async(session_id: str, task):
    """Process session batch asynchronously."""
    try:
        db = get_database()
        
        # Get session
        session = await db.exam_sessions.find_one({"_id": ObjectId(session_id)})
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Get pending scripts
        pending_scripts = await db.answer_scripts.find(
            {"session_id": ObjectId(session_id), "status": ScriptStatus.PENDING}
        ).to_list(length=1000)
        
        total_scripts = len(pending_scripts)
        if total_scripts == 0:
            return {"message": "No pending scripts to process", "processed": 0}
        
        # Update session status
        await db.exam_sessions.update_one(
            {"_id": ObjectId(session_id)},
            {"$set": {"status": "processing"}}
        )
        
        processed_count = 0
        failed_count = 0
        
        # Process each script
        for i, script in enumerate(pending_scripts):
            try:
                progress = int((i / total_scripts) * 100)
                task.update_state(
                    state='PROGRESS',
                    meta={
                        'stage': 'processing_scripts',
                        'progress': progress,
                        'processed': processed_count,
                        'failed': failed_count,
                        'total': total_scripts,
                        'current_script': script.get("student_name", "Unknown"),
                        'session_id': session_id
                    }
                )
                
                await _process_script_async(str(script["_id"]), None)
                processed_count += 1
                
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to process script {script['_id']}: {e}")
                
                await db.answer_scripts.update_one(
                    {"_id": script["_id"]},
                    {
                        "$set": {
                            "status": ScriptStatus.FAILED,
                            "processing_errors": [str(e)]
                        }
                    }
                )
        
        # Update session status
        await db.exam_sessions.update_one(
            {"_id": ObjectId(session_id)},
            {
                "$set": {
                    "status": "completed",
                    "completed_at": datetime.utcnow()
                }
            }
        )
        
        return {
            "message": "Batch processing completed",
            "session_id": session_id,
            "total_scripts": total_scripts,
            "processed_successfully": processed_count,
            "failed": failed_count,
            "success_rate": (processed_count / total_scripts * 100) if total_scripts > 0 else 0
        }
        
    except Exception as e:
        logger.error(f"Error in batch session processing: {e}")
        raise

async def _update_script_status(script_id: str, status: ScriptStatus, errors: list = None):
    """Update script status."""
    try:
        db = get_database()
        update_data = {"status": status}
        
        if errors:
            update_data["processing_errors"] = errors
            
        await db.answer_scripts.update_one(
            {"_id": ObjectId(script_id)},
            {"$set": update_data}
        )
        
    except Exception as e:
        logger.error(f"Error updating script status: {e}")

def _determine_review_reason(evaluation_result, verification, ocr_confidence):
    """Determine review reason."""
    if ocr_confidence < 0.6:
        return ReviewReason.OCR_ERRORS
    elif getattr(verification, 'flagged_for_review', False):
        return ReviewReason.GEMINI_FLAG
    elif evaluation_result.percentage < 30:
        return ReviewReason.BELOW_PASSING
    else:
        return ReviewReason.LOW_CONFIDENCE