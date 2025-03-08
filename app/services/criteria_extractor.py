"""
Criteria extraction service for extracting ranking criteria from job descriptions.
"""

import time
from typing import Any, List

from ..crews.resume_ranker_crew import ResumeRankerCrew
from ..logger import get_logger

logger = get_logger(__name__)


async def extract_criteria_from_text(job_description: str) -> List[str]:
    """
    Extract ranking criteria from job description text using CrewAI.

    Args:
        job_description (str): Text content of job description

    Returns:
        List[str]: List of extracted criteria

    Raises:
        ValueError: If extraction fails or returns invalid data
    """
    if not job_description or job_description.strip() == "":
        logger.error("Empty job description provided")
        raise ValueError("Job description cannot be empty")

    logger.info(
        f"Extracting criteria from job description ({len(job_description)} chars)"
    )
    start_time = time.time()

    try:
        # Initialize the resume ranker crew
        resume_ranker_crew = ResumeRankerCrew()

        # Execute the crew with only criteria extraction task
        result = resume_ranker_crew.kickoff({"job_description": job_description})

        # Try to parse the result as a list of criteria
        import json

        try:
            # Convert CrewOutput to string for parsing
            result_str = str(result)

            # Log the first part of the result for debugging
            if len(result_str) > 500:
                logger.debug(f"Result preview (first 500 chars): {result_str[:500]}...")
            else:
                logger.debug(f"Result: {result_str}")

            # Parse the result
            criteria_list = json.loads(result_str)

            # Validate the result
            if not isinstance(criteria_list, list):
                logger.error(f"Invalid criteria format: {type(criteria_list)}")
                raise ValueError(
                    "Criteria extraction returned invalid format (expected list)"
                )

            # Filter out empty or non-string criteria
            criteria_list = [
                criterion
                for criterion in criteria_list
                if isinstance(criterion, str) and criterion.strip()
            ]

            if not criteria_list:
                logger.warning("No criteria extracted from job description")
                return []

            # Log the criteria
            logger.info(
                f"Extracted {len(criteria_list)} criteria in {time.time() - start_time:.2f} seconds"
            )
            for i, criterion in enumerate(criteria_list):
                logger.debug(f"Criterion {i+1}: {criterion}")

            return criteria_list

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse criteria extraction result: {str(e)}")
            raise ValueError(f"Failed to parse criteria extraction result: {str(e)}")

    except Exception as e:
        logger.error(f"Error extracting criteria: {str(e)}")
        raise ValueError(f"Failed to extract criteria: {str(e)}")
