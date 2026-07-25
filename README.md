# MedMatch

> AI-Powered Clinical Trial Matching Platform

MedMatch is an AI-powered platform that assists healthcare professionals in matching patients with relevant clinical trials using Retrieval-Augmented Generation (RAG), semantic search, and Large Language Models (LLMs).

The platform combines Spring Boot, FastAPI, PostgreSQL with pgvector, Redis, Celery, React, and Docker into a production-ready microservices architecture.

---

# Features

## Authentication & Authorization

- JWT Authentication (RS256)
- Role-Based Access Control (RBAC)
- Multi-Tenant Hospital Isolation
- Secure Password Hashing
- Spring Security

---

## Hospital Management

- Hospital CRUD
- Hospital Isolation
- Tenant-Aware Data Access

---

## User Management

- User CRUD
- Role Assignment
- Hospital Assignment
- Secure Registration

---

## Patient Management

- Patient CRUD
- Clinical Notes
- Hospital Isolation

---

## Clinical Trial Management

- Upload Clinical Trial PDFs
- Automatic PDF Extraction
- AI-Based Eligibility Criteria Extraction
- Trial Storage
- Trial Criteria Storage

---

## AI Matching

- Semantic Search using pgvector
- SentenceTransformer Embeddings
- Retrieval-Augmented Generation (RAG)
- Gemini LLM Evaluation
- Eligibility Classification

Possible outcomes:

- Eligible
- Possibly Eligible
- Not Eligible

---

## Background Processing

- Redis
- Celery Workers
- Asynchronous Trial Processing

---

## Production Features

- Docker
- Docker Compose
- Nginx Reverse Proxy
- Health Checks
- Environment Configuration
- GitHub Actions CI
- Structured Logging

---

# Architecture

```text
                           User
                             │
                             ▼
                     React Frontend
                       (Nginx)
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
 Spring Boot Authentication          FastAPI AI Service
            │                                 │
            ▼                                 ▼
      PostgreSQL + pgvector              Redis Cache
            │                                 │
            └──────────────┐                  │
                           ▼                  ▼
                    Celery Worker      Gemini API
```

---

# Technology Stack

## Frontend

- React 19
- TypeScript
- Vite
- React Hook Form
- Zod
- TanStack Query
- Axios
- Tailwind CSS
- shadcn/ui

---

## Backend

### Authentication Service

- Java 21
- Spring Boot 3
- Spring Security
- Spring Data JPA
- JWT (RS256)
- Flyway

---

### AI Service

- Python 3.12
- FastAPI
- SQLAlchemy
- Pydantic
- LangChain
- SentenceTransformers
- Google Gemini

---

## Database

- PostgreSQL 17
- pgvector

---

## Background Processing

- Redis
- Celery

---

## DevOps

- Docker
- Docker Compose
- Nginx
- GitHub Actions

---

# Project Structure

```text
medmatch/

├── frontend/
│   └── medmatch-ui/
│
├── services/
│   ├── auth-service/
│   └── ai-service/
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

# Prerequisites

Install the following software:

- Docker Desktop
- Git
- Java 21
- Python 3.12
- Node.js 22

---

# Environment Setup

Copy the example environment file.

```bash
cp .env.example .env
```

Configure:

- Database credentials
- Gemini API Key
- Ports
- JWT Keys

---

# Running the Application (Docker)

Build and start all services.

```bash
docker compose up --build
```

The following services will start automatically:

- PostgreSQL
- Redis
- Spring Boot Authentication Service
- FastAPI AI Service
- Celery Worker
- React Frontend

---

# Running Without Docker

## Spring Boot

```bash
cd services/auth-service

./mvnw spring-boot:run
```

---

## FastAPI

```bash
cd services/ai-service

uvicorn app.main:app --reload
```

---

## Celery

```bash
celery -A app.celery.celery_app worker --loglevel=info
```

---

## Frontend

```bash
cd frontend/medmatch-ui

npm install

npm run dev
```

---

# Services

| Service | URL |
|----------|-----|
| Frontend | http://localhost |
| Auth Service | http://localhost:8081 |
| AI Service | http://localhost:8000 |
| PostgreSQL | localhost:5434 |
| Redis | localhost:6379 |

---

# Docker Containers

```text
medmatch-postgres

medmatch-redis

medmatch-auth

medmatch-ai

medmatch-worker

medmatch-frontend
```

---

# API Overview

## Authentication

- Login
- Register
- JWT Authentication

---

## Hospitals

- Create Hospital
- Update Hospital
- Delete Hospital
- Get Hospitals

---

## Users

- Create User
- Update User
- Delete User
- Get Users

---

## Patients

- Create Patient
- Update Patient
- Delete Patient
- Get Patients

---

## Trials

- Upload Trial PDF
- Retrieve Trials

---

## AI Matching

- Semantic Search
- Eligibility Evaluation

---

# Security

- JWT (RS256)
- Password Hashing
- RBAC
- Multi-Tenancy
- Environment-Based Configuration
- Secure CORS
- Security Headers
- Production Profiles

---

# CI/CD

GitHub Actions automatically:

- Builds Spring Boot
- Runs Java Tests
- Builds FastAPI
- Runs Python Tests
- Builds React
- Builds Docker Images

---

# Health Checks

The following services expose health endpoints.

Spring Boot

```
GET /health
```

FastAPI

```
GET /health
```

Docker Compose waits until services become healthy before starting dependent services.

---

# Logging

Structured logging includes:

Spring Boot

- Authentication
- Authorization
- Errors

FastAPI

- Trial Uploads
- Retrieval
- Matching
- Celery Tasks
- Exceptions

---

# End-to-End Workflow

```text
Login
   │
   ▼
Create Hospital
   │
   ▼
Create User
   │
   ▼
Create Patient
   │
   ▼
Upload Trial PDF
   │
   ▼
Background Processing
   │
   ▼
Generate Embeddings
   │
   ▼
Semantic Search
   │
   ▼
Gemini Eligibility Evaluation
   │
   ▼
Eligibility Result
```

---

# Development Workflow

```bash
git clone <repository>

cp .env.example .env

docker compose up --build
```

---

# Future Enhancements

- Kubernetes Deployment
- AWS Deployment
- Monitoring with Prometheus & Grafana
- OpenTelemetry Tracing
- Elasticsearch Logging
- Email Notifications
- Clinical Trial Recommendation Dashboard
- Advanced Analytics

---

# License

This project is developed for educational and research purposes.

---

# Author

**Sneha Singh**

B.E. Artificial Intelligence & Machine Learning

MedMatch – AI-Powered Clinical Trial Matching Platform