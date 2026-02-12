# AI Task Performance Analyzer Backend

A machine learning-powered API that analyzes task performance data to provide efficiency scores, risk assessments, and AI-generated coaching feedback for staff and supervisors.

## 🎯 What It Does

This backend service analyzes task performance patterns using ML models and provides:

- **Pattern Detection**: Uses IsolationForest ML models to identify anomaly patterns in task completion behavior
- **Efficiency Scoring**: Calculates a 0-100 efficiency score based on completion rates, overdue tasks, and worklog activity
- **Risk Assessment**: Determines Low/Medium/High risk levels based on performance patterns
- **AI Feedback**: Generates personalized coaching feedback using Google's FLAN-T5 language model
- **Role-Specific Analysis**: Different metrics for staff members vs supervisors/admins
  - **Staff**: Completion rate, overdue rate, worklog consistency
  - **Supervisors**: Additional metrics for approval speed and rejection rates

## 🚀 Features

- ✅ ML-powered pattern detection using IsolationForest
- ✅ Dynamic efficiency scoring (combines ML predictions with behavioral metrics)
- ✅ Risk level classification (Low/Medium/High)
- ✅ AI-generated personalized feedback using FLAN-T5
- ✅ Statistical breakdown (completion %, overdue %, approval speed, etc.)
- ✅ Role-based analysis (staff vs supervisor metrics)
- ✅ RESTful API with FastAPI
- ✅ Automatic CORS handling
- ✅ Production-ready deployment configuration

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
- Git (for cloning the repository)

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

**Note**: Installing PyTorch and transformers may take a few minutes as these are large packages.

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

## 📁 Project Structure

```
ai_backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── models.py               # Pydantic data models
│   ├── staff_model.pkl         # Trained staff performance model
│   ├── supervisor_model.pkl   # Trained supervisor performance model
│   └── services/
│       ├── __init__.py
│       ├── analyzer.py         # ML analysis and scoring logic
│       └── generator.py        # FLAN-T5 feedback generation
├── train_model.py              # Script to train ML models
├── inspect_model.py            # Model inspection utilities
├── tasks_export.xlsx           # Training data (Excel file)
├── requirements.txt            # Python dependencies
├── Procfile                    # Railway/Render deployment config
├── railway.json                # Railway-specific config
├── runtime.txt                 # Python version specification
└── README.md                   # This file
```

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

## 🚢 Deployment

### Railway (Recommended)

1. Push code to GitHub
2. Go to [railway.app](https://railway.app)
3. Create new project → Deploy from GitHub
4. Select your repository
5. Railway auto-detects configuration and deploys

### Other Platforms

See deployment configuration files:
- `Procfile` - For Railway/Render
- `railway.json` - Railway-specific settings
- `requirements.txt` - Dependencies

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
- CORS is currently set to allow all origins (`*`) - update for production

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

[Add your license information here]

## 👤 Author

[Your name/team]

---

For questions or issues, please open an issue on GitHub.
