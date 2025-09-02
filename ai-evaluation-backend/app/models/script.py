from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from bson import ObjectId
from .user import PyObjectId

class ScriptStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    MANUAL_REVIEW = "manual_review"
    FAILED = "failed"

class QuestionFragment(BaseModel):
    fragment_text: str
    confidence: float = Field(ge=0.0, le=1.0)
    page_number: Optional[int] = None
    position: Optional[Dict[str, Any]] = None  # For storing coordinates

class ExtractedQuestion(BaseModel):
    question_number: int
    raw_text: str
    fragments: List[QuestionFragment] = []
    is_complete: bool = True
    has_duplicates: bool = False
    confidence: float = Field(ge=0.0, le=1.0)

class AnswerScriptBase(BaseModel):
    student_name: str
    student_id: str
    file_name: str

class AnswerScriptCreate(AnswerScriptBase):
    session_id: PyObjectId

class AnswerScriptUpdate(BaseModel):
    ocr_text: Optional[str] = None
    questions_extracted: Optional[List[ExtractedQuestion]] = None
    status: Optional[ScriptStatus] = None
    processing_errors: Optional[List[str]] = None

class AnswerScriptInDB(AnswerScriptBase):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    session_id: PyObjectId
    image_path: str
    ocr_text: Optional[str] = None
    questions_extracted: List[ExtractedQuestion] = []
    status: ScriptStatus = ScriptStatus.PENDING
    processing_errors: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    ocr_confidence: float = 0.0

class AnswerScript(AnswerScriptBase):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    session_id: PyObjectId
    image_path: str
    ocr_text: Optional[str] = None
    questions_extracted: List[ExtractedQuestion] = []
    status: ScriptStatus = ScriptStatus.PENDING
    processing_errors: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    ocr_confidence: float = 0.0