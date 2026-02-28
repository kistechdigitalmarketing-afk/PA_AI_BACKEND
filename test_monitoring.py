"""
Test script for the Real-Time Monitoring API
Run this after starting the server with: python main.py
"""

import requests
import json
import time
import sys
import io

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# API endpoint
BASE_URL = "http://localhost:8000"

def test_monitoring():
    """Test the real-time monitoring endpoints"""
    
    user_id = "test_user_monitoring"
    
    print("=" * 60)
    print("Testing Real-Time Monitoring API")
    print("=" * 60)
    print()
    
    # Test 1: First update - user doing 2 tasks
    print("Test 1: User completes 2 tasks (first update)")
    response = requests.post(
        f"{BASE_URL}/monitor-task-update",
        json={
            "user_id": user_id,
            "task_count": 2
        }
    )
    result1 = response.json()
    print(f"Pattern Count: {result1['pattern_count']}")
    print(f"Current Pattern: {result1['current_pattern']}")
    print(f"Task Count: {result1['current_task_count']}")
    print(f"Feedback: {result1['feedback_suggestion']}")
    print()
    
    time.sleep(1)
    
    # Test 2: Second update - still doing 2 tasks (consistent)
    print("Test 2: User completes 2 tasks again (consistent pattern)")
    response = requests.post(
        f"{BASE_URL}/monitor-task-update",
        json={
            "user_id": user_id,
            "task_count": 2
        }
    )
    result2 = response.json()
    print(f"Pattern Count: {result2['pattern_count']}")
    print(f"Current Pattern: {result2['current_pattern']}")
    print(f"Task Count: {result2['current_task_count']}")
    print(f"Feedback: {result2['feedback_suggestion']}")
    print()
    
    time.sleep(1)
    
    # Test 3: Third update - still doing 2 tasks (still consistent)
    print("Test 3: User completes 2 tasks again (maintaining consistency)")
    response = requests.post(
        f"{BASE_URL}/monitor-task-update",
        json={
            "user_id": user_id,
            "task_count": 2
        }
    )
    result3 = response.json()
    print(f"Pattern Count: {result3['pattern_count']}")
    print(f"Current Pattern: {result3['current_pattern']}")
    print(f"Task Count: {result3['current_task_count']}")
    print(f"Feedback: {result3['feedback_suggestion']}")
    print()
    
    time.sleep(1)
    
    # Test 4: Pattern change - now doing 4 tasks (increasing)
    print("Test 4: User now completes 4 tasks (pattern change!)")
    response = requests.post(
        f"{BASE_URL}/monitor-task-update",
        json={
            "user_id": user_id,
            "task_count": 4
        }
    )
    result4 = response.json()
    print(f"Pattern Count: {result4['pattern_count']}")
    print(f"Current Pattern: {result4['current_pattern']}")
    print(f"Task Count: {result4['current_task_count']}")
    print(f"Feedback: {result4['feedback_suggestion']}")
    print()
    
    # Test 5: Get status
    print("Test 5: Get current monitoring status")
    response = requests.get(f"{BASE_URL}/monitor-status/{user_id}")
    status = response.json()
    print(f"Pattern Count: {status['pattern_count']}")
    print(f"Current Pattern: {status['current_pattern']}")
    print(f"Task Count: {status['current_task_count']}")
    print(f"Feedback: {status['feedback_suggestion']}")
    if status.get('pattern_history'):
        print(f"Pattern History: {json.dumps(status['pattern_history'], indent=2)}")
    print()
    
    print("=" * 60)
    print("All tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_monitoring()
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server.")
        print("Make sure the server is running on http://localhost:8000")
        print("Start it with: python performance_backend/main.py")
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
