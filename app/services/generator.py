from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

# Global variables to store the model in memory
tokenizer = None
model = None

def load_model():
    """Loads the FLAN-T5 model on server startup."""
    global tokenizer, model
    # FLAN-T5-small is lightweight but requires very clear instructions
    model_name = "google/flan-t5-small"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    print("✨ Generative AI Model Loaded")

def generate_text_feedback(score: int, risk: str, role: str, stats: dict) -> str:
    """Generates professional coaching feedback based on performance metrics."""
    global tokenizer, model
    if model is None:
        return "Analyzing performance data..."

    # Build detailed statistical context for pattern analysis
    stats_details = []
    if "completion_rate_pct" in stats:
        stats_details.append(f"completion rate of {stats['completion_rate_pct']}%")
    if "overdue_rate_pct" in stats:
        stats_details.append(f"overdue rate of {stats['overdue_rate_pct']}%")
    if "avg_working_logs" in stats:
        stats_details.append(f"average of {stats['avg_working_logs']} working logs per task")
    if "avg_approval_speed_hrs" in stats:
        stats_details.append(f"approval speed of {stats['avg_approval_speed_hrs']} hours")
    if "rejection_rate_pct" in stats:
        stats_details.append(f"rejection rate of {stats['rejection_rate_pct']}%")
    
    stats_summary = ", ".join(stats_details)

    # Improved prompt focused on pattern analysis and productivity feedback
    # Use direct, specific instructions without examples to avoid echo
    comp_rate = stats.get("completion_rate_pct", 0)
    overdue_rate = stats.get("overdue_rate_pct", 0)
    approval_speed = stats.get("avg_approval_speed_hrs", 0) if stats.get("avg_approval_speed_hrs") is not None else None
    
    prompt = (
        f"Performance review for {role}: "
        f"Completed {comp_rate}% of tasks, {overdue_rate}% overdue. "
        f"{f'Approval speed: {approval_speed} hours. ' if approval_speed is not None else ''}"
        f"Efficiency score {score}/100, {risk} risk. "
        f"Write feedback analyzing their work pattern. "
        f"Use the actual numbers {comp_rate}%, {overdue_rate}%, {f'{approval_speed} hours' if approval_speed is not None else ''}. "
        f"Give specific productivity advice based on these numbers."
    )

    # Try the AI model first for pattern analysis
    inputs = tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs, 
            max_length=150,  # Increased for more detailed feedback
            do_sample=True, 
            temperature=0.7,  # Lower temperature for more focused output
            top_p=0.9,
            repetition_penalty=2.5,
            no_repeat_ngram_size=3,
            num_beams=4,  # Use beam search for better quality
            early_stopping=True
        )
    
    feedback = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Comprehensive quality checks for pattern analysis feedback
    feedback_lower = feedback.lower()
    
    # Check if model is echoing the prompt
    is_echoing = (
        "efficiency:" in feedback_lower and "risk:" in feedback_lower and
        ("analyze" in feedback_lower or "pattern" in feedback_lower) and
        len(feedback.split()) < 20
    )
    
    # Check for instruction-like output
    is_instruction = (
        feedback_lower.startswith(("write", "provide", "give", "be ", "make ", "analyze", "identify")) or
        ("then " in feedback_lower and "feedback" in feedback_lower) or
        ("example format" in feedback_lower)
    )
    
    # Check for robotic patterns
    is_robotic = (
        "overall, the" in feedback_lower or
        "output rating" in feedback_lower or
        feedback.count("%") > 4  # Too many percentages without context
    )
    
    # Check if feedback contains actual analysis and numbers (not placeholders)
    has_placeholders = (
        "X%" in feedback or "Y hours" in feedback or "Z" in feedback or
        "x%" in feedback_lower or "y hours" in feedback_lower
    )
    
    has_analysis = (
        ("%" in feedback or "hours" in feedback_lower or "logs" in feedback_lower) and
        ("you" in feedback_lower or "your" in feedback_lower) and
        len(feedback.split()) >= 15 and
        not has_placeholders  # Must not contain placeholder variables
    )
    
    # Use AI feedback if it's good quality, otherwise use fallback
    if not (is_echoing or is_instruction or is_robotic or has_placeholders) and has_analysis and len(feedback) >= 25:
        return feedback
    
    # Fallback: Generate pattern-focused productivity feedback with all statistics
    # This analyzes user patterns and provides actionable insights
    feedback_parts = []
    
    # Analyze patterns and build comprehensive feedback
    stats_mentioned = []
    pattern_insights = []
    
    # Completion Rate - always mention
    comp_rate = stats.get("completion_rate_pct", 0)
    if comp_rate >= 95:
        stats_mentioned.append(f"an outstanding {int(comp_rate)}% completion rate")
    elif comp_rate >= 80:
        stats_mentioned.append(f"a solid {int(comp_rate)}% completion rate")
    elif comp_rate > 0:
        stats_mentioned.append(f"a {int(comp_rate)}% completion rate")
    else:
        stats_mentioned.append(f"a {int(comp_rate)}% completion rate (no tasks completed yet)")
    
    # Overdue Rate - always mention
    overdue_rate = stats.get("overdue_rate_pct", 0)
    if overdue_rate == 0:
        stats_mentioned.append("perfect on-time delivery with zero overdue tasks")
    elif overdue_rate < 5:
        stats_mentioned.append(f"excellent timeliness with only {overdue_rate}% overdue rate")
    elif overdue_rate < 20:
        stats_mentioned.append(f"a {overdue_rate}% overdue rate that needs attention")
    else:
        stats_mentioned.append(f"a concerning {overdue_rate}% overdue rate requiring immediate focus")
    
    # Average Working Logs - always mention if available
    avg_logs = stats.get("avg_working_logs", 0)
    if avg_logs > 0:
        if avg_logs >= 25:
            stats_mentioned.append(f"strong activity with an average of {int(avg_logs)} working logs per task")
        elif avg_logs >= 10:
            stats_mentioned.append(f"moderate activity with an average of {int(avg_logs)} working logs per task")
        else:
            stats_mentioned.append(f"an average of {int(avg_logs)} working logs per task")
    else:
        stats_mentioned.append("no working logs recorded yet")
    
    # Approval Speed - always mention if available (for supervisors/admins)
    if stats.get("avg_approval_speed_hrs") is not None:
        approval_speed = stats.get("avg_approval_speed_hrs", 0)
        if approval_speed < 2:
            stats_mentioned.append(f"lightning-fast approval speed of {approval_speed} hours")
        elif approval_speed < 8:
            stats_mentioned.append(f"quick approval turnaround of {approval_speed} hours")
        elif approval_speed < 24:
            stats_mentioned.append(f"approval speed of {approval_speed} hours")
        elif approval_speed < 168:  # Less than a week
            stats_mentioned.append(f"slow approval speed of {approval_speed} hours (over {int(approval_speed/24)} days)")
        else:
            stats_mentioned.append(f"very slow approval speed of {approval_speed} hours (over {int(approval_speed/24)} days)")
    
    # Rejection Rate - always mention if available (for supervisors/admins)
    if stats.get("rejection_rate_pct") is not None:
        rej_rate = stats.get("rejection_rate_pct", 0)
        if rej_rate == 0:
            stats_mentioned.append("zero rejections showing high quality work")
        elif rej_rate < 5:
            stats_mentioned.append(f"a low {rej_rate}% rejection rate")
        elif rej_rate < 15:
            stats_mentioned.append(f"a {rej_rate}% rejection rate that could be improved")
        else:
            stats_mentioned.append(f"a high {rej_rate}% rejection rate requiring attention")
    
    # Analyze patterns and identify productivity insights
    # Pattern: Low completion + High overdue = Procrastination pattern
    if comp_rate < 50 and overdue_rate > 50:
        pattern_insights.append("Your pattern shows tasks are being delayed, leading to overdue items. This suggests a procrastination pattern that's impacting productivity.")
    # Pattern: High completion + Zero overdue = Excellent time management
    elif comp_rate >= 90 and overdue_rate == 0:
        pattern_insights.append("Your pattern demonstrates excellent time management with consistent task completion and zero overdue items.")
    # Pattern: Slow approval + High rejection = Quality control issues
    elif stats.get("avg_approval_speed_hrs") and stats.get("avg_approval_speed_hrs", 0) > 48 and stats.get("rejection_rate_pct", 0) > 10:
        pattern_insights.append("Your approval pattern shows slow processing combined with high rejection rates, indicating potential quality control bottlenecks.")
    # Pattern: Fast approval + Zero rejection = Efficient workflow
    elif stats.get("avg_approval_speed_hrs") and stats.get("avg_approval_speed_hrs", 0) < 4 and stats.get("rejection_rate_pct", 0) == 0:
        pattern_insights.append("Your approval pattern shows quick turnaround with zero rejections, indicating an efficient and quality-focused workflow.")
    
    # Construct pattern-aware feedback
    if pattern_insights:
        feedback_parts.append(pattern_insights[0])
    
    # Remind them of their specific work details
    if len(stats_mentioned) > 0:
        reminder_text = "Your current work details: "
        if len(stats_mentioned) == 1:
            reminder_text += stats_mentioned[0] + "."
        elif len(stats_mentioned) == 2:
            reminder_text += stats_mentioned[0] + " and " + stats_mentioned[1] + "."
        elif len(stats_mentioned) == 3:
            reminder_text += ", ".join(stats_mentioned[:2]) + ", and " + stats_mentioned[2] + "."
        else:
            reminder_text += ", ".join(stats_mentioned[:3]) + f", and {len(stats_mentioned) - 3} more metrics."
        feedback_parts.append(reminder_text)
    
    # Add productivity-focused improvement suggestions
    productivity_tips = []
    
    if comp_rate < 80:
        productivity_tips.append(f"increase your completion rate from {int(comp_rate)}% by breaking tasks into smaller steps")
    if overdue_rate > 20:
        productivity_tips.append(f"reduce your {overdue_rate}% overdue rate by setting earlier internal deadlines")
    if stats.get("avg_approval_speed_hrs") and stats.get("avg_approval_speed_hrs", 0) > 24:
        productivity_tips.append(f"speed up your {stats.get('avg_approval_speed_hrs', 0)}-hour approval process by reviewing tasks in batches")
    if stats.get("avg_working_logs", 0) == 0:
        productivity_tips.append("start logging your work activities to track productivity patterns")
    if score < 70:
        productivity_tips.append("focus on workflow optimization to boost your efficiency score")
    
    if productivity_tips:
        if len(productivity_tips) == 1:
            feedback_parts.append(f"To become more productive: {productivity_tips[0]}.")
        else:
            tips_text = ", ".join(productivity_tips[:-1]) + f", and {productivity_tips[-1]}"
            feedback_parts.append(f"To become more productive: {tips_text}.")
    
    # Return the comprehensive feedback
    if feedback_parts:
        return " ".join(feedback_parts)
    
    # Final fallback (should rarely be reached)
    return f"Your current efficiency score is {score}/100 with {risk} risk level. Continue working on optimizing your workflow performance."