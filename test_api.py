"""
Simple test script for the AI Task Performance Analyzer API
Run this after starting the server with: uvicorn app.main:app --reload
"""

import requests
import json
import sys
import io

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# API endpoint
API_URL = "http://localhost:8000/analyze"

# Test data for a staff member
test_data_staff = {
    "user_id": "test_user_123",
    "user_role": "staff",
    "tasks": [
        {
            "task_id": "task1",
            "user_id": "test_user_123",
            "user_role": "staff",
            "status": "completed",
            "priority": 1,
            "approval_status": "approved",
            "working_count": 5,
            "due_date": "2024-01-15T00:00:00.000Z",
            "submitted_at": "2024-01-14T10:00:00.000Z",
            "approved_at": "2024-01-14T12:00:00.000Z"
        },
        {
            "task_id": "task2",
            "user_id": "test_user_123",
            "user_role": "staff",
            "status": "completed",
            "priority": 2,
            "approval_status": "approved",
            "working_count": 3,
            "due_date": "2024-01-20T00:00:00.000Z",
            "submitted_at": "2024-01-19T14:00:00.000Z",
            "approved_at": "2024-01-19T16:00:00.000Z"
        },
        {
            "task_id": "task3",
            "user_id": "test_user_123",
            "user_role": "staff",
            "status": "in progress",
            "priority": 1,
            "approval_status": "pending",
            "working_count": 2,
            "due_date": "2024-01-25T00:00:00.000Z"
        }
    ]
}

# Test data for a supervisor
test_data_supervisor = {
    "user_id": "supervisor_456",
    "user_role": "supervisor",
    "tasks": [
        {
            "task_id": "task1",
            "user_id": "supervisor_456",
            "user_role": "supervisor",
            "status": "completed",
            "priority": 1,
            "approval_status": "approved",
            "working_count": 4,
            "due_date": "2024-01-15T00:00:00.000Z",
            "submitted_at": "2024-01-14T10:00:00.000Z",
            "approved_at": "2024-01-14T11:00:00.000Z"
        }
    ]
}


def test_api(data, description):
    """Test the API with given data"""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"{'='*60}")
    
    try:
        response = requests.post(API_URL, json=data, timeout=60)
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n[SUCCESS] Response:")
            print(json.dumps(result, indent=2))
            print(f"\nResponse time: {response.elapsed.total_seconds():.2f} seconds")
        else:
            print(f"\n[ERROR] Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Connection Error: Make sure the server is running!")
        print("   Start it with: python -m uvicorn app.main:app --reload")
    except requests.exceptions.Timeout:
        print("\n[TIMEOUT] The request took too long (model inference can take 5-10 seconds)")
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")


if __name__ == "__main__":
    print("Testing AI Task Performance Analyzer API")
    print("=" * 60)
    
    # Test staff member
    test_api(test_data_staff, "Staff Member Analysis")
    
    # Test supervisor
    test_api(test_data_supervisor, "Supervisor Analysis")
    
    print("\n" + "=" * 60)
    print("[COMPLETE] Testing finished!")
    print("=" * 60)
