"""
Routes for criteria extraction functionality.
"""
from fastapi import APIRouter, File, UploadFile, HTTPException
from typing import Dict, List

from ..models.schemas import CriteriaResponse, ErrorResponse
from ..services.criteria_extractor import extract_criteria_from_text
from ..services.document_processor import DocumentProcessor
from ..logger import get_logger

logger = get_logger(__name__)

# Create router
router = APIRouter(
    prefix="/extract-criteria",
    tags=["Criteria Extraction"],
)

@router.post("",
          response_model=CriteriaResponse,
          responses={
              200: {
                  "description": "Successfully extracted criteria",
                  "model": CriteriaResponse
              },
              400: {
                  "description": "Invalid file format or processing error",
                  "model": ErrorResponse
              }
          },
          summary="Extract ranking criteria from job description file")
async def extract_criteria_endpoint(
    file: UploadFile = File(..., description="Job description file (PDF or DOCX)")
) -> Dict[str, List[str]]:
    """
    Extract ranking criteria from an uploaded job description file.
    
    Args:
        file (UploadFile): Job description file in PDF or DOCX format
        
    Returns:
        Dict[str, List[str]]: Dictionary containing list of extracted criteria
        
    Example Output:
        {
          "criteria": [
            "[Required] Must have certification XYZ",
            "[Required] 5+ years of experience in Python development",
            "[Preferred] Strong background in Machine Learning"
          ]
        }
        
    Raises:
        HTTPException: If file processing fails or invalid format
    """
    # Log the request
    logger.info(f"Extracting criteria from file: {file.filename}")
    
    try:
        # Process the uploaded file
        doc_processor = DocumentProcessor()
        content = await doc_processor.extract_text_from_file(file)
        
        # Extract criteria from the content
        criteria_list = await extract_criteria_from_text(content)
        
        # Return the criteria
        return {"criteria": criteria_list}
        
    except ValueError as e:
        logger.error(f"Error processing job description: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
