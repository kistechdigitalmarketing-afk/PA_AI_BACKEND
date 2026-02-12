import pandas as pd
import joblib
import os
from datetime import datetime

# 1. LOAD THE BRAINS
# Using the model filenames you saved in your train_model.py
STAFF_MODEL_PATH = "app/staff_model.pkl"
SUP_MODEL_PATH = "app/supervisor_model.pkl"

staff_model = joblib.load(STAFF_MODEL_PATH) if os.path.exists(STAFF_MODEL_PATH) else None
sup_model = joblib.load(SUP_MODEL_PATH) if os.path.exists(SUP_MODEL_PATH) else None

def calculate_metrics(tasks: list[dict], user_role: str) -> tuple[int, str, dict]:
    """
    Calculates efficiency score, risk level, and statistical report based on user role.
    """
    if not tasks:
        return 0, "High", {}

    # Convert incoming JSON data to a DataFrame
    df = pd.DataFrame(tasks)
    
    # Clean column names to lowercase for internal processing
    df.columns = df.columns.str.lower().str.strip()
    
    # Convert dates to datetime objects for mathematical subtraction.
    # Incoming dates like '2026-01-12T00:00:00.000Z' are UTC tz-aware; we normalize
    # everything to timezone-naive so comparisons work reliably.
    df['due_date'] = pd.to_datetime(df['due_date'], errors='coerce', utc=True).dt.tz_convert(None)
    df['submitted_at'] = pd.to_datetime(df['submitted_at'], errors='coerce', utc=True).dt.tz_convert(None)
    df['approved_at'] = pd.to_datetime(df['approved_at'], errors='coerce', utc=True).dt.tz_convert(None)
    
    # Use a timezone-naive "now" to match the normalized columns above
    today = pd.Timestamp.now().replace(tzinfo=None)
    role = user_role.lower().strip()

    # --- PART A: STAFF PERFORMANCE LOGIC (Every user gets this) ---
    total_tasks = len(df)
    
    # Handle null status values safely
    df['status'] = df['status'].fillna('').astype(str).str.lower()
    comp_rate = df[df['status'] == 'completed'].shape[0] / total_tasks
    
    # Check if overdue: Due date has passed AND status is "planned" or "in progress" (not "in review")
    is_overdue = (df['due_date'] < today) & (df['status'].isin(['planned', 'in progress'])) & (df['status'] != 'in review')
    overdue_rate = df[is_overdue].shape[0] / total_tasks
    
    # Worklog consistency - handle missing or null values
    if 'working_count' in df.columns:
        df['working_count'] = pd.to_numeric(df['working_count'], errors='coerce').fillna(0)
        avg_logs = df['working_count'].mean()
    else:
        avg_logs = 0

    # Prepare features for the Staff Brain
    features = [[comp_rate, overdue_rate, avg_logs]]
    
    staff_anomaly_score = 0
    if staff_model:
        # decision_function returns raw distance from the "normal" cluster
        staff_anomaly_score = staff_model.decision_function(features)[0]

    # --- PART B: SUPERVISOR PERFORMANCE LOGIC (Only for admins/supervisors) ---
    sup_anomaly_score = 0
    is_leader = role in ['supervisor', 'country_admin']
    sup_features = None 

    # Initialize supervisor-specific variables to 0 for the report
    avg_speed = 0
    rej_rate = 0

    if is_leader:
        # Calculate Approval Speed in Hours
        df['speed'] = (df['approved_at'] - df['submitted_at']).dt.total_seconds() / 3600
        valid_speeds = df[df['speed'] > 0]['speed']
        avg_speed = valid_speeds.mean() if not valid_speeds.empty else 0
        
        # Rejection Rate - handle null approval_status safely
        df['approval_status'] = df['approval_status'].fillna('').astype(str).str.lower()
        rej_rate = df[df['approval_status'] == 'rejected'].shape[0] / total_tasks
        
        sup_features = [[avg_speed, rej_rate]]
        if sup_model:
            sup_anomaly_score = sup_model.decision_function(sup_features)[0]

    # --- PART C: DYNAMIC SCORE & RISK CALCULATION ---
    # 1. Model-based anomaly score (IsolationForest-style)
    final_anomaly_val = (staff_anomaly_score + sup_anomaly_score) / 2 if is_leader else staff_anomaly_score
    model_score = int(((final_anomaly_val + 0.2) / 0.4) * 100)
    model_score = max(0, min(100, model_score))

    # 2. Behavior-based score from raw metrics
    #    For staff: completion rate, overdue rate, worklog consistency
    #    For supervisors: also includes approval speed and rejection rate
    if is_leader:
        # Supervisor behavior score includes their approval performance
        # Fast approvals (< 24 hours) and low rejection rates are good
        # Normalize approval speed: < 24h = 1.0, > 7 days = 0.0
        speed_score = max(0, min(1.0, 1.0 - (avg_speed / (7 * 24)))) if avg_speed > 0 else 0.5
        # Low rejection rate is good (0% rejection = 1.0, 100% rejection = 0.0)
        rejection_score = 1.0 - rej_rate
        
        behavior_score = (
            (comp_rate * 0.35) +                # 35% weight - task completion
            ((1 - overdue_rate) * 0.20) +       # 20% weight - overdue avoidance
            (min(avg_logs / 5, 1.0) * 0.10) +   # 10% weight - worklog consistency
            (speed_score * 0.20) +              # 20% weight - approval speed
            (rejection_score * 0.15)            # 15% weight - low rejection rate
        ) * 100
    else:
        # Staff behavior score (completion, overdue, logs only)
        behavior_score = (
            (comp_rate * 0.6) +                 # 60% weight
            ((1 - overdue_rate) * 0.3) +        # 30% weight
            (min(avg_logs / 5, 1.0) * 0.1)      # 10% weight, capped, logs per task
        ) * 100
    
    behavior_score = max(0, min(100, int(behavior_score)))

    # 3. Final efficiency score: Model learns patterns, but behavior must match reality.
    #    - If behavior is terrible (0% completion, 100% overdue), behavior_score dominates
    #    - If behavior is good, model can fine-tune and spot subtle patterns
    #    - This ensures the model "identifies patterns properly" by being forced to
    #      respect clear behavioral signals (completion, overdue rates)
    
    # When behavior is extremely bad, heavily penalize the model score
    if behavior_score < 20:  # Very poor performance
        # Model score gets capped at behavior_score level when behavior is terrible
        adjusted_model_score = min(model_score, behavior_score + 10)
        dynamic_score = int(adjusted_model_score * 0.3 + behavior_score * 0.7)
    elif behavior_score < 50:  # Poor performance
        # Still weight behavior heavily
        dynamic_score = int(model_score * 0.4 + behavior_score * 0.6)
    else:  # Decent to good performance
        # Model can fine-tune and spot patterns
        dynamic_score = int(model_score * 0.5 + behavior_score * 0.5)
    
    dynamic_score = max(0, min(100, dynamic_score))

    # 2. Determine Risk Level using the Model's internal threshold (.predict())
    is_staff_normal = staff_model.predict(features)[0] == 1 if staff_model else True
    
    is_leader_normal = True
    if is_leader and sup_model and sup_features:
        is_leader_normal = sup_model.predict(sup_features)[0] == 1

    is_overall_normal = is_staff_normal and is_leader_normal

    # 3. Final Risk Assignment Logic
    if is_overall_normal and dynamic_score > 70:
        risk = "Low"
    elif not is_overall_normal or dynamic_score < 40:
        risk = "High"
    else:
        risk = "Medium"

    # --- PART D: PREPARE STATISTICAL REPORT ---
    report_stats = {
        "completion_rate_pct": round(comp_rate * 100, 1),
        "overdue_rate_pct": round(overdue_rate * 100, 1),
        "avg_working_logs": round(avg_logs, 2)
    }

    if is_leader:
        report_stats["avg_approval_speed_hrs"] = round(avg_speed, 2)
        report_stats["rejection_rate_pct"] = round(rej_rate * 100, 1)

    return dynamic_score, risk, report_stats