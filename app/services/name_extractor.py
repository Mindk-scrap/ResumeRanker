"""
Name extraction service for extracting candidate names from resumes.
"""

import json
import os
import time
from typing import Any, Dict

from ..crews.resume_ranker_crew import ResumeRankerCrew
from ..logger import get_logger

logger = get_logger(__name__)


async def extract_candidate_name(content: str, file_name: str = None) -> Dict[str, Any]:
    """
    Extract candidate name from resume content using CrewAI's name extraction specialist.

    Args:
        content (str): Text content of resume
        file_name (str, optional): Original filename, used as fallback if extraction fails

    Returns:
        Dict[str, Any]: Dictionary containing:
            - name (str): Extracted candidate name or empty string if not found
            - confidence (int): Confidence score (0-100)
            - source (str): Where the name was found

    Raises:
        ValueError: If extraction fails or returns invalid data
    """
    logger.info(f"Extracting name from content ({len(content)} chars)")
    start_time = time.time()

    try:
        # Initialize the resume ranker crew
        resume_ranker_crew = ResumeRankerCrew()

        result = resume_ranker_crew.kickoff(
            {
                "resume_content": content,
                "extract_name_only": True,
                "filename": file_name,  # Pass filename to crew for context
            }
        )

        # Parse and validate the result
        try:
            result_dict = json.loads(str(result))
            name = result_dict.get("name", "").strip()
            confidence = result_dict.get("confidence", 0)
            source = result_dict.get("source", "")

            # Immediate rejection of Emily Chen which is frequently returned despite warnings
            if name.lower() == "emily chen":
                logger.error(
                    "Model returned the explicitly forbidden example name 'Emily Chen'"
                )
                return {
                    "name": file_name,
                    "confidence": 0,
                    "source": "forbidden_example_name",
                }

            # Comprehensive name validation
            if not name:
                logger.warning("Empty name returned from extraction")
                return {"name": file_name, "confidence": 0, "source": "empty_result"}

            # Reject known example/placeholder names
            example_names = {
                "emily chen",
                "john smith",
                "john doe",
                "jane doe",
                "emily j. miller",
                "james wilson",
                "sarah johnson",
                "[actual extracted name]",
                "your name",
                "candidate name",
                "resume",
            }
            if name.lower() in example_names:
                logger.warning(
                    f"Detected example/placeholder name '{name}' - rejecting"
                )
                return {
                    "name": file_name,
                    "confidence": 0,
                    "source": "example_name_rejected",
                }

            # Check for placeholder text markers
            if any(
                marker in name.lower()
                for marker in ["[", "]", "{", "}", "<", ">", "example"]
            ):
                logger.warning(
                    f"Detected placeholder text in name: '{name}' - rejecting"
                )
                return {
                    "name": file_name,
                    "confidence": 0,
                    "source": "placeholder_rejected",
                }

            # Basic name structure validation (at least two parts, reasonable length)
            name_parts = name.split()
            if len(name_parts) < 2:
                logger.warning(f"Invalid name structure: '{name}' - rejecting")
                return {
                    "name": file_name,
                    "confidence": 0,
                    "source": "invalid_structure",
                }

            # Check for overly long names (likely parsing errors)
            if len(name) > 50:
                logger.warning(f"Name too long: '{name}' - rejecting")
                return {"name": file_name, "confidence": 0, "source": "name_too_long"}

            # Log extraction metrics
            duration = time.time() - start_time
            logger.debug(f"Name extraction completed in {duration:.2f}s")
            logger.debug(f"Extracted name: {name}")
            logger.debug(f"Confidence: {confidence}")
            logger.debug(f"Extraction source: {source}")

            # Use filename as fallback for low confidence results
            if confidence < 70 and file_name:
                logger.info(
                    f"Low confidence score ({confidence}), using filename '{file_name}' instead"
                )
                return {
                    "name": file_name,
                    "confidence": 100,
                    "source": "filename_fallback",
                }

            # Return successful extraction result
            return {
                "name": name,
                "confidence": confidence,
                "source": source or "content_extraction",
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse name extraction result: {str(e)}")
            return {"name": file_name, "confidence": 0, "source": "parse_error"}

    except Exception as e:
        logger.error(f"Error in name extraction: {str(e)}")
        return {"name": file_name, "confidence": 0, "source": f"error: {str(e)}"}
