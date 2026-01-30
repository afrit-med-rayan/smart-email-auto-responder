import logging
import os
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from prometheus_fastapi_instrumentator import Instrumentator

from src.model_server.inference import InferenceEngine
from src.logging_config import setup_logging

# Setup Logging
setup_logging("ModelServer", log_level="INFO")
logger = logging.getLogger("ModelServer")

app = FastAPI(
    title="Smart Email Auto-Responder Model Server",
    description="Dedicated service for AI model inference.",
    version="1.0.0"
)

# Setup Metrics
Instrumentator().instrument(app).expose(app)

# Global variables for model engine
engine: InferenceEngine = None

class PredictionRequest(BaseModel):
    text: str

class BatchPredictionRequest(BaseModel):
    texts: List[str]

@app.on_event("startup")
async def startup_event():
    """Initialize model engine on startup."""
    global engine
    try:
        model_name = os.getenv("MODEL_NAME", "distilbert-base-uncased")
        device = os.getenv("INFERENCE_DEVICE", "cpu")
        
        logger.info(f"Loading model: {model_name} on {device}")
        
        # Load model and tokenizer
        # In a real scenario, we might load fine-tuned models from a local path
        model = AutoModelForSequenceClassification.from_pretrained(model_name)
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        engine = InferenceEngine(
            model=model,
            tokenizer=tokenizer,
            device=device,
            max_workers=int(os.getenv("WORKERS", "4")),
            batch_size=int(os.getenv("BATCH_SIZE", "8"))
        )
        
        # Warm up
        engine.warm_up()
        logger.info("Model server ready.")
        
    except Exception as e:
        logger.error(f"Failed to start model server: {e}", exc_info=True)
        raise e

@app.on_event("shutdown")
async def shutdown_event():
    if engine:
        engine.shutdown()

@app.get("/health")
async def health_check():
    if engine is None:
        raise HTTPException(status_code=503, detail="Model engine not initialized")
    return {"status": "ok", "service": "model-server"}

@app.post("/predict")
async def predict(request: PredictionRequest):
    if not engine:
        raise HTTPException(status_code=503, detail="Model engine not initialized")
    
    result = engine.predict_single(request.text, return_probabilities=True)
    return result

@app.post("/predict/batch")
async def predict_batch(request: BatchPredictionRequest):
    if not engine:
        raise HTTPException(status_code=503, detail="Model engine not initialized")
    
    results = engine.predict_batch(request.texts, return_probabilities=True)
    return results

@app.get("/stats")
async def get_stats():
    if not engine:
        raise HTTPException(status_code=503, detail="Model engine not initialized")
    return engine.get_performance_stats()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
