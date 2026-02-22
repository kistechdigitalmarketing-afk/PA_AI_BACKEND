"""
Quick test to verify the API responds and doesn't hang
"""

import requests
import json
import time

API_URL = "http://localhost:8000/analyze"

# Minimal test data
test_data = {
    "user_id": "test_user",
    "user_role": "staff",
    "tasks": [
        {
            "task_id": "1",
            "user_id": "test_user",
            "user_role": "staff",
            "status": "completed",
            "priority": 1,
            "approval_status": "approved",
            "working_count": 3,
            "due_date": "2024-01-15T00:00:00.000Z"
        }
    ]
}

print("Testing API endpoint...")
print(f"URL: {API_URL}")
print("Sending request...")

try:
    start_time = time.time()
    response = requests.post(API_URL, json=test_data, timeout=60)
    elapsed = time.time() - start_time
    
    print(f"\nResponse received in {elapsed:.2f} seconds")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("\n[SUCCESS] API is working correctly!")
        print(f"Efficiency Score: {result.get('efficiency_score')}")
        print(f"Risk Level: {result.get('risk_level')}")
        print(f"\nFull Response:")
        print(json.dumps(result, indent=2))
        
        if elapsed < 60:
            print(f"\n[PASS] Response time ({elapsed:.2f}s) is acceptable - API won't hang!")
        else:
            print(f"\n[WARNING] Response took {elapsed:.2f}s - might be slow for frontend")
    else:
        print(f"\n[ERROR] Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("\n[ERROR] Cannot connect to server!")
    print("Make sure the server is running:")
    print("  ./venv/Scripts/python.exe -m uvicorn app.main:app --reload")
except requests.exceptions.Timeout:
    print("\n[ERROR] Request timed out after 60 seconds!")
    print("The API might be hanging - check server logs")
except Exception as e:
    print(f"\n[ERROR] {str(e)}")
