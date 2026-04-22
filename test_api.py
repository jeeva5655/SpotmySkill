import requests
import json

url = "http://127.0.0.1:8000/api/extract_skills"
payload = {
    "text": "I am a skilled software engineer with 5 years of experience in Python, Django, REST APIs, and AWS. I have excellent communication skills and know how to work with Microsoft Excel, SQL, and Git."
}

try:
    response = requests.post(url, json=payload)
    response.raise_for_status()
    result = response.json()
    print("Success! Extracted skills:")
    print(json.dumps(result, indent=2))
except Exception as e:
    print(f"Failed to extract skills: {e}")
