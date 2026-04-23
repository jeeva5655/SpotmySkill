import pandas as pd, json

df = pd.read_parquet('train-00000-of-00001.parquet')

for idx, row in df.iterrows():
    msgs = row['messages']
    print(f'Row {idx}: type={type(msgs).__name__}, len={len(msgs)}')
    print(f'  msgs[0] type: {type(msgs[0]).__name__}')
    if isinstance(msgs[0], dict):
        print(f'  msgs[0]: {json.dumps(msgs[0], default=str)[:200]}')
        print(f'  msgs[1]: {json.dumps(msgs[1], default=str)[:200]}')
        print(f'  msgs[2]: {json.dumps(msgs[2], default=str)[:200]}')
    else:
        print(f'  msgs[0] repr: {repr(msgs[0])[:200]}')
        print(f'  attrs: {[a for a in dir(msgs[0]) if not a.startswith("_")]}')
    print()
    if idx >= 3:
        break
