# Troubleshooting Guide

This guide addresses common issues encountered when deploying and running the Smart Email Auto-Responder.

## Database Connection Issues

### Symptom: `FATAL: password authentication failed for user "postgres"`
**Cause:** Incorrect password in `.env` or `docker-compose.yml`.
**Solution:**
1.  Verify `POSTGRES_PASSWORD` in `.env` matches the `POSTGRES_PASSWORD` in `docker-compose.yml` (or checks out if using `env_file`).
2.  Check for lingering volumes if you changed passwords:
    ```bash
    docker-compose down -v
    docker-compose up -d
    ```
    *Warning: This deletes all database data.*

### Symptom: `could not connect to server: Connection refused`
**Cause:** Database container is not running or not healthy.
**Solution:**
1.  Check container status: `docker-compose ps`
2.  Check logs: `docker-compose logs postgres`
3.  Ensure `backend` service `depends_on` includes `postgres` with `condition: service_healthy`.

## Model Service Issues

### Symptom: `Model not found` or `Download error`
**Cause:** Internet connectivity issues or incorrect model name.
**Solution:**
1.  Verify `MODEL_NAME` in `.env` is a valid HuggingFace model ID.
2.  Ensure the container has internet access to download models on first run.
3.  Check if `models/` directory is writable.

### Symptom: OOM (Out of Memory) Kills
**Cause:** Model is too large for available RAM.
**Solution:**
1.  Increase Docker resource limits (memory) in `docker-compose.prod.yml`.
2.  Switch to a smaller model (e.g., `distilbert` instead of `bert-large`).
3.  Enable quantization (ensure `quantization.py` logic is active).

## API & Frontend Issues

### Symptom: Frontend cannot connect to Backend (CORS errors)
**Cause:** CORS misconfiguration or incorrect API URL.
**Solution:**
1.  Check browser console for CORS errors.
2.  Verify `BACKEND_URL` environment variable in frontend service matches the public URL of the backend (or Nginx proxy).
3.  Ensure Nginx is correctly proxying requests to `/api` -> `backend:8000`.

### Symptom: `502 Bad Gateway` from Nginx
**Cause:** Backend service is down or not listening.
**Solution:**
1.  Check backend logs: `docker-compose logs backend`.
2.  Wait for backend to become healthy (healthchecks in `docker-compose.yml` help avoid this during startup).

## Telegram Bot Issues

### Symptom: Bot not responding
**Cause:** Invalid token or webhook issues (if using webhooks).
**Solution:**
1.  Verify `TELEGRAM_BOT_TOKEN`.
2.  If using polling (default), ensure only one instance of the bot is running.
3.  Check logs for `TelegramNetworkError` or `Unauthorized`.

## General Debugging

- **View Logs:** `docker-compose logs -f [service_name]`
- **Shell into Container:** `docker-compose exec [service_name] /bin/sh` or `/bin/bash`
- **Inspect Network:** `docker network inspect email-responder-network`
