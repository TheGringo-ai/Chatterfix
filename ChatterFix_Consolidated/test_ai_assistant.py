import requests
import json

url = "http://localhost:8000/ai/assist"
data = {
    "message": "Create a work order for broken conveyor belt",
    "context": "Dashboard"
}

try:
    response = requests.post(url, data=data)
    print(f"Status Code: {response.status_code}")
    print("Response JSON:")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")
