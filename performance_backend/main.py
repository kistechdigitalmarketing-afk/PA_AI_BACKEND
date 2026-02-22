from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.analyze_performance import router
import generator
import asyncio
import threading

# Flag to track model loading status
model_loading = False
model_loaded = False

def load_model_background():
    """Load model in background thread."""
    global model_loading, model_loaded
    model_loading = True
    print("[INFO] Loading FLAN-T5 model in background (this takes ~30 seconds)...")
    generator.load_model()
    model_loaded = True
    model_loading = False
    print("[OK] FLAN-T5 model loaded and ready")

# Lifespan handler (replaces deprecated on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start model loading in background thread (non-blocking)
    print("[INFO] Starting server...")
    thread = threading.Thread(target=load_model_background, daemon=True)
    thread.start()
    
    print("[OK] Server is ready to accept requests (model loading in background)")
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
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
