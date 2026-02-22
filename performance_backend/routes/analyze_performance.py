from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from generator import generate_flan_sentence

router = APIRouter()

# Pydantic Models
class WeekHistory(BaseModel):
    week: str
    score: float

class PerformanceRequest(BaseModel):
    user_id: str
    current_score: float
    previous_score: Optional[float] = None
    performance_band: str  # "Excellent"|"Very Good"|"Good"|"Average"|"Needs Attention"
    weekly_history: List[WeekHistory] = []
    productivity: float
    consistency: float
    quality: float
    overdue_rate: float


def detect_trend(data: PerformanceRequest) -> str:
    """Detect trend based on current_score and previous_score."""
    if data.previous_score is None:
        return "Stable"
    
    delta = data.current_score - data.previous_score
    if delta >= 5:
        return "Improving"
    elif delta <= -5:
        return "Declining"
    else:
        return "Stable"


def detect_patterns(data: PerformanceRequest) -> List[str]:
    """Detect performance patterns based on metrics."""
    patterns = []
    
    # Check conditions IN ORDER
    if data.productivity > 65 and data.quality < 50:
        patterns.append("rushing")
    
    if data.quality < 45:
        patterns.append("quality_decline")
    
    if data.overdue_rate > 30:
        patterns.append("planning_issue")
    
    if data.productivity < 50 and data.quality < 50 and data.consistency < 50:
        patterns.append("performance_instability")
    
    if data.consistency < 40 and data.productivity > 60:
        patterns.append("inconsistent_sprinter")
    
    if data.productivity > 70 and data.quality > 70 and data.consistency > 70:
        patterns.append("high_performer")
    
    # If no patterns detected, return balanced
    if not patterns:
        patterns.append("balanced")
    
    return patterns


def assign_risk_state(trend: str, patterns: List[str], data: PerformanceRequest) -> str:
    """Assign risk state based on trend, patterns, and data."""
    if trend == "Improving" and data.current_score >= 56:
        return "Improving"
    
    if ("performance_instability" in patterns or 
        data.current_score < 45 or 
        trend == "Declining"):
        return "Needs Attention"
    
    return "Stable"


def generate_feedback(data: PerformanceRequest, trend: str, patterns: List[str], risk_state: str) -> dict:
    """Generate feedback with professional_summary, data_analysis, supportive_interpretation, and actionable_suggestions."""
    
    primary_pattern = patterns[0]
    score = round(data.current_score)
    p = round(data.productivity)
    c = round(data.consistency)
    q = round(data.quality)
    o = round(data.overdue_rate)
    
    # SECTION 1 — professional_summary
    performance_band_map = {
        "Excellent": f"Excellent performance this period at {score}%. All three dimensions are performing well above expectations.",
        "Very Good": f"Strong performance at {score}%. You are close to excellence with minor areas to refine.",
        "Good": f"Solid performance at {score}%. Deliberate effort in weaker areas will push you into the strong range.",
        "Average": f"Performance at {score}% is meeting the baseline. There is clear and achievable room for growth.",
        "Needs Attention": f"Performance at {score}% needs focused effort this week. The data highlights specific areas to address."
    }
    
    professional_summary = performance_band_map.get(data.performance_band, f"Performance at {score}%.")
    
    # Append trend suffix
    if trend == "Improving":
        professional_summary += " Your trajectory is moving in the right direction."
    elif trend == "Declining":
        professional_summary += " There has been a dip compared to last week — worth addressing early."
    else:
        professional_summary += " Your performance has been consistent week over week."
    
    # SECTION 2 — data_analysis
    data_analysis = f"Productivity: {p}% | Consistency: {c}% | Quality: {q}%. "
    
    # Append overdue sentence
    if data.overdue_rate > 30:
        data_analysis += f"Overdue rate is high at {o}%, negatively impacting score. "
    elif data.overdue_rate > 15:
        data_analysis += f"Overdue rate is moderate at {o}% — worth monitoring. "
    else:
        data_analysis += f"Overdue rate is well controlled at {o}%. "
    
    # Append pattern sentence
    pattern_sentences = {
        "rushing": "High productivity alongside lower quality suggests tasks may be moving to submission too quickly. ",
        "quality_decline": "Quality is the weakest dimension — submissions are requiring corrections more than expected. ",
        "planning_issue": "Overdue tasks indicate a planning or prioritization challenge mid-week. ",
        "performance_instability": "All three buckets are below 50%, suggesting performance pressure across the board. ",
        "inconsistent_sprinter": "Output is solid but consistency gaps show uneven working patterns across the week. ",
        "high_performer": "All three dimensions are performing strongly — this is well-rounded performance. ",
        "balanced": "Metrics are reasonably balanced across all three dimensions. "
    }
    
    data_analysis += pattern_sentences.get(primary_pattern, "")
    
    # SECTION 3 — supportive_interpretation (empathetic, not action items)
    fallback_map = {
        "rushing": "It looks like you're working hard to get things done quickly — that drive is valuable. A small adjustment to pace could help your quality scores catch up to your productivity.",
        "quality_decline": "Quality dips can happen when workload increases or requirements aren't clear. This is a recoverable situation with some focused attention.",
        "planning_issue": "Overdue tasks often signal competing priorities or unexpected blockers rather than lack of effort. Recognizing this pattern early is the first step to addressing it.",
        "performance_instability": "When multiple metrics dip at once, it often reflects a challenging period rather than a capability issue. Small, consistent daily efforts can turn this around quickly.",
        "inconsistent_sprinter": "Your ability to produce strong output is clear from your productivity numbers. The opportunity here is channeling that energy more evenly throughout the week.",
        "high_performer": "This is excellent, well-rounded performance. The habits and discipline that got you here are clearly working.",
        "balanced": "Your metrics are reasonably balanced across all areas. There's a solid foundation here to build on."
    }
    
    fallback = fallback_map.get(primary_pattern, "Every week is a fresh opportunity to build momentum. Small improvements compound over time.")
    
    # Build prompt for FLAN
    pattern_display = primary_pattern.replace("_", " ")
    prompt = (
        f"A staff member scored {score}% this week. "
        f"Productivity: {p}%, Quality: {q}%, Consistency: {c}%. "
        f"Performance pattern: {pattern_display}. "
        f"Trend: {trend}. "
        f"Write one supportive and specific coaching sentence for them."
    )
    
    supportive_interpretation = generate_flan_sentence(prompt, fallback)
    
    # SECTION 4 — actionable_suggestions (prioritized, max 2)
    suggestions = []
    
    # Priority 1: Address the primary pattern first
    if primary_pattern == "planning_issue" and data.overdue_rate > 20:
        suggestions.append("By Wednesday, identify any task at risk of going overdue and flag it to your supervisor so you have time to act.")
    elif primary_pattern == "rushing" and data.quality < 55:
        suggestions.append("Before submitting a task, check it against the original requirements once — catching one issue saves a correction cycle.")
    elif primary_pattern == "quality_decline" and data.quality < 55:
        suggestions.append("Before submitting a task, check it against the original requirements once — catching one issue saves a correction cycle.")
    elif primary_pattern == "inconsistent_sprinter" and data.consistency < 55:
        suggestions.append("Log your worklog every working day this week — even a brief entry earns a full consistency point.")
    
    # Priority 2: Address the weakest metric (if not already covered)
    weakest = min(
        ("consistency", data.consistency),
        ("quality", data.quality),
        ("productivity", data.productivity),
        key=lambda x: x[1]
    )
    
    if len(suggestions) < 2:
        if weakest[0] == "consistency" and data.consistency < 55 and "worklog" not in " ".join(suggestions):
            suggestions.append("Log your worklog every working day this week — even a brief entry earns a full consistency point.")
        elif weakest[0] == "quality" and data.quality < 55 and "requirements" not in " ".join(suggestions):
            suggestions.append("Before submitting a task, check it against the original requirements once — catching one issue saves a correction cycle.")
        elif weakest[0] == "productivity" and data.productivity < 55:
            suggestions.append("Push at least one in-progress task to in-review before the week ends to protect your productivity score.")
    
    # Fallback if no suggestions
    if not suggestions:
        suggestions.append("Maintain your current habits and aim to push your lowest-scoring bucket up by 5 points next week.")
    
    # Limit to max 2 suggestions
    actionable_suggestions = " ".join(suggestions[:2])
    
    return {
        "professional_summary": professional_summary,
        "data_analysis": data_analysis,
        "supportive_interpretation": supportive_interpretation,
        "actionable_suggestions": actionable_suggestions
    }


@router.post("/analyze-performance")
def analyze_performance(request: PerformanceRequest):
    """
    Analyze performance data and return feedback.
    """
    try:
        print(f"[DEBUG] Received request for user_id: {request.user_id}")
        
        # 1. Detect trend
        trend = detect_trend(request)
        print(f"[DEBUG] Trend detected: {trend}")
        
        # 2. Detect patterns
        patterns = detect_patterns(request)
        print(f"[DEBUG] Patterns detected: {patterns}")
        
        # 3. Assign risk state
        risk_state = assign_risk_state(trend, patterns, request)
        print(f"[DEBUG] Risk state: {risk_state}")
        
        # 4. Generate feedback
        print("[DEBUG] Generating feedback...")
        feedback = generate_feedback(request, trend, patterns, risk_state)
        print("[DEBUG] Feedback generated successfully")
        
        # 5. Return all fields merged
        response = {
            "trend": trend,
            "risk_state": risk_state,
            "patterns": patterns,
            "professional_summary": feedback["professional_summary"],
            "data_analysis": feedback["data_analysis"],
            "supportive_interpretation": feedback["supportive_interpretation"],
            "actionable_suggestions": feedback["actionable_suggestions"]
        }
        print("[DEBUG] Returning response")
        return response
    
    except Exception as e:
        import traceback
        print(f"[ERROR] Exception in analyze_performance: {str(e)}")
        print(f"[ERROR] Traceback:\n{traceback.format_exc()}")
        raise
