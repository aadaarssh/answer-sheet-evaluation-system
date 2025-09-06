from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
import aiofiles
from pathlib import Path
import uuid
from datetime import datetime

from ..database import get_database
from ..models.user import UserInDB
from ..models.script import AnswerScript, AnswerScriptCreate, ScriptStatus
from ..models.session import ExamSession
from ..utils.auth import get_current_active_user
from ..utils.image_processing import validate_image, extract_image_metadata
from ..config import settings
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

# Import Celery tasks with error handling
CELERY_AVAILABLE = False
process_answer_script = None
batch_process_session = None

try:
    from ..workers.evaluation_worker import process_answer_script, batch_process_session
    CELERY_AVAILABLE = True
    logger.info("Celery tasks imported successfully")
except ImportError as e:
    logger.warning(f"Celery tasks not available: {e}")
except Exception as e:
    logger.error(f"Error importing Celery tasks: {e}")

router = APIRouter(prefix="/scripts", tags=["answer_scripts"])

@router.post("/upload-batch")
async def upload_batch_scripts(
    session_id: str = Form(...),
    files: List[UploadFile] = File(...),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Upload multiple answer script images for batch processing."""
    try:
        db = get_database()
        
        # Verify session exists and belongs to user
        session = await db.exam_sessions.find_one({
            "_id": ObjectId(session_id),
            "professor_id": current_user.id
        })
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exam session not found"
            )
        
        if not files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No files provided"
            )
        
        # Create session upload directory
        session_dir = Path(settings.upload_dir) / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        uploaded_scripts = []
        errors = []
        
        for file in files:
            try:
                # Validate file
                if not file.content_type or not file.content_type.startswith('image/'):
                    errors.append(f"{file.filename}: Invalid file type. Only images allowed.")
                    continue
                
                # Check file size (in MB)
                file.file.seek(0, 2)  # Seek to end
                file_size = file.file.tell()
                file.file.seek(0)  # Reset to beginning
                
                if file_size > settings.max_file_size_mb * 1024 * 1024:
                    errors.append(f"{file.filename}: File too large. Maximum {settings.max_file_size_mb}MB allowed.")
                    continue
                
                # Generate unique filename
                file_extension = Path(file.filename).suffix.lower()
                unique_filename = f"{uuid.uuid4()}{file_extension}"
                file_path = session_dir / unique_filename
                
                # Save file
                async with aiofiles.open(file_path, 'wb') as f:
                    content = await file.read()
                    await f.write(content)
                
                # Validate saved image
                is_valid, error_msg = validate_image(str(file_path))
                if not is_valid:
                    # Remove invalid file
                    os.unlink(file_path)
                    errors.append(f"{file.filename}: {error_msg}")
                    continue
                
                # Extract student info from filename if possible
                student_name, student_id = extract_student_info_from_filename(file.filename)
                
                # Create answer script record
                script_data = {
                    "session_id": ObjectId(session_id),
                    "student_name": student_name,
                    "student_id": student_id,
                    "file_name": file.filename,
                    "image_path": str(file_path),
                    "status": ScriptStatus.PENDING,
                    "processing_errors": [],
                    "created_at": datetime.utcnow(),
                    "ocr_confidence": 0.0
                }
                
                # Insert into database
                result = await db.answer_scripts.insert_one(script_data)
                
                # Get created script
                created_script = await db.answer_scripts.find_one({"_id": result.inserted_id})
                uploaded_scripts.append(AnswerScript(**created_script))
                
                logger.info(f"Uploaded script: {file.filename}")
                
            except Exception as e:
                logger.error(f"Error processing file {file.filename}: {e}")
                errors.append(f"{file.filename}: {str(e)}")
        
        # Update session total students count
        await db.exam_sessions.update_one(
            {"_id": ObjectId(session_id)},
            {"$set": {"total_students": len(uploaded_scripts)}}
        )
        
        # Determine processing mode based on count
        processing_mode = "real_time" if len(uploaded_scripts) <= settings.real_time_threshold else "async"
        
        response = {
            "message": f"Uploaded {len(uploaded_scripts)} files successfully",
            "uploaded_count": len(uploaded_scripts),
            "error_count": len(errors),
            "errors": errors,
            "processing_mode": processing_mode,
            "scripts": [{"id": str(script.id), "filename": script.file_name} for script in uploaded_scripts]
        }
        
        # Start processing based on mode
        if CELERY_AVAILABLE and process_answer_script and batch_process_session:
            try:
                if processing_mode == "real_time":
                    # Trigger individual processing for each script
                    processing_tasks = []
                    for script in uploaded_scripts:
                        try:
                            task = process_answer_script.delay(str(script.id))
                            processing_tasks.append({
                                "script_id": str(script.id),
                                "task_id": task.id,
                                "filename": script.file_name
                            })
                            logger.info(f"Queued script {script.id} for processing. Task ID: {task.id}")
                        except Exception as e:
                            logger.error(f"Failed to queue script {script.id}: {e}")
                            errors.append(f"{script.file_name}: Failed to queue for processing")
                    
                    response["processing_tasks"] = processing_tasks
                    response["message"] += f". Processing started immediately for {len(processing_tasks)} scripts."
                    
                else:
                    # Queue entire session for batch processing
                    try:
                        task = batch_process_session.delay(session_id)
                        response["batch_task_id"] = task.id
                        response["message"] += ". Queued for batch processing."
                        logger.info(f"Queued session {session_id} for batch processing. Task ID: {task.id}")
                    except Exception as e:
                        logger.error(f"Failed to queue session {session_id} for batch processing: {e}")
                        response["message"] += ". Upload successful but processing queue failed."
                        
            except Exception as e:
                logger.error(f"Error during task queuing: {e}")
                response["message"] += ". Upload successful but processing unavailable."
        else:
            logger.warning("Celery not available. Processing will not start automatically.")
            response["message"] += ". Processing will be available when worker is started."
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload files"
        )

@router.post("/upload-single")
async def upload_single_script(
    session_id: str = Form(...),
    student_name: str = Form(...),
    student_id: str = Form(...),
    file: UploadFile = File(...),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Upload a single answer script for immediate processing."""
    try:
        db = get_database()
        
        # Verify session
        session = await db.exam_sessions.find_one({
            "_id": ObjectId(session_id),
            "professor_id": current_user.id
        })
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exam session not found"
            )
        
        # Validate file
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Only images allowed."
            )
        
        # Check file size
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        
        if file_size > settings.max_file_size_mb * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum {settings.max_file_size_mb}MB allowed."
            )
        
        # Create session directory
        session_dir = Path(settings.upload_dir) / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        file_extension = Path(file.filename).suffix.lower()
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = session_dir / unique_filename
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Validate image
        is_valid, error_msg = validate_image(str(file_path))
        if not is_valid:
            os.unlink(file_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid image: {error_msg}"
            )
        
        # Create answer script record
        script_data = {
            "session_id": ObjectId(session_id),
            "student_name": student_name,
            "student_id": student_id,
            "file_name": file.filename,
            "image_path": str(file_path),
            "status": ScriptStatus.PENDING,
            "processing_errors": [],
            "created_at": datetime.utcnow(),
            "ocr_confidence": 0.0
        }
        
        # Insert into database
        result = await db.answer_scripts.insert_one(script_data)
        created_script = await db.answer_scripts.find_one({"_id": result.inserted_id})
        
        logger.info(f"Uploaded single script: {file.filename}")
        
        response = {
            "message": "File uploaded successfully",
            "script_id": str(result.inserted_id),
            "filename": file.filename,
            "processing_mode": "real_time"
        }
        
        # Trigger immediate processing if Celery is available
        if CELERY_AVAILABLE and process_answer_script:
            try:
                task = process_answer_script.delay(str(result.inserted_id))
                response["task"] = {
                    "task_id": task.id,
                    "status": "queued"
                }
                response["message"] += " and queued for processing"
                logger.info(f"Queued script {result.inserted_id} for immediate processing. Task ID: {task.id}")
            except Exception as e:
                logger.error(f"Failed to queue script {result.inserted_id} for processing: {e}")
                response["message"] += " but processing queue failed"
        else:
            response["message"] += " but processing unavailable (worker not started)"
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading single file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file"
        )

@router.get("/{session_id}/status")
async def get_session_scripts_status(
    session_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get status of all scripts in a session."""
    try:
        db = get_database()
        
        # Verify session belongs to user
        session = await db.exam_sessions.find_one({
            "_id": ObjectId(session_id),
            "professor_id": current_user.id
        })
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Get all scripts in the session
        cursor = db.answer_scripts.find(
            {"session_id": ObjectId(session_id)},
            {
                "student_name": 1,
                "student_id": 1,
                "file_name": 1,
                "status": 1,
                "created_at": 1,
                "processed_at": 1,
                "processing_errors": 1,
                "ocr_confidence": 1
            }
        ).sort("created_at", 1)
        
        scripts = await cursor.to_list(length=1000)
        
        # Calculate summary stats
        status_counts = {}
        for script in scripts:
            status = script["status"]
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "session_id": session_id,
            "total_scripts": len(scripts),
            "status_counts": status_counts,
            "scripts": [
                {
                    "id": str(script["_id"]),
                    "student_name": script["student_name"],
                    "student_id": script["student_id"],
                    "filename": script["file_name"],
                    "status": script["status"],
                    "created_at": script["created_at"].isoformat(),
                    "processed_at": script.get("processed_at").isoformat() if script.get("processed_at") else None,
                    "has_errors": len(script.get("processing_errors", [])) > 0,
                    "ocr_confidence": script.get("ocr_confidence", 0.0)
                }
                for script in scripts
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session scripts status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get scripts status"
        )

@router.get("/{script_id}/details")
async def get_script_details(
    script_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get detailed information about a specific script."""
    try:
        db = get_database()
        
        # Get script
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
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Script not found"
            )
        
        # Get evaluation result if exists
        evaluation = await db.evaluation_results.find_one({"script_id": ObjectId(script_id)})
        
        # Get image metadata
        metadata = extract_image_metadata(script["image_path"]) if os.path.exists(script["image_path"]) else {}
        
        script_details = AnswerScript(**script)
        
        return {
            "script": script_details,
            "evaluation": evaluation,
            "image_metadata": metadata,
            "session_info": {
                "id": str(session["_id"]),
                "name": session["session_name"],
                "status": session["status"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting script details {script_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get script details"
        )

@router.get("/task/{task_id}/status")
async def get_task_status(
    task_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get the status of a Celery task."""
    try:
        if not CELERY_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Task processing not available. Worker not started."
            )
        
        from ..workers.celery_app import celery_app
        
        # Get task result
        result = celery_app.AsyncResult(task_id)
        
        response = {
            "task_id": task_id,
            "status": result.status,
            "ready": result.ready()
        }
        
        if result.info:
            response["info"] = result.info
        
        if result.successful():
            response["result"] = result.result
        elif result.failed():
            response["error"] = str(result.info)
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting task status {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get task status"
        )

def extract_student_info_from_filename(filename: str) -> tuple[str, str]:
    """
    Extract student name and ID from filename using common patterns.
    
    Args:
        filename: The uploaded filename
        
    Returns:
        tuple: (student_name, student_id)
    """
    # Remove file extension
    name_without_ext = Path(filename).stem
    
    # Common patterns: 
    # "John_Doe_123456.jpg" -> ("John Doe", "123456")
    # "123456_John_Doe.jpg" -> ("John Doe", "123456")
    # "JohnDoe123456.jpg" -> ("Unknown", "Unknown")
    
    # Try pattern: Name_ID or ID_Name
    parts = name_without_ext.replace('_', ' ').split()
    
    if len(parts) >= 2:
        # Check if last part is numeric (student ID)
        if parts[-1].isdigit():
            student_id = parts[-1]
            student_name = ' '.join(parts[:-1])
            return (student_name, student_id)
        # Check if first part is numeric (student ID)
        elif parts[0].isdigit():
            student_id = parts[0]
            student_name = ' '.join(parts[1:])
            return (student_name, student_id)
    
    # Default fallback
    return ("Unknown", "Unknown")