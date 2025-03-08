# ResumeRanker

A production-grade FastAPI application that automates resume ranking based on job descriptions using CrewAI and Groq LLM.

## Features

- Extract ranking criteria from job descriptions (PDF/DOCX)
- Score multiple resumes against extracted criteria
- Automated scoring using CrewAI and Groq Provider
- Intelligent candidate name extraction from resumes
- Export results in CSV format
- Swagger UI documentation
- Production-ready error handling and input validation

## Prerequisites

- Python 3.11.8
- Groq API Key

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Mindk-scrap/ResumeRanker.git
cd ResumeRanker
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
```
Edit `.env` and add your Groq API key.

## Usage

1. Start the server:
```bash
uvicorn app.main:app --reload
```

2. Access the API documentation at `http://localhost:8000/docs`

### API Endpoints

#### POST /extract-criteria
Extract ranking criteria from a job description file.

**Input:**
- Job description file (PDF/DOCX)

**Output:**
```json
{
  "criteria": [
    "[Required] Must have certification XYZ",
    "[Required] 5+ years of experience in Python development",
    "[Preferred] Strong background in Machine Learning"
  ]
}
```

Each criterion is prefixed with [Required] or [Preferred] to indicate its importance.

#### POST /score-resumes
Score multiple resumes against provided criteria.

**Input:**
- List of criteria
- Multiple resume files (PDF/DOCX)

**Output:**
- CSV file with candidate scores and rankings (0-5 scale)

#### POST /rank-resumes-from-job
Combined pipeline endpoint that handles both criteria extraction and resume scoring in one step.

**Input:**
- Job description file
- Multiple resume files

**Output:**
- CSV file with complete ranking results

## Name Extraction Feature

The system includes intelligent name extraction capability that:
- Extracts candidate names from resume content
- Uses pattern matching and context analysis
- Returns name with confidence score (0-100)
- Only accepts names with confidence >= 70%
- Falls back to filename if name extraction fails

This enhances the accuracy of candidate identification in the output reports.

## Project Structure

```
ResumeRanker/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application and routes
│   ├── logger.py               # Logging configuration
│   ├── crews/                  # CrewAI implementation
│   │   └── ...                 # Crew agents and tasks
│   ├── models/
│   │   └── ...                 # Pydantic models
│   ├── routes/
│   │   ├── criteria.py         # Endpoints for criteria extraction
│   │   ├── scoring.py          # Endpoints for resume scoring
│   │   └── pipeline.py         # Combined workflow endpoints
│   └── services/
│       ├── document_processor.py  # PDF/DOCX processing
│       └── ...                 # Other service modules
├── logs/                       # Application logs
├── requirements.txt
├── .env.example
└── README.md
```