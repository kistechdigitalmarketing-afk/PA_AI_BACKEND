# AI Task Performance Analyzer Backend

A machine learning-powered API that analyzes task performance data to provide efficiency scores, risk assessments, and AI-generated coaching feedback for staff and supervisors.

## What It Does

This backend service analyzes task performance patterns using ML models and provides:

- **Pattern Detection**: Uses IsolationForest ML models to identify anomaly patterns in task completion behavior
- **Efficiency Scoring**: Calculates a 0-100 efficiency score based on completion rates, overdue tasks, and worklog activity
- **Risk Assessment**: Determines Low/Medium/High risk levels based on performance patterns
- **AI Feedback**: Generates personalized coaching feedback using Google's FLAN-T5 language model
- **Role-Specific Analysis**: Different metrics for staff members vs supervisors/admins
  - **Staff**: Completion rate, overdue rate, worklog consistency
  - **Supervisors**: Additional metrics for approval speed and rejection rates


## 🛠️ Technologies Used

- **FastAPI** - Modern Python web framework
- **scikit-learn** - ML models (IsolationForest for anomaly detection)
- **transformers** - Hugging Face transformers (FLAN-T5 model)
- **PyTorch** - Deep learning framework
- **pandas** - Data manipulation and analysis
- **joblib** - Model serialization
- **Pydantic** - Data validation

## 📋 Prerequisites

- Python 3.11 or higher
- pip (Python package manager)


## 🔧 Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/kistechdigitalmarketing-afk/PA_AI_BACKEND.git
cd PA_AI_BACKEND
```

### 2. Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```


### 4. Verify Model Files

Ensure the following model files exist in the `app/` directory:
- `app/staff_model.pkl` - Staff performance ML model
- `app/supervisor_model.pkl` - Supervisor performance ML model

If these files are missing, you'll need to train the models first (see [Training Models](#training-models) section).

## 🏃 Running the Application

### Development Mode

```bash
uvicorn app.main:app --reload
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Note**: On first startup, the FLAN-T5 model will be downloaded and loaded into memory. This takes 30-60 seconds and requires ~500MB RAM.

### Docker Deployment (Recommended)

Docker makes deployment easier and ensures consistent environments across different platforms.

#### Using Docker Compose (Easiest)

```bash
# Build and run the container
docker-compose up --build

# Run in detached mode (background)
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs

#### Using Docker directly

```bash
# Build the Docker image
docker build -t ai-task-analyzer .

# Run the container
docker run -p 8000:8000 ai-task-analyzer

# Run in detached mode with custom port
docker run -d -p 8080:8000 --name ai-backend ai-task-analyzer
```

#### Docker Benefits

- ✅ Consistent environment across development, staging, and production
- ✅ Easy deployment to any Docker-compatible platform (Railway, AWS, GCP, Azure, etc.)
- ✅ Isolated dependencies - no conflicts with system Python
- ✅ Reproducible builds
- ✅ Easy scaling with container orchestration

## 📡 API Endpoints

### POST `/analyze`

Analyzes task performance data and returns efficiency score, risk level, and AI feedback.

**Request Body:**
```json
{
  "user_id": "user123",
  "user_role": "staff",
  "tasks": [
    {
      "task_id": "task1",
      "user_id": "user123",
      "user_role": "staff",
      "status": "completed",
      "priority": 1,
      "approval_status": "approved",
      "working_count": 5,
      "due_date": "2024-01-15T00:00:00.000Z",
      "submitted_at": "2024-01-14T10:00:00.000Z",
      "approved_at": "2024-01-14T12:00:00.000Z"
    }
  ]
}
```

**Response:**
```json
{
  "user_id": "user123",
  "efficiency_score": 85,
  "risk_level": "Low",
  "feedback": "Your pattern demonstrates excellent time management...",
  "stats": {
    "completion_rate_pct": 95.0,
    "overdue_rate_pct": 0.0,
    "avg_working_logs": 4.5
  }
}
```

**User Roles:**
- `"staff"` - Regular staff member
- `"supervisor"` - Supervisor role (includes approval metrics)
- `"country_admin"` - Country admin role (includes approval metrics)

**Task Status Values:**
- `"planned"` - Task is planned
- `"in progress"` - Task is in progress
- `"in review"` - Task is under review
- `"completed"` - Task is completed

**Overdue Logic:**
A task is considered overdue if:
- The due date has passed
- Status is `"planned"` or `"in progress"`
- Status is NOT `"in review"`



## 🤖 Training Models

If you need to retrain the ML models:

1. Ensure `tasks_export.xlsx` contains your training data with columns:
   - `User Role`, `Status`, `Due Date`, `Submitted At`, `Approved At`
   - `Approval Status`, `Working Count`

2. Run the training script:
```bash
python train_model.py
```

This will generate:
- `app/staff_model.pkl` - Staff performance anomaly detection model
- `app/supervisor_model.pkl` - Supervisor performance anomaly detection model



**Memory Requirements:**
- Minimum: 2GB RAM (for FLAN-T5 model)
- Recommended: 4GB+ RAM

## 🔍 How It Works

1. **Data Analysis**: Receives task data and calculates metrics:
   - Completion rate
   - Overdue rate (based on due dates and status)
   - Average working logs
   - Approval speed (for supervisors)
   - Rejection rate (for supervisors)

2. **ML Pattern Detection**: Uses IsolationForest models to detect anomaly patterns in performance data

3. **Score Calculation**: Combines ML anomaly scores with behavioral metrics to generate a 0-100 efficiency score

4. **Risk Assessment**: Determines risk level based on model predictions and efficiency score

5. **AI Feedback Generation**: Uses FLAN-T5 to generate personalized coaching feedback based on the analysis

## 🧪 Testing

Test the API using the interactive docs at `http://localhost:8000/docs` or with curl:

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "user_role": "staff",
    "tasks": [
      {
        "task_id": "1",
        "user_id": "test_user",
        "user_role": "staff",
        "status": "completed",
        "priority": 1,
        "approval_status": "approved",
        "working_count": 3,
        "due_date": "2024-01-15T00:00:00.000Z"
      }
    ]
  }'
```

## 📝 Notes

- The FLAN-T5 model is loaded on server startup and kept in memory
- First API call may be slower due to model initialization
- Model files (`.pkl`) should be committed to the repository
- CORS is currently set to allow all origins (`*`) 

