import pandas as pd

def explore():
    df = pd.read_parquet("train-00000-of-00001.parquet")
    unique_prompts = set()
    
    for idx, row in df.iterrows():
        for msg in row['messages']:
            if msg.get('role') == 'user':
                # Just get the instruction part before the resume
                text = msg.get('content', '')
                if ':' in text:
                    instruction = text.split(':')[0].strip()
                    unique_prompts.add(instruction)
        
        if idx > 2000: # just sample first 2000 to be fast
            break
            
    with open("explore_prompts.txt", "w", encoding="utf-8") as f:
        f.write("Unique Prompts Found:\n")
        for p in unique_prompts:
            f.write(f"- {p}\n")

if __name__ == "__main__":
    explore()
