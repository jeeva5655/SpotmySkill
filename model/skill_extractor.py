import spacy
from spacy.pipeline import EntityRuler
import json
import os

# Extended noise words that should NEVER be extracted as skills.
# These are resume-filler words that leak through from the vocab.
NOISE_WORDS = {
    # Common English stop words
    "the", "with", "users", "user", "and", "or", "for", "in", "to", "a", "an",
    "of", "on", "at", "by", "is", "are", "was", "were", "be", "been", "being",
    "it", "its", "this", "that", "we", "they", "he", "she", "you", "i", "me",
    # Resume filler / generic words
    "proficient", "proficient in", "experienced", "experience", "experience in",
    "experiences", "expert", "expertise", "knowledge", "understanding",
    "years", "year", "month", "months", "5 years of", "years of",
    "years of experience", "responsible", "responsible for",
    "excellent", "strong", "good", "well", "able", "hands",
    "senior", "junior", "lead", "work", "working", "skills",
    "team", "management", "project", "projects", "support",
    "develop", "developed", "developing", "development",
    "design", "system", "systems", "data", "tools", "tool",
    "new", "high", "based", "full", "key", "set", "part",
    "level", "type", "end", "run", "test", "build", "plan",
    "help", "need", "range", "time", "best", "large", "small",
    "open", "close", "step", "area", "role", "field", "line",
    "rest", "cloud", "deployment", "day", "day-to-day",
}


class SkillExtractor:
    def __init__(self, vocab_path=None):
        # Load the base spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Model 'en_core_web_sm' not found. Please run: python -m spacy download en_core_web_sm")
            raise
            
        # Add the EntityRuler to the pipeline
        # We put it before 'ner' so that our rules take precedence over general English entities
        self.ruler = self.nlp.add_pipe("entity_ruler", before="ner")
        
        # Resolve vocab path
        if vocab_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            vocab_path = os.path.join(current_dir, "skill_vocab.json")
        
        # Load our extracted skills vocabulary
        try:
            with open(vocab_path, "r", encoding="utf-8") as f:
                skill_vocab = json.load(f)
        except FileNotFoundError:
            print(f"Warning: Skill vocab file not found at {vocab_path}")
            skill_vocab = []

        # Create patterns for each skill phrase
        patterns = []
        for skill in skill_vocab:
            skill_clean = skill.strip()
            if not skill_clean:
                continue
            
            # Skip noise words at vocab-load time too
            if skill_clean.lower() in NOISE_WORDS:
                continue
            
            # Skip single characters unless they are known single-char skills
            if len(skill_clean) <= 1 and skill_clean.lower() not in ('c', 'r'):
                continue
            
            # Build token-level pattern: match each token case-insensitively
            # using the LOWER attribute (expects a plain string value)
            tokens = skill_clean.split()
            pattern = [{"LOWER": t.lower()} for t in tokens if t]
            
            if pattern:
                patterns.append({"label": "SKILL", "pattern": pattern})
        
        if patterns:
            self.ruler.add_patterns(patterns)
            print(f"Loaded {len(patterns)} skill patterns into EntityRuler.")
            
    def _extract_raw_skills(self, text):
        if not text:
            return {}
        doc = self.nlp(text)
        extracted = {}
        
        for ent in doc.ents:
            if ent.label_ == "SKILL":
                skill_text = ent.text.strip()
                skill_lower = skill_text.lower()
                
                # Final runtime filter for noise
                if skill_lower in NOISE_WORDS:
                    continue
                    
                # Ignore single character skills unless they are specifically common like 'C' or 'R'
                if len(skill_text) <= 1 and skill_lower not in ('c', 'r'):
                    continue
                
                # Normalize capitalization to the most common format we see
                # We'll use the title case or original case if it's an acronym
                normalized_skill = skill_text if skill_text.isupper() else skill_text.title()
                
                # We use lowercased key for tracking to avoid duplicates like Python vs python
                if skill_lower not in extracted:
                    extracted[skill_lower] = {"name": normalized_skill, "count": 1}
                else:
                    extracted[skill_lower]["count"] += 1
                    
        return extracted

    def extract_skills(self, text, domain="", company_requirement=""):
        resume_skills_dict = self._extract_raw_skills(text)
        
        req_text = f"{domain} {company_requirement}".strip()
        match_score = None
        
        if req_text:
            req_skills_dict = self._extract_raw_skills(req_text)
            
            if req_skills_dict:
                # Perform intersection
                matched_skills = []
                req_skills_lower = set(req_skills_dict.keys())
                
                for s_lower, skill_data in resume_skills_dict.items():
                    if s_lower in req_skills_lower:
                        matched_skills.append(skill_data)
                
                # Calculate ATS Match Score
                total_reqs = len(req_skills_lower)
                matched_reqs = len(matched_skills)
                if total_reqs > 0:
                    match_score = round((matched_reqs / total_reqs) * 100)
                
                # Sort by frequency, then alphabetically
                matched_skills.sort(key=lambda x: (-x["count"], x["name"]))
                
                return {
                    "skills": matched_skills,
                    "match_score": match_score,
                    "total_required": total_reqs
                }
            
            # If they provided requirements but NO skills could be extracted
            # fall back to all resume skills
            all_skills = list(resume_skills_dict.values())
            all_skills.sort(key=lambda x: (-x["count"], x["name"]))
            return {
                "skills": all_skills,
                "match_score": None,
                "total_required": 0
            }
            
        all_skills = list(resume_skills_dict.values())
        all_skills.sort(key=lambda x: (-x["count"], x["name"]))
        return {
            "skills": all_skills,
            "match_score": None,
            "total_required": 0
        }

# Singleton instance for the API
# We will initialize this lazily in the FastAPI app to avoid loading latency on import
extractor_instance = None

def get_extractor():
    global extractor_instance
    if extractor_instance is None:
        extractor_instance = SkillExtractor()
    return extractor_instance
