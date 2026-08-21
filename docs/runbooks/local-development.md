# MedMatch Local Development Runbook

---

# 1. Document Information

| Field | Value |
|---|---|
| Document Name | MedMatch Local Development Runbook |
| Document ID | RUN-001 |
| Version | 1.0.0 |
| Status | Draft |
| Owner | MedMatch Engineering Team |
| Applies To | Developer Environment |
| Last Updated | YYYY-MM-DD |

---

# 2. Purpose

This document describes how to configure and run the MedMatch platform locally.

A developer should be able to:

- Clone the repository
- Configure dependencies
- Start services
- Run the complete platform
- Troubleshoot common issues

---

# 3. System Requirements

## Required Software

| Software | Version |
|---|---|
| Java | 21+ |
| Python | 3.11+ |
| Node.js | 22+ |
| Docker | Latest |
| Docker Compose | Latest |
| Git | Latest |

---

# 4. Repository Structure

```
MedMatch

├── services
│
├── frontend
│
├── infra
│
└── docs
```

---

# 5. Clone Repository

Clone the repository:

```bash
git clone <repository-url>
```

Navigate:

```bash
cd MedMatch
```

---

# 6. Environment Configuration

MedMatch uses environment variables for configuration.

Create environment files:

```
.env
```

Required configurations:

---

## Database

```
DATABASE_HOST

DATABASE_PORT

DATABASE_NAME

DATABASE_USERNAME

DATABASE_PASSWORD
```

---

## Redis

```
REDIS_HOST

REDIS_PORT
```

---

## Authentication

```
JWT_PUBLIC_KEY

JWT_PRIVATE_KEY
```

---

## AI Service

```
AI_SERVICE_URL

LLM_API_KEY
```

---

# 7. Running With Docker Compose

The recommended development method is Docker Compose.

Start all services:

```bash
docker compose up --build
```

---

# 8. Running Services

Expected services:

| Service | Port |
|---|---|
| Frontend | 5173 |
| Spring Boot Backend | 8081 |
| FastAPI AI Service | 8000 |
| PostgreSQL | 5434 |
| Redis | 6379 |

---

# 9. Service Verification

Check running containers:

```bash
docker compose ps
```

Expected:

```
medmatch-ui

medmatch-auth

medmatch-ai

medmatch-worker

medmatch-postgres

medmatch-redis
```

---

# 10. Health Checks

Verify backend:

```
GET /health
```

Verify AI service:

```
GET /health
```

Expected:

```json
{
 "status": "UP"
}
```

---

# 11. Database Setup

PostgreSQL is started through Docker.

Database:

```
medmatch
```

Required extensions:

```
pgvector
```

Verify:

```sql
SELECT * FROM pg_extension;
```

---

# 12. Database Migration

Database schema changes are managed through migrations.

Before starting services:

Verify:

```
flyway_schema_history
```

exists.

---

# 13. Running Backend Manually

Navigate:

```
services/auth-service
```

Run:

```bash
./mvnw spring-boot:run
```

---

# 14. Running AI Service Manually

Navigate:

```
services/ai-service
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run:

```bash
uvicorn app.main:app --reload
```

---

# 15. Running Celery Worker

Navigate:

```
services/ai-service
```

Start worker:

```bash
celery -A app.celery.celery_app worker --loglevel=info
```

---

# 16. Running Frontend

Navigate:

```
frontend
```

Install dependencies:

```bash
npm install
```

Start:

```bash
npm run dev
```

---

# 17. Common Issues

## Database Connection Failed

Check:

```
docker compose ps
```

Verify:

- PostgreSQL running
- Correct credentials
- Correct port

---

## Redis Connection Failed

Check:

```bash
docker logs medmatch-redis
```

Verify:

```
REDIS_HOST
REDIS_PORT
```

---

## Celery Worker Not Starting

Check:

- Redis availability
- Celery module path
- Python dependencies

---

## JWT Authentication Failure

Verify:

- Public key matches private key
- Token expiration
- Authorization header format

Expected:

```
Authorization: Bearer <token>
```

---

# 18. Development Workflow

Recommended flow:

```
Create Feature Branch

↓

Implement Change

↓

Run Tests

↓

Start Docker Environment

↓

Verify APIs

↓

Create Pull Request
```

---

# 19. Debugging Commands

View logs:

```bash
docker compose logs -f
```

Restart services:

```bash
docker compose restart
```

Rebuild:

```bash
docker compose up --build
```

Stop services:

```bash
docker compose down
```

---

# 20. Revision History

| Version | Date | Description |
|---|---|---|
| 1.0.0 | YYYY-MM-DD | Initial local development runbook |

---

# End of Document