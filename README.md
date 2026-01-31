# Smart Email Auto-Responder

Context-aware AI system that automatically classifies incoming emails, detects urgency and tone, and generates safe, confidence-based replies with human escalation.

## Features

- **Automated Email Classification:** Categorizes emails by intent, urgency, and sentiment using fine-tuned BERT models.
- **Intelligent Response Generation:** Drafts context-aware replies using LLMs.
- **Human-in-the-Loop:** sophisticated review system via Telegram bot integration.
- **Production Ready:** Dockerized deployment with PostgreSQL, Redis, and Nginx.

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Gmail API Credentials
- Telegram Bot Token

### Deployment

1.  Clone the repository:
    ```bash
    git clone https://github.com/afrit-med-rayan/smart-email-auto-responder.git
    cd smart-email-auto-responder
    ```

2.  Configure Environment:
    ```bash
    cp .env.example .env
    # Edit .env with your credentials
    ```

3.  Run with Docker Compose:
    ```bash
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
    ```

## Documentation

- [Deployment Guide](docs/deployment.md) - Detailed deployment instructions.
- [Environment Variables](docs/env_variables.md) - Configuration reference.
- [Troubleshooting](docs/troubleshooting.md) - Common issues and fixes.
- [Production Checklist](docs/production_checklist.md) - Pre-deployment verification.


## Infrastructure Requirements

- **CPU:** 4+ Cores recommended for model inference.
- **RAM:** 8GB+ (16GB recommended if running local LLMs without quantization).
- **GPU:** Optional but recommended for faster inference (NVIDIA CUDA).
- **Storage:** 20GB+ for Docker images and database.
