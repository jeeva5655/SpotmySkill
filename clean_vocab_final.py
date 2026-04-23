"""
Final targeted vocab cleanup - removes remaining noise entries
found by inspecting the dataset output samples.
"""
import json
import re

VOCAB_PATH = "model/skill_vocab.json"

# Additional entries confirmed as noise from dataset inspection
ADDITIONAL_NOISE = {
    # Too generic single words
    "bills", "image", "certified", "claims", "attendance", "audit",
    "capabilities", "capacity", "call center", "bi-weekly payroll",
    "assessments", "administrative duties",
    "linkedin", "engineers", "engineer",
    "java",  # Keep JAVA as upper but this lowercase form is duplicate
    "certificates", "certificate", "certified management accountant",
    # Location/org names that snuck through
    "california state university", "university",
    # Resume section headers that snuck through
    "assistant manager",  # job title, not a skill
    "business analyst",   # job title
    "business solutions", # vague
    # Generic phrases
    "critical thinking",  # soft skill, OK but very common noise
}

# Actual tech/real skills to PROTECT even if they appear generic
PROTECTED = {
    "java", "linux", "c++", "natural language processing",
    "image processing", "call center", "capacity planning",
    "critical thinking",  # some want to keep this
    "audit",
}

with open(VOCAB_PATH, "r", encoding="utf-8") as f:
    vocab = json.load(f)

print(f"Original: {len(vocab)}")

removed = []
kept = []
for v in vocab:
    vl = v.lower().strip()
    if vl in ADDITIONAL_NOISE and vl not in PROTECTED:
        removed.append(v)
    else:
        kept.append(v)

print(f"Removed {len(removed)} additional noise entries:")
for r in removed:
    print(f"  {repr(r)}")

# Dedup
seen = set()
deduped = []
for v in kept:
    k = v.lower().strip()
    if k not in seen:
        seen.add(k)
        deduped.append(v)

deduped.sort(key=str.lower)
print(f"Final size: {len(deduped)}")

with open(VOCAB_PATH, "w", encoding="utf-8") as f:
    json.dump(deduped, f, indent=2, ensure_ascii=False)

print(f"Saved to {VOCAB_PATH}")
