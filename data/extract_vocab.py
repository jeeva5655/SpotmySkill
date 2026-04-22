import json
import re

def build_skill_vocab():
    with open("skills_dataset.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        
    skills_set = set()
    print("Extracting skills section from resumes...")
    for item in data:
        resume = item.get("resume", "")
        # Find 'Skills' section
        match = re.search(r'Skills\s+(.*?)(?:\n\n|\Z|Experience|Education)', resume, re.IGNORECASE | re.DOTALL)
        if match:
            skills_text = match.group(1).strip()
            # Split by commas, newlines, or dots
            candidate_skills = re.split(r'[,•\n]+', skills_text)
            for skill in candidate_skills:
                skill = skill.strip()
                if 2 < len(skill) < 40:
                    skills_set.add(skill)
                    
    skills_list = sorted(list(skills_set))
    print(f"Found {len(skills_list)} unique skill phrases.")
    
    with open("../model/skill_vocab.json", "w", encoding="utf-8") as f:
        json.dump(skills_list, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    build_skill_vocab()
