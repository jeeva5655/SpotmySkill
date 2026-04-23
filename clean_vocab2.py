"""
Final deep vocab cleaning pass for skill_vocab.json.
Removes remaining noise categories found after initial cleaning:
- "and X" / "or X" fragment phrases
- Generic single-word business terms that aren't technical skills
- Sentence fragments
"""
import json
import re
import os

VOCAB_PATH = "model/skill_vocab.json"

# ── Additional single generic words to exclude ────────────────
# These are real English words that leaked into the vocab but aren't skills
GENERIC_SINGLE_WORDS = {
    # Too generic to be a skill on its own
    "accurate", "accuracy", "acquisition", "agents", "agent",
    "administrative", "administration", "advertising", "analyst",
    "analysis", "assessment", "architecture", "assistant",
    "benefits", "budget", "budgeting", "conferences", "conference",
    "designed", "designing", "email", "award", "awards",
    "accounting",  # ambiguous (it is a field but also a very generic term)
    "accurate", "accuracy",
    # Business role words not distinct skills
    "director", "manager", "coordinator", "specialist", "officer",
    "supervisor", "administrator", "associate", "representative",
    "executive", "consultant", "analyst", "intern", "contractor",
    # Generic actions
    "responsible", "accountability", "accountable",
    "communications", "communication",
    "planning", "organizing", "reporting", "monitoring",
    "implementation", "operations", "coordination",
    "presentation", "presentations",
    # Body/time words
    "annual", "monthly", "weekly", "daily",
    "current", "previous", "prior", "additional",
    "multiple", "various", "several",
}

# ── Regex patterns for noise ──────────────────────────────────
NOISE_PATTERNS = [
    # "and XYZ" fragments
    (re.compile(r"^and\s", re.IGNORECASE), "and_fragment"),
    (re.compile(r"^or\s", re.IGNORECASE), "or_fragment"),
    (re.compile(r"^for\s", re.IGNORECASE), "for_fragment"),
    (re.compile(r"^in\s", re.IGNORECASE), "in_fragment"),
    (re.compile(r"^a\s", re.IGNORECASE), "article_fragment"),
    (re.compile(r"^an\s", re.IGNORECASE), "article_fragment"),
    (re.compile(r"^the\s", re.IGNORECASE), "article_fragment"),
    (re.compile(r"^all\s", re.IGNORECASE), "all_fragment"),
    (re.compile(r"^along\s", re.IGNORECASE), "along_fragment"),
    # Sentences with multiple clauses
    (re.compile(r"\band\s+\w+ing\b"), "verb_clause"),
    # Number-starting
    (re.compile(r"^\d"), "starts_with_number"),
    # Contains quotes or angle brackets
    (re.compile(r'[<>"\']{2,}'), "quote_garbage"),
    # WPB, 87, etc. — internal reference codes
    (re.compile(r"\b\d+['\"]\s+WPB\b"), "reference_code"),
]

# ── Known tech & professional skills to PROTECT ───────────────
# These might match generic word patterns above but must be kept
PROTECTED = {
    "accounting software", "administrative support", "agent",
    "annual reports", "budget management", "budget planning",
    "communications skills", "operations management",
    "program management", "project management",
    "financial analysis", "data analysis", "business analysis",
    "marketing communications", "digital marketing",
    "accounting principles",
}


def is_still_noisy(entry: str):
    """Returns (is_noisy: bool, reason: str) for remaining noise."""
    w = entry.strip()
    wl = w.lower()

    if not w:
        return True, "empty"

    # Protected
    if wl in PROTECTED:
        return False, "protected"

    # Run regex patterns
    for pat, reason in NOISE_PATTERNS:
        if pat.search(w):
            return True, reason

    # Single generic word
    words = w.split()
    if len(words) == 1 and wl in GENERIC_SINGLE_WORDS:
        return True, "generic_single_word"

    return False, "ok"


def run():
    with open(VOCAB_PATH, "r", encoding="utf-8") as f:
        vocab = json.load(f)

    print(f"Starting vocab size: {len(vocab)}")

    from collections import Counter
    removal_reasons = Counter()
    cleaned = []

    for entry in vocab:
        noisy, reason = is_still_noisy(entry)
        if noisy:
            removal_reasons[reason] += 1
        else:
            cleaned.append(entry.strip())

    # Dedup (case-insensitive)
    seen = set()
    deduped = []
    for skill in cleaned:
        key = skill.lower()
        if key not in seen:
            seen.add(key)
            deduped.append(skill)

    dups = len(cleaned) - len(deduped)
    removal_reasons["duplicates"] += dups

    deduped.sort(key=str.lower)

    print(f"\nRemoval Breakdown:")
    for reason, count in removal_reasons.most_common():
        print(f"  {reason:<30}: {count}")

    removed = len(vocab) - len(deduped)
    print(f"\n  TOTAL REMOVED: {removed}")
    print(f"  FINAL SIZE   : {len(deduped)}")

    with open(VOCAB_PATH, "w", encoding="utf-8") as f:
        json.dump(deduped, f, indent=2, ensure_ascii=False)

    print(f"\nVocab saved to {VOCAB_PATH}")


if __name__ == "__main__":
    run()
