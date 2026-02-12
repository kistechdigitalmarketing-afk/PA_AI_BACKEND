from pydantic import BaseModel

class TaskItem(BaseModel):
    task_id: str
    user_id: str
    user_role: str
    status: str
    priority: int
    approval_status: str
    working_count: int
    last_worklog_date: str | None = None
    due_date: str | None = None
    created_at: str | None = None
    submitted_at: str | None = None
    approved_at: str | None = None

class AnalysisRequest(BaseModel):
    user_id: str
    user_role: str
    tasks: list[TaskItem]

class AnalysisResponse(BaseModel):
    user_id: str
    efficiency_score: int
    risk_level: str
    feedback: str
    stats: dict[str, float | int]