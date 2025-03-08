"""
Resume scoring service for scoring resumes against criteria.
"""
import json
import re
import time
from typing import Dict, List, Any

from ..crews.resume_ranker_crew import ResumeRankerCrew
from ..logger import get_logger

logger = get_logger(__name__)

async def score_resume_against_criteria(resume_content: str, criteria: List[str]) -> Dict[str, int]:
    """
    Score a resume against provided criteria using CrewAI
    
    Args:
        resume_content (str): Text content of resume
        criteria (List[str]): List of criteria to score against
        
    Returns:
        Dict[str, int]: Dictionary mapping criteria to scores (0-5)
    """
    if not resume_content or resume_content.strip() == "":
        logger.error("Empty resume content provided")
        raise ValueError("Resume content cannot be empty")
        
    if not criteria or not isinstance(criteria, list) or len(criteria) == 0:
        logger.error("No criteria provided for scoring")
        raise ValueError("At least one criterion must be provided")
        
    logger.info(f"Scoring resume ({len(resume_content)} chars) against {len(criteria)} criteria")
    start_time = time.time()
    
    try:
        # Initialize the resume ranker crew
        resume_ranker_crew = ResumeRankerCrew()
        
        # Run the crew with score_resume task
        result = resume_ranker_crew.kickoff({
            "resume_content": resume_content,
            "criteria": criteria
        })
        
        # Parse the result into a dictionary
        # Expected format: JSON object with scores array containing criterion, score, and justification
        try:
            # Convert CrewOutput to string for parsing
            result_str = str(result)
            
            # Log the first part of the result for debugging
            if len(result_str) > 500:
                logger.debug(f"Result preview (first 500 chars): {result_str[:500]}...")
            else:
                logger.debug(f"Result: {result_str}")
                
            # Try to parse JSON
            try:
                result_dict = json.loads(result_str)
            except json.JSONDecodeError as e:
                logger.warning(f"Initial JSON parse error: {str(e)}")
                
                # Advanced recovery for malformed JSON responses
                logger.info("Attempting to recover partial JSON response")
                
                # Try to extract all valid score objects even if overall JSON is invalid
                import re
                
                # Look for objects with criterion, score, and justification fields
                score_pattern = re.compile(r'\{\s*"criterion":\s*"([^"]*)"\s*,\s*"score":\s*(\d+)\s*,\s*"justification":\s*"([^"]*?)"\s*\}')
                matches = score_pattern.findall(result_str)
                
                if matches:
                    # Reconstruct scores from regex matches - more resilient to malformed JSON
                    scores_objects = []
                    unique_criteria = set()  # To track and prevent duplicate criteria
                    
                    for criterion, score, justification in matches:
                        # Skip duplicate criteria entries
                        if criterion in unique_criteria:
                            logger.warning(f"Skipping duplicate criterion: {criterion}")
                            continue
                            
                        unique_criteria.add(criterion)
                        
                        # Create a clean score object
                        clean_object = {
                            "criterion": criterion,
                            "score": int(score),
                            "justification": justification
                        }
                        scores_objects.append(clean_object)
                    
                    logger.info(f"Reconstructed JSON with {len(scores_objects)} complete score objects")
                    result_dict = {"scores": scores_objects}
                else:
                    # If regex approach fails, try extracting criteria and scores separately
                    criterion_pattern = re.compile(r'"criterion":\s*"([^"]*)"')
                    criteria_matches = criterion_pattern.findall(result_str)
                    
                    score_pattern = re.compile(r'"score":\s*(\d+)')
                    score_matches = score_pattern.findall(result_str)
                    
                    # If we have any criteria or scores, use them to construct a result
                    if criteria_matches or score_matches:
                        scores_objects = []
                        # Use the minimum length to avoid index errors
                        min_length = min(len(criteria_matches), len(score_matches))
                        
                        for i in range(min_length):
                            scores_objects.append({
                                "criterion": criteria_matches[i],
                                "score": int(score_matches[i]),
                                "justification": f"Recovered from partial response (item {i+1})"
                            })
                        
                        result_dict = {"scores": scores_objects}
                        logger.info(f"Recovered {len(scores_objects)} criteria-score pairs using pattern matching")
                    else:
                        # Last resort: Try to find any integers in the response that might be scores
                        number_pattern = re.compile(r'(\d+)')
                        number_matches = number_pattern.findall(result_str)
                        
                        if number_matches and len(criteria) > 0:
                            # Take the minimum of available numbers and criteria to match
                            min_length = min(len(number_matches), len(criteria))
                            
                            # Prepare result structure
                            scores_objects = []
                            for i in range(min_length):
                                score_value = int(number_matches[i])
                                # Ensure score is in valid range (0-5)
                                if score_value > 5:
                                    score_value = 5
                                
                                scores_objects.append({
                                    "criterion": criteria[i],
                                    "score": score_value,
                                    "justification": "Extracted from numeric values in response"
                                })
                            
                            result_dict = {"scores": scores_objects}
                            logger.warning(f"Last resort recovery: matched {min_length} numbers to criteria")
                        else:
                            logger.error("Could not recover any score data: no valid patterns found")
                            result_dict = {"scores": []}
            
            # Initialize scores dictionary
            scores = {}
            
            # Validate the parsed dictionary structure
            if not isinstance(result_dict, dict) or 'scores' not in result_dict:
                logger.error("Invalid response format: missing 'scores' array")
                # Create empty scores array if missing
                result_dict = {"scores": []}
            
            # Process each score object
            for score_obj in result_dict['scores']:
                if not all(k in score_obj for k in ('criterion', 'score')):
                    logger.warning(f"Invalid score object format: {score_obj}")
                    continue
                    
                criterion = score_obj['criterion']
                score = score_obj['score']
                
                # Validate score value
                if not isinstance(score, (int, float)) or score < 0 or score > 5:
                    logger.warning(f"Invalid score value for {criterion}: {score}, clamping to valid range")
                    score = max(0, min(5, int(score) if isinstance(score, (int, float)) else 0))
                    
                scores[criterion] = int(score)  # Convert to int to ensure consistent type
                
            # Ensure all criteria have scores
            for criterion in criteria:
                if criterion not in scores:
                    logger.warning(f"No score for criterion: {criterion}")
                    # Assign default score of 0 for any missing criteria
                    scores[criterion] = 0
                    
            logger.info(f"Successfully scored resume in {time.time() - start_time:.2f} seconds")
            return scores
            
        except Exception as e:
            logger.error(f"Failed to process scoring response: {str(e)}")
            
            # Assign default scores if parsing fails
            logger.warning("Using default scores (0) for all criteria due to parsing error")
            return {criterion: 0 for criterion in criteria}
            
    except Exception as e:
        logger.error(f"Error scoring resume: {str(e)}")
        raise ValueError(f"Failed to score resume: {str(e)}")
