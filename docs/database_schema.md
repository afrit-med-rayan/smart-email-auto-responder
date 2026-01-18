# Database Schema Documentation

## Overview

This document describes the PostgreSQL database schema for the Smart Email Auto-Responder application.

## Entity Relationship Diagram

```mermaid
erDiagram
    Email ||--o| Classification : has
    Email ||--o| Draft : has
    Email ||--o| ProcessingMetadata : has
    
    Email {
        int id PK
        string gmail_message_id UK
        string sender
        string subject
        text body
        datetime timestamp
        datetime created_at
        datetime updated_at
    }
    
    Classification {
        int id PK
        int email_id FK
        string intent
        float intent_confidence
        string intent_method
        json intent_scores
        string urgency
        float urgency_confidence
        text urgency_reasoning
        string sentiment
        float sentiment_confidence
        string sentiment_tone
        boolean sentiment_escalate
        datetime created_at
    }
    
    Draft {
        int id PK
        int email_id FK
        text draft_text
        string method
        float confidence
        string template_used
        int word_count
        string status
        datetime approved_at
        datetime sent_at
        datetime created_at
        datetime updated_at
    }
    
    ProcessingMetadata {
        int id PK
        int email_id FK
        string action
        string status
        text reason
        datetime processing_started_at
        datetime processing_completed_at
        datetime created_at
        datetime updated_at
    }
```

## Tables

### `emails`

Stores core email data.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing email ID |
| gmail_message_id | VARCHAR(255) | UNIQUE, NULLABLE | Gmail API message ID |
| sender | VARCHAR(255) | NOT NULL, INDEXED | Email sender address |
| subject | VARCHAR(500) | NOT NULL | Email subject line |
| body | TEXT | NOT NULL | Email body content |
| timestamp | DATETIME | NOT NULL, INDEXED | Email received timestamp |
| created_at | DATETIME | NOT NULL, DEFAULT NOW | Record creation time |
| updated_at | DATETIME | NOT NULL, DEFAULT NOW | Last update time |

**Indexes:**
- `ix_emails_id` (PRIMARY KEY)
- `ix_emails_gmail_message_id` (UNIQUE)
- `ix_emails_sender`
- `ix_emails_timestamp`

---

### `classifications`

Stores email classification results (intent, urgency, sentiment).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing classification ID |
| email_id | INTEGER | FOREIGN KEY, UNIQUE, NOT NULL | Reference to emails table |
| intent | VARCHAR(50) | NOT NULL, INDEXED | Classified intent |
| intent_confidence | FLOAT | NOT NULL | Intent confidence score (0-1) |
| intent_method | VARCHAR(50) | NULLABLE | Classification method used |
| intent_scores | JSON | NULLABLE | All intent scores |
| urgency | VARCHAR(50) | NOT NULL, INDEXED | Urgency level |
| urgency_confidence | FLOAT | NOT NULL | Urgency confidence score (0-1) |
| urgency_reasoning | TEXT | NULLABLE | Urgency reasoning text |
| sentiment | VARCHAR(50) | NOT NULL | Sentiment classification |
| sentiment_confidence | FLOAT | NOT NULL | Sentiment confidence score (0-1) |
| sentiment_tone | VARCHAR(50) | NULLABLE | Detected tone |
| sentiment_escalate | BOOLEAN | DEFAULT FALSE | Whether to escalate |
| created_at | DATETIME | NOT NULL, DEFAULT NOW | Record creation time |

**Indexes:**
- `ix_classifications_id` (PRIMARY KEY)
- `ix_classifications_email_id` (UNIQUE, FOREIGN KEY)
- `ix_classifications_intent`
- `ix_classifications_urgency`

---

### `drafts`

Stores generated draft responses.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing draft ID |
| email_id | INTEGER | FOREIGN KEY, UNIQUE, NOT NULL | Reference to emails table |
| draft_text | TEXT | NOT NULL | Generated draft content |
| method | VARCHAR(50) | NULLABLE | Generation method (template/llm/hybrid) |
| confidence | FLOAT | NULLABLE | Generation confidence score |
| template_used | VARCHAR(100) | NULLABLE | Template name if used |
| word_count | INTEGER | NULLABLE | Draft word count |
| status | VARCHAR(50) | DEFAULT 'pending', INDEXED | Draft status |
| approved_at | DATETIME | NULLABLE | Approval timestamp |
| sent_at | DATETIME | NULLABLE | Sent timestamp |
| created_at | DATETIME | NOT NULL, DEFAULT NOW | Record creation time |
| updated_at | DATETIME | NOT NULL, DEFAULT NOW | Last update time |

**Status values:** `pending`, `approved`, `sent`, `ignored`

**Indexes:**
- `ix_drafts_id` (PRIMARY KEY)
- `ix_drafts_email_id` (UNIQUE, FOREIGN KEY)
- `ix_drafts_status`

---

### `processing_metadata`

Stores processing pipeline metadata and status.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing metadata ID |
| email_id | INTEGER | FOREIGN KEY, UNIQUE, NOT NULL | Reference to emails table |
| action | VARCHAR(100) | NULLABLE | Recommended action |
| status | VARCHAR(50) | NOT NULL, INDEXED | Processing status |
| reason | TEXT | NULLABLE | Status reason/details |
| processing_started_at | DATETIME | NULLABLE | Processing start time |
| processing_completed_at | DATETIME | NULLABLE | Processing completion time |
| created_at | DATETIME | NOT NULL, DEFAULT NOW | Record creation time |
| updated_at | DATETIME | NOT NULL, DEFAULT NOW | Last update time |

**Status values:** `pending`, `success`, `error`

**Indexes:**
- `ix_processing_metadata_id` (PRIMARY KEY)
- `ix_processing_metadata_email_id` (UNIQUE, FOREIGN KEY)
- `ix_processing_metadata_status`

## Redis Caching Strategy

### Cache Keys

- **Classification:** `classification:email_{email_id}` (TTL: 1 hour)
- **Draft:** `draft:email_{email_id}` (TTL: 24 hours)
- **Metadata:** `metadata:email_{email_id}` (TTL: 30 minutes)

### Cache Invalidation

- Invalidate all caches for an email when:
  - Email is updated
  - Classification is re-run
  - Draft is modified
  - Processing status changes

## Setup Instructions

### 1. Start Database Services

```bash
# Using Docker
docker run -d --name email-responder-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=email_responder \
  -p 5432:5432 \
  postgres:15-alpine

docker run -d --name email-responder-redis \
  -p 6379:6379 \
  redis:7-alpine redis-server --appendonly yes
```

### 2. Set Environment Variables

Create `.env` file:

```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/email_responder
REDIS_URL=redis://localhost:6379/0
```

### 3. Install Dependencies

```bash
pip install sqlalchemy[asyncio] asyncpg alembic redis psycopg2-binary
```

### 4. Initialize Database

```bash
python -c "import asyncio; from src.database import init_db; asyncio.run(init_db())"
```

### 5. Migrate Data

```bash
python scripts/migrate_json_to_db.py
```

## Migration Guide

The migration script (`scripts/migrate_json_to_db.py`) transfers data from:
- `data/pending_drafts.json` → PostgreSQL tables
- `data/sample_emails.json` → PostgreSQL tables

Original JSON files are preserved as backups.

## API Usage

### Query Emails with Filtering

```python
GET /api/v1/emails?intent=academic&urgency=high&limit=50
```

### Response Format

```json
{
  "id": 1,
  "subject": "Project submission deadline",
  "sender": "professor@univ.edu",
  "body": "Hello Rayan...",
  "classification": {
    "intent": "academic",
    "urgency": "high",
    "sentiment": "neutral",
    "confidence": 0.85
  },
  "generatedDraft": "Dear Professor..."
}
```
