"""
Full dataset noise analysis and cleaning script for SpotmySkill.
Targets both:
  1. model/skill_vocab.json   — the skill vocabulary
  2. data/skills_dataset.json — the training/extraction dataset

Run from the project root:
  python analyze_and_clean.py
"""
import json
import re
import os
import sys
from collections import Counter, defaultdict

# ────────────────────────────────────────────────
# NOISE DETECTION RULES
# ────────────────────────────────────────────────

# Articles / filler starters
ARTICLE_STARTERS = {
    "a ", "an ", "the ", "all ", "along ", "being ", "while ",
    "some ", "any ", "each ", "both ", "such ", "this ", "that ",
    "these ", "those ", "my ", "your ", "his ", "her ", "our ", "their ",
}

# Generic business/resume filler words (not real skills)
FILLER_WORDS = {
    "proficient", "proficient in", "experienced", "experience", "experience in",
    "experiences", "expert", "expertise", "knowledge", "understanding",
    "years", "year", "month", "months", "day", "days", "week", "weeks",
    "responsible", "responsible for", "excellent", "strong", "good",
    "well", "able", "hands", "hands-on", "senior", "junior", "lead",
    "work", "working", "skills", "skill", "team", "teams", "management",
    "project", "projects", "support", "develop", "developed", "developing",
    "development", "design", "system", "systems", "data", "tools", "tool",
    "new", "high", "based", "full", "key", "set", "part", "level", "type",
    "end", "run", "test", "build", "plan", "help", "need", "range", "time",
    "best", "large", "small", "open", "close", "step", "area", "role",
    "field", "line", "rest", "cloud", "deployment", "day-to-day",
    "ability", "ability to", "able to",
}

# Clear non-skill proper nouns found in vocab
KNOWN_NOISE_ENTRIES = {
    # People/entertainment
    "alex darvish", "lionel richie", "the bees gees", "the temptations",
    "the today show", "the works consulting", "akanksha foundation",
    # Places / events
    "alaskan way viaduct", "alcohol awareness week", "linus project",
    "lighthouse ministries", "year 2000",
    # Noise fragments
    "along with my", "all star", "airline tickets", "all sales",
    "all financials", "all information", "all beverage ordering",
    "all pc hardware", "all microsoft", "the accounting", "the accounts",
    "the food bank", "the ladder", "the med/surg unit", "the office",
    "the sales", "the uk", "abc.com", "abcnews.com", "abc 7 news",
    "wsam image", "wsam-dc fiber", "x-51 hypersonic engine",
    "zyrtec", "allegra", "youth participants", "yahoo and",
    "accomplish", "accomplishments", "accomplishments created", "academic",
    "accessories", "accommodations", "aardwolf", "abandon rate",
    "listen effectively", "listen intently", "listening skills",
    "literary analysis", "linguistic behaviors",
    "light bookkeeping knowledge", "life support",
    "writing test", "wounds", "woven shirts", "yoga", "youth",
    "wound care", "a&e",
}

# Stop words
STOP_WORDS = {
    "the", "with", "users", "user", "use", "using", "used", "make", "making",
    "all", "any", "some", "many", "much", "other", "another", "such",
    "and", "or", "but", "if", "then", "else", "when", "where", "why", "how",
    "this", "that", "these", "those", "is", "am", "are", "was", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "doing",
    "a", "an", "for", "in", "on", "at", "to", "from", "by", "about", "as",
    "into", "like", "through", "after", "over", "between", "out", "against",
    "during", "without", "before", "under", "around", "among", "we", "they",
    "it", "you", "he", "she", "i", "me", "him", "her", "us", "them", "my",
    "your", "their", "our", "its", "whose", "who", "whom", "which", "what",
    "can", "will", "would", "should", "could", "may", "might", "must", "very",
    "too", "also", "just", "only", "even", "more", "most", "less", "least",
    "of", "no", "not", "nor", "so", "up", "down",
}

# Short known tech acronyms to keep
KEEP_SHORT = {
    "c", "r", "go", "sql", "css", "html", "php", "xml", "api",
    "aws", "gcp", "npm", "git", "vim", "ssh", "tcp", "udp",
    "dns", "sap", "erp", "crm", "ios", "ux", "ui", "qa",
    "ci", "cd", "ai", "ml", "nlp", "ocr", "rpa", "etl",
    "seo", "sem", "ppc", "roi", "kpi", "vpn", "lan", "wan",
    "ip", "os", "db", "oop", "dba", "bi", "emr", "ehr",
    "bls", "cpr", "rn", "lpn", "cna", "cma", "emt",
    "hvac", "osha", "cad", "bim", "gis", "plc",
    "iot", "sdk", "ide", "gaap", "ifrs", "cpa", "aml", "kyc",
    "jira", "asana", "figma", ".net",
}

# Section headers
SECTION_HEADERS = {
    "education", "experience", "summary", "objective", "references",
    "certifications", "awards", "publications", "interests", "hobbies",
    "languages", "projects", "achievements", "qualifications",
    "professional experience", "work experience", "professional summary",
    "career objective", "career summary", "additional information",
    "contact information", "personal information", "technical skills",
}


def is_vocab_noise(entry: str):
    """Returns (is_noisy: bool, reason: str)"""
    w = entry.strip()
    wl = w.lower()
    words = w.split()

    # Empty
    if not w:
        return True, "empty"

    # Garbled unicode (replacement character or common garbage)
    if "\ufffd" in w or "\u200b" in w or "\xa0" in w or "\u25cf" in w:
        return True, "unicode_garbage"

    # Non-ASCII with encoding artifacts (? in middle of word suggests bad decode)
    if re.search(r"[^\x00-\x7F]", w) and "?" in w:
        return True, "garbled_encoding"

    # Garbled – non-ASCII chars that aren't legit diacritics
    for ch in w:
        code = ord(ch)
        if code > 127 and ch not in ("é", "ñ", "ü", "ö", "ä", "ß", "ó", "á", "í", "ú"):
            return True, "non_ascii_garbage"

    # Purely numeric / date-like
    if re.match(r"^[\d/\-\.\,\s\\]+$", w):
        return True, "numeric_or_date"

    # Starts with digit
    if re.match(r"^\d", w):
        return True, "starts_with_number"

    # Dollar amounts
    if "$" in w:
        return True, "dollar_amount"

    # Starts with bullet / punctuation
    if re.match(r"^[\*\-\+\u2022\u2013\u2014\"\'\\]", w):
        return True, "bullet_punct_start"

    # Starts with ". " or "/ " or ", " — parsing fragments
    if re.match(r"^[\.\\/,;:]\s", w):
        return True, "parse_fragment"

    # Tab or double-space formatting
    if "\t" in w or "  " in w:
        return True, "formatting_artifact"

    # Ampersand fragments
    if w.startswith("&") or w.endswith(" &") or w.endswith(" and"):
        return True, "ampersand_fragment"

    # Parenthesis fragments
    if w.startswith("(") and not w.endswith(")"):
        return True, "unclosed_paren"
    if w.endswith(")") and "(" not in w:
        return True, "stray_close_paren"

    # Colon fragments (Category: value)
    if re.search(r":\s", w) and not any(t in wl for t in ["c:", "c#", "http:", "https:", "tcp:", "udp:", "ftp:"]):
        return True, "colon_fragment"

    # Section headers
    if wl in SECTION_HEADERS:
        return True, "section_header"

    # Single stop words
    if wl in STOP_WORDS and wl not in KEEP_SHORT:
        return True, "stop_word"

    # Filler words
    if wl in FILLER_WORDS:
        return True, "resume_filler"

    # Known non-skill entries
    if wl in KNOWN_NOISE_ENTRIES:
        return True, "known_non_skill"

    # Starts with article / filler word
    for starter in ARTICLE_STARTERS:
        if wl.startswith(starter):
            return True, "article_or_filler_start"

    # Ends with a stop word (incomplete phrase)
    stop_endings = {"and", "or", "for", "in", "to", "of", "the", "with", "at", "by", "on", "as", "an", "a"}
    if len(words) >= 2 and words[-1].lower() in stop_endings:
        if wl not in {"single sign on", "single sign-on"}:
            return True, "stop_word_ending"

    # "ability to" or "able to" patterns
    if wl.startswith("ability to") or wl.startswith("able to"):
        return True, "ability_phrase"

    # Ends with period (sentence ending) but not a tech abbreviation
    if w.endswith(".") and len(w) > 5 and not re.match(r"^[\w\.\+\#]+$", w):
        return True, "sentence_ending_period"

    # Very long entry or many words
    if len(w) > 45 or len(words) >= 5:
        return True, "too_long"

    # 4 words where all are title-case → likely a sentence fragment or org name
    if len(words) == 4 and all(wd[0].isupper() for wd in words if wd):
        # Exception: well-known multi-word tech terms
        known_4word = {
            "natural language processing", "machine learning models",
            "deep learning frameworks",
        }
        if wl not in known_4word:
            return True, "likely_title_case_name_or_fragment"

    # Very short single words (≤3 chars) not in known tech
    if len(words) == 1 and len(w) <= 3 and w.lower().isalpha():
        if wl not in KEEP_SHORT:
            if not w.isupper():  # uppercase acronym? keep it
                return True, "too_short_unknown"

    return False, "ok"


def clean_vocab(path: str):
    """Load, clean, deduplicate and save skill_vocab.json"""
    with open(path, "r", encoding="utf-8") as f:
        vocab = json.load(f)

    print(f"\n{'='*60}")
    print(f" VOCAB CLEANING: {path}")
    print(f"{'='*60}")
    print(f"Original size: {len(vocab)}")

    removal_reasons = Counter()
    cleaned = []

    for entry in vocab:
        noisy, reason = is_vocab_noise(entry)
        if noisy:
            removal_reasons[reason] += 1
        else:
            cleaned.append(entry.strip())

    # Deduplicate (case-insensitive), keep first occurrence
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
        print(f"  {reason:<35} : {count}")

    total_removed = len(vocab) - len(deduped)
    print(f"\n  TOTAL REMOVED  : {total_removed}")
    print(f"  CLEANED SIZE   : {len(deduped)}")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(deduped, f, indent=2, ensure_ascii=False)

    print(f"\nVocabulary saved to {path}")
    return deduped


def analyze_dataset(path: str):
    """Analyze skills_dataset.json and report noise patterns."""
    with open(path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    print(f"\n{'='*60}")
    print(f" DATASET ANALYSIS: {path}")
    print(f"{'='*60}")
    print(f"Total records: {len(dataset)}")

    # Inspect the 'skills' field format
    skills_formats = Counter()
    empty_skills = 0
    generic_placeholder = 0
    good_records = 0

    generic_pattern = re.compile(
        r"The key skills for this .+ professional include relevant experience",
        re.IGNORECASE
    )

    for rec in dataset:
        skills_text = rec.get("skills", "").strip()
        resume_text = rec.get("resume", "").strip()

        if not skills_text:
            empty_skills += 1
        elif generic_pattern.search(skills_text):
            generic_placeholder += 1
        else:
            good_records += 1

        # Detect format
        if skills_text.startswith("1.") or skills_text.startswith("1)"):
            skills_formats["numbered_list"] += 1
        elif "\n-" in skills_text or skills_text.startswith("-"):
            skills_formats["bullet_list"] += 1
        elif "," in skills_text and len(skills_text.split(",")) > 2:
            skills_formats["comma_separated"] += 1
        else:
            skills_formats["prose_paragraph"] += 1

    print(f"\nSkills Field Quality:")
    print(f"  Good records         : {good_records}")
    print(f"  Generic placeholders : {generic_placeholder}  (<-- NOISE)")
    print(f"  Empty skills         : {empty_skills}         (<-- NOISE)")
    print(f"  Total noise records  : {generic_placeholder + empty_skills}")
    print(f"\nSkills Format Distribution:")
    for fmt, cnt in skills_formats.most_common():
        print(f"  {fmt:<25}: {cnt}")

    # Show sample good and bad records
    print("\nSample GOOD records (skills field):")
    shown = 0
    for rec in dataset:
        skills_text = rec.get("skills", "").strip()
        if skills_text and not generic_pattern.search(skills_text) and shown < 3:
            print(f"  ---\n  {skills_text[:300]}")
            shown += 1

    print("\nSample PLACEHOLDER records (noise):")
    shown = 0
    for rec in dataset:
        skills_text = rec.get("skills", "").strip()
        if generic_pattern.search(skills_text) and shown < 3:
            print(f"  ---\n  {skills_text[:200]}")
            shown += 1

    return dataset, generic_pattern


def clean_dataset(path: str):
    """Remove noise records from skills_dataset.json and save."""
    dataset, generic_pattern = analyze_dataset(path)

    original_count = len(dataset)

    cleaned = []
    removed_empty = 0
    removed_generic = 0
    removed_short_resume = 0

    for rec in dataset:
        skills_text = rec.get("skills", "").strip()
        resume_text = rec.get("resume", "").strip()

        # Skip empty skills
        if not skills_text:
            removed_empty += 1
            continue

        # Skip generic placeholder skills (useless signal)
        if generic_pattern.search(skills_text):
            removed_generic += 1
            continue

        # Skip records with very short resume text (likely bad extractions)
        if len(resume_text) < 100:
            removed_short_resume += 1
            continue

        # Clean whitespace in fields
        rec["resume"] = resume_text
        rec["skills"] = skills_text
        cleaned.append(rec)

    print(f"\n{'='*60}")
    print(f" DATASET CLEANING RESULTS")
    print(f"{'='*60}")
    print(f"  Original records     : {original_count}")
    print(f"  Removed (empty)      : {removed_empty}")
    print(f"  Removed (generic)    : {removed_generic}")
    print(f"  Removed (short resume): {removed_short_resume}")
    print(f"  Cleaned records      : {len(cleaned)}")
    print(f"  Removed total        : {original_count - len(cleaned)}")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, indent=2, ensure_ascii=False)

    print(f"\nDataset saved to {path}")
    return cleaned


if __name__ == "__main__":
    base = os.path.dirname(os.path.abspath(__file__))

    vocab_path = os.path.join(base, "model", "skill_vocab.json")
    dataset_path = os.path.join(base, "data", "skills_dataset.json")

    # Step 1: Clean the vocabulary
    if os.path.exists(vocab_path):
        clean_vocab(vocab_path)
    else:
        print(f"[WARN] Vocab not found: {vocab_path}")

    # Step 2: Clean the dataset
    if os.path.exists(dataset_path):
        clean_dataset(dataset_path)
    else:
        print(f"[WARN] Dataset not found: {dataset_path}")

    print("\n[OK] All done!")
