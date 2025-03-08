import asyncio
import os
import time
from functools import wraps
from typing import Any, Dict, List

from dotenv import load_dotenv

from ..crews.resume_ranker_crew import ResumeRankerCrew
from ..logger import get_logger

# Get configured logger
logger = get_logger(__name__)

# Load environment variables
load_dotenv()


def async_retry(max_retries=5, delay=2):
    """Decorator for async functions to retry on failure"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(
                            f"Final retry failed for {func.__name__}: {str(e)}"
                        )
                        raise
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {str(e)}"
                    )
                    await asyncio.sleep(delay * (attempt + 1))  # Exponential backoff

        return wrapper

    return decorator


class CrewManager:
    """Manages CrewAI agents and tasks for resume ranking"""

    def __init__(self):
        self._validate_environment()
        self.resume_ranker_crew = ResumeRankerCrew()

    def _validate_environment(self) -> None:
        """Validate required environment variables"""
        required_vars = ["GROQ_API_KEY"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if missing_vars:
            error_msg = (
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info("Environment validation successful")

    @async_retry(max_retries=3, delay=2)
    async def extract_criteria(self, job_description: str) -> List[str]:
        """
        Extract ranking criteria from job description using CrewAI

        Args:
            job_description (str): Text content of job description

        Returns:
            List[str]: List of extracted criteria
        """
        if not job_description or job_description.strip() == "":
            logger.error("Empty job description provided")
            raise ValueError("Job description cannot be empty")

        logger.info(
            f"Extracting criteria from job description ({len(job_description)} chars)"
        )
        start_time = time.time()

        try:
            # Create inputs for the crew
            inputs = {
                "job_description": job_description,
                "resume_content": "",  # Add empty resume_content to prevent template error
            }

            # Run the crew with extract_criteria task
            result = self.resume_ranker_crew.crew().kickoff(inputs=inputs)

            # Parse the result into a list of criteria
            if not result or not isinstance(result, str):
                logger.warning("Invalid response format from crew")
                return []

            # Split the result into lines and clean up
            criteria = [
                line.strip() for line in result.strip().split("\n") if line.strip()
            ]

            logger.info(
                f"Successfully extracted {len(criteria)} criteria in {time.time() - start_time:.2f} seconds"
            )
            return criteria

        except Exception as e:
            logger.error(f"Error extracting criteria: {str(e)}")
            raise ValueError(f"Failed to extract criteria: {str(e)}")

    @async_retry(max_retries=3, delay=2)
    async def score_resume(
        self, resume_content: str, criteria: List[str]
    ) -> Dict[str, Any]:
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

        logger.info(
            f"Scoring resume ({len(resume_content)} chars) against {len(criteria)} criteria"
        )
        start_time = time.time()

        try:
            # Create inputs for the crew
            inputs = {"resume_content": resume_content, "criteria": criteria}

            # Run the crew with score_resume task
            result = self.resume_ranker_crew.crew().kickoff(inputs=inputs)

            # Parse the result into a dictionary of scores
            if not result or not isinstance(result, str):
                logger.warning("Invalid scoring response format")
                return {}

            # Parse the result into a dictionary
            # Expected format: "[Criterion]: [Score] - [Justification]"
            scores = {}
            for line in result.strip().split("\n"):
                if ":" in line:
                    parts = line.split(":", 1)
                    criterion = parts[0].strip()
                    score_part = parts[1].strip()

                    # Extract the numeric score (assuming format "4 - Justification")
                    if " - " in score_part:
                        score = score_part.split(" - ")[0].strip()
                        try:
                            scores[criterion] = int(score)
                        except ValueError:
                            scores[criterion] = 0
                    else:
                        try:
                            scores[criterion] = int(score_part)
                        except ValueError:
                            scores[criterion] = 0

            # Ensure all criteria have scores
            for criterion in criteria:
                if criterion not in scores:
                    logger.warning(f"No score for criterion: {criterion}")
                    scores[criterion] = 0

            logger.info(
                f"Successfully scored resume in {time.time() - start_time:.2f} seconds"
            )
            return scores

        except Exception as e:
            logger.error(f"Error scoring resume: {str(e)}")
            raise ValueError(f"Failed to score resume: {str(e)}")
