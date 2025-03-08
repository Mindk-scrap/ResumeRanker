"""
Routes for combined pipeline functionality (criteria extraction + resume scoring).
"""
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from typing import List

from ..services.document_processor import DocumentProcessor
from ..services.criteria_extractor import extract_criteria_from_text
from ..routes.scoring import score_resumes
from ..models.schemas import ErrorResponse
from ..logger import get_logger

logger = get_logger(__name__)

# Create router
router = APIRouter(
    prefix="/all",
    tags=["Resume Ranking Pipeline"],
)

@router.post("",
          summary="Extract criteria from job description and rank resumes in one step",
          response_class=StreamingResponse,
          responses={
              200: {
                  "description": "Successfully ranked resumes",
                  "content": {
                      "text/csv": {
                          "example": "Candidate,Criterion 1 Score,Criterion 2 Score,Total Score\nJohn Smith,4,5,9"
                      }
                  }
              },
              400: {
                  "description": "Invalid file format or processing error",
                  "model": ErrorResponse
              }
          })
async def rank_resumes_from_job(
    job_description: UploadFile = File(..., description="Job description file (PDF or DOCX)"),
    resumes: List[UploadFile] = File(..., description="Resume files (PDF or DOCX)")
) -> StreamingResponse:
    """
    Extract ranking criteria from a job description and score resumes against it in one step.
    
    This endpoint combines two operations:
    1. Extracts ranking criteria from the job description file
    2. Scores the provided resumes against those criteria
    
    The output is a CSV file containing:
    - Candidate names (extracted from resumes)
    - Individual scores for each criterion (0-5 scale)
    - Total score
    - Any processing errors
    
    Args:
        job_description (UploadFile): Job description file in PDF or DOCX format
        resumes (List[UploadFile]): List of resume files in PDF or DOCX format
        
    Returns:
        StreamingResponse: CSV file with scoring results
        
    Raises:
        HTTPException: If file processing fails or invalid format
    """
    # Log the request
    logger.info(f"Ranking {len(resumes)} resumes against job description: {job_description.filename}")
    
    try:
        # Extract text from job description file
        doc_processor = DocumentProcessor()
        jd_content = await doc_processor.extract_text_from_file(job_description)
        
        # Extract criteria from job description
        criteria_list = await extract_criteria_from_text(jd_content)
        
        if not criteria_list:
            logger.warning("No criteria extracted from job description")
            raise HTTPException(status_code=400, detail="No criteria could be extracted from the job description")
            
        logger.info(f"Extracted {len(criteria_list)} criteria from job description")
        
        # Convert criteria list to JSON
        import json
        criteria_json = json.dumps(criteria_list)
        
        # Score resumes using the extracted criteria
        return await score_resumes(criteria=criteria_json, resumes=resumes)
        
    except ValueError as e:
        logger.error(f"Error in ranking pipeline: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"Unexpected error in ranking pipeline: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
