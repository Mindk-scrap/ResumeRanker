from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class ErrorResponse(BaseModel):
    """Response model for errors"""
    detail: str
    status_code: Optional[int] = None

class CriteriaRequest(BaseModel):
    """Request model for extracting criteria from job description"""
    job_description: str

class CriteriaResponse(BaseModel):
    """Response model for extracted criteria"""
    criteria: List[str]

class NameExtractionResult(BaseModel):
    """Result model for name extraction"""
    name: str
    confidence: int = Field(..., ge=0, le=100)
    source: str

class ScoreObject(BaseModel):
    """Model for individual score object"""
    criterion: str
    score: int = Field(..., ge=0, le=5)
    justification: Optional[str] = None

class ScoringResponse(BaseModel):
    """Response model for resume scoring result"""
    scores: List[ScoreObject]

class ResumeScoreResult(BaseModel):
    """Complete result model for a scored resume"""
    candidate_name: str
    scores: Dict[str, int]
    total_score: Optional[int] = None
    error: Optional[str] = None
