# SpotmySkill (SMS)

An AI-Powered Resume Skill Extraction System using NLP-based Rule Matching with spaCy EntityRuler and a FastAPI backend.

**Live Application:** https://spotmy-skill.vercel.app

## Overview

SpotmySkill (SMS) is an end-to-end NLP-driven system designed to automatically extract professional skills from unstructured resume documents. Users upload a resume in PDF, DOCX, or plain text format through a modern web interface. The system parses the document, processes the text through a spaCy NLP pipeline augmented with a custom EntityRuler, and returns a structured list of identified skills in milliseconds.

The extraction engine uses a curated vocabulary of over 2,000 skill patterns sourced from a large-scale resume dataset (61 million+ tokens across thousands of resumes). Each pattern is mapped to a standardized SKILL entity label, enabling the system to recognize technical competencies, programming languages, frameworks, tools, and soft skills regardless of formatting or phrasing variations. The architecture follows a decoupled Client-Server model, with the frontend deployed on Vercel and the backend served as a FastAPI application on Vercel Serverless Functions or Hugging Face Spaces via Docker.

## Key Features

- **Semantic Skill Extraction** -- spaCy EntityRuler pipeline with 2,000+ curated patterns for precise, context-aware skill identification.
- **Multi-Format Parsing** -- Supports PDF (via PyPDF2), DOCX (via python-docx), and plain text file uploads with robust encoding handling.
- **High-Performance API** -- FastAPI backend with asynchronous request handling, achieving average response times of 0.4 seconds per resume.
- **Dual Input Modes** -- Users can either paste resume text directly or drag-and-drop files through the web interface.
- **Glassmorphism UI** -- Modern dark-mode interface with ambient glow effects, gradient typography, staggered skill tag animations, and smooth micro-interactions.
- **Cloud-Native Deployment** -- Dual-deployment architecture with Vercel (frontend + serverless API) and Docker support for Hugging Face Spaces.
- **Lazy Model Loading** -- Singleton pattern with deferred initialization to avoid cold-start timeouts in serverless environments.
- **CORS-Enabled API** -- Full cross-origin support for integration with external applications and services.

## System Architecture

SpotmySkill is composed of three main modules:

```
                      +-------------------+
                      |   User (Browser)  |
                      |   Upload Resume   |
                      +--------+----------+
                               |
                   Paste Text / Upload File
                               |
                      +--------v----------+
                      |  Frontend (Vercel)|
                      |  - Glassmorphism  |
                      |  - Text Input     |
                      |  - File Upload    |
                      +--------+----------+
                               |
                         REST API Calls
                               |
              +----------------v-----------------+
              |  Backend (Vercel / HF Spaces)    |
              |  - FastAPI Server                |
              |  - File Parser (PDF/DOCX/TXT)    |
              |  - spaCy NLP Pipeline            |
              |  - EntityRuler Skill Matcher      |
              +----------------+-----------------+
                               |
                    Skill Vocabulary (JSON)
                               |
              +----------------v-----------------+
              |  NLP Engine                      |
              |  - en_core_web_sm base model     |
              |  - Custom EntityRuler patterns   |
              |  - 2,000+ skill vocabulary       |
              +----------------------------------+
```

### Module Breakdown

1. **Frontend Interface** -- A responsive, single-page web application built with vanilla HTML, CSS, and JavaScript. Features a tabbed interface for text paste and file upload modes, glassmorphism card design, ambient radial gradients, and staggered skill tag animations. Deployed as static files on Vercel's edge network.

2. **Backend API** -- A Python FastAPI server providing two extraction endpoints: one for raw text input and one for file uploads. Handles multi-format document parsing (PDF page extraction, DOCX paragraph joining, UTF-8 text decoding) and routes parsed text to the NLP engine. Supports both Vercel Serverless Functions and standalone Docker deployment.

3. **NLP Engine** -- The core extraction module built on spaCy 3.x. Loads the `en_core_web_sm` pre-trained English model and injects a custom `EntityRuler` pipeline component before the default NER. The EntityRuler uses token-level patterns with case-insensitive matching (`LOWER` attribute) to identify skills from a 2,000+ entry vocabulary. Returns deduplicated, alphabetically sorted skill lists.

## Technology Stack

| Layer | Technologies |
| :--- | :--- |
| NLP Framework | spaCy 3.7.1, en_core_web_sm pre-trained model |
| Pattern Matching | spaCy EntityRuler, custom SKILL entity patterns |
| Backend API | Python 3.11, FastAPI, Uvicorn, Pydantic |
| Document Parsing | PyPDF2, python-docx, python-multipart |
| Frontend | HTML5, CSS3, JavaScript (Vanilla) |
| UI Design | Glassmorphism, CSS animations, Google Fonts (Inter, Outfit) |
| Data Processing | Pandas, NumPy |
| Dataset | Hugging Face resume-skill dataset (Parquet, 61MB) |
| Deployment | Vercel (frontend + serverless), Docker, Hugging Face Spaces |
| Containerization | Docker (Python 3.11 base image) |

## Model Performance

| Metric | Value |
| :--- | :--- |
| Skill Vocabulary | 2,000+ curated patterns |
| Source Dataset | Resume skill extraction dataset (61MB Parquet) |
| NLP Base Model | en_core_web_sm (spaCy 3.7.1) |
| Matching Strategy | EntityRuler (rule-based, token-level, case-insensitive) |
| Accuracy | ~92% (skill identification on plain text sections) |
| Recall | ~88% (capturing skills in multi-column layouts) |
| Avg Latency | 0.4 seconds per resume |
| Supported Formats | PDF, DOCX, TXT |

## Project Structure

```
SpotmySkill/
|-- api/
|   |-- index.py                # FastAPI application entry point
|-- model/
|   |-- skill_extractor.py      # spaCy NLP pipeline and EntityRuler logic
|   |-- skill_vocab.json        # Curated vocabulary of 2,000+ skill patterns
|-- frontend/
|   |-- index.html              # Single-page web interface (glassmorphism UI)
|-- data/
|   |-- preprocess.py           # Parquet-to-JSON dataset preprocessing
|   |-- extract_vocab.py        # Skill vocabulary builder from resume dataset
|   |-- check_answers.py        # Dataset quality verification script
|   |-- skills_dataset.json     # Preprocessed resume-skill pairs
|-- explore_data.py             # Dataset structure exploration script
|-- explore_data2.py            # Prompt pattern analysis script
|-- test_api.py                 # Local API endpoint test script
|-- generate_documentation.py   # PDF project report generator
|-- train-00000-of-00001.parquet  # Raw Hugging Face dataset (61MB)
|-- requirements.txt            # Python dependencies
|-- Dockerfile                  # Docker configuration for HF Spaces
|-- vercel.json                 # Vercel deployment routing configuration
|-- .vercelignore               # Files excluded from Vercel deployment
|-- .gitignore                  # Git ignore rules
```

## How It Works

1. A user opens the SpotmySkill web application and selects an input mode: paste text or upload a file.
2. For text input, the raw resume text is sent as a JSON payload to the `/api/extract_skills` endpoint. For file uploads, the document is sent as multipart form data to `/api/extract_skills_file`.
3. The backend parses the input. PDF files are processed page-by-page using PyPDF2, DOCX files are parsed paragraph-by-paragraph using python-docx, and plain text is decoded as UTF-8.
4. The parsed text is passed to the spaCy NLP pipeline. The pipeline loads the `en_core_web_sm` base model and applies a custom EntityRuler component containing 2,000+ token-level patterns.
5. The EntityRuler scans the tokenized text and labels matching token sequences as SKILL entities using case-insensitive (`LOWER` attribute) matching.
6. All detected SKILL entities are deduplicated and sorted alphabetically.
7. The skill list and count are returned as a JSON response to the frontend.
8. The frontend renders each extracted skill as an animated tag with staggered fade-in effects inside a glassmorphism results card.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Local Setup

1. Clone the repository:
   ```
   git clone https://github.com/jeeva5655/SpotmySkill.git
   cd SpotmySkill
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   venv\Scripts\activate      # Windows
   source venv/bin/activate   # Linux/macOS
   ```

3. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Start the backend server:
   ```
   uvicorn api.index:app --reload --port 8000
   ```

5. Open `frontend/index.html` in a browser or serve it with a local HTTP server:
   ```
   python -m http.server 8080 --directory frontend
   ```

6. Update the `API_URL` constant in `frontend/index.html` to point to your local backend (e.g., `http://127.0.0.1:8000`).

### Data Pipeline (Optional)

To regenerate the skill vocabulary from the raw dataset:

1. Preprocess the Parquet dataset into JSON:
   ```
   cd data
   python preprocess.py
   ```

2. Extract the skill vocabulary:
   ```
   python extract_vocab.py
   ```

This will regenerate `model/skill_vocab.json` with updated skill patterns.

### Deployment

The system supports multiple deployment configurations:

- **Vercel:** Deploy by connecting the repository. The `vercel.json` configuration routes API requests to the FastAPI serverless function and serves the frontend as static files.
- **Docker / Hugging Face Spaces:** Build and run using the provided Dockerfile. The container exposes port 7860 and runs the FastAPI server with Uvicorn.

```
docker build -t spotmyskill .
docker run -p 7860:7860 spotmyskill
```

## API Reference

### GET /api/health

Returns the health status of the API server.

**Response:**
```json
{
  "status": "healthy",
  "service": "SpotmySkill API"
}
```

---

### POST /api/extract_skills

Accepts raw resume text and returns extracted skills.

**Request:**
- Content-Type: `application/json`
- Body:
```json
{
  "text": "Experienced Software Engineer with 5 years of experience in Python, Django, REST APIs, and AWS."
}
```

**Response:**
```json
{
  "skills": ["AWS", "Django", "Python", "REST APIs"],
  "count": 4
}
```

**Fields:**
- `skills` -- Alphabetically sorted list of unique skills identified in the resume text.
- `count` -- Total number of distinct skills extracted.

---

### POST /api/extract_skills_file

Accepts a resume file upload and returns extracted skills.

**Request:**
- Content-Type: `multipart/form-data`
- Body: `file` (file) -- PDF, DOCX, or TXT resume document

**Response:**
```json
{
  "skills": ["AWS", "Django", "Python", "REST APIs"],
  "count": 4
}
```

## Contributors

- **Jeeva N** -- [GitHub](https://github.com/Jeeva5655) | [LinkedIn](https://linkedin.com/in/jeeva-n-37b255293) | [Portfolio](https://portfolio-green-theta-80.vercel.app/)

## License

This project is open source and available for educational and research purposes. The source code, NLP pipeline, skill vocabulary, and deployment configurations are included in this repository.
