from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum
from bson import ObjectId
from .user import PyObjectId

class SessionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ExamSessionBase(BaseModel):
    session_name: str
    total_students: int = 0

class ExamSessionCreate(ExamSessionBase):
    scheme_id: PyObjectId

class ExamSessionUpdate(BaseModel):
    session_name: Optional[str] = None
    total_students: Optional[int] = None
    processed_count: Optional[int] = None
    status: Optional[SessionStatus] = None

class ExamSessionInDB(ExamSessionBase):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    professor_id: PyObjectId
    scheme_id: PyObjectId
    processed_count: int = 0
    status: SessionStatus = SessionStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    estimated_completion: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class ExamSession(ExamSessionBase):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    professor_id: PyObjectId
    scheme_id: PyObjectId
    processed_count: int = 0
    status: SessionStatus = SessionStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    estimated_completion: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class SessionProgress(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    session_id: PyObjectId
    total_scripts: int
    processed: int
    in_progress: int
    failed: int
    pending: int
    estimated_completion: Optional[datetime]
    last_updated: datetime = Field(default_factory=datetime.utcnow)