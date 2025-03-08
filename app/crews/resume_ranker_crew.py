import json
import os
from pathlib import Path
import urllib3
import ssl
import os
import logging
import warnings
import requests

from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, task, crew

from ..logger import get_logger

# Suppress OpenTelemetry warnings
warnings.filterwarnings("ignore", category=Warning, module="opentelemetry")
logging.getLogger("opentelemetry").setLevel(logging.ERROR)

# Completely disable SSL verification to prevent SSL certificate verification errors
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
os.environ["PYTHONHTTPSVERIFY"] = "0"
ssl._create_default_https_context = ssl._create_unverified_context

# Disable SSL verification in requests
requests.packages.urllib3.disable_warnings()

# Disable telemetry to prevent SSL errors
os.environ["CREWAI_TELEMETRY"] = "False"
# Disable OpenTelemetry to prevent multiple initialization warnings
os.environ["OTEL_SDK_DISABLED"] = "true"
# Disable OpenTelemetry traces exporter
os.environ["OTEL_TRACES_EXPORTER"] = "none"

logger = get_logger(__name__)

@CrewBase
class ResumeRankerCrew:
    """Resume Ranking Crew implementation using CrewAI"""

    def __init__(self):
        self.config_dir = Path(__file__).parent / 'config'
        self.crew_inputs = {}
        
        logger.info("Initializing ResumeRankerCrew")
        
        # Load configurations
        self.agents_config = self._load_yaml_config('agents.yaml')
        self.tasks_config = self._load_yaml_config('tasks.yaml')
        self.crews_config = self._load_yaml_config('crews.yaml')
        self.llms = self._load_llm_config()
        
        logger.info("ResumeRankerCrew initialized successfully")

    def _load_yaml_config(self, filename: str) -> dict:
        """Load YAML configuration file"""
        config_path = self.config_dir / filename
        logger.debug(f"Loading configuration from {config_path}")
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                logger.debug(f"Successfully loaded configuration from {filename}")
                return config
        except Exception as e:
            logger.error(f"Error loading configuration from {filename}: {str(e)}")
            raise ValueError(f"Failed to load configuration file {filename}: {str(e)}")
    
    def _load_llm_config(self):
        """Load the LLM configuration from JSON file."""
        llm_config_path = self.config_dir / 'llms.json'
        if not os.path.exists(llm_config_path):
            logger.error("LLM configuration file not found at %s", llm_config_path)
            raise FileNotFoundError(f"LLM configuration file not found at {llm_config_path}")

        try:
            with open(llm_config_path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON format in llms.json: %s", e)
            raise ValueError(f"Invalid JSON format in llms.json: {e}")

    def _get_llm_config(self, key: str):
        """Retrieve and validate LLM configuration for a given agent."""
        llm_data = self.llms.get(key)
        if not llm_data or not llm_data.get("llm"):
            logger.error("Missing or invalid LLM configuration for %s", key)
            raise ValueError(f"Missing or invalid LLM configuration for {key}")
        
        # Use base configuration without modifications that might cause serialization issues
        return LLM(**llm_data["llm"])

    @agent
    def job_requirements_analyst(self) -> Agent:
        """Defines the Job Requirements Analyst agent."""
        return Agent(
            config=self.agents_config.get("job_requirements_analyst", {}),
            llm=self._get_llm_config("job_requirements_analyst"),
            verbose=True,
        )

    @agent
    def resume_evaluation_specialist(self) -> Agent:
        """Defines the Resume Evaluation Specialist agent."""
        return Agent(
            config=self.agents_config.get("resume_evaluation_specialist", {}),
            llm=self._get_llm_config("resume_evaluation_specialist"),
            verbose=True,
        )

    @agent
    def name_extraction_specialist(self) -> Agent:
        """Defines the Name Extraction Specialist agent."""
        return Agent(
            config=self.agents_config.get("name_extraction_specialist", {}),
            llm=self._get_llm_config("name_extraction_specialist"),
            verbose=True,
        )

    @task
    def extract_criteria(self) -> Task:
        """Task to extract ranking criteria."""
        return Task(
            config=self.tasks_config["extract_criteria"],
            agent=self.job_requirements_analyst(),
        )

    @task
    def extract_name(self) -> Task:
        """Task to extract candidate name from resume."""
        return Task(
            config=self.tasks_config["extract_name"],
            agent=self.name_extraction_specialist(),
        )

    @task
    def score_resume(self) -> Task:
        """Task to score a resume."""
        return Task(
            config=self.tasks_config["score_resume"],
            agent=self.resume_evaluation_specialist(),
            context=[self.extract_criteria()]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Resume Ranking Crew based on the provided inputs."""
        # Get the task list from the inputs
        task_list = []
        if "resume_content" in self.crew_inputs and "extract_name_only" in self.crew_inputs:
            # Only extracting name
            task_list = [self.extract_name()]
            agents = [self.name_extraction_specialist()]
        elif "job_description" in self.crew_inputs and "resume_content" not in self.crew_inputs:
            # Only extracting criteria
            task_list = [self.extract_criteria()]
            agents = [self.job_requirements_analyst()]
        else:
            # Full resume scoring flow - we skip name extraction here as it's already done in main.py
            # to avoid duplicate extraction and unnecessary costs
            task_list = [
                self.extract_criteria(),  # Extract criteria
                self.score_resume()  # Score the resume
            ]
            agents = [
                self.job_requirements_analyst(),
                self.resume_evaluation_specialist()
            ]
        
        # Create and configure the crew
        crew = Crew(
            agents=agents,
            tasks=task_list,
            process=Process.sequential,  # Tasks must run in order
            verbose=self.crews_config.get("resume_ranking_crew", {}).get("verbose", True)
        )
        
        # Log the crew configuration
        logger.info(f"Created crew with {len(agents)} agents and {len(task_list)} tasks")
        logger.debug(f"Agents: {[type(agent).__name__ for agent in agents]}")
        logger.debug(f"Tasks: {[type(task).__name__ for task in task_list]}")
        
        return crew

    def kickoff(self, inputs: dict = None) -> str:
        """
        Initialize the crew with inputs and run the tasks.
        
        Args:
            inputs (dict): The input parameters for the crew tasks
                - resume_content (str): Text content of the resume
                - job_description (str): Text content of the job description
                - extract_name_only (bool): If True, only extract name from resume
        
        Returns:
            str: JSON string containing the task results
        """
        self.crew_inputs = inputs or {}
        
        # Validate required inputs
        if not self.crew_inputs:
            raise ValueError("No inputs provided to the crew")
            
        # Log the operation being performed
        if "extract_name_only" in self.crew_inputs:
            logger.info("Starting name extraction task")
        elif "job_description" in self.crew_inputs and "resume_content" not in self.crew_inputs:
            logger.info("Starting criteria extraction task")
        else:
            logger.info("Starting full resume scoring flow")
        
        # Execute crew tasks
        result = self.crew().kickoff()
        
        # Validate and sanitize JSON responses for scoring tasks
        if "extract_name_only" not in self.crew_inputs and "resume_content" in self.crew_inputs:
            try:
                # If this is a scoring task, validate the JSON structure
                result_str = str(result)
                
                # Try to parse as JSON to verify format
                import json
                import re
                
                try:
                    # Attempt direct JSON parsing first
                    json_result = json.loads(result_str)
                    
                    # If parsed successfully but missing scores array, add empty one
                    if not isinstance(json_result, dict) or "scores" not in json_result:
                        json_result = {"scores": []}
                        result = json.dumps(json_result)
                        logger.warning("Response missing 'scores' array, creating empty one")
                        
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON response from crew, attempting repair")
                    
                    # Enhanced JSON repair for common LLM response issues
                    
                    # 1. Fix common pattern: Truncated JSON with missing closing braces and brackets
                    # Extract all complete score objects using regex
                    score_pattern = re.compile(r'\{\s*"criterion":\s*"([^"]*)"\s*,\s*"score":\s*(\d+)\s*,\s*"justification":\s*"([^"]*?)"\s*\}')
                    matches = score_pattern.findall(result_str)
                    
                    if matches:
                        # Rebuild a valid JSON from the extracted objects
                        scores_array = []
                        for criterion, score, justification in matches:
                            scores_array.append({
                                "criterion": criterion,
                                "score": int(score),
                                "justification": justification
                            })
                        
                        # Create repaired JSON
                        repaired_json = {"scores": scores_array}
                        result = json.dumps(repaired_json)
                        logger.info(f"Successfully repaired JSON with {len(scores_array)} score objects")
                    else:
                        # 2. If no complete objects found, search for partial objects
                        # Look for criterion-score pairs
                        criterion_pattern = re.compile(r'"criterion":\s*"([^"]*)"')
                        criteria = criterion_pattern.findall(result_str)
                        
                        score_pattern = re.compile(r'"score":\s*(\d+)')
                        scores = score_pattern.findall(result_str)
                        
                        if criteria and scores:
                            # Use the minimum length to avoid index errors
                            min_length = min(len(criteria), len(scores))
                            
                            scores_array = []
                            for i in range(min_length):
                                scores_array.append({
                                    "criterion": criteria[i],
                                    "score": int(scores[i]),
                                    "justification": "Extracted from partial response"
                                })
                            
                            # Create repaired JSON
                            repaired_json = {"scores": scores_array}
                            result = json.dumps(repaired_json)
                            logger.info(f"Partially repaired JSON with {len(scores_array)} criterion-score pairs")
                        else:
                            # If all repair attempts fail, return empty scores array
                            logger.warning("Failed to repair JSON response from crew, returning empty scores array")
                            result = '{"scores": []}'
                    
            except Exception as e:
                logger.error(f"Error validating/repairing response: {str(e)}")
                # Return safe empty JSON as fallback
                result = '{"scores": []}'
                
        return result
