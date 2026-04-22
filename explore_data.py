import pandas as pd
import json

def explore():
    df = pd.read_parquet("train-00000-of-00001.parquet")
    print("\n--- Shape ---")
    print(df.shape)
    print("\n--- Columns ---")
    print(df.dtypes)
    print("\n--- First Row Sample ---")
    
    first_row = df.head(1).to_dict(orient="records")[0]
    # format nicely if lists/dicts
    print(json.dumps(first_row, default=str, indent=2)[:1000] + "\n...")

if __name__ == "__main__":
    explore()
