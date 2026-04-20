import spacy
from spacy.pipeline import EntityRuler
import json
import os

class SkillExtractor:
    def __init__(self, model_name="en_core_web_sm", vocab_path="model/skill_vocab.json"):
        # Load the base spaCy model
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            print(f"Model '{model_name}' not found. Please run: python -m spacy download {model_name}")
            raise
            
        # Add the EntityRuler to the pipeline
        # We put it before 'ner' so that our rules take precedence over general English entities
        self.ruler = self.nlp.add_pipe("entity_ruler", before="ner")
        
        # Load our extracted skills vocabulary
        # Use an absolute path relative to this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        vocab_path_full = os.path.join(current_dir, "skill_vocab.json")
        try:
            with open(vocab_path_full, "r", encoding="utf-8") as f:
                skill_vocab = json.load(f)
        except FileNotFoundError:
            print(f"Warning: Skill vocab file not found at {vocab_path_full}")
            skill_vocab = []

        # Create patterns for each skill phrase
        patterns = []
        for skill in skill_vocab:
            # Simple exact match (case insensitive approach built into EntityRuler using lowercasing if configured,
            # or we can just supply the string pattern. Spacy's default string pattern matches exact case,
            # so we'll match lowercase via LOWER attribute for resilience)
            # A more robust pattern matches tokens ignoring case:
            # We split the skill term by spaces to match individual tokens
            tokens = skill.split()
            pattern = [{"LOWER": {"IN": [t.lower(), t]}} for t in tokens if t]
            
            # Use 'SKILL' as the entity label
            patterns.append({"label": "SKILL", "pattern": pattern})
        
        # We don't want to load all 11k skills if some are noisy. 
        # But letting EntityRuler handle them is highly efficient.
        # Ensure we only load non-empty patterns
        valid_patterns = [p for p in patterns if p["pattern"]]
        
        if valid_patterns:
            self.ruler.add_patterns(valid_patterns)
            print(f"Loaded {len(valid_patterns)} skill patterns into EntityRuler.")
            
    def _extract_raw_skills(self, text):
        if not text:
            return set()
        doc = self.nlp(text)
        extracted = set()
        
        # Basic list of persistent stop words just in case
        stop_words = {"the", "with", "users", "user", "and", "or", "for", "in", "to", "a"}
        
        for ent in doc.ents:
            if ent.label_ == "SKILL":
                skill_text = ent.text.strip()
                skill_lower = skill_text.lower()
                
                if skill_lower in stop_words:
                    continue
                    
                # Ignore single character skills unless they are specifically common like 'c' or 'r'
                if len(skill_text) <= 1 and skill_lower not in ['c', 'r']:
                    continue
                    
                extracted.add(skill_text)
        return extracted

    def extract_skills(self, text, domain="", company_requirement=""):
        resume_skills = self._extract_raw_skills(text)
        
        req_text = f"{domain} {company_requirement}".strip()
        
        if req_text:
            req_skills = self._extract_raw_skills(req_text)
            
            if req_skills:
                # Lowercase requirements for robust matching
                req_skills_lower = {s.lower() for s in req_skills}
                
                # Perform intersection
                matched_skills = set()
                for s in resume_skills:
                    if s.lower() in req_skills_lower:
                        matched_skills.add(s)
                return sorted(list(matched_skills))
            
            # If they provided requirements but NO skills could be extracted from them,
            # we might want to still return the resume skills, or empty list.
            # Usually it's better to return empty if they strictly filtered, 
            # but to be safe we'll fallback to returning empty list since they wanted intersection.
            return []
            
        return sorted(list(resume_skills))

# Singleton instance for the API
# We will initialize this lazily in the FastAPI app to avoid loading latency on import
extractor_instance = None

def get_extractor():
    global extractor_instance
    if extractor_instance is None:
        extractor_instance = SkillExtractor()
    return extractor_instance
