from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from bson import ObjectId
from .user import PyObjectId

class ConceptEvaluation(BaseModel):
    concept: str
    similarity_score: float = Field(ge=0.0, le=1.0)
    marks_awarded: float
    max_marks: float
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: Optional[str] = None

class QuestionEvaluation(BaseModel):
    question_number: int
    score: float
    max_score: float
    concept_breakdown: List[ConceptEvaluation]
    overall_confidence: float = Field(ge=0.0, le=1.0)
    needs_review: bool = False
    review_reasons: List[str] = []

class GeminiVerification(BaseModel):
    verified: bool
    confidence_score: float = Field(ge=0.0, le=1.0)
    suggested_adjustments: List[Dict[str, Any]] = []
    flagged_for_review: bool = False
    verification_notes: str = ""
    original_score: Optional[float] = None
    suggested_score: Optional[float] = None

class EvaluationResultBase(BaseModel):
    total_score: float
    max_possible_score: float
    percentage: float = Field(ge=0.0, le=100.0)

class EvaluationResultCreate(EvaluationResultBase):
    script_id: PyObjectId
    session_id: PyObjectId
    question_scores: List[QuestionEvaluation]

class EvaluationResultUpdate(BaseModel):
    total_score: Optional[float] = None
    max_possible_score: Optional[float] = None
    percentage: Optional[float] = None
    question_scores: Optional[List[QuestionEvaluation]] = None
    gemini_verification: Optional[GeminiVerification] = None
    requires_manual_review: Optional[bool] = None
    review_reasons: Optional[List[str]] = None

class ReviewReason(str, Enum):
    LOW_CONFIDENCE = "low_confidence"
    BELOW_PASSING = "below_passing"
    OCR_ERRORS = "ocr_errors"
    GEMINI_FLAG = "gemini_flag"
    PROCESSING_ERROR = "processing_error"

class EvaluationResultInDB(EvaluationResultBase):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    script_id: PyObjectId
    session_id: PyObjectId
    question_scores: List[QuestionEvaluation]
    gemini_verification: Optional[GeminiVerification] = None
    requires_manual_review: bool = False
    review_reasons: List[ReviewReason] = []
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
    manual_override: Optional[Dict[str, Any]] = None

class EvaluationResult(EvaluationResultBase):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    script_id: PyObjectId
    session_id: PyObjectId
    question_scores: List[QuestionEvaluation]
    gemini_verification: Optional[GeminiVerification] = None
    requires_manual_review: bool = False
    review_reasons: List[ReviewReason] = []
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
    manual_override: Optional[Dict[str, Any]] = None

class ManualReviewPriority(str, Enum):
    HIGH = 1
    MEDIUM = 2
    LOW = 3

class ManualReviewStatus(str, Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    COMPLETED = "completed"

class ManualReview(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    script_id: PyObjectId
    evaluation_id: PyObjectId
    reason: ReviewReason
    priority: ManualReviewPriority = ManualReviewPriority.MEDIUM
    assigned_to: Optional[PyObjectId] = None
    status: ManualReviewStatus = ManualReviewStatus.PENDING
    original_score: float
    manual_score: Optional[float] = None
    reviewer_notes: str = ""
    flagged_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = None