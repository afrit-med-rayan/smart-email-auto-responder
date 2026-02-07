# Metrics Documentation

This document describes all available Prometheus metrics for the Smart Email Auto-Responder application.

## Accessing Metrics

Metrics are exposed at the `/metrics` endpoint:

```bash
curl http://localhost:8000/metrics
```

## Available Metrics

### Email Processing Metrics

#### `emails_processed_total`
**Type**: Counter  
**Description**: Total number of emails processed  
**Labels**:
- `status`: `success` or `failed`

**Example Query**:
```promql
# Total emails processed
sum(emails_processed_total)

# Success rate
rate(emails_processed_total{status="success"}[5m]) / rate(emails_processed_total[5m])
```

#### `emails_classified_total`
**Type**: Counter  
**Description**: Total number of emails classified by intent  
**Labels**:
- `intent`: Email intent (academic, internship, meeting, support, spam, etc.)
- `urgency`: Urgency level (critical, high, medium, low)
- `sentiment`: Sentiment (positive, negative, neutral)

**Example Query**:
```promql
# Emails by intent
sum by (intent) (emails_classified_total)

# High urgency emails
sum(emails_classified_total{urgency="high"})
```

---

### Response Generation Metrics

#### `responses_generated_total`
**Type**: Counter  
**Description**: Total number of responses generated  
**Labels**:
- `strategy`: Generation strategy (template, llm, rag+llm)

**Example Query**:
```promql
# Responses by strategy
sum by (strategy) (responses_generated_total)
```

#### `response_generation_duration_seconds`
**Type**: Histogram  
**Description**: Time spent generating responses  
**Labels**:
- `strategy`: Generation strategy

**Buckets**: 0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0 seconds

**Example Query**:
```promql
# Average response generation time
rate(response_generation_duration_seconds_sum[5m]) / rate(response_generation_duration_seconds_count[5m])

# 95th percentile response time
histogram_quantile(0.95, rate(response_generation_duration_seconds_bucket[5m]))
```

---

### Model Inference Metrics

#### `model_inference_total`
**Type**: Counter  
**Description**: Total number of model inferences  
**Labels**:
- `model_type`: Type of model (intent, sentiment, urgency, generator)
- `status`: `success` or `failed`

**Example Query**:
```promql
# Inference error rate
rate(model_inference_total{status="failed"}[5m]) / rate(model_inference_total[5m])
```

#### `model_inference_duration_seconds`
**Type**: Histogram  
**Description**: Time spent on model inference  
**Labels**:
- `model_type`: Type of model

**Buckets**: 0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0 seconds

**Example Query**:
```promql
# Average inference time by model
rate(model_inference_duration_seconds_sum[5m]) / rate(model_inference_duration_seconds_count[5m])

# Slowest model
topk(1, avg by (model_type) (rate(model_inference_duration_seconds_sum[5m])))
```

---

### Classification Accuracy Metrics

#### `classification_confidence_score`
**Type**: Histogram  
**Description**: Confidence scores for classifications  
**Labels**:
- `model_type`: Type of model

**Buckets**: 0.0 to 1.0 in 0.1 increments

**Example Query**:
```promql
# Average confidence score
rate(classification_confidence_score_sum[5m]) / rate(classification_confidence_score_count[5m])

# Low confidence predictions (< 0.7)
sum(classification_confidence_score_bucket{le="0.7"})
```

#### `low_confidence_predictions_total`
**Type**: Counter  
**Description**: Number of predictions below confidence threshold  
**Labels**:
- `model_type`: Type of model
- `predicted_class`: Predicted class

**Example Query**:
```promql
# Low confidence prediction rate
rate(low_confidence_predictions_total[5m])
```

---

### Cache Metrics

#### `cache_hits_total`
**Type**: Counter  
**Description**: Total number of cache hits  
**Labels**:
- `cache_type`: Type of cache (redis, local)

**Example Query**:
```promql
# Cache hit rate
rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))
```

#### `cache_misses_total`
**Type**: Counter  
**Description**: Total number of cache misses  
**Labels**:
- `cache_type`: Type of cache

#### `cache_size_bytes`
**Type**: Gauge  
**Description**: Current size of cache in bytes  
**Labels**:
- `cache_type`: Type of cache

**Example Query**:
```promql
# Cache size in MB
cache_size_bytes / 1024 / 1024
```

---

### Database Metrics

#### `db_query_duration_seconds`
**Type**: Histogram  
**Description**: Time spent on database queries  
**Labels**:
- `operation`: Database operation (select, insert, update, delete)

**Buckets**: 0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0 seconds

**Example Query**:
```promql
# Average query time by operation
rate(db_query_duration_seconds_sum[5m]) / rate(db_query_duration_seconds_count[5m])

# Slow queries (> 100ms)
sum(rate(db_query_duration_seconds_bucket{le="0.1"}[5m]))
```

#### `db_connections_active`
**Type**: Gauge  
**Description**: Number of active database connections

**Example Query**:
```promql
# Current active connections
db_connections_active

# Alert if connections > 80% of pool size
db_connections_active > 8
```

---

### API Metrics

#### `api_requests_by_endpoint_total`
**Type**: Counter  
**Description**: Total API requests by endpoint  
**Labels**:
- `endpoint`: API endpoint path
- `method`: HTTP method
- `status_code`: HTTP status code

**Example Query**:
```promql
# Requests per second by endpoint
rate(api_requests_by_endpoint_total[5m])

# Error rate (5xx responses)
rate(api_requests_by_endpoint_total{status_code=~"5.."}[5m])
```

---

### Error Metrics

#### `errors_total`
**Type**: Counter  
**Description**: Total number of errors  
**Labels**:
- `error_type`: Type of error
- `component`: Component where error occurred

**Example Query**:
```promql
# Error rate by component
rate(errors_total[5m])

# Most common errors
topk(5, sum by (error_type) (errors_total))
```

---

## 🪵 Observability Stack

### Structured JSON Logging

The application uses structured JSON logging for all services. This allows for easy parsing and analysis by log aggregation systems (e.g., ELK, Grafana Loki).

**Log Format**:
```json
{
  "timestamp": "2026-02-05T22:30:15.123Z",
  "level": "INFO",
  "name": "api.main",
  "message": "Email processed successfully",
  "email_id": "12345",
  "duration_ms": 125,
  "status": "success"
}
```

**Key Benefits**:
- **Searchable Attributes**: Filter logs by `level`, `component`, or custom fields like `email_id`.
- **Consistency**: All services follow the same log structure.
- **Machine Readable**: Optimized for automated monitoring and alerting.

### Prometheus Integration

All custom metrics described above are exposed via a `/metrics` endpoint compatible with Prometheus.

- **Scrape Internal**: Default 15s.
- **Port**: 8000 (Backend API).
- **Endpoint**: `/metrics`.

---

## Standard FastAPI Metrics

The application also exposes standard HTTP metrics via `prometheus-fastapi-instrumentator`:

- `http_requests_total`: Total HTTP requests
- `http_request_duration_seconds`: HTTP request duration
- `http_request_size_bytes`: HTTP request size
- `http_response_size_bytes`: HTTP response size

---

## Alerting Guidelines

### Critical Alerts

**High Error Rate**:
```promql
rate(errors_total[5m]) > 10
```
Action: Investigate logs immediately

**Database Connection Pool Exhausted**:
```promql
db_connections_active >= 10
```
Action: Check for connection leaks, scale database

**Model Inference Failures**:
```promql
rate(model_inference_total{status="failed"}[5m]) / rate(model_inference_total[5m]) > 0.1
```
Action: Check model server health, review logs

### Warning Alerts

**Low Cache Hit Rate**:
```promql
rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m])) < 0.5
```
Action: Review cache configuration, consider increasing cache size

**Slow Response Generation**:
```promql
histogram_quantile(0.95, rate(response_generation_duration_seconds_bucket[5m])) > 5
```
Action: Optimize generation strategy, check model performance

**Low Classification Confidence**:
```promql
rate(low_confidence_predictions_total[5m]) / rate(emails_classified_total[5m]) > 0.2
```
Action: Review model performance, consider retraining

---

## Grafana Dashboard

### Recommended Panels

1. **Email Processing Overview**
   - Total emails processed (counter)
   - Processing success rate (gauge)
   - Emails by intent (pie chart)

2. **Performance Metrics**
   - Response generation time (graph)
   - Model inference time (graph)
   - Database query time (graph)

3. **Cache Performance**
   - Cache hit rate (gauge)
   - Cache size (graph)

4. **System Health**
   - Active database connections (gauge)
   - Error rate (graph)
   - API request rate (graph)

### Sample Dashboard JSON

```json
{
  "dashboard": {
    "title": "Email Auto-Responder Metrics",
    "panels": [
      {
        "title": "Emails Processed",
        "targets": [
          {
            "expr": "sum(rate(emails_processed_total[5m]))"
          }
        ]
      },
      {
        "title": "Response Generation Time (p95)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(response_generation_duration_seconds_bucket[5m]))"
          }
        ]
      }
    ]
  }
}
```

---

## Prometheus Configuration

Add this job to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'email-responder-api'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

---

## Testing Metrics

### Manual Testing

```bash
# Start the API
uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# Generate some traffic
curl http://localhost:8000/api/v1/emails

# Check metrics
curl http://localhost:8000/metrics | grep email
```

### Automated Testing

```python
import requests

# Fetch metrics
response = requests.get("http://localhost:8000/metrics")
metrics = response.text

# Verify specific metric exists
assert "emails_processed_total" in metrics
assert "response_generation_duration_seconds" in metrics
```

---

## Best Practices

1. **Use Labels Wisely**: Don't create high-cardinality labels (e.g., user IDs, email addresses)
2. **Monitor Rates**: Use `rate()` for counters to see changes over time
3. **Set Appropriate Buckets**: Adjust histogram buckets based on actual data distribution
4. **Create Alerts**: Set up alerts for critical metrics
5. **Regular Review**: Review metrics regularly to identify trends and issues

---

## Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [PromQL Cheat Sheet](https://promlabs.com/promql-cheat-sheet/)
- [Grafana Dashboards](https://grafana.com/grafana/dashboards/)
