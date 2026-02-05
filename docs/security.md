# Security Best Practices

This document outlines security best practices for the Smart Email Auto-Responder project.

## Table of Contents
- [Secrets Management](#secrets-management)
- [Security Scanning](#security-scanning)
- [Dependency Management](#dependency-management)
- [API Security](#api-security)
- [Database Security](#database-security)
- [Vulnerability Response](#vulnerability-response)

## Secrets Management

### Environment Variables

**CRITICAL**: Never commit `.env` files or hardcode secrets in source code.

#### Required Secrets
All sensitive credentials must be stored in environment variables:

- `GMAIL_CLIENT_ID` - Gmail API client ID
- `GMAIL_CLIENT_SECRET` - Gmail API client secret
- `GMAIL_REFRESH_TOKEN` - Gmail refresh token
- `TELEGRAM_BOT_TOKEN` - Telegram bot authentication token
- `TELEGRAM_CHAT_ID` - Telegram chat ID
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `API_KEY` - API authentication key (production only)

#### Best Practices

1. **Use `.env.example` as a template**:
   ```bash
   cp .env.example .env
   # Then fill in actual values
   ```

2. **Never commit `.env` files**:
   - `.env` is already in `.gitignore`
   - Double-check before committing

3. **Validate secrets on startup**:
   - Application validates required secrets exist
   - Fails fast if critical secrets are missing

4. **Production secrets**:
   - Use secret management services (AWS Secrets Manager, Azure Key Vault, etc.)
   - Rotate secrets regularly
   - Use different secrets for each environment

5. **Development vs Production**:
   - Use dummy/test credentials in development
   - Never use production secrets locally

### Secret Rotation

Rotate secrets regularly:
- **API Keys**: Every 90 days
- **Database Passwords**: Every 90 days
- **OAuth Tokens**: When compromised or every 180 days

## Security Scanning

### Bandit - Python Security Linter

Bandit scans Python code for common security issues.

#### Running Bandit

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run bandit scan
bandit -r src/ -f screen

# Generate JSON report
bandit -r src/ -f json -o bandit-report.json

# Run with config file
bandit -r src/ -c .bandit
```

#### Common Issues Detected

- Hardcoded passwords
- SQL injection vulnerabilities
- Use of insecure functions (`eval`, `exec`, `pickle`)
- Weak cryptographic algorithms
- Insecure random number generation

#### Configuration

Bandit configuration is in [`.bandit`](file:///.bandit):
- Excludes: test files, virtual environments
- Severity: MEDIUM or higher
- Confidence: MEDIUM or higher

### Safety - Dependency Vulnerability Scanner

Safety checks dependencies for known security vulnerabilities.

#### Running Safety

```bash
# Check all dependencies
safety check

# Check with policy file
safety check --policy-file .safety-policy.yml

# Generate JSON report
safety check --json

# Check specific requirements file
safety check -r requirements.txt
```

#### Handling Vulnerabilities

1. **Critical/High**: Fix immediately
2. **Medium**: Fix within 30 days
3. **Low**: Fix within 90 days or accept risk

#### Updating Dependencies

```bash
# Check for outdated packages
pip list --outdated

# Update specific package
pip install --upgrade package-name

# Update requirements file
pip freeze > requirements.txt
```

## Dependency Management

### Pinning Versions

All dependencies are pinned to specific versions in `requirements.txt`:
- Ensures reproducible builds
- Prevents unexpected breaking changes
- Makes security audits easier

### Regular Updates

Update dependencies regularly:
```bash
# Monthly security updates
safety check
pip list --outdated

# Update and test
pip install --upgrade package-name
pytest
```

## API Security

### Authentication

The API uses API key authentication for production:

```python
# In production, set API_KEY environment variable
API_KEY=your-secure-random-key
```

#### Generating Secure API Keys

```python
import secrets
api_key = secrets.token_urlsafe(32)
print(api_key)
```

### CORS Configuration

**Development**: Allow all origins (for testing)
**Production**: Restrict to specific domains

```python
# Update src/api/main.py for production
allow_origins=["https://yourdomain.com"]
```

### Rate Limiting

Consider implementing rate limiting for production:
- Prevents abuse
- Protects against DDoS attacks
- Use libraries like `slowapi` or `fastapi-limiter`

## Database Security

### Connection Security

1. **Use SSL/TLS** for database connections in production:
   ```
   DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db?ssl=require
   ```

2. **Principle of Least Privilege**:
   - Create dedicated database user for application
   - Grant only necessary permissions
   - Avoid using superuser accounts

3. **Connection Pooling**:
   - Limit maximum connections
   - Set appropriate timeouts
   - Monitor connection usage

### SQL Injection Prevention

- **Always use parameterized queries** (SQLAlchemy ORM handles this)
- Never concatenate user input into SQL queries
- Validate and sanitize all inputs

### Data Encryption

- **At Rest**: Enable database encryption
- **In Transit**: Use SSL/TLS connections
- **Sensitive Fields**: Consider field-level encryption for PII

## Vulnerability Response

### Response Process

1. **Detection**:
   - Automated scans (bandit, safety)
   - Security advisories
   - User reports

2. **Assessment**:
   - Determine severity (Critical, High, Medium, Low)
   - Identify affected components
   - Assess exploitability

3. **Remediation**:
   - Develop fix
   - Test thoroughly
   - Deploy to production

4. **Communication**:
   - Document in changelog
   - Notify users if necessary
   - Update security advisories

### Severity Levels

| Severity | Response Time | Example |
|----------|--------------|---------|
| **Critical** | 24 hours | Remote code execution, data breach |
| **High** | 7 days | Authentication bypass, privilege escalation |
| **Medium** | 30 days | XSS, CSRF, information disclosure |
| **Low** | 90 days | Minor information leaks, low-impact issues |

## Security Checklist

### Development
- [ ] No secrets in code
- [ ] All dependencies pinned
- [ ] Bandit scan passes
- [ ] Safety check passes
- [ ] Input validation implemented
- [ ] Error messages don't leak sensitive info

### Pre-Production
- [ ] Security scan in CI/CD
- [ ] Secrets in environment variables
- [ ] CORS properly configured
- [ ] API authentication enabled
- [ ] Database connections use SSL
- [ ] Logging doesn't expose secrets

### Production
- [ ] All secrets rotated
- [ ] Monitoring and alerting configured
- [ ] Regular security scans scheduled
- [ ] Incident response plan documented
- [ ] Backup and recovery tested
- [ ] Security headers configured

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [SQLAlchemy Security](https://docs.sqlalchemy.org/en/20/faq/security.html)

## Contact

For security issues, please contact the development team immediately.
