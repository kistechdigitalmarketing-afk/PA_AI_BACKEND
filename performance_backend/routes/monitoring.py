from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from collections import defaultdict, deque
from performance_backend.generator import generate_flan_sentence

router = APIRouter()

# In-memory storage for real-time monitoring
# Structure: {user_id: {pattern_history: deque, last_update: datetime, task_counts: list}}
user_monitoring_data: Dict[str, Dict] = defaultdict(lambda: {
    "pattern_history": deque(maxlen=10),  # Keep last 10 patterns
    "last_update": None,
    "task_counts": deque(maxlen=10),  # Keep last 10 task counts
    "consistent_pattern_count": 0,  # Number of times same pattern repeated
    "current_pattern": None
})

# Pydantic Models
class TaskUpdate(BaseModel):
    user_id: str
    task_count: int  # Number of tasks completed/worked on
    timestamp: Optional[str] = None  # Optional timestamp, defaults to now

class MonitoringRequest(BaseModel):
    user_id: str


def detect_task_pattern(current_count: int, previous_counts: List[int]) -> str:
    """
    Detect pattern based on task count changes.
    Returns: 'increasing', 'decreasing', 'stable', 'fluctuating'
    """
    if len(previous_counts) < 2:
        return "stable"
    
    # Get recent trend
    recent = list(previous_counts[-3:]) + [current_count]
    
    # Check if stable (within 1-2 tasks)
    if all(abs(recent[i] - recent[i+1]) <= 2 for i in range(len(recent)-1)):
        return "stable"
    
    # Check if consistently increasing
    if all(recent[i] <= recent[i+1] for i in range(len(recent)-1)):
        return "increasing"
    
    # Check if consistently decreasing
    if all(recent[i] >= recent[i+1] for i in range(len(recent)-1)):
        return "decreasing"
    
    return "fluctuating"


def generate_pattern_feedback(
    user_id: str,
    pattern_count: int,
    current_pattern: str,
    previous_pattern: Optional[str],
    current_task_count: int,
    previous_task_count: Optional[int]
) -> str:
    """
    Generate feedback based on pattern changes.
    Example: "You were doing 2 tasks consistently but now you do this..."
    """
    
    # If user was consistent and now changed
    if pattern_count >= 2 and previous_pattern and current_pattern != previous_pattern:
        if previous_pattern == "stable" and previous_task_count:
            if current_pattern == "increasing":
                feedback = f"You were doing {previous_task_count} tasks consistently, but now you're increasing your workload. This shows growth, but make sure to maintain quality as you take on more."
            elif current_pattern == "decreasing":
                feedback = f"You were doing {previous_task_count} tasks consistently, but now you're doing fewer tasks. Consider if this is due to task complexity or if you need to adjust your approach."
            else:
                feedback = f"You were doing {previous_task_count} tasks consistently, but now your pattern has changed. This shift might indicate a change in priorities or workload."
        else:
            feedback = f"Your work pattern has changed after {pattern_count} consistent periods. This shift may require adjusting your approach to maintain performance."
    elif pattern_count >= 2 and current_pattern == "stable":
        # User is maintaining consistency
        feedback = f"You've maintained a consistent pattern for {pattern_count} periods, doing around {current_task_count} tasks. This consistency is a strength - keep it up!"
    elif current_pattern == "fluctuating":
        feedback = f"Your task completion pattern is fluctuating. Consider establishing a more consistent routine to improve predictability and performance."
    elif current_pattern == "increasing":
        feedback = f"You're increasing your task completion rate. Great progress! Just ensure you're maintaining quality as you scale up."
    elif current_pattern == "decreasing":
        feedback = f"Your task completion has decreased. This might be due to task complexity or other factors. Consider reviewing your priorities and time management."
    else:
        feedback = f"Your current task completion is {current_task_count}. Focus on maintaining consistency to build strong performance habits."
    
    # Use AI to enhance the feedback
    prompt = (
        f"Write a professional performance feedback sentence for an employee. "
        f"Situation: {feedback} "
        f"Use 'you'. Focus on what they should do next, not what happened. "
        f"Be specific, professional, and encouraging."
    )
    
    fallback = feedback
    enhanced_feedback = generate_flan_sentence(prompt, fallback)
    
    return enhanced_feedback


@router.post("/monitor-task-update")
def monitor_task_update(update: TaskUpdate):
    """
    Real-time monitoring endpoint that tracks user task patterns.
    Updates the monitoring data and returns pattern count + feedback.
    """
    try:
        user_id = update.user_id
        current_count = update.task_count
        
        # Get or initialize user data
        user_data = user_monitoring_data[user_id]
        
        # Get previous state
        previous_pattern = user_data.get("current_pattern")
        previous_task_count = user_data["task_counts"][-1] if user_data["task_counts"] else None
        
        # Add current task count
        user_data["task_counts"].append(current_count)
        user_data["last_update"] = datetime.now()
        
        # Detect current pattern
        current_pattern = detect_task_pattern(current_count, list(user_data["task_counts"]))
        
        # Check if pattern is consistent
        if current_pattern == previous_pattern:
            user_data["consistent_pattern_count"] += 1
        else:
            # Pattern changed, save previous pattern to history before resetting
            if previous_pattern is not None:
                old_count = user_data["consistent_pattern_count"]
                user_data["pattern_history"].append({
                    "pattern": previous_pattern,
                    "count": old_count,
                    "task_count": previous_task_count,
                    "timestamp": user_data["last_update"]
                })
            # Reset count for new pattern
            user_data["consistent_pattern_count"] = 1
        
        user_data["current_pattern"] = current_pattern
        
        # Generate feedback
        feedback = generate_pattern_feedback(
            user_id=user_id,
            pattern_count=user_data["consistent_pattern_count"],
            current_pattern=current_pattern,
            previous_pattern=previous_pattern,
            current_task_count=current_count,
            previous_task_count=previous_task_count
        )
        
        return {
            "pattern_count": user_data["consistent_pattern_count"],
            "current_pattern": current_pattern,
            "current_task_count": current_count,
            "feedback_suggestion": feedback
        }
    
    except Exception as e:
        import traceback
        print(f"[ERROR] Exception in monitor_task_update: {str(e)}")
        print(f"[ERROR] Traceback:\n{traceback.format_exc()}")
        raise


@router.get("/monitor-status/{user_id}")
def get_monitor_status(user_id: str):
    """
    Get current monitoring status for a user.
    Returns pattern count and latest feedback.
    """
    try:
        if user_id not in user_monitoring_data:
            return {
                "pattern_count": 0,
                "current_pattern": None,
                "current_task_count": None,
                "feedback_suggestion": "No monitoring data available yet. Start tracking your tasks to receive feedback."
            }
        
        user_data = user_monitoring_data[user_id]
        current_count = user_data["task_counts"][-1] if user_data["task_counts"] else None
        
        # Get previous pattern from history if available
        previous_pattern_from_history = None
        if user_data["pattern_history"]:
            previous_pattern_from_history = user_data["pattern_history"][-1]["pattern"]
        
        feedback = generate_pattern_feedback(
            user_id=user_id,
            pattern_count=user_data["consistent_pattern_count"],
            current_pattern=user_data["current_pattern"],
            previous_pattern=previous_pattern_from_history,
            current_task_count=current_count,
            previous_task_count=user_data["task_counts"][-2] if len(user_data["task_counts"]) >= 2 else None
        )
        
        return {
            "pattern_count": user_data["consistent_pattern_count"],
            "current_pattern": user_data["current_pattern"],
            "current_task_count": current_count,
            "feedback_suggestion": feedback,
            "pattern_history": [
                {
                    "pattern": p["pattern"],
                    "count": p["count"],
                    "task_count": p["task_count"]
                }
                for p in list(user_data["pattern_history"])[-5:]  # Last 5 patterns
            ]
        }
    
    except Exception as e:
        import traceback
        print(f"[ERROR] Exception in get_monitor_status: {str(e)}")
        print(f"[ERROR] Traceback:\n{traceback.format_exc()}")
        raise
