"""
Service for formatting results as CSV and other output formats.
"""
import io
import pandas as pd
from typing import Dict, List, Any
from fastapi.responses import StreamingResponse

from ..logger import get_logger

logger = get_logger(__name__)

def generate_csv_from_scores(results: List[Dict[str, Any]], criteria_list: List[str]) -> StreamingResponse:
    """
    Generate a CSV file from resume scoring results.
    
    Args:
        results (List[Dict[str, Any]]): List of scoring results for each resume
        criteria_list (List[str]): List of criteria used for scoring
        
    Returns:
        StreamingResponse: CSV file containing the scoring results
    """
    logger.info(f"Generating CSV file for {len(results)} candidates")
    
    # Create a pandas DataFrame
    df = pd.DataFrame(results)
    
    # Calculate the total score
    if 'error' not in df.columns:
        if len(criteria_list) > 0:
            # Only include the specific criteria for the calculation
            score_columns = [col for col in df.columns if col in criteria_list or 
                           col.replace('[Required] ', '').replace('[Preferred] ', '') in 
                           [c.replace('[Required] ', '').replace('[Preferred] ', '') for c in criteria_list]]
            
            if score_columns:
                df['Total Score'] = df[score_columns].sum(axis=1)
                
                # Sort by total score in descending order
                df = df.sort_values('Total Score', ascending=False)
    
    # Convert DataFrame to CSV
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    
    # Return as StreamingResponse
    return StreamingResponse(
        iter([csv_buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=resume_scores.csv"}
    )

def generate_criteria_json(criteria_list: List[str]) -> Dict[str, List[str]]:
    """
    Format criteria list as a JSON object.
    
    Args:
        criteria_list (List[str]): List of criteria
        
    Returns:
        Dict[str, List[str]]: JSON object with criteria list
    """
    return {"criteria": criteria_list}
