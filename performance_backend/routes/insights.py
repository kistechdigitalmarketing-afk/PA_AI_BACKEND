from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from performance_backend.generator import generate_flan_sentence


router = APIRouter()


class WeekHistory(BaseModel):
    week: str
    score: float


class TimeSummary(BaseModel):
    required_hours: float
    worked_hours: float


class TaskBuckets(BaseModel):
    planned: int
    completed: int
    in_progress: int
    in_review: int
    overdue: int


class InsightsRequest(BaseModel):
    # Core identity
    user_name: str

    # Performance + leadership
    performance_score: float  # 0–100
    leadership_score: Optional[float] = None  # 0–100, optional

    # Time + weeks
    time: TimeSummary
    weekly_avg_score: Optional[float] = None
    current_week_score: Optional[float] = None
    weekly_history: List[WeekHistory] = []

    # Three buckets from the existing system (optional but recommended)
    productivity: Optional[float] = None
    quality: Optional[float] = None
    consistency: Optional[float] = None

    # Task buckets
    tasks: TaskBuckets

    # Optional weaker areas to reference in suggestions
    weaker_areas: List[str] = []


def _describe_score_bucket(score: float, name: str) -> str:
    rounded = round(score)
    if score < 50:
        base_text = f"your current performance score of {rounded} needs urgent attention."
        prompt = (
            f"Write a supportive but direct opening sentence for {name} about their performance score of {rounded}. "
            f"The score is below 50 and needs urgent attention. Use 'you' and 'your'. Be encouraging but clear about the need for immediate action. "
            f"Keep it professional and motivating, not harsh."
        )
        fallback = base_text
        ai_text = generate_flan_sentence(prompt, base_text)
        return ai_text
    if score < 75:
        base_text = f"your current performance score of {rounded} shows you are on the right track but there is clear room to improve."
        prompt = (
            f"Write an encouraging opening sentence for {name} about their performance score of {rounded}. "
            f"The score is between 50-75, showing progress but with room to improve. Use 'you' and 'your'. "
            f"Be positive and motivating, acknowledging their progress while encouraging growth."
        )
        fallback = base_text
        ai_text = generate_flan_sentence(prompt, base_text)
        return ai_text
    base_text = f"great job — your current performance score of {rounded} is strong."
    prompt = (
        f"Write a congratulatory opening sentence for {name} about their strong performance score of {rounded}. "
        f"The score is 75 or above, showing excellent performance. Use 'you' and 'your'. "
        f"Be genuine and encouraging, celebrating their achievement."
    )
    fallback = base_text
    ai_text = generate_flan_sentence(prompt, base_text)
    return ai_text


def _describe_time(time: TimeSummary) -> str:
    required = time.required_hours
    worked = time.worked_hours
    base = f"Out of the required {required:.1f} hours, you have worked {worked:.1f} hours in this period"

    diff = worked - required
    if abs(diff) <= 1:
        return base + ", which is broadly on track with expectations."
    if diff < 0:
        return base + ", which is below the expected time and may be limiting your overall score."
    return base + ", which is above the expected time — just ensure this effort is focused on the highest‑value tasks."


def _compute_weekly_comparison(
    weekly_avg_score: Optional[float],
    current_week_score: Optional[float],
    weekly_history: List[WeekHistory],
) -> Optional[str]:
    avg = weekly_avg_score
    current = current_week_score

    # Derive from history if not explicitly provided
    if (avg is None or current is None) and weekly_history:
        scores = [w.score for w in weekly_history]
        if scores:
            derived_avg = sum(scores) / len(scores)
            derived_current = scores[-1]
            if avg is None:
                avg = derived_avg
            if current is None:
                current = derived_current

    if avg is None or current is None:
        return None

    diff = current - avg
    avg_r = round(avg)
    cur_r = round(current)

    if diff > 3:
        return f"This week, your score of {cur_r} is above your usual weekly average of {avg_r}, showing a clear improvement."
    if diff < -3:
        return f"This week, your score of {cur_r} is below your usual weekly average of {avg_r}, so it’s worth paying closer attention to your habits and focus."
    return f"This week, your score of {cur_r} is close to your usual weekly average of {avg_r}, indicating stable performance."


def _describe_buckets(productivity: Optional[float], quality: Optional[float], consistency: Optional[float]) -> Optional[str]:
    if productivity is None and quality is None and consistency is None:
        return None

    parts = []
    if productivity is not None:
        parts.append(f"productivity is at {round(productivity)}%")
    if quality is not None:
        parts.append(f"quality is at {round(quality)}%")
    if consistency is not None:
        parts.append(f"consistency is at {round(consistency)}%")

    joined = ", ".join(parts)
    return f"As per the three system buckets, {joined}."


def _describe_tasks(tasks: TaskBuckets) -> str:
    return (
        f"You planned {tasks.planned} tasks and completed {tasks.completed}, "
        f"with {tasks.in_progress} in progress, {tasks.in_review} in review, "
        f"and {tasks.overdue} overdue."
    )


def _task_status_feedback(tasks: TaskBuckets) -> str:
    pieces = []
    if tasks.in_progress > 0:
        base = "Try to move your in‑progress tasks into review or completion over the next few days."
        prompt = (
            f"Write a helpful suggestion about managing {tasks.in_progress} in-progress tasks. "
            f"Use 'you' and 'your'. Be encouraging and actionable. Focus on moving tasks forward to completion."
        )
        pieces.append(generate_flan_sentence(prompt, base))
    if tasks.in_review > 0:
        base = "For tasks in review, check in with your supervisor or reviewer so they can close them out or clarify any changes needed."
        prompt = (
            f"Write a helpful suggestion about {tasks.in_review} tasks currently in review. "
            f"Use 'you' and 'your'. Encourage proactive communication with reviewers to move tasks forward."
        )
        pieces.append(generate_flan_sentence(prompt, base))
    if tasks.overdue > 0:
        base = "Your overdue tasks need urgent attention — prioritise clearing these first to protect your score."
        prompt = (
            f"Write an urgent but supportive message about {tasks.overdue} overdue tasks. "
            f"Use 'you' and 'your'. Be clear about the priority but remain encouraging and actionable."
        )
        pieces.append(generate_flan_sentence(prompt, base))
    if not pieces:
        base = "You are keeping your task pipeline healthy with no overdue work — aim to maintain this pattern."
        prompt = (
            f"Write a positive acknowledgment about maintaining a healthy task pipeline with no overdue work. "
            f"Use 'you' and 'your'. Be encouraging and reinforce the good pattern."
        )
        pieces.append(generate_flan_sentence(prompt, base))
    return " ".join(pieces)


def _score_improvement_suggestions(score: float, weaker_areas: List[str], name: str) -> str:
    area_text = ""
    if weaker_areas:
        # Mention at most two weaker areas
        focus_areas = weaker_areas[:2]
        joined = ", ".join(focus_areas)
        area_text = f" especially around {joined}"

    if score < 50:
        base = (
            f"Your current score means you need focused, urgent actions now{area_text}. "
            f"Block dedicated time each day for your top 2–3 tasks, update your worklog or task status after each working block, "
            f"and break larger items into smaller steps so they are easier to finish within the week."
        )
        prompt = (
            f"Write actionable improvement suggestions for {name} who has a performance score below 50{area_text}. "
            f"Use 'you' and 'your'. Focus on urgent, practical steps they can take immediately. "
            f"Be supportive but clear about the need for focused action. Include specific, actionable advice."
        )
        return generate_flan_sentence(prompt, base)
    if score < 75:
        base = (
            f"Your score shows you are on the right path, and with a bit more structure you can move into a higher band{area_text}. "
            f"Plan your week around a short daily priority list, close out tasks fully instead of carrying them forward, "
            f"and log your work regularly so your effort is reflected in your score."
        )
        prompt = (
            f"Write encouraging improvement suggestions for {name} who has a performance score between 50-75{area_text}. "
            f"Use 'you' and 'your'. Acknowledge their progress while providing practical steps to reach the next level. "
            f"Be motivating and specific about actions they can take."
        )
        return generate_flan_sentence(prompt, base)
    base = (
        f"Your strong score is worth maintaining — keep up the good work and look for small ways to push even higher{area_text}. "
        f"Continue logging your work consistently, protect focused time for your most important tasks, "
        f"and use weekly reflections to spot any early signs of slippage."
    )
    prompt = (
        f"Write maintenance and growth suggestions for {name} who has a strong performance score of 75+{area_text}. "
        f"Use 'you' and 'your'. Celebrate their success while encouraging continued excellence and small improvements. "
        f"Be positive and forward-looking."
    )
    return generate_flan_sentence(prompt, base)


def _leadership_feedback(leadership_score: Optional[float]) -> Optional[str]:
    if leadership_score is None:
        return None

    ls = round(leadership_score)
    if leadership_score < 50:
        return (
            f"From a leadership perspective, a score of {ls} suggests that closer guidance from supervisors would help — "
            f"clearer priorities, more frequent check‑ins, and practical coaching on planning and communication can support stronger performance."
        )
    if leadership_score < 75:
        return (
            f"A leadership score of {ls} indicates a developing foundation. "
            f"Targeted support from supervisors around delegation, prioritisation, and feedback conversations can help unlock the next level of impact."
        )
    return (
        f"A leadership score of {ls} shows strong potential. Supervisors can amplify this by offering stretch opportunities, "
        f"recognising contributions publicly, and involving you in guiding or mentoring others where appropriate."
    )


@router.post("/generate-insights")
def generate_insights(request: InsightsRequest):
    """
    Generate a single, user-friendly insight string combining:
    - score bucket feedback
    - three system buckets (productivity, quality, consistency)
    - time worked vs required time
    - weekly comparison (average vs current week)
    - task bucket overview + status-based feedback
    - improvement suggestions
    - leadership-oriented supervisor feedback
    """
    name = request.user_name.strip() or "there"

    # 1) Score bucket opening (AI-enhanced)
    opening = f"Hi {name}, " + _describe_score_bucket(request.performance_score, name)

    # 2) Three buckets (if available)
    buckets_text = _describe_buckets(request.productivity, request.quality, request.consistency)

    # 3) Time worked vs required
    time_text = _describe_time(request.time)

    # 4) Weekly comparison
    weekly_text = _compute_weekly_comparison(
        request.weekly_avg_score,
        request.current_week_score,
        request.weekly_history,
    )

    # 5) Task overview + pipeline feedback (AI-enhanced)
    tasks_overview = _describe_tasks(request.tasks)
    tasks_feedback = _task_status_feedback(request.tasks)

    # 6) Suggestions to improve score (AI-enhanced)
    improvement = _score_improvement_suggestions(request.performance_score, request.weaker_areas, name)

    # 7) Leadership / supervisor-oriented feedback
    leadership_text = _leadership_feedback(request.leadership_score)

    # Build paragraphs
    parts = [opening]

    bucket_and_time_parts = []
    if buckets_text:
        bucket_and_time_parts.append(buckets_text)
    bucket_and_time_parts.append(time_text)
    if weekly_text:
        bucket_and_time_parts.append(weekly_text)
    parts.append(" ".join(bucket_and_time_parts))

    parts.append(f"{tasks_overview} {tasks_feedback}")
    parts.append(improvement)
    if leadership_text:
        parts.append(leadership_text)

    # 8) Generate a personalized closing summary with AI
    summary_context = f"Performance score: {round(request.performance_score)}, "
    if buckets_text:
        summary_context += f"{buckets_text.lower()} "
    summary_context += f"Tasks: {request.tasks.completed} completed out of {request.tasks.planned} planned."
    
    closing_prompt = (
        f"Write a brief, encouraging closing sentence for {name}'s performance insights. "
        f"Context: {summary_context} "
        f"Use 'you' and 'your'. Be warm, professional, and forward-looking. Keep it to one sentence."
    )
    closing_fallback = "Keep up the great work and continue building on your progress."
    closing = generate_flan_sentence(closing_prompt, closing_fallback)
    parts.append(closing)

    insight_text = "\n\n".join(parts)

    return {
        "insights": insight_text
    }

