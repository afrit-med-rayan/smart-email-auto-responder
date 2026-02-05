"""Custom metrics package."""

from src.metrics.custom_metrics import (
    record_email_processed,
    record_classification,
    record_response_generated,
    record_model_inference,
    record_classification_confidence,
    record_cache_hit,
    record_cache_miss,
    record_db_query,
    record_error,
)

__all__ = [
    "record_email_processed",
    "record_classification",
    "record_response_generated",
    "record_model_inference",
    "record_classification_confidence",
    "record_cache_hit",
    "record_cache_miss",
    "record_db_query",
    "record_error",
]
