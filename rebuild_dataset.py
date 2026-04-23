"""
Fast dataset rebuilder for SpotmySkill.

Uses tokenization-based matching (not regex per skill) for speed.
Instead of running 6600 regex patterns per resume, we:
1. Tokenize the resume into n-grams (1 to 3 words)
2. Do a set intersection with the vocab set

This is ~100x faster than the regex approach.
"""
import pandas as pd
import json
import re
import os

PARQUET_PATH = "train-00000-of-00001.parquet"
VOCAB_PATH   = "model/skill_vocab.json"
OUTPUT_PATH  = "data/skills_dataset.json"

# ── Load vocab ────────────────────────────────────────────────
with open(VOCAB_PATH, "r", encoding="utf-8") as f:
    raw_vocab = json.load(f)

# Case-insensitive lookup: lowercase -> original cased form
vocab_lower_to_orig = {}
for v in raw_vocab:
    vs = v.strip()
    if vs:
        vl = vs.lower()
        # Keep the first occurrence (alphabetically sorted, first = shortest or first alpha)
        if vl not in vocab_lower_to_orig:
            vocab_lower_to_orig[vl] = vs

# Max n-gram size in vocab
max_ngram = max(len(v.split()) for v in vocab_lower_to_orig.keys())
print(f"Vocab: {len(vocab_lower_to_orig)} unique skills, max n-gram={max_ngram}")

# Cleanup tokenizer
_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9\.\+\#\-\/]*")

def extract_skills_fast(text: str) -> list:
    """Tokenize text into n-grams, intersect with vocab set."""
    text_lower = text.lower()
    tokens = _TOKEN_RE.findall(text_lower)
    matched = set()

    for n in range(1, min(max_ngram + 1, 4)):  # cap at 3-gram for speed
        for i in range(len(tokens) - n + 1):
            gram = " ".join(tokens[i:i+n])
            if gram in vocab_lower_to_orig:
                matched.add(vocab_lower_to_orig[gram])

    return sorted(matched, key=str.lower)


def extract_resume_text(user_msg: str) -> str:
    idx = user_msg.find("\n\n")
    if idx != -1:
        return user_msg[idx:].strip()
    return user_msg.strip()


def build_skills_text(skills: list) -> str:
    return "\n".join(f"{i+1}. {s}" for i, s in enumerate(skills))


def rebuild():
    print(f"Loading {PARQUET_PATH} ...")
    df = pd.read_parquet(PARQUET_PATH)
    total = len(df)
    print(f"Total rows: {total}")

    extracted = []
    stats = dict(skill_rows=0, summarize_rows=0, rewrite_rows=0,
                 skipped_short=0, skipped_no_skills=0, skipped_dup=0)

    seen_fps = set()

    for idx, row in df.iterrows():
        msgs = row.get("messages", [])
        if len(msgs) < 3:
            continue

        user_msg = msgs[1].get("content", "") if isinstance(msgs[1], dict) else ""
        user_lower = user_msg.lower()

        is_skill_row     = "what are the key skills" in user_lower
        is_summarize_row = "please summarize the following resume" in user_lower
        is_rewrite_row   = "rewrite and improve this resume" in user_lower

        if not (is_skill_row or is_summarize_row or is_rewrite_row):
            continue

        resume_text = extract_resume_text(user_msg)

        if len(resume_text) < 150:
            stats["skipped_short"] += 1
            continue

        # Dedup fingerprint
        fp = resume_text[:250].lower().strip()
        if fp in seen_fps:
            stats["skipped_dup"] += 1
            continue
        seen_fps.add(fp)

        skills = extract_skills_fast(resume_text)

        if not skills:
            stats["skipped_no_skills"] += 1
            continue

        extracted.append({
            "resume": resume_text,
            "skills": build_skills_text(skills),
        })

        if is_skill_row:     stats["skill_rows"] += 1
        elif is_summarize_row: stats["summarize_rows"] += 1
        elif is_rewrite_row:  stats["rewrite_rows"] += 1

        if idx % 2000 == 0:
            print(f"  Progress: {idx}/{total} rows scanned, {len(extracted)} good records...")

    print(f"\n--- Extraction Summary ---")
    for k, v in stats.items():
        print(f"  {k:<28}: {v}")
    print(f"  FINAL RECORDS            : {len(extracted)}")

    # Sample display
    print("\n--- Sample Records ---")
    for rec in extracted[:3]:
        print(f"\n  [Resume] {rec['resume'][:200]}...")
        skills_preview = rec['skills'].split('\n')[:8]
        print(f"  [Skills]\n" + "\n".join("    " + s for s in skills_preview))

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(extracted, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(extracted)} records to {OUTPUT_PATH}")


if __name__ == "__main__":
    rebuild()
