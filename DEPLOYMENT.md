# Deployment Guide

This guide covers deploying the AI Task Performance Analyzer backend to various platforms.

## Prerequisites

- Python 3.11+
- Git repository connected to GitHub
- Account on your chosen hosting platform

## Deployment Options

### 🚂 Railway (Recommended - Easiest)

1. **Sign up/Login**: Go to [railway.app](https://railway.app) and sign in with GitHub
2. **New Project**: Click "New Project" → "Deploy from GitHub repo"
3. **Select Repository**: Choose `PA_AI_BACKEND`
4. **Auto-Deploy**: Railway will automatically detect the `requirements.txt` and `Procfile`
5. **Set Environment Variables** (if needed): Go to Variables tab
6. **Get URL**: Railway will provide a URL like `https://your-app.railway.app`

**Note**: Railway automatically uses the `Procfile` and `railway.json` configuration.

### 🌐 Render

1. **Sign up**: Go to [render.com](https://render.com) and connect GitHub
2. **New Web Service**: Click "New" → "Web Service"
3. **Select Repository**: Choose `PA_AI_BACKEND`
4. **Configure**:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Python Version**: 3.11
5. **Deploy**: Click "Create Web Service"

### 🐳 Docker (Alternative)

If you prefer Docker, you can use the included Dockerfile:

```bash
docker build -t ai-backend .
docker run -p 8000:8000 ai-backend
```

## Important Notes

### Memory Requirements

This application loads ML models (FLAN-T5) which require:
- **Minimum**: 2GB RAM
- **Recommended**: 4GB+ RAM

Make sure your hosting plan supports this.

### Model Files

The `.pkl` model files (`staff_model.pkl`, `supervisor_model.pkl`) are included in the repository. Ensure they're committed and pushed.

### CORS Configuration

Currently, CORS is set to allow all origins (`allow_origins=["*"]`). For production, update `app/main.py` to restrict to your frontend domain:

```python
allow_origins=["https://your-frontend-domain.com"]
```

### Environment Variables

If you need to configure environment variables (API keys, etc.), set them in your hosting platform's dashboard.

## Testing Deployment

After deployment, test your API:

```bash
# Health check (if you add a health endpoint)
curl https://your-app-url.railway.app/docs

# Test analyze endpoint
curl -X POST https://your-app-url.railway.app/analyze \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "user_role": "staff", "tasks": []}'
```

## Troubleshooting

### Build Fails
- Check Python version matches `runtime.txt`
- Verify all dependencies in `requirements.txt` are correct
- Check build logs for specific errors

### App Crashes on Startup
- Check memory limits (ML models need RAM)
- Verify model files are present
- Check logs for import errors

### Slow Startup
- Normal! Loading FLAN-T5 model takes 30-60 seconds
- Consider using a smaller model or lazy loading

## Local Testing

Test locally before deploying:

```bash
# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` for API documentation.
