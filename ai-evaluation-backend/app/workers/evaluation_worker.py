from celery import current_task
from .celery_app import celery_app
from ..database import get_database
from ..services.ocr_service import OCRService
from ..services.evaluation_service import EvaluationService
from ..services.verification_service import VerificationService
from ..services.notification_service import NotificationService
from ..models.script import ScriptStatus
from ..models.evaluation import ReviewReason, ManualReviewStatus, ManualReviewPriority
from ..models.scheme import EvaluationScheme
from bson import ObjectId
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)

# Initialize services
ocr_service = OCRService()
evaluation_service = EvaluationService()
verification_service = VerificationService()
notification_service = NotificationService()

@celery_app.task(bind=True, name='app.workers.evaluation_worker.process_answer_script')
def process_answer_script(self, script_id: str):
    """
    Process a single answer script through the complete evaluation pipeline.
    
    Args:
        script_id: ID of the answer script to process
    """
    try:
        logger.info(f"Starting processing of script {script_id}")
        
        # Update task progress
        current_task.update_state(
            state='PROGRESS',
            meta={'stage': 'initializing', 'progress': 0}
        )
        
        # Run async processing in sync context
        result = asyncio.run(_process_script_async(script_id, current_task))
        
        logger.info(f"Successfully processed script {script_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error processing script {script_id}: {e}")
        
        # Update script status to failed in database
        asyncio.run(_update_script_status(script_id, ScriptStatus.FAILED, [str(e)]))
        
        # Re-raise the exception to mark task as failed
        raise

async def _process_script_async(script_id: str, task):
    """Async version of script processing."""
    try:
        db = get_database()
        
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
            raise ValueError(f"Evaluation scheme not found for script {script_id}")
        
        # Update script status to processing
        await db.answer_scripts.update_one(
            {"_id": ObjectId(script_id)},
            {"$set": {"status": ScriptStatus.PROCESSING}}
        )
        
        # Step 1: OCR and question extraction (20% progress)
        task.update_state(
            state='PROGRESS',
            meta={'stage': 'ocr', 'progress': 20}
        )
        
        logger.info(f"Starting OCR for script {script_id}")
        extracted_questions, ocr_confidence = await ocr_service.extract_and_segment_questions(
            script["image_path"]
        )
        
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
            meta={'stage': 'evaluation', 'progress': 60}
        )
        
        logger.info(f"Starting evaluation for script {script_id}")
        scheme_obj = EvaluationScheme(**scheme)
        
        evaluation_result = await evaluation_service.evaluate_answer_script(
            extracted_questions, scheme_obj
        )
        
        # Add script and session IDs
        evaluation_result.script_id = ObjectId(script_id)
        evaluation_result.session_id = ObjectId(session["_id"])
        
        # Save evaluation result
        result_dict = evaluation_result.dict()
        result_dict["script_id"] = ObjectId(script_id)
        result_dict["session_id"] = ObjectId(session["_id"])
        
        eval_insert_result = await db.evaluation_results.insert_one(result_dict)
        
        # Step 3: Verification (80% progress)
        task.update_state(
            state='PROGRESS',
            meta={'stage': 'verification', 'progress': 80}
        )
        
        logger.info(f"Starting verification for script {script_id}")
        student_answers = {
            q.question_number: q.raw_text for q in extracted_questions
        }
        
        verification = await verification_service.verify_evaluation(
            evaluation_result, scheme_obj, student_answers
        )
        
        # Update evaluation with verification
        await db.evaluation_results.update_one(
            {"_id": eval_insert_result.inserted_id},
            {"$set": {"gemini_verification": verification.dict()}}
        )
        
        # Step 4: Check if manual review needed (90% progress)
        task.update_state(
            state='PROGRESS',
            meta={'stage': 'review_check', 'progress': 90}
        )
        
        needs_review = (
            evaluation_result.requires_manual_review or
            verification.flagged_for_review or
            ocr_confidence < 0.6
        )
        
        if needs_review:
            # Determine priority based on severity
            priority = ManualReviewPriority.HIGH if ocr_confidence < 0.4 else ManualReviewPriority.MEDIUM
            
            # Create manual review entry
            review_entry = {
                "script_id": ObjectId(script_id),
                "evaluation_id": eval_insert_result.inserted_id,
                "reason": _determine_review_reason(evaluation_result, verification, ocr_confidence),
                "priority": priority,
                "status": ManualReviewStatus.PENDING,
                "original_score": evaluation_result.total_score,
                "flagged_at": datetime.utcnow()
            }
            
            await db.manual_review_queue.insert_one(review_entry)
            logger.info(f"Script {script_id} flagged for manual review")
        
        # Step 5: Finalization (100% progress)
        task.update_state(
            state='PROGRESS',
            meta={'stage': 'finalizing', 'progress': 100}
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
        
        return {
            "script_id": script_id,
            "total_score": evaluation_result.total_score,
            "max_score": evaluation_result.max_possible_score,
            "percentage": evaluation_result.percentage,
            "needs_manual_review": needs_review,
            "ocr_confidence": ocr_confidence,
            "verification_confidence": verification.confidence_score
        }
        
    except Exception as e:
        logger.error(f"Error in async processing for script {script_id}: {e}")
        raise

@celery_app.task(bind=True, name='app.workers.evaluation_worker.batch_process_session')
def batch_process_session(self, session_id: str):
    """
    Process all pending scripts in a session.
    
    Args:
        session_id: ID of the exam session to process
    """
    try:
        logger.info(f"Starting batch processing for session {session_id}")
        
        # Update task progress
        current_task.update_state(
            state='PROGRESS',
            meta={'stage': 'initializing', 'progress': 0, 'processed': 0, 'total': 0}
        )
        
        # Run async processing
        result = asyncio.run(_batch_process_session_async(session_id, current_task))
        
        logger.info(f"Successfully completed batch processing for session {session_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error in batch processing for session {session_id}: {e}")
        raise

async def _batch_process_session_async(session_id: str, task):
    """Async version of batch session processing."""
    try:
        db = get_database()
        
        # Get session
        session = await db.exam_sessions.find_one({"_id": ObjectId(session_id)})
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Get all pending scripts in the session
        pending_scripts = await db.answer_scripts.find(
            {"session_id": ObjectId(session_id), "status": ScriptStatus.PENDING}
        ).to_list(length=1000)
        
        total_scripts = len(pending_scripts)
        if total_scripts == 0:
            return {"message": "No pending scripts to process", "processed": 0}
        
        # Update session status to processing
        await db.exam_sessions.update_one(
            {"_id": ObjectId(session_id)},
            {"$set": {"status": "processing"}}
        )
        
        processed_count = 0
        failed_count = 0
        
        # Process each script
        for i, script in enumerate(pending_scripts):
            try:
                # Update progress
                progress = int((i / total_scripts) * 100)
                task.update_state(
                    state='PROGRESS',
                    meta={
                        'stage': 'processing_scripts',
                        'progress': progress,
                        'processed': processed_count,
                        'failed': failed_count,
                        'total': total_scripts,
                        'current_script': script["student_name"]
                    }
                )
                
                # Process the script
                await _process_script_async(str(script["_id"]), None)
                processed_count += 1
                
                logger.info(f"Processed script {i+1}/{total_scripts}: {script['student_name']}")
                
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to process script {script['_id']}: {e}")
                
                # Update script status to failed
                await db.answer_scripts.update_one(
                    {"_id": script["_id"]},
                    {
                        "$set": {
                            "status": ScriptStatus.FAILED,
                            "processing_errors": [str(e)]
                        }
                    }
                )
        
        # Update session status to completed
        await db.exam_sessions.update_one(
            {"_id": ObjectId(session_id)},
            {
                "$set": {
                    "status": "completed",
                    "completed_at": datetime.utcnow()
                }
            }
        )
        
        # Send notification to professor
        try:
            await notification_service.send_batch_completion_notification(
                session_id, processed_count, failed_count, total_scripts
            )
        except Exception as e:
            logger.warning(f"Failed to send completion notification: {e}")
        
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
        
        # Update session status to failed
        try:
            await db.exam_sessions.update_one(
                {"_id": ObjectId(session_id)},
                {"$set": {"status": "failed"}}
            )
        except:
            pass
        
        raise

async def _update_script_status(script_id: str, status: ScriptStatus, errors: list = None):
    """Update script status in database."""
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
    """Determine the primary reason for manual review."""
    if ocr_confidence < 0.6:
        return ReviewReason.OCR_ERRORS
    elif verification.flagged_for_review:
        return ReviewReason.GEMINI_FLAG
    elif evaluation_result.percentage < 30:  # Very low score
        return ReviewReason.BELOW_PASSING
    else:
        return ReviewReason.LOW_CONFIDENCE

# Task to clean up old completed tasks
@celery_app.task(name='app.workers.evaluation_worker.cleanup_old_tasks')
def cleanup_old_tasks():
    """Clean up old task results and temporary files."""
    try:
        logger.info("Starting cleanup of old tasks")
        
        # This would implement cleanup logic for old files and database entries
        # For now, just log the cleanup attempt
        
        logger.info("Cleanup completed successfully")
        return {"message": "Cleanup completed"}
        
    except Exception as e:
        logger.error(f"Error in cleanup task: {e}")
        raise