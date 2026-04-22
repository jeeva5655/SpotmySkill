import pandas as pd
import json

df = pd.read_parquet("../train-00000-of-00001.parquet")

count = 0
for idx, row in df.iterrows():
    msgs = row.get("messages", [])
    if len(msgs) >= 3:
        user_msg = msgs[1].get("content", "")
        assistant_msg = msgs[2].get("content", "")
        
        if "skill" in user_msg.lower() and "skill" in assistant_msg.lower() and len(assistant_msg) > 50:
            print("USER:", user_msg[:150])
            print("ASSISTANT:", assistant_msg)
            print("---")
            count += 1
        if count >= 3:
            break
