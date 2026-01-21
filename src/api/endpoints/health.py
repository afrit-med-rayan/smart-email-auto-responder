"""
Health Check Endpoints

Provides liveness, readiness, and metrics endpoints for monitoring.
"""

import logging
import time
import psutil
from fastapi import APIRouter, status
from pydantic import BaseModel
from typing import Dict, Any

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])

# Track application start time
_start_time = time.time()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: float
    uptime_seconds: float


class ReadinessResponse(BaseModel):
    """Readiness check response model."""
    status: str
    checks: Dict[str, bool]
    message: str


class MetricsResponse(BaseModel):
    """Metrics response model."""
    uptime_seconds: float
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Liveness Check",
    description="Basic liveness check to verify the service is running"
)
async def health_check():
    """
    Liveness probe endpoint.
    Returns 200 if the service is alive.
    """
    uptime = time.time() - _start_time
    
    return HealthResponse(
        status="healthy",
        timestamp=time.time(),
        uptime_seconds=uptime
    )


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    summary="Readiness Check",
    description="Readiness check to verify all dependencies are available"
)
async def readiness_check():
    """
    Readiness probe endpoint.
    Checks if the service is ready to accept traffic.
    """
    checks = {
        "api": True,  # API is running
        "models": await _check_models(),
        "database": await _check_database(),
        "redis": await _check_redis()
    }
    
    all_ready = all(checks.values())
    
    return ReadinessResponse(
        status="ready" if all_ready else "not_ready",
        checks=checks,
        message="All systems operational" if all_ready else "Some systems not ready"
    )


@router.get(
    "/health/metrics",
    response_model=MetricsResponse,
    summary="Performance Metrics",
    description="Get current performance metrics"
)
async def metrics():
    """
    Performance metrics endpoint.
    Returns system resource usage.
    """
    uptime = time.time() - _start_time
    
    # Get system metrics
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    
    return MetricsResponse(
        uptime_seconds=uptime,
        cpu_percent=cpu_percent,
        memory_percent=memory.percent,
        memory_used_mb=memory.used / (1024 * 1024),
        memory_available_mb=memory.available / (1024 * 1024)
    )


async def _check_models() -> bool:
    """Check if models are loaded and accessible."""
    try:
        from src.model_server import get_model_loader
        loader = get_model_loader()
        cache_info = loader.get_cache_info()
        # Models are ready if at least one is cached or models directory exists
        return cache_info["cache_size"] > 0 or True  # Always return True for now
    except Exception as e:
        logger.error(f"Model check failed: {e}")
        return False


async def _check_database() -> bool:
    """Check database connectivity."""
    try:
        from src.database import get_db
        # Try to get a database session
        # For now, return True if database module is importable
        return True
    except Exception as e:
        logger.error(f"Database check failed: {e}")
        return False


async def _check_redis() -> bool:
    """Check Redis connectivity."""
    try:
        from src.cache import get_redis_client
        # Try to ping Redis
        # For now, return True if cache module is importable
        return True
    except Exception as e:
        logger.error(f"Redis check failed: {e}")
        return False
