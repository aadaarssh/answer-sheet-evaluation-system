from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from typing import List, Optional
from ..database import get_database
from ..models.user import UserInDB
from ..models.scheme import (
    EvaluationScheme, EvaluationSchemeCreate, EvaluationSchemeUpdate,
    EvaluationSchemeInDB, SchemeFile
)
from ..utils.auth import get_current_active_user
from bson import ObjectId
from datetime import datetime
import logging
import aiofiles
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/schemes", tags=["evaluation_schemes"])

@router.post("/", response_model=EvaluationScheme)
async def create_scheme(
    scheme: EvaluationSchemeCreate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Create a new evaluation scheme."""
    try:
        db = get_database()
        
        # Check if scheme with same name exists for this user
        existing = await db.evaluation_schemes.find_one({
            "professor_id": current_user.id,
            "scheme_name": scheme.scheme_name
        })
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Scheme with this name already exists"
            )
        
        # Create scheme document
        scheme_dict = scheme.dict()
        scheme_dict['professor_id'] = current_user.id
        scheme_dict['created_at'] = datetime.utcnow()
        scheme_dict['updated_at'] = datetime.utcnow()
        
        # Insert into database
        result = await db.evaluation_schemes.insert_one(scheme_dict)
        
        # Retrieve created scheme
        created_scheme = await db.evaluation_schemes.find_one({"_id": result.inserted_id})
        
        return EvaluationScheme(**created_scheme)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating scheme: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create scheme"
        )

@router.get("/", response_model=List[EvaluationScheme])
async def list_schemes(
    skip: int = 0,
    limit: int = 100,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """List evaluation schemes for current user."""
    try:
        db = get_database()
        
        cursor = db.evaluation_schemes.find(
            {"professor_id": current_user.id}
        ).sort("created_at", -1).skip(skip).limit(limit)
        
        schemes = await cursor.to_list(length=limit)
        
        return [EvaluationScheme(**scheme) for scheme in schemes]
        
    except Exception as e:
        logger.error(f"Error listing schemes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list schemes"
        )

@router.get("/{scheme_id}", response_model=EvaluationScheme)
async def get_scheme(
    scheme_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get a specific evaluation scheme."""
    try:
        db = get_database()
        
        scheme = await db.evaluation_schemes.find_one({
            "_id": ObjectId(scheme_id),
            "professor_id": current_user.id
        })
        
        if not scheme:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scheme not found"
            )
        
        return EvaluationScheme(**scheme)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting scheme {scheme_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get scheme"
        )

@router.put("/{scheme_id}", response_model=EvaluationScheme)
async def update_scheme(
    scheme_id: str,
    scheme_update: EvaluationSchemeUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Update an evaluation scheme."""
    try:
        db = get_database()
        
        # Check if scheme exists and belongs to user
        existing_scheme = await db.evaluation_schemes.find_one({
            "_id": ObjectId(scheme_id),
            "professor_id": current_user.id
        })
        
        if not existing_scheme:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scheme not found"
            )
        
        # Update scheme
        update_data = {k: v for k, v in scheme_update.dict().items() if v is not None}
        update_data['updated_at'] = datetime.utcnow()
        
        await db.evaluation_schemes.update_one(
            {"_id": ObjectId(scheme_id)},
            {"$set": update_data}
        )
        
        # Retrieve updated scheme
        updated_scheme = await db.evaluation_schemes.find_one({"_id": ObjectId(scheme_id)})
        
        return EvaluationScheme(**updated_scheme)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating scheme {scheme_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update scheme"
        )

@router.delete("/{scheme_id}")
async def delete_scheme(
    scheme_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Delete an evaluation scheme."""
    try:
        db = get_database()
        
        # Check if scheme exists and belongs to user
        scheme = await db.evaluation_schemes.find_one({
            "_id": ObjectId(scheme_id),
            "professor_id": current_user.id
        })
        
        if not scheme:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scheme not found"
            )
        
        # Check if scheme is being used in any sessions
        sessions = await db.exam_sessions.find_one({"scheme_id": ObjectId(scheme_id)})
        if sessions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete scheme: it is being used in exam sessions"
            )
        
        # Delete scheme
        await db.evaluation_schemes.delete_one({"_id": ObjectId(scheme_id)})
        
        return {"message": "Scheme deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting scheme {scheme_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete scheme"
        )

@router.post("/{scheme_id}/upload-file")
async def upload_scheme_file(
    scheme_id: str,
    file: UploadFile = File(...),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Upload a scheme file (PDF) for the evaluation scheme."""
    try:
        db = get_database()
        
        # Check if scheme exists and belongs to user
        scheme = await db.evaluation_schemes.find_one({
            "_id": ObjectId(scheme_id),
            "professor_id": current_user.id
        })
        
        if not scheme:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scheme not found"
            )
        
        # Validate file type
        if not file.content_type.startswith('application/pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are allowed"
            )
        
        # Read file content
        content = await file.read()
        
        # For now, store as base64 encoded string (in production, use file storage)
        import base64
        encoded_content = base64.b64encode(content).decode('utf-8')
        
        # Create scheme file object
        scheme_file = SchemeFile(
            name=file.filename,
            content=encoded_content,
            uploaded_at=datetime.utcnow()
        )
        
        # Update scheme with file
        await db.evaluation_schemes.update_one(
            {"_id": ObjectId(scheme_id)},
            {
                "$set": {
                    "scheme_file": scheme_file.dict(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return {"message": "Scheme file uploaded successfully", "filename": file.filename}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading scheme file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload scheme file"
        )