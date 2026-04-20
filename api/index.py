from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse
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
        skills = extractor.extract_skills(resume.text, domain=resume.domain, company_requirement=resume.company_requirement)
        return {"skills": skills, "count": len(skills)}
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
        skills = extractor.extract_skills(text, domain=domain, company_requirement=company_requirement)
        return {"skills": skills, "count": len(skills)}
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Unable to decode file. Please upload a .pdf, .docx, or .txt file.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
