"""
Scan the parquet for ALL 'key skills' rows and inspect content
to understand what assistant responses look like.
"""
import pandas as pd
import re

df = pd.read_parquet('train-00000-of-00001.parquet')

SKILL_RE = re.compile(r"What are the key skills and qualifications", re.IGNORECASE)
GENERIC_RE = re.compile(r"The key skills for this .+ professional include relevant experience", re.IGNORECASE)

found = 0
generic_count = 0
real_count = 0

real_samples = []
generic_samples = []

for idx, row in df.iterrows():
    msgs = row['messages']
    if len(msgs) < 3:
        continue

    user_msg = msgs[1].get('content', '') if isinstance(msgs[1], dict) else ''
    asst_msg = msgs[2].get('content', '') if isinstance(msgs[2], dict) else ''

    if not SKILL_RE.search(user_msg):
        continue

    found += 1

    if GENERIC_RE.search(asst_msg):
        generic_count += 1
        if len(generic_samples) < 2:
            generic_samples.append(asst_msg[:300])
    else:
        real_count += 1
        if len(real_samples) < 5:
            real_samples.append({
                'user': user_msg[:200],
                'asst': asst_msg[:400],
            })

print(f"Total rows: {len(df)}")
print(f"Skill prompt rows found: {found}")
print(f"  Generic placeholder : {generic_count}")
print(f"  REAL answers        : {real_count}")
print()
print("--- REAL answer samples ---")
for i, s in enumerate(real_samples):
    print(f"\n[{i}] USER: {s['user']}")
    print(f"    ASST: {s['asst']}")

print()
print("--- Generic placeholder samples ---")
for s in generic_samples:
    print(f"  {s}")
