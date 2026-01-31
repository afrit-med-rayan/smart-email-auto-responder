# Deployment Guide

This guide details how to deploy the Smart Email Auto-Responder using Docker Compose.

## Prerequisites

- **Docker**: Engine version 20.10+
- **Docker Compose**: Version 2.0+
- **NVIDIA Container Toolkit** (Optional, for GPU support): If using GPU inference.
- **Git**: To clone the repository.

## Quick Start (Production)

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd smart-email-auto-responder
    ```

2.  **Environment Setup:**
    allowed configuration variables are in `.env.example`.
    ```bash
    cp .env.example .env
    # Edit .env with your specific credentials
    nano .env
    ```
    See [Environment Variables](env_variables.md) for details.

3.  **Run with Docker Compose:**
    For production, we use the `docker-compose.prod.yml` override to set resource limits and restart policies.
    ```bash
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
    ```

4.  **Verify Deployment:**
    Check status of containers:
    ```bash
    docker-compose ps
    ```
    View logs:
    ```bash
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f
    ```

## Infrastructure

The application consists of the following services:

| Service | Description | Container Name | Port (Internal/External) |
| :--- | :--- | :--- | :--- |
| **Frontend** | React SPA | `email-responder-frontend` | 80/3000 |
| **Backend** | FastAPI Application | `email-responder-backend` | 8000 |
| **Model Service** | ONNX/TorchServe Inference | `email-responder-model-service` | 8001 |
| **PostgreSQL** | Primary Database | `email-responder-postgres` | 5432 |
| **Redis** | Caching Layer | `email-responder-redis` | 6379 |
| **Nginx** | Reverse Proxy | `email-responder-nginx` | 80 |

## Updating the Application

To update the application to the latest version:

1.  Pull latest changes:
    ```bash
    git pull origin main
    ```
2.  Rebuild and restart containers:
    ```bash
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
    ```

## Scaling

To scale specific services (e.g., model service workers):

```bash
# Example: Scale model-service to 2 instances (requires load balancer config update if not using internal docker DNS round-robin properly)
# Note: Nginx configuration might need adjustment for dynamic scaling if not using a swarm/k8s orchestrator.
# For simple compose, vertical scaling (increasing resources) is often easier.
```
*Note: For horizontal scaling, consider migrating to Kubernetes or Docker Swarm.*
