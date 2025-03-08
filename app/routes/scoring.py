"""
Routes for resume scoring functionality.
"""
from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from typing import Dict, List, Any
import json
import os
import time

from ..models.schemas import ErrorResponse
from ..services.document_processor import DocumentProcessor
from ..services.name_extractor import extract_candidate_name
from ..services.resume_scorer import score_resume_against_criteria
from ..services.result_formatter import generate_csv_from_scores
from ..logger import get_logger

logger = get_logger(__name__)

# Create router
router = APIRouter(
    prefix="/score-resumes",
    tags=["Resume Scoring"],
)

@router.post("",
          responses={
              200: {
                  "description": "Successfully scored resumes",
                  "content": {
                      "text/csv": {
                          "schema": {
                              "type": "string",
                              "format": "binary",
                              "description": "CSV file containing candidate scores"
                          }
                      }
                  }
              },
              400: {"model": ErrorResponse, "description": "Bad request - Invalid input"},
              422: {"model": ErrorResponse, "description": "Validation error"},
              500: {"model": ErrorResponse, "description": "Internal server error"}
          },
          summary="Score multiple resumes against provided criteria")
async def score_resumes(
    criteria: str = Form(..., description="JSON array of ranking criteria strings or comma-separated list of criteria"),
    resumes: List[UploadFile] = File(..., description="Resume files (PDF or DOCX)")
) -> StreamingResponse:
    """
    Score multiple resumes against provided ranking criteria.
    
    The endpoint processes multiple resume files and scores them against the provided criteria
    using an intelligent scoring system powered by CrewAI.
    
    Args:
        criteria (str): Can be one of:
                        - JSON array of criteria strings: ["criterion1", "criterion2"]
                        - JSON object with a "criteria" key: {"criteria": ["criterion1", "criterion2"]}
                        - Comma-separated list of criteria: "criterion1,criterion2"
        resumes (List[UploadFile]): List of resume files in PDF or DOCX format
        
    Returns:
        StreamingResponse: CSV file containing:
            - Candidate names (extracted or from filename)
            - Individual scores for each criterion (0-5 scale)
            - Total score
            - Any processing errors
            
    Example criteria:
        [
            "[Required] Must have certification XYZ",
            "[Required] 5+ years of experience in Python development",
            "[Preferred] Strong background in Machine Learning"
        ]
        
    Note:
        - Scores are on a 0-5 scale where:
            0 = Not mentioned/No match
            1 = Poor match
            2 = Fair match
            3 = Good match
            4 = Very good match
            5 = Excellent match
        - The output CSV file is sorted by total score in descending order
    """
    # Log the request
    logger.info(f"Scoring {len(resumes)} resumes")
    start_time = time.time()
    
    # Parse criteria
    criteria_list = []
    try:
        # Try to parse as JSON array or object
        try:
            criteria_parsed = json.loads(criteria)
            if isinstance(criteria_parsed, list):
                criteria_list = criteria_parsed
            elif isinstance(criteria_parsed, dict) and "criteria" in criteria_parsed:
                criteria_list = criteria_parsed["criteria"]
            else:
                raise ValueError("Invalid criteria format, expected array or object with 'criteria' key")
        except json.JSONDecodeError:
            # Try to parse as comma-separated list
            criteria_list = [c.strip() for c in criteria.split(",") if c.strip()]
            
        if not criteria_list:
            raise ValueError("No valid criteria provided")
            
        logger.info(f"Parsed {len(criteria_list)} criteria")
        
    except Exception as e:
        logger.error(f"Failed to parse criteria: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid criteria format: {str(e)}")
    
    # Process resumes
    doc_processor = DocumentProcessor()
    results = []
    
    for file in resumes:
        try:
            logger.info(f"Processing resume: {file.filename}")
            resume_start_time = time.time()
            
            # Extract text from file
            content = await doc_processor.extract_text_from_file(file)
            
            # Extract candidate name using intelligent name extraction
            name_result = await extract_candidate_name(content, file.filename)
            candidate_name = name_result.get('name') if name_result and name_result.get('confidence', 0) >= 70 else None
            
            # Fallback to filename if name extraction fails
            if not candidate_name:
                candidate_name = os.path.splitext(file.filename)[0].replace('_', ' ').title()
                logger.warning(f"Using filename as candidate name for {file.filename}")
            
            # Score resume against criteria
            scores = await score_resume_against_criteria(content, criteria_list)
            
            # Create result dictionary with proper column names
            result = {'Candidate Name': candidate_name}
            for criterion, score in scores.items():
                # Ensure score is within 0-5 range
                score = max(0, min(5, score))
                # Use criterion as column name, cleaned up
                column_name = criterion.replace('[Required] ', '').replace('[Preferred] ', '')
                result[column_name] = score
            
            # Calculate total score
            result['Total Score'] = sum(scores.values())
            
            # Add processing time
            result['Processing Time (s)'] = round(time.time() - resume_start_time, 2)
            
            results.append(result)
            logger.info(f"Successfully scored resume: {file.filename}")
            
        except Exception as e:
            logger.error(f"Error processing resume {file.filename}: {str(e)}")
            results.append({
                'Candidate Name': os.path.splitext(file.filename)[0].replace('_', ' ').title(),
                'error': str(e)
            })
    
    # Generate CSV response
    logger.info(f"Total processing time: {time.time() - start_time:.2f} seconds")
    return generate_csv_from_scores(results, criteria_list)
