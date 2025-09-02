from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from .user import PyObjectId

class Concept(BaseModel):
    concept: str
    keywords: List[str]
    weight: float = Field(ge=0.0, le=1.0)
    marks_allocation: float

class Question(BaseModel):
    question_number: int
    max_marks: float
    concepts: List[Concept]

class SchemeFile(BaseModel):
    name: str
    content: str  # For now, storing as text. In production, store file path
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

class EvaluationSchemeBase(BaseModel):
    scheme_name: str
    subject: str
    total_marks: float
    questions: List[Question]
    passing_marks: float = 40.0

class EvaluationSchemeCreate(EvaluationSchemeBase):
    pass

class EvaluationSchemeUpdate(BaseModel):
    scheme_name: Optional[str] = None
    subject: Optional[str] = None
    total_marks: Optional[float] = None
    questions: Optional[List[Question]] = None
    passing_marks: Optional[float] = None

class EvaluationSchemeInDB(EvaluationSchemeBase):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    professor_id: PyObjectId
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    scheme_file: Optional[SchemeFile] = None

class EvaluationScheme(EvaluationSchemeBase):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    professor_id: PyObjectId
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    scheme_file: Optional[SchemeFile] = None