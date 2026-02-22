"""
Quick test script for the analyze-performance endpoint
"""
import requests
import json

# Test data
test_data = {
    "user_id": "test123",
    "current_score": 75.0,
    "previous_score": 70.0,
    "performance_band": "Good",
    "weekly_history": [],
    "productivity": 80.0,
    "consistency": 65.0,
    "quality": 70.0,
    "overdue_rate": 15.0
}

print("Testing /analyze-performance endpoint...")
print(f"Request data: {json.dumps(test_data, indent=2)}")
print("\nSending request...")

try:
    response = requests.post(
        "http://localhost:8000/analyze-performance",
        json=test_data,
        timeout=60  # 60 second timeout
    )
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"\nResponse Body:")
    print(json.dumps(response.json(), indent=2))
    
except requests.exceptions.Timeout:
    print("\n[ERROR] Request timed out after 60 seconds")
    print("The FLAN model generation might be taking too long.")
except requests.exceptions.ConnectionError:
    print("\n[ERROR] Could not connect to server")
    print("Make sure the server is running on http://localhost:8000")
except Exception as e:
    print(f"\n[ERROR] {str(e)}")
    import traceback
    traceback.print_exc()
