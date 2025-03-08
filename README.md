# ResumeRanker

A production-grade FastAPI application that automates resume ranking based on job descriptions using CrewAI and Groq LLM.

## Explaination Video

[https://www.loom.com/share/c69fe3c7b7bc44e296243e6d0657ab60?sid=b6458446-2fd0-452f-b8dc-8b727b18b3de](https://www.loom.com/share/c69fe3c7b7bc44e296243e6d0657ab60?sid=b6458446-2fd0-452f-b8dc-8b727b18b3de)

## Demo Video

[https://www.loom.com/share/6284aa46e16643a1b2141edfd59128c5?sid=f3b7b3a8-c7c8-485c-b9f0-b63c6cd8c97a](https://www.loom.com/share/6284aa46e16643a1b2141edfd59128c5?sid=f3b7b3a8-c7c8-485c-b9f0-b63c6cd8c97a)

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

## Example API Usage

### Extracting Criteria from Job Description

```python
import requests

url = "http://localhost:8000/extract-criteria"
files = {"job_description_file": open("job_description.pdf", "rb")}

response = requests.post(url, files=files)
criteria = response.json()["criteria"]
print(criteria)
```

### Scoring Resumes Against Criteria

```python
import requests

url = "http://localhost:8000/score-resumes"
files = [
    ("criteria_file", open("criteria.json", "rb")),
    ("resumes", open("resume1.pdf", "rb")),
    ("resumes", open("resume2.pdf", "rb")),
    ("resumes", open("resume3.pdf", "rb")),
]

response = requests.post(url, files=files)
with open("resume_scores.csv", "wb") as f:
    f.write(response.content)
```

### Complete Resume Ranking Pipeline

```python
import requests

url = "http://localhost:8000/all"
files = [
    ("job_description_file", open("job_description.pdf", "rb")),
    ("resumes", open("resume1.pdf", "rb")),
    ("resumes", open("resume2.pdf", "rb")),
    ("resumes", open("resume3.pdf", "rb")),
]

response = requests.post(url, files=files)
with open("rankings.csv", "wb") as f:
    f.write(response.content)
```

## Contributing

We welcome contributions to ResumeRanker! Please follow these steps:

1. Fork the repository
2. Create a new branch: `git checkout -b feature-name`
3. Make your changes
4. Run tests to ensure they pass: `pytest`
5. Commit your changes: `git commit -m 'Add some feature'`
6. Push to the branch: `git push origin feature-name`
7. Submit a pull request

### Code Style

We follow PEP 8 coding standards. Please ensure your code adheres to these standards by running:

```bash
black .
flake8
```

### Pull Request Process

1. Update the README.md with details of changes if applicable
2. Update the requirements.txt if you've added new dependencies
3. The PR will be merged once it has been reviewed and approved

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

Copyright 2025 Mindk-scrap

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

## Acknowledgments

- [CrewAI](https://github.com/joaomdmoura/crewAI) for the agent framework
- [Groq](https://groq.com/) for their efficient LLM inference API
- [FastAPI](https://fastapi.tiangolo.com/) for the API framework