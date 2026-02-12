from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.models import AnalysisRequest, AnalysisResponse
from app.services.analyzer import calculate_metrics
from app.services.generator import load_model, generate_text_feedback


# Lifespan handles the startup/shutdown logic of the AI model
@asynccontextmanager
async def lifespan(app: FastAPI):
    load_model()  # Load FLAN-T5 weights
    yield


app = FastAPI(
    title="AI Task Performance Analyzer",
    description="ML-powered insights for Staff and Supervisors",
    lifespan=lifespan,
)

# Allow your frontend (e.g. React on localhost:3000) to call this API
app.add_middleware(
    CORSMiddleware,
    # For local development, allow all origins so any dev frontend can call this API.
    # If you deploy this service, tighten this list to specific domains.
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_user_data(request: AnalysisRequest):
    try:
        # 1. Convert Pydantic task objects to a list of dictionaries for Pandas
        tasks_list = [task.model_dump() for task in request.tasks]

        # 2. Run the math and anomaly detection.
        # Note: We now receive THREE variables from the modified analyzer.
        score, risk, report_stats = calculate_metrics(tasks_list, request.user_role)

        # 3. Generate the human-like coaching advice with statistical context
        ai_feedback = generate_text_feedback(score, risk, request.user_role, report_stats)

        # 4. Return the complete report including the statistical breakdown
        return AnalysisResponse(
            user_id=request.user_id,
            efficiency_score=score,
            risk_level=risk,
            feedback=ai_feedback,
            stats=report_stats,
        )
    except Exception as e:
        # Log the error for debugging
        import traceback
        print(f"❌ Error in /analyze endpoint: {str(e)}")
        print(f"📋 Traceback:\n{traceback.format_exc()}")
        print(f"📦 Request data: user_id={request.user_id}, user_role={request.user_role}, tasks_count={len(request.tasks)}")
        if request.tasks:
            print(f"📋 First task sample: {request.tasks[0].model_dump()}")
        # Re-raise to return 500 with error details
        raise