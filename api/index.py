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

# Note: We don't mount the static directory here because Vercel handles
# static files at the edge. Mounting a missing directory would cause a 500 error.

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

# In-memory database for tracking (Note: Resets on Vercel cold start)
# For production, this should be replaced with Redis/Postgres
tracking_db = {}

class TrackResumeRequest(BaseModel):
    text: str
    filename: str = "Resume"

@app.post("/api/track/generate")
async def generate_tracking_link(request: TrackResumeRequest):
    """Generates a unique tracking ID for a resume."""
    track_id = str(uuid.uuid4())[:8] # Short ID
    
    tracking_db[track_id] = {
        "text": request.text,
        "filename": request.filename,
        "views": 0,
        "last_viewed": None,
        "created_at": datetime.datetime.now().isoformat()
    }
    
    return {"track_id": track_id}

@app.get("/api/track/stats/{track_id}")
async def get_tracking_stats(track_id: str):
    """Gets the view statistics for a specific resume."""
    if track_id not in tracking_db:
        raise HTTPException(status_code=404, detail="Tracking ID not found")
        
    data = tracking_db[track_id]
    return {
        "views": data["views"],
        "last_viewed": data["last_viewed"],
        "filename": data["filename"]
    }

@app.get("/view/{track_id}", response_class=HTMLResponse)
async def view_shared_resume(track_id: str):
    """The endpoint the recruiter visits. Logs the view and shows the resume."""
    if track_id not in tracking_db:
        return HTMLResponse(content="<h1>Resume not found or link expired.</h1>", status_code=404)
        
    # Log the view
    tracking_db[track_id]["views"] += 1
    tracking_db[track_id]["last_viewed"] = datetime.datetime.now().isoformat()
    
    # Render a simple professional view for the recruiter
    data = tracking_db[track_id]
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{data['filename']}} - SpotmySkill</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; background: #f9fafb; }}
            .container {{ background: white; padding: 40px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
            h1 {{ color: #4f46e5; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; }}
            .footer {{ margin-top: 40px; text-align: center; color: #6b7280; font-size: 0.8em; }}
            pre {{ white-space: pre-wrap; font-family: inherit; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>{{data['filename']}}</h1>
            <pre>{{data['text'][:2000]}}... [Resume Truncated for Preview]</pre>
        </div>
        <div class="footer">
            Shared securely via SpotmySkill AI
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
