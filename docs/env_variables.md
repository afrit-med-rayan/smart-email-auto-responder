# Environment Variables

This document lists environment variables supported by the application. Copy `.env.example` to `.env` and configure accordingly.

## Core Configuration

| Variable | Description | Required | Default |
| :--- | :--- | :--- | :--- |
| `LOG_LEVEL` | Logging verbosity (DEBUG, INFO, WARNING, ERROR) | No | `INFO` |
| `WORKERS` | Number of Uvicorn workers for backend/model service | No | `1` |

## Gmail API Integration

| Variable | Description | Required |
| :--- | :--- | :--- |
| `GMAIL_CLIENT_ID` | OAuth2 Client ID from Google Cloud Console | Yes |
| `GMAIL_CLIENT_SECRET` | OAuth2 Client Secret | Yes |
| `GMAIL_REFRESH_TOKEN` | OAuth2 Refresh Token for offline access | Yes |

## Telegram Integration

| Variable | Description | Required |
| :--- | :--- | :--- |
| `TELEGRAM_BOT_TOKEN` | Bot Token from @BotFather | Yes |
| `TELEGRAM_CHAT_ID` | Chat ID where the bot sends notifications | Yes |

## Database & Cache

| Variable | Description | Required | Default |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | PostgreSQL Connection String | Yes | `postgresql+asyncpg://postgres:postgres@postgres:5432/email_responder` |
| `REDIS_URL` | Redis Connection String | Yes | `redis://redis:6379/0` |

## Model Service

| Variable | Description | Required | Default |
| :--- | :--- | :--- | :--- |
| `MODEL_SERVICE_URL` | URL where backend can reach the model service | Yes | `http://model-service:8001` |
| `INFERENCE_DEVICE` | Computation device (`cpu` or `cuda`) | No | `cpu` |
| `MODEL_NAME` | Name of the HuggingFace model to load | No | `distilbert-base-uncased` |
| `MODEL_CACHE_DIR` | Directory to cache downloaded models | No | `/app/models` |

## External Services

| Variable | Description | Required |
| :--- | :--- | :--- |
| `LANGUAGETOOL_API_KEY` | API Key for LanguageTool (grammar checking) | No |

## User Personalization

| Variable | Description | Required | Default |
| :--- | :--- | :--- | :--- |
| `USER_NAME` | Name used in auto-generated signatures | No | `Rayan` |
| `USER_EMAIL` | Email address associated with the account | No | |
| `USER_SIGNATURE` | Custom signature block | No | `Best regards,\nRayan` |
