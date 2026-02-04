import logging
from typing import Dict, Any
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from src.api.routes import router
from src.logging_config import setup_logging
from src.database import check_db_health

# Setup Logging
setup_logging("API", log_level="INFO")
logger = logging.getLogger("API")

app = FastAPI(
    title="Smart Email Auto-Responder API",
    description="API for AI-powered email classification and response generation.",
    version="1.0.0"
)

# Setup Metrics
Instrumentator().instrument(app).expose(app)

# CORS (Allow all for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1", tags=["v1"])

@app.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint returning status of services.
    """
    db_status = await check_db_health()
    status = "ok" if db_status else "degraded"
    
    return {
        "status": status, 
        "service": "email-responder",
        "database": "connected" if db_status else "disconnected"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
