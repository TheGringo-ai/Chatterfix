import requests
import json
import os

# Ensure we can see the response even if it fails
url = "http://localhost:8000/ai/assist"
data = {
    "message": "Search for 'industrial conveyor belt maintenance checklist'",
    "context": "Dashboard",
}

try:
    response = requests.post(url, data=data)
    print(f"Status Code: {response.status_code}")
    print("Response JSON:")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")
