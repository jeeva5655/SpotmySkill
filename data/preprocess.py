import pandas as pd
import json
import os

def preprocess_dataset():
    input_file = "../train-00000-of-00001.parquet"
    output_file = "skills_dataset.json"
    
    print(f"Loading {input_file}...")
    df = pd.read_parquet(input_file)
    
    extracted_data = []
    print("Extracting skill prompts...")
    
    for idx, row in df.iterrows():
        msgs = row.get("messages", [])
        if len(msgs) >= 3:
            user_msg = msgs[1].get("content", "")
            assistant_msg = msgs[2].get("content", "")
            
            # Check if this is a skill extraction task
            if "What are the key skills and qualifications in this" in user_msg:
                # The prompt usually contains the instruction and then the resume text.
                # It might have a colon ':' as a separator or a line break.
                # Let's split smartly
                parts = user_msg.split("resume?\n\n", 1)
                if len(parts) == 2:
                    resume_text = parts[1].strip()
                    extracted_data.append({
                        "resume": resume_text,
                        "skills": assistant_msg.strip()
                    })
    
    print(f"Extracted {len(extracted_data)} examples.")
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(extracted_data, f, indent=2, ensure_ascii=False)
        
    print(f"Saved extracted data to {output_file}")

if __name__ == "__main__":
    preprocess_dataset()
