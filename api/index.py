from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os
import io
import PyPDF2
import docx

# Model import will happen lazily within the handlers
# from model.skill_extractor import get_extractor

app = FastAPI(title="SpotmySkill API")

# Add CORS middleware to allow cross-origin requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ResumeText(BaseModel):
    text: str
    domain: str = ""
    company_requirement: str = ""

# Mount frontend for local development (Vercel handles this at the edge in production)
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.isdir(frontend_dir):
    app.mount("/frontend", StaticFiles(directory=frontend_dir, html=True), name="frontend")

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "SpotmySkill API"}

@app.get("/")
async def read_root():
    return {"message": "SpotmySkill API is RUNNING. Use /docs for API documentation."}

@app.post("/api/extract_skills")
def extract_skills_endpoint(resume: ResumeText):
    if not resume.text or not resume.text.strip():
        raise HTTPException(status_code=400, detail="Resume text cannot be empty.")
        
    try:
        # Import lazily to avoid startup timeout
        from model.skill_extractor import get_extractor
        extractor = get_extractor()
        skills_data = extractor.extract_skills(resume.text, domain=resume.domain, company_requirement=resume.company_requirement)
        return {
            "skills": skills_data["skills"], 
            "count": len(skills_data["skills"]),
            "match_score": skills_data["match_score"],
            "total_required": skills_data["total_required"]
        }
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Extraction Error: {error_details}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/extract_skills_file")
async def extract_skills_file_endpoint(
    file: UploadFile = File(...),
    domain: str = Form(""),
    company_requirement: str = Form("")
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded.")
        
    try:
        content = await file.read()
        filename = file.filename.lower()
        
        text = ""
        if filename.endswith(".pdf"):
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        elif filename.endswith(".docx"):
            doc = docx.Document(io.BytesIO(content))
            text = "\n".join([para.text for para in doc.paragraphs])
        else:
            # Assume plain text
            text = content.decode("utf-8")
        
        # Import lazily
        from model.skill_extractor import get_extractor
        extractor = get_extractor()
        skills_data = extractor.extract_skills(text, domain=domain, company_requirement=company_requirement)
        return {
            "skills": skills_data["skills"], 
            "count": len(skills_data["skills"]),
            "match_score": skills_data["match_score"],
            "total_required": skills_data["total_required"]
        }
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Unable to decode file. Please upload a .pdf, .docx, or .txt file.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Resume Tracking Features ---
import uuid
import datetime
import tempfile
import json as json_lib

# File-based persistence for tracking data
# Survives across warm Vercel invocations and works locally / Docker
TRACKING_FILE = os.path.join(tempfile.gettempdir(), "spotmyskill_tracking.json")
tracking_db = {}

def _load_tracking_db():
    """Load tracking data from file into memory."""
    global tracking_db
    try:
        if os.path.exists(TRACKING_FILE):
            with open(TRACKING_FILE, 'r', encoding='utf-8') as f:
                loaded = json_lib.load(f)
                tracking_db.update(loaded)
    except Exception as e:
        print(f"[Tracking] Could not load: {e}")

def _save_tracking_db():
    """Persist in-memory tracking data to file."""
    try:
        with open(TRACKING_FILE, 'w', encoding='utf-8') as f:
            json_lib.dump(tracking_db, f, ensure_ascii=False)
    except Exception as e:
        print(f"[Tracking] Could not save: {e}")

# Load any existing tracking data on startup
_load_tracking_db()

class TrackResumeRequest(BaseModel):
    text: str
    filename: str = "Resume"

@app.post("/api/track/generate")
async def generate_tracking_link(request: TrackResumeRequest):
    """Generates a unique tracking ID for a resume."""
    _load_tracking_db()
    track_id = str(uuid.uuid4())[:8]
    
    tracking_db[track_id] = {
        "text": request.text,
        "filename": request.filename,
        "views": 0,
        "view_log": [],
        "last_viewed": None,
        "created_at": datetime.datetime.now().isoformat()
    }
    _save_tracking_db()
    
    return {"track_id": track_id}

@app.get("/api/track/stats/{track_id}")
async def get_tracking_stats(track_id: str):
    """Gets the view statistics for a specific resume."""
    _load_tracking_db()
    if track_id not in tracking_db:
        raise HTTPException(status_code=404, detail="Tracking ID not found")
        
    data = tracking_db[track_id]
    return {
        "views": data["views"],
        "last_viewed": data["last_viewed"],
        "filename": data["filename"],
        "view_log": data.get("view_log", [])
    }

@app.get("/view/{track_id}", response_class=HTMLResponse)
async def view_shared_resume(track_id: str):
    """The endpoint the recruiter visits. Logs the view and shows the resume."""
    _load_tracking_db()
    if track_id not in tracking_db:
        return HTMLResponse(content="<h1>Resume not found or link expired.</h1>", status_code=404)
        
    # Log the view
    now = datetime.datetime.now().isoformat()
    tracking_db[track_id]["views"] += 1
    tracking_db[track_id]["last_viewed"] = now
    if "view_log" not in tracking_db[track_id]:
        tracking_db[track_id]["view_log"] = []
    tracking_db[track_id]["view_log"].append({"timestamp": now})
    _save_tracking_db()
    
    # Extract values BEFORE the f-string so we use simple variables
    data = tracking_db[track_id]
    resume_filename = data['filename']
    resume_text = data['text'][:3000]
    view_count = data['views']
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{resume_filename} - SpotmySkill</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Inter', sans-serif; background: #0f172a; color: #e2e8f0; min-height: 100vh; padding: 2rem; }}
        .container {{ max-width: 800px; margin: 0 auto; background: rgba(30,41,59,0.85); border: 1px solid rgba(255,255,255,0.1); padding: 3rem; border-radius: 1.5rem; backdrop-filter: blur(12px); box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5); }}
        .brand {{ font-size: 0.9rem; font-weight: 600; background: linear-gradient(to right, #60a5fa, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 1.5rem; }}
        h1 {{ font-size: 1.75rem; font-weight: 700; color: #f8fafc; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid rgba(255,255,255,0.1); }}
        .resume-body {{ white-space: pre-wrap; font-family: inherit; font-size: 0.95rem; line-height: 1.8; color: #cbd5e1; background: rgba(15,23,42,0.5); padding: 2rem; border-radius: 1rem; border: 1px solid rgba(255,255,255,0.05); }}
        .footer {{ margin-top: 2rem; text-align: center; color: #64748b; font-size: 0.8rem; }}
        .footer a {{ color: #60a5fa; text-decoration: none; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="brand">SpotmySkill AI</div>
        <h1>{resume_filename}</h1>
        <div class="resume-body">{resume_text}</div>
    </div>
    <div class="footer">
        Shared securely via <a href="/">SpotmySkill</a> &middot; View #{view_count}
    </div>
</body>
</html>"""
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

