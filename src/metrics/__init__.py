"""
Custom Prometheus Metrics for Email Auto-Responder

Defines business-specific metrics for monitoring application performance.
"""

from prometheus_client import Counter, Histogram, Gauge, Info

# ============================================================================
# Email Processing Metrics
# ============================================================================

emails_processed_total = Counter(
    'emails_processed_total',
    'Total number of emails processed',
    ['status']  # success, failed
)

emails_classified_total = Counter(
    'emails_classified_total',
    'Total number of emails classified by intent',
    ['intent', 'urgency', 'sentiment']
)

# ============================================================================
# Response Generation Metrics
# ============================================================================

responses_generated_total = Counter(
    'responses_generated_total',
    'Total number of responses generated',
    ['strategy']  # template, llm, rag+llm
)

response_generation_duration = Histogram(
    'response_generation_duration_seconds',
    'Time spent generating responses',
    ['strategy'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

# ============================================================================
# Model Inference Metrics
# ============================================================================

model_inference_duration = Histogram(
    'model_inference_duration_seconds',
    'Time spent on model inference',
    ['model_type'],  # intent, sentiment, urgency, generator
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0]
)

model_inference_total = Counter(
    'model_inference_total',
    'Total number of model inferences',
    ['model_type', 'status']  # success, failed
)

# ============================================================================
# Classification Accuracy Metrics
# ============================================================================

classification_confidence = Histogram(
    'classification_confidence_score',
    'Confidence scores for classifications',
    ['model_type'],
    buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

low_confidence_predictions = Counter(
    'low_confidence_predictions_total',
    'Number of predictions below confidence threshold',
    ['model_type', 'predicted_class']
)

# ============================================================================
# Cache Metrics
# ============================================================================

cache_hits_total = Counter(
    'cache_hits_total',
    'Total number of cache hits',
    ['cache_type']  # redis, local
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total number of cache misses',
    ['cache_type']
)

cache_size = Gauge(
    'cache_size_bytes',
    'Current size of cache in bytes',
    ['cache_type']
)

# ============================================================================
# Database Metrics
# ============================================================================

db_query_duration = Histogram(
    'db_query_duration_seconds',
    'Time spent on database queries',
    ['operation'],  # select, insert, update, delete
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]
)

db_connections_active = Gauge(
    'db_connections_active',
    'Number of active database connections'
)

# ============================================================================
# API Metrics
# ============================================================================

api_requests_by_endpoint = Counter(
    'api_requests_by_endpoint_total',
    'Total API requests by endpoint',
    ['endpoint', 'method', 'status_code']
)

# ============================================================================
# Error Metrics
# ============================================================================

errors_total = Counter(
    'errors_total',
    'Total number of errors',
    ['error_type', 'component']
)

# ============================================================================
# Application Info
# ============================================================================

app_info = Info(
    'email_responder_app',
    'Email Auto-Responder application information'
)

# Set application info
app_info.info({
    'version': '1.0.0',
    'environment': 'development'
})


# ============================================================================
# Helper Functions
# ============================================================================

def record_email_processed(status: str = "success") -> None:
    """Record an email processing event."""
    emails_processed_total.labels(status=status).inc()


def record_classification(intent: str, urgency: str, sentiment: str) -> None:
    """Record an email classification event."""
    emails_classified_total.labels(
        intent=intent,
        urgency=urgency,
        sentiment=sentiment
    ).inc()


def record_response_generated(strategy: str, duration: float) -> None:
    """Record a response generation event."""
    responses_generated_total.labels(strategy=strategy).inc()
    response_generation_duration.labels(strategy=strategy).observe(duration)


def record_model_inference(model_type: str, duration: float, status: str = "success") -> None:
    """Record a model inference event."""
    model_inference_total.labels(model_type=model_type, status=status).inc()
    model_inference_duration.labels(model_type=model_type).observe(duration)


def record_classification_confidence(model_type: str, confidence: float, below_threshold: bool = False) -> None:
    """Record classification confidence score."""
    classification_confidence.labels(model_type=model_type).observe(confidence)
    
    if below_threshold:
        low_confidence_predictions.labels(
            model_type=model_type,
            predicted_class="unknown"
        ).inc()


def record_cache_hit(cache_type: str = "redis") -> None:
    """Record a cache hit."""
    cache_hits_total.labels(cache_type=cache_type).inc()


def record_cache_miss(cache_type: str = "redis") -> None:
    """Record a cache miss."""
    cache_misses_total.labels(cache_type=cache_type).inc()


def record_db_query(operation: str, duration: float) -> None:
    """Record a database query."""
    db_query_duration.labels(operation=operation).observe(duration)


def record_error(error_type: str, component: str) -> None:
    """Record an error."""
    errors_total.labels(error_type=error_type, component=component).inc()
