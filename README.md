# MedMatch

<div align="center">

# 🩺 MedMatch
### AI-Powered Clinical Trial Matching Platform

An intelligent microservices-based platform that leverages **Retrieval-Augmented Generation (RAG)**, **Large Language Models (LLMs)**, and **semantic search** to assist healthcare professionals in matching patients with the most relevant clinical trials.

---

![Java](https://img.shields.io/badge/Java-21-orange)
![Spring Boot](https://img.shields.io/badge/Spring_Boot-3.5-green)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688)
![React](https://img.shields.io/badge/React-19-61DAFB)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-336791)
![pgvector](https://img.shields.io/badge/pgvector-Enabled-blueviolet)
![Redis](https://img.shields.io/badge/Redis-8-red)
![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED)
![GitHub Actions](https://img.shields.io/badge/CI-GitHub_Actions-success)

</div>

---

# Overview

MedMatch is a production-ready AI-powered clinical trial matching platform designed to streamline patient eligibility assessment for clinical trials.

Instead of manually reviewing lengthy eligibility criteria across numerous clinical trials, healthcare professionals can upload patient information and clinical trial documents into MedMatch. The platform automatically extracts structured trial criteria, performs semantic retrieval using vector embeddings, and utilizes Large Language Models (LLMs) to generate an explainable eligibility decision.

The project demonstrates modern software engineering practices by combining AI technologies with scalable microservices architecture, secure authentication, asynchronous processing, containerization, and automated CI pipelines.

---

# Why MedMatch?

Matching patients to clinical trials is traditionally a manual, repetitive, and time-consuming process that requires clinicians to review extensive eligibility documents.

MedMatch automates this workflow by combining:

- Semantic vector search
- Retrieval-Augmented Generation (RAG)
- Large Language Models
- Explainable AI reasoning
- Hospital-aware multi-tenant architecture

The result is a faster, more consistent, and AI-assisted eligibility evaluation process while maintaining secure data isolation across healthcare organizations.

---

# Key Features

## Authentication & Authorization

- JWT Authentication (RS256)
- Spring Security
- Role-Based Access Control (RBAC)
- Secure Password Hashing
- Token-Based Authentication
- Multi-Tenant Authorization

---

## Hospital Management

- Hospital CRUD Operations
- Hospital Isolation
- Tenant-Aware Data Access
- Organization-Level Security

---

## User Management

- User Registration
- User Authentication
- Role Assignment
- Hospital Assignment
- Secure Password Storage

---

## Patient Management

- Patient CRUD Operations
- Clinical Notes Management
- Secure Patient Storage
- Hospital Data Isolation

---

## Clinical Trial Processing

- Upload Clinical Trial PDFs
- Automatic PDF Text Extraction
- AI-Based Eligibility Criteria Extraction
- Structured Trial Storage
- Trial Criteria Management

---

## AI Matching Engine

MedMatch combines semantic retrieval with Large Language Models to evaluate patient eligibility against clinical trial criteria.

### Core Capabilities

- Semantic Search using pgvector
- SentenceTransformer Embeddings
- Retrieval-Augmented Generation (RAG)
- Google Gemini Integration
- AI-Assisted Eligibility Evaluation
- Explainable Decision Making

### Eligibility Outcomes

- ✅ Eligible
- ⚠️ Possibly Eligible
- ❌ Not Eligible

---

## Background Processing

Long-running operations are executed asynchronously using Redis and Celery.

Features include:

- Background PDF Processing
- AI Extraction Pipeline
- Embedding Generation
- Trial Indexing
- Queue-Based Task Execution
- Automatic Retry Support

---

## Production Features

The platform is designed with production deployment in mind.

- Dockerized Microservices
- Docker Compose Orchestration
- Health Checks
- Structured Logging
- Environment-Based Configuration
- GitHub Actions CI
- Container Health Monitoring
- Secure Secret Management

---

# Architecture

```text
                              Healthcare Professional
                                        │
                                        ▼
                             React Frontend (Vite)
                                        │
                                        ▼
                             Nginx Reverse Proxy
                                        │
                   ┌────────────────────┴────────────────────┐
                   ▼                                         ▼
      Spring Boot Authentication Service          FastAPI AI Service
                   │                                         │
                   ▼                                         ▼
             PostgreSQL + pgvector                    Redis + Celery
                   │                                         │
                   └──────────────┬──────────────────────────┘
                                  ▼
                       Google Gemini API (LLM)
```

---

## Architecture Overview

The platform is built using a microservices architecture where each service has a well-defined responsibility.

### React Frontend

Responsible for:

- User Interface
- Authentication
- Dashboard
- Patient Management
- Trial Upload
- AI Matching Interface

---

### Spring Boot Authentication Service

Responsible for:

- User Authentication
- JWT Token Generation
- Role-Based Authorization
- Hospital Management
- User Management
- Audit Logging

---

### FastAPI AI Service

Responsible for:

- PDF Processing
- Criteria Extraction
- Embedding Generation
- Semantic Search
- Eligibility Evaluation
- Trial Management

---

### PostgreSQL + pgvector

Stores:

- Users
- Hospitals
- Patients
- Clinical Trials
- Trial Criteria
- Vector Embeddings
- Audit Logs

Provides both relational storage and vector similarity search.

---

### Redis

Redis serves as the messaging broker and caching layer.

Responsibilities:

- Celery Message Broker
- Background Task Queue
- Temporary Cache Storage
- High-Speed Data Access

---

### Celery Worker

The Celery worker executes computationally intensive tasks asynchronously.

Responsibilities:

- Trial PDF Processing
- Eligibility Criteria Extraction
- Embedding Generation
- AI Pipeline Execution

---

### Google Gemini

Gemini provides reasoning capabilities for patient eligibility evaluation.

Responsibilities:

- Clinical Reasoning
- Eligibility Assessment
- Explainable AI Responses
- Natural Language Evaluation

---

# Technology Stack

## Frontend

| Technology | Purpose |
|------------|---------|
| React 19 | User Interface |
| TypeScript | Type Safety |
| Vite | Build Tool |
| Tailwind CSS | Styling |
| shadcn/ui | UI Components |
| Axios | HTTP Client |
| React Hook Form | Form Handling |
| Zod | Validation |
| TanStack Query | Server State Management |

---

## Authentication Service

| Technology | Purpose |
|------------|---------|
| Java 21 | Programming Language |
| Spring Boot 3 | Backend Framework |
| Spring Security | Authentication |
| Spring Data JPA | Database ORM |
| JWT (RS256) | Authentication Tokens |
| Flyway | Database Migrations |
| Maven | Dependency Management |

---

## AI Service

| Technology | Purpose |
|------------|---------|
| Python 3.12 | Programming Language |
| FastAPI | REST API Framework |
| SQLAlchemy | ORM |
| Pydantic | Data Validation |
| LangChain | LLM Integration |
| SentenceTransformers | Embedding Generation |
| Google Gemini | AI Reasoning |

---

## Database

| Technology | Purpose |
|------------|---------|
| PostgreSQL 17 | Relational Database |
| pgvector | Vector Similarity Search |

---

## Background Processing

| Technology | Purpose |
|------------|---------|
| Redis | Message Broker |
| Celery | Asynchronous Task Queue |

---

## DevOps

| Technology | Purpose |
|------------|---------|
| Docker | Containerization |
| Docker Compose | Service Orchestration |
| GitHub Actions | Continuous Integration |
| Nginx | Frontend Web Server |

---

# Project Structure

```text
medmatch/
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── frontend/
│   └── medmatch-ui/
│       ├── public/
│       ├── src/
│       ├── Dockerfile
│       └── nginx.conf
│
├── services/
│   ├── auth-service/
│   │   ├── src/
│   │   ├── Dockerfile
│   │   └── pom.xml
│   │
│   └── ai-service/
│       ├── app/
│       ├── Dockerfile
│       ├── requirements.txt
│       └── uploads/
│
├── docker-compose.yml
├── .env.example
├── .gitignore
├── .dockerignore
└── README.md
```

---

# Project Highlights

- Microservices Architecture
- AI-Powered Clinical Trial Matching
- Retrieval-Augmented Generation (RAG)
- Semantic Search with pgvector
- Secure JWT Authentication
- Multi-Tenant Hospital Isolation
- Background Task Processing
- Production-Ready Docker Deployment
- Automated GitHub Actions CI Pipeline
- Fully Containerized Development Environment

---

# Screenshots

Screenshots will be added after the frontend reaches production quality.

The planned screenshots include:

- Login Page
- Dashboard
- Patient Management
- Clinical Trial Upload
- Trial Details
- AI Eligibility Evaluation
- Hospital Management
- User Management
- Responsive Mobile View

---

# REST API Overview

## Authentication APIs

Responsible for user authentication and authorization.

### Available Endpoints

- User Login
- User Registration
- JWT Token Generation
- Token Validation
- Current User Information

---

## Hospital APIs

Manage hospitals within the platform.

### Available Endpoints

- Create Hospital
- Update Hospital
- Delete Hospital
- Get Hospital
- List Hospitals

---

## User APIs

Manage healthcare users.

### Available Endpoints

- Create User
- Update User
- Delete User
- Get User
- List Users
- Assign Role
- Assign Hospital

---

## Patient APIs

Manage patient records.

### Available Endpoints

- Create Patient
- Update Patient
- Delete Patient
- Get Patient
- List Patients
- Upload Clinical Notes

---

## Clinical Trial APIs

Manage clinical trial data.

### Available Endpoints

- Upload Trial PDF
- Get Trial
- List Trials
- Delete Trial
- Retrieve Trial Criteria

---

## AI Matching APIs

Perform AI-powered patient matching.

### Available Endpoints

- Generate Patient Embedding
- Semantic Trial Retrieval
- Eligibility Evaluation
- AI Matching Result

---

# End-to-End Workflow

```text
                    User Login
                         │
                         ▼
               JWT Authentication
                         │
                         ▼
               Create / Select Hospital
                         │
                         ▼
                 Register Healthcare User
                         │
                         ▼
                  Register Patient
                         │
                         ▼
               Upload Clinical Trial PDF
                         │
                         ▼
          Celery Background Processing
                         │
        ┌────────────────┴────────────────┐
        ▼                                 ▼
 PDF Text Extraction             AI Criteria Extraction
        │                                 │
        └────────────────┬────────────────┘
                         ▼
              Structured Trial Criteria
                         │
                         ▼
             Generate Vector Embeddings
                         │
                         ▼
             Store in PostgreSQL + pgvector
                         │
                         ▼
               Submit Patient Clinical Note
                         │
                         ▼
             Generate Patient Embedding
                         │
                         ▼
            Semantic Similarity Search
                         │
                         ▼
          Retrieve Top Matching Trial Criteria
                         │
                         ▼
           Google Gemini Eligibility Analysis
                         │
                         ▼
          Eligible / Possibly / Not Eligible
```

---

# Security

MedMatch follows modern application security practices.

## Authentication

- JWT Authentication (RS256)
- Stateless Authentication
- Token Validation
- Secure Session Management

---

## Authorization

- Role-Based Access Control (RBAC)
- Administrator Permissions
- Tenant-Level Authorization
- Endpoint Protection

---

## Data Security

- BCrypt Password Hashing
- Environment-Based Configuration
- Secure Secret Management
- Hospital Data Isolation
- Multi-Tenant Database Access

---

## Infrastructure Security

- Docker Container Isolation
- Health Monitoring
- Secure HTTP Configuration
- Production Profiles

---

# CI/CD Pipeline

MedMatch uses GitHub Actions for continuous integration.

Every push and pull request automatically performs:

- Spring Boot Build
- Java Unit Tests
- FastAPI Dependency Installation
- Python Unit Tests
- React Production Build
- Docker Image Build
- Docker Compose Validation
- Container Health Verification

This ensures every commit maintains build stability across all services.

---

# Health Checks

To improve reliability and service orchestration, each microservice exposes a dedicated health endpoint.

Docker Compose waits until dependent services become healthy before starting dependent containers.

---

## Authentication Service

```http
GET /health
```

Example

```
http://localhost:8081/health
```

---

## AI Service

```http
GET /api/health
```

Example

```
http://localhost:8000/api/health
```

---

## Docker Health Monitoring

The following containers expose Docker health checks:

- PostgreSQL
- Redis
- Authentication Service
- AI Service

Container health is automatically verified during:

- Docker Compose startup
- GitHub Actions CI
- Production deployments

---

# Logging

Each service produces structured logs to simplify monitoring and debugging.

---

## Authentication Service Logs

Includes:

- Authentication Requests
- Authorization Events
- User Registration
- Login Attempts
- Audit Logs
- Exception Handling
- Security Events

---

## AI Service Logs

Includes:

- Trial Upload Processing
- PDF Extraction
- Eligibility Criteria Extraction
- Embedding Generation
- Semantic Search
- AI Matching
- API Requests
- Error Handling

---

## Celery Worker Logs

Includes:

- Background Tasks
- Queue Processing
- Retry Operations
- Task Completion
- Worker Status

---

## Docker Logs

Container logs can be viewed using:

```bash
docker compose logs
```

Individual services:

```bash
docker compose logs auth-service
```

```bash
docker compose logs ai-service
```

```bash
docker compose logs celery-worker
```

---

# Testing

MedMatch includes automated testing for every major service.

## Spring Boot

Run Java tests.

```bash
cd services/auth-service

./mvnw test
```

---

## FastAPI

Run Python tests.

```bash
cd services/ai-service

pytest
```

---

## Frontend

Run the production build.

```bash
cd frontend/medmatch-ui

npm run build
```

---

# Continuous Integration

GitHub Actions automatically validates every push and pull request.

The CI pipeline performs:

- Checkout Repository
- Build Spring Boot Service
- Execute Java Tests
- Build FastAPI Service
- Execute Python Tests
- Build React Frontend
- Validate Docker Compose
- Build Docker Images
- Deploy Temporary Containers
- Verify Health Checks
- Clean Up Containers

This ensures every commit maintains a deployable state.

---

# Performance Highlights

MedMatch is designed for scalability and production deployment.

Highlights include:

- Semantic Retrieval using pgvector
- Asynchronous Background Processing
- Stateless JWT Authentication
- Multi-Tenant Architecture
- Containerized Deployment
- Health Monitoring
- Automated CI Validation
- Layer-Cached Docker Builds

---

# Future Roadmap

The following enhancements are planned for future releases.

## Infrastructure

- Kubernetes Deployment
- Helm Charts
- Horizontal Scaling
- AWS Deployment
- Terraform Infrastructure

---

## Monitoring

- Prometheus
- Grafana
- OpenTelemetry
- Centralized Logging
- Distributed Tracing

---

## AI

- Multiple LLM Support
- Hybrid Retrieval
- Medical Knowledge Graph
- Trial Recommendation Ranking
- Explainable AI Improvements

---

## Application

- Doctor Dashboard
- Patient Dashboard
- Trial Analytics
- Email Notifications
- Advanced Search Filters
- Admin Analytics
- Audit Dashboard

---

# Contributing

Contributions, suggestions, and improvements are welcome.

If you would like to contribute:

1. Fork the repository.
2. Create a feature branch.
3. Commit your changes.
4. Push the branch.
5. Open a Pull Request.

Please ensure all tests pass before submitting a Pull Request.

---

# License

This project was developed as an educational and portfolio project to demonstrate modern AI engineering, Retrieval-Augmented Generation (RAG), microservices architecture, and production-ready software development practices.

---

# Author

**Sneha Singh**

B.E. Artificial Intelligence & Machine Learning

### Connect

- GitHub: *Add your GitHub profile*
- LinkedIn: *Add your LinkedIn profile*

---

<div align="center">

### ⭐ If you found this project interesting, consider giving it a star.

**MedMatch — AI-Powered Clinical Trial Matching Platform**

Built with Spring Boot • FastAPI • React • PostgreSQL • pgvector • Redis • Docker • GitHub Actions

</div>