from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from performance_backend.routes.analyze_performance import router
from performance_backend import generator

# Flag to track model status
model_ready = False

# Lifespan handler - load model BEFORE accepting requests
@asynccontextmanager
async def lifespan(app: FastAPI):
    global model_ready
    print("[INFO] Starting server...")
    print("[INFO] Loading FLAN-T5 model (this takes ~60 seconds on first start)...")
    
    # Load model synchronously - server won't accept requests until done
    generator.load_model()
    model_ready = True
    
    print("[OK] FLAN-T5 model loaded and ready")
    print("[OK] Server is now accepting requests")
    yield

app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register router
app.include_router(router)

# Health check route
@app.get("/")
def health_check():
    return {
        "status": "ok",
        "model_ready": model_ready
    }

# Model status endpoint
@app.get("/status")
def model_status():
    if not model_ready:
        raise HTTPException(status_code=503, detail="Model is still loading, please wait...")
    return {
        "status": "ready",
        "model": "flan-t5-base",
        "message": "API is ready to accept requests"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
