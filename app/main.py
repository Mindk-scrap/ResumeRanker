"""
Resume Ranker API - Main Application Entry Point

This module initializes the FastAPI application and includes all the routes
for the Resume Ranker system.
"""

import os
from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .logger import get_logger
from .routes import criteria, pipeline, scoring

# Initialize logger
logger = get_logger(__name__)

# Load environment variables
load_dotenv()


def validate_environment() -> None:
    """Validate required environment variables"""
    required_vars = ["GROQ_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.info("Environment validation successful")


# Define lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Tasks to run on application startup and shutdown"""
    # Startup
    logger.info("Starting Resume Ranker API")
    validate_environment()

    yield
    # Shutdown
    logger.info("Shutting down Resume Ranker API")


# Initialize FastAPI app
app = FastAPI(
    title="Resume Ranker API",
    description="API endpoints for ranking resumes based on job descriptions using CrewAI and Groq",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root endpoint
@app.get("/", tags=["Root"], summary="Root endpoint")
async def root():
    """
    Root endpoint that provides basic information about the API.

    Returns:
        dict: Basic information about the API
    """
    return {
        "name": "Resume Ranker API",
        "version": "1.0.0",
        "description": "API endpoints for ranking resumes against job descriptions",
        "endpoints": {
            "/extract-criteria": "Extract criteria from job description file",
            "/score-resumes": "Score resumes against provided criteria",
            "/all": "Extract criteria and score resumes in one step",
        },
    }


# Include routers from modules
app.include_router(criteria.router)
app.include_router(scoring.router)
app.include_router(pipeline.router)

# Main entry point
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
