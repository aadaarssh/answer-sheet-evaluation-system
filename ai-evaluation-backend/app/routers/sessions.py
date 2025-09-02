from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from ..database import get_database
from ..models.user import UserInDB
from ..models.session import (
    ExamSession, ExamSessionCreate, ExamSessionUpdate,
    SessionStatus, SessionProgress
)
from ..models.scheme import EvaluationScheme
from ..utils.auth import get_current_active_user
from bson import ObjectId
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["exam_sessions"])

@router.post("/", response_model=ExamSession)
async def create_session(
    session: ExamSessionCreate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Create a new exam session."""
    try:
        db = get_database()
        
        # Verify that the scheme exists and belongs to the user
        scheme = await db.evaluation_schemes.find_one({
            "_id": session.scheme_id,
            "professor_id": current_user.id
        })
        
        if not scheme:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluation scheme not found"
            )
        
        # Create session document
        session_dict = session.dict()
        session_dict['professor_id'] = current_user.id
        session_dict['status'] = SessionStatus.PENDING
        session_dict['processed_count'] = 0
        session_dict['created_at'] = datetime.utcnow()
        
        # Insert into database
        result = await db.exam_sessions.insert_one(session_dict)
        
        # Retrieve created session
        created_session = await db.exam_sessions.find_one({"_id": result.inserted_id})
        
        logger.info(f"Created exam session: {created_session['session_name']}")
        
        return ExamSession(**created_session)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating exam session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create exam session"
        )

@router.get("/", response_model=List[ExamSession])
async def list_sessions(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[SessionStatus] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """List exam sessions for current user."""
    try:
        db = get_database()
        
        # Build query
        query = {"professor_id": current_user.id}
        if status_filter:
            query["status"] = status_filter
        
        cursor = db.exam_sessions.find(query).sort("created_at", -1).skip(skip).limit(limit)
        sessions = await cursor.to_list(length=limit)
        
        return [ExamSession(**session) for session in sessions]
        
    except Exception as e:
        logger.error(f"Error listing exam sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list exam sessions"
        )

@router.get("/{session_id}", response_model=ExamSession)
async def get_session(
    session_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get a specific exam session."""
    try:
        db = get_database()
        
        session = await db.exam_sessions.find_one({
            "_id": ObjectId(session_id),
            "professor_id": current_user.id
        })
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exam session not found"
            )
        
        return ExamSession(**session)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting exam session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get exam session"
        )

@router.put("/{session_id}", response_model=ExamSession)
async def update_session(
    session_id: str,
    session_update: ExamSessionUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Update an exam session."""
    try:
        db = get_database()
        
        # Check if session exists and belongs to user
        existing_session = await db.exam_sessions.find_one({
            "_id": ObjectId(session_id),
            "professor_id": current_user.id
        })
        
        if not existing_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exam session not found"
            )
        
        # Update session
        update_data = {k: v for k, v in session_update.dict().items() if v is not None}
        
        await db.exam_sessions.update_one(
            {"_id": ObjectId(session_id)},
            {"$set": update_data}
        )
        
        # Retrieve updated session
        updated_session = await db.exam_sessions.find_one({"_id": ObjectId(session_id)})
        
        return ExamSession(**updated_session)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating exam session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update exam session"
        )

@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Delete an exam session."""
    try:
        db = get_database()
        
        # Check if session exists and belongs to user
        session = await db.exam_sessions.find_one({
            "_id": ObjectId(session_id),
            "professor_id": current_user.id
        })
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exam session not found"
            )
        
        # Check if session has any answer scripts
        scripts = await db.answer_scripts.find_one({"session_id": ObjectId(session_id)})
        if scripts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete session: it contains answer scripts"
            )
        
        # Delete session
        await db.exam_sessions.delete_one({"_id": ObjectId(session_id)})
        
        return {"message": "Exam session deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting exam session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete exam session"
        )

@router.get("/{session_id}/progress", response_model=SessionProgress)
async def get_session_progress(
    session_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get progress information for an exam session."""
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
                detail="Exam session not found"
            )
        
        # Get script counts by status
        pipeline = [
            {"$match": {"session_id": ObjectId(session_id)}},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        
        status_counts = {}
        async for doc in db.answer_scripts.aggregate(pipeline):
            status_counts[doc["_id"]] = doc["count"]
        
        # Calculate totals
        total_scripts = sum(status_counts.values())
        processed = status_counts.get("completed", 0)
        in_progress = status_counts.get("processing", 0)
        failed = status_counts.get("failed", 0)
        pending = status_counts.get("pending", 0)
        
        # Estimate completion time based on processing rate
        estimated_completion = None
        if in_progress > 0 and session.get("created_at"):
            # Simple estimation: assume 2 minutes per script
            remaining_time = (pending + in_progress) * 2  # minutes
            estimated_completion = datetime.utcnow() + timedelta(minutes=remaining_time)
        
        progress = SessionProgress(
            session_id=ObjectId(session_id),
            total_scripts=total_scripts,
            processed=processed,
            in_progress=in_progress,
            failed=failed,
            pending=pending,
            estimated_completion=estimated_completion
        )
        
        return progress
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session progress {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get session progress"
        )