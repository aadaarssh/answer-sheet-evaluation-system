from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from ..database import get_database
from ..models.user import UserInDB
from ..models.evaluation import (
    EvaluationResult, ManualReview, ManualReviewStatus, 
    ManualReviewPriority, ReviewReason
)
from ..models.script import AnswerScript
from ..models.session import ExamSession
from ..utils.auth import get_current_active_user
from ..services.ocr_service import OCRService
from ..services.evaluation_service import EvaluationService
from ..services.verification_service import VerificationService
from bson import ObjectId
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/evaluations", tags=["evaluations"])

# Initialize services
ocr_service = OCRService()
evaluation_service = EvaluationService()
verification_service = VerificationService()

@router.post("/process-script/{script_id}")
async def process_single_script(
    script_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Process a single answer script through the complete evaluation pipeline."""
    try:
        db = get_database()
        
        # Get script and verify ownership
        script = await db.answer_scripts.find_one({"_id": ObjectId(script_id)})
        if not script:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Script not found"
            )
        
        # Verify user owns the session
        session = await db.exam_sessions.find_one({
            "_id": script["session_id"],
            "professor_id": current_user.id
        })
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Get evaluation scheme
        scheme = await db.evaluation_schemes.find_one({"_id": session["scheme_id"]})
        if not scheme:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluation scheme not found"
            )
        
        # Update script status to processing
        await db.answer_scripts.update_one(
            {"_id": ObjectId(script_id)},
            {"$set": {"status": "processing"}}
        )
        
        try:
            # Step 1: OCR and question extraction
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
            
            # Step 2: Evaluation
            logger.info(f"Starting evaluation for script {script_id}")
            from ..models.scheme import EvaluationScheme
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
            
            # Step 3: Verification (if enabled)
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
            
            # Step 4: Check if manual review needed
            needs_review = (
                evaluation_result.requires_manual_review or
                verification.flagged_for_review or
                ocr_confidence < 0.6
            )
            
            if needs_review:
                # Create manual review entry
                review_entry = {
                    "script_id": ObjectId(script_id),
                    "evaluation_id": eval_insert_result.inserted_id,
                    "reason": ReviewReason.LOW_CONFIDENCE,
                    "priority": ManualReviewPriority.MEDIUM,
                    "status": ManualReviewStatus.PENDING,
                    "original_score": evaluation_result.total_score,
                    "flagged_at": datetime.utcnow()
                }
                
                await db.manual_review_queue.insert_one(review_entry)
                logger.info(f"Script {script_id} flagged for manual review")
            
            # Update script status to completed
            await db.answer_scripts.update_one(
                {"_id": ObjectId(script_id)},
                {"$set": {"status": "completed"}}
            )
            
            # Update session processed count
            await db.exam_sessions.update_one(
                {"_id": ObjectId(session["_id"])},
                {"$inc": {"processed_count": 1}}
            )
            
            logger.info(f"Successfully processed script {script_id}")
            
            return {
                "message": "Script processed successfully",
                "script_id": script_id,
                "total_score": evaluation_result.total_score,
                "max_score": evaluation_result.max_possible_score,
                "percentage": evaluation_result.percentage,
                "needs_manual_review": needs_review,
                "ocr_confidence": ocr_confidence,
                "verification_confidence": verification.confidence_score
            }
            
        except Exception as processing_error:
            logger.error(f"Error processing script {script_id}: {processing_error}")
            
            # Update script status to failed
            await db.answer_scripts.update_one(
                {"_id": ObjectId(script_id)},
                {
                    "$set": {
                        "status": "failed",
                        "processing_errors": [str(processing_error)]
                    }
                }
            )
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Processing failed: {str(processing_error)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in process_single_script: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process script"
        )

@router.get("/{session_id}/results")
async def get_session_results(
    session_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get evaluation results for all scripts in a session."""
    try:
        db = get_database()
        
        # Verify session ownership
        session = await db.exam_sessions.find_one({
            "_id": ObjectId(session_id),
            "professor_id": current_user.id
        })
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Get evaluation results with script details
        pipeline = [
            {"$match": {"session_id": ObjectId(session_id)}},
            {
                "$lookup": {
                    "from": "answer_scripts",
                    "localField": "script_id",
                    "foreignField": "_id",
                    "as": "script_info"
                }
            },
            {"$unwind": "$script_info"},
            {"$sort": {"evaluated_at": -1}},
            {"$skip": skip},
            {"$limit": limit}
        ]
        
        results = await db.evaluation_results.aggregate(pipeline).to_list(length=limit)
        
        # Format results
        formatted_results = []
        for result in results:
            script_info = result["script_info"]
            
            formatted_result = {
                "id": str(result["_id"]),
                "script_id": str(result["script_id"]),
                "student_name": script_info["student_name"],
                "student_id": script_info["student_id"],
                "file_name": script_info["file_name"],
                "total_score": result["total_score"],
                "max_score": result["max_possible_score"],
                "percentage": result["percentage"],
                "passed": result["percentage"] >= session.get("passing_marks", 40),
                "question_scores": result["question_scores"],
                "requires_manual_review": result.get("requires_manual_review", False),
                "review_reasons": result.get("review_reasons", []),
                "evaluated_at": result["evaluated_at"],
                "verification": result.get("gemini_verification"),
                "manual_override": result.get("manual_override")
            }
            
            formatted_results.append(formatted_result)
        
        # Get summary statistics
        total_results = await db.evaluation_results.count_documents({"session_id": ObjectId(session_id)})
        
        # Calculate pass/fail stats
        pass_count = sum(1 for r in formatted_results if r["passed"])
        fail_count = len(formatted_results) - pass_count
        
        average_score = sum(r["percentage"] for r in formatted_results) / len(formatted_results) if formatted_results else 0
        
        return {
            "session_id": session_id,
            "session_name": session["session_name"],
            "total_results": total_results,
            "results_shown": len(formatted_results),
            "statistics": {
                "total_evaluated": len(formatted_results),
                "passed": pass_count,
                "failed": fail_count,
                "pass_rate": (pass_count / len(formatted_results) * 100) if formatted_results else 0,
                "average_score": round(average_score, 2)
            },
            "results": formatted_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session results: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get session results"
        )

@router.get("/{script_id}/detailed")
async def get_detailed_evaluation(
    script_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get detailed evaluation for a specific script."""
    try:
        db = get_database()
        
        # Get evaluation result
        evaluation = await db.evaluation_results.find_one({"script_id": ObjectId(script_id)})
        if not evaluation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluation not found"
            )
        
        # Verify ownership through session
        session = await db.exam_sessions.find_one({
            "_id": evaluation["session_id"],
            "professor_id": current_user.id
        })
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Get script details
        script = await db.answer_scripts.find_one({"_id": ObjectId(script_id)})
        
        # Get scheme details
        scheme = await db.evaluation_schemes.find_one({"_id": session["scheme_id"]})
        
        return {
            "evaluation": evaluation,
            "script": script,
            "session": {
                "id": str(session["_id"]),
                "name": session["session_name"]
            },
            "scheme": {
                "id": str(scheme["_id"]),
                "name": scheme["scheme_name"],
                "subject": scheme["subject"],
                "total_marks": scheme["total_marks"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting detailed evaluation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get detailed evaluation"
        )

@router.get("/review-queue")
async def get_review_queue(
    status_filter: Optional[ManualReviewStatus] = None,
    priority_filter: Optional[ManualReviewPriority] = None,
    limit: int = 50,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get manual review queue for current user's sessions."""
    try:
        db = get_database()
        
        # Build aggregation pipeline to get reviews for user's sessions
        match_stage = {}
        if status_filter:
            match_stage["status"] = status_filter
        if priority_filter:
            match_stage["priority"] = priority_filter
        
        pipeline = [
            {
                "$lookup": {
                    "from": "evaluation_results",
                    "localField": "evaluation_id",
                    "foreignField": "_id",
                    "as": "evaluation_info"
                }
            },
            {"$unwind": "$evaluation_info"},
            {
                "$lookup": {
                    "from": "exam_sessions",
                    "localField": "evaluation_info.session_id",
                    "foreignField": "_id",
                    "as": "session_info"
                }
            },
            {"$unwind": "$session_info"},
            {"$match": {"session_info.professor_id": current_user.id, **match_stage}},
            {
                "$lookup": {
                    "from": "answer_scripts",
                    "localField": "script_id",
                    "foreignField": "_id",
                    "as": "script_info"
                }
            },
            {"$unwind": "$script_info"},
            {"$sort": {"priority": 1, "flagged_at": 1}},
            {"$limit": limit}
        ]
        
        reviews = await db.manual_review_queue.aggregate(pipeline).to_list(length=limit)
        
        # Format reviews
        formatted_reviews = []
        for review in reviews:
            formatted_review = {
                "id": str(review["_id"]),
                "script_id": str(review["script_id"]),
                "evaluation_id": str(review["evaluation_id"]),
                "student_name": review["script_info"]["student_name"],
                "student_id": review["script_info"]["student_id"],
                "session_name": review["session_info"]["session_name"],
                "subject": review["session_info"].get("subject", ""),
                "reason": review["reason"],
                "priority": review["priority"],
                "status": review["status"],
                "original_score": review["original_score"],
                "manual_score": review.get("manual_score"),
                "flagged_at": review["flagged_at"],
                "reviewed_at": review.get("reviewed_at"),
                "reviewer_notes": review.get("reviewer_notes", "")
            }
            formatted_reviews.append(formatted_review)
        
        return {
            "total_reviews": len(formatted_reviews),
            "reviews": formatted_reviews
        }
        
    except Exception as e:
        logger.error(f"Error getting review queue: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get review queue"
        )

@router.post("/{review_id}/manual-review")
async def submit_manual_review(
    review_id: str,
    review_data: Dict[str, Any],
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Submit manual review for a flagged evaluation."""
    try:
        db = get_database()
        
        # Get review entry and verify ownership
        review = await db.manual_review_queue.find_one({"_id": ObjectId(review_id)})
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found"
            )
        
        # Verify ownership through session
        evaluation = await db.evaluation_results.find_one({"_id": review["evaluation_id"]})
        session = await db.exam_sessions.find_one({
            "_id": evaluation["session_id"],
            "professor_id": current_user.id
        })
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Update review entry
        manual_score = review_data.get("manual_score", review["original_score"])
        reviewer_notes = review_data.get("reviewer_notes", "")
        
        await db.manual_review_queue.update_one(
            {"_id": ObjectId(review_id)},
            {
                "$set": {
                    "manual_score": manual_score,
                    "reviewer_notes": reviewer_notes,
                    "status": ManualReviewStatus.COMPLETED,
                    "reviewed_at": datetime.utcnow(),
                    "assigned_to": current_user.id
                }
            }
        )
        
        # Update evaluation result if score changed
        if manual_score != review["original_score"]:
            # Recalculate based on manual adjustments
            manual_adjustments = {
                review_data.get("question_number", 1): {
                    "score": manual_score,
                    "reason": reviewer_notes
                }
            }
            
            await db.evaluation_results.update_one(
                {"_id": review["evaluation_id"]},
                {
                    "$set": {
                        "manual_override": manual_adjustments,
                        "requires_manual_review": False,
                        "total_score": manual_score  # Simplified - in production, recalculate properly
                    }
                }
            )
        
        return {
            "message": "Manual review submitted successfully",
            "review_id": review_id,
            "manual_score": manual_score,
            "original_score": review["original_score"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting manual review: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit manual review"
        )