# Performance Analysis Backend

An AI-powered employee performance feedback system that analyzes work metrics and generates personalized coaching feedback using Google's FLAN-T5 language model.

## What This Does

Takes raw performance data (productivity, quality, consistency, overdue rate) and generates:

| Output | Description |
|--------|-------------|
| **Trend** | `Improving` / `Stable` / `Declining` based on score change |
| **Risk State** | `Improving` / `Stable` / `Needs Attention` |
| **Patterns** | Detected issues like `rushing`, `quality_decline`, `planning_issue` |
| **Professional Summary** | Overall assessment based on performance band |
| **Data Analysis** | Breakdown of metrics with pattern insights |
| **Supportive Interpretation** | AI-generated coaching sentence (FLAN-T5) |
| **Actionable Suggestions** | Specific steps to improve |

## Architecture

```
FastAPI Server (main.py)
    |
    +-- /analyze-performance endpoint
    |       |
    |       +-- detect_trend()      -> Improving | Declining | Stable
    |       +-- detect_patterns()   -> [rushing, quality_decline, etc.]
    |       +-- assign_risk_state() -> Improving | Stable | Needs Attention
    |       +-- generate_feedback() -> 4 feedback sections
    |
    +-- generator.py (FLAN-T5 model)
            +-- generate_flan_sentence() -> AI-generated coaching text
```

### Hybrid Approach

- **Deterministic rules** for trend/pattern/risk detection (predictable, fast)
- **AI generation** only for the supportive coaching sentence (adds human touch)
- **Fallback text** if AI output fails quality checks

## Quick Start

### 1. Install dependencies
```bash
cd performance_backend
pip install -r requirements.txt
```

### 2. Run the server
```bash
python main.py
```

### 3. Test it
Open http://localhost:8000/docs for Swagger UI, or run:
```bash
python test_endpoint.py
```

## API Reference

### Real-Time Monitoring Endpoints

#### POST `/monitor-task-update`

Real-time monitoring endpoint that tracks user task patterns and provides feedback suggestions.

**Request:**
```json
{
  "user_id": "string",
  "task_count": 2,
  "timestamp": "2024-01-15T10:00:00Z"  // Optional
}
```

**Response:**
```json
{
  "pattern_count": 2,
  "current_pattern": "stable",
  "current_task_count": 2,
  "feedback_suggestion": "You were doing 2 tasks consistently, but now you're increasing your workload. This shows growth, but make sure to maintain quality as you take on more."
}
```

**Pattern Types:**
- `stable` - Task count remains consistent (within 1-2 tasks)
- `increasing` - Task count is consistently increasing
- `decreasing` - Task count is consistently decreasing
- `fluctuating` - Task count varies without clear pattern

**How it works:**
- Tracks user task completion patterns over time
- Detects when users maintain consistent patterns (e.g., "doing 2 tasks consistently")
- Provides feedback when patterns change (e.g., "you were doing 2 tasks consistently but now you do this...")
- Returns a pattern count (number of periods with the same pattern) and AI-generated feedback

#### GET `/monitor-status/{user_id}`

Get current monitoring status and feedback for a user.

**Response:**
```json
{
  "pattern_count": 3,
  "current_pattern": "stable",
  "current_task_count": 2,
  "feedback_suggestion": "You've maintained a consistent pattern for 3 periods, doing around 2 tasks. This consistency is a strength - keep it up!",
  "pattern_history": [
    {
      "pattern": "stable",
      "count": 2,
      "task_count": 2
    }
  ]
}
```

### POST `/analyze-performance`

**Request:**
```json
{
  "user_id": "string",
  "current_score": 75.0,
  "previous_score": 70.0,
  "performance_band": "Good",
  "weekly_history": [],
  "productivity": 80.0,
  "consistency": 65.0,
  "quality": 70.0,
  "overdue_rate": 15.0
}
```

**Response:**
```json
{
  "trend": "Improving",
  "risk_state": "Improving",
  "patterns": ["balanced"],
  "professional_summary": "Solid performance at 75%...",
  "data_analysis": "Productivity: 80% | Consistency: 65% | Quality: 70%...",
  "supportive_interpretation": "AI-generated coaching sentence...",
  "actionable_suggestions": "Maintain your current habits..."
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `user_id` | string | Unique identifier for the employee |
| `current_score` | float | This week's overall performance score (0-100) |
| `previous_score` | float | Last week's score (optional, for trend detection) |
| `performance_band` | string | `Excellent` / `Very Good` / `Good` / `Average` / `Needs Attention` |
| `productivity` | float | Task completion rate (0-100) |
| `consistency` | float | Daily worklog consistency (0-100) |
| `quality` | float | Work quality score (0-100) |
| `overdue_rate` | float | Percentage of tasks overdue (0-100) |

## Pattern Detection Logic

| Pattern | Trigger Condition |
|---------|-------------------|
| `rushing` | Productivity > 65% AND Quality < 50% |
| `quality_decline` | Quality < 45% |
| `planning_issue` | Overdue rate > 30% |
| `performance_instability` | All three metrics < 50% |
| `inconsistent_sprinter` | Consistency < 40% AND Productivity > 60% |
| `high_performer` | All three metrics > 70% |
| `balanced` | No issues detected |

## Test Payloads

### High Performer
```json
{
  "user_id": "user001",
  "current_score": 92.0,
  "previous_score": 88.0,
  "performance_band": "Excellent",
  "weekly_history": [],
  "productivity": 85.0,
  "consistency": 80.0,
  "quality": 90.0,
  "overdue_rate": 5.0
}
```

### Struggling Employee
```json
{
  "user_id": "user002",
  "current_score": 38.0,
  "previous_score": 45.0,
  "performance_band": "Needs Attention",
  "weekly_history": [],
  "productivity": 40.0,
  "consistency": 35.0,
  "quality": 42.0,
  "overdue_rate": 45.0
}
```

### Rushing Pattern
```json
{
  "user_id": "user003",
  "current_score": 55.0,
  "previous_score": 58.0,
  "performance_band": "Average",
  "weekly_history": [],
  "productivity": 85.0,
  "consistency": 60.0,
  "quality": 40.0,
  "overdue_rate": 20.0
}
```

## Tech Stack

- **FastAPI** - Web framework
- **Uvicorn** - ASGI server
- **PyTorch** - ML framework
- **Transformers** - Hugging Face library
- **FLAN-T5 Small** - Google's instruction-tuned model (~300MB)
- **Pydantic** - Data validation

## Notes

- First startup downloads the FLAN-T5 model (~300MB) and takes ~30 seconds
- Model is loaded in background thread so server starts immediately
- Server runs on port 8000 by default
- All print statements use ASCII-safe characters for Windows compatibility
