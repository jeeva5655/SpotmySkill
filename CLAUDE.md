# SPOTMYSKILL CAVE-MEM
# PRJ
name: SpotmySkill (SMS)
type: NLP Resume Skill Extractor
stack: FastAPI (backend), spaCy 3.7.1 (NLP), vanilla HTML/CSS/JS (frontend)
deploy: Vercel, Docker, HF Spaces

# ARCH
frontend: index.html (glassmorphism UI) -> /api/extract_skills or /api/extract_skills_file
backend: api/index.py (FastAPI), multi-format parser (PDF, DOCX, TXT)
nlp: model/skill_extractor.py (spaCy en_core_web_sm, EntityRuler), model/skill_vocab.json (2k+ patterns)

# RULES
- fast execution
- lazy load model
- async IO
- clean UI, dark mode

# END
