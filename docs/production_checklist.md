# Production Checklist

Before deploying to a live production environment, complete this checklist to ensure security, stability, and performance.

## Security

- [ ] **Change Default Passwords:**
    - [ ] PostgreSQL `POSTGRES_PASSWORD` (use a strong, random string).
    - [ ] Update `.env` and `docker-compose.yml` accordingly.
- [ ] **Secure API Keys:**
    - [ ] Ensure `.env` is **NOT** committed to version control.
    - [ ] Rotate keys (Gmail, Telegram) periodically.
- [ ] **HTTPS/SSL:**
    - [ ] Configure Nginx with SSL certificates (e.g., Let's Encrypt).
    - [ ] Force HTTP to HTTPS redirection.
- [ ] **Firewall:**
    - [ ] Restrict access to database (5432) and Redis (6379) ports to internal network only (done by default in `docker-compose` if ports aren't exposed to host 0.0.0.0 unnecessarily).
    - [ ] Only expose ports 80/443 publically.

## Performance

- [ ] **Resource Limits:**
    - [ ] Review `docker-compose.prod.yml` limits for CPU and Memory. Adjust based on server capacity.
- [ ] **Database Optimization:**
    - [ ] Ensure indexes are created for frequent queries.
    - [ ] Tune PostgreSQL config (`postgresql.conf`) for production workloads.
- [ ] **Caching:**
    - [ ] Verify Redis is running and caching is enabled in the backend.
- [ ] **Model Oprimization:**
    - [ ] Use quantized models if possible to save memory and reduce latency.
    - [ ] Enable GPU inference (`INFERENCE_DEVICE=cuda`) if hardware is available.

## Reliability

- [ ] **Health Checks:**
    - [ ] Verify all services have valid `healthcheck` definitions in `docker-compose.yml`.
- [ ] **Restart Policies:**
    - [ ] Ensure `restart: always` or `unless-stopped` is set for all critical services.
- [ ] **Logging:**
    - [ ] Configure log rotation (already in `docker-compose.prod.yml`) to prevent disk exhaustion.
    - [ ] Consider shipping logs to a centralized logging service (ELK, Splunk, etc.).
- [ ] **Backups:**
    - [ ] Schedule regular backups of the PostgreSQL database (`pg_dump`).
    - [ ] Backup configuration files (`.env`, `docker-compose*.yml`).

## Application Specific

- [ ] **Gmail Token Refresh:**
    - [ ] Ensure the refresh token logic works seamlessly to avoid authentication failures after a few days.
- [ ] **Telegram Webhook:**
    - [ ] Consider switching from polling to webhooks for lower latency and better scaling.
