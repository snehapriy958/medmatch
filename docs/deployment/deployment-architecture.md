docker build -f infra/docker/ai-service.Dockerfile -t medmatch/ai-service:latest .# MedMatch Deployment Architecture

---

# 1. Document Information

| Field | Value |
|---|---|
| Document Name | MedMatch Deployment Architecture |
| Document ID | DEPLOY-001 |
| Version | 1.0.0 |
| Status | Draft |
| Owner | MedMatch Engineering Team |
| Applies To | Development and Production Environments |
| Last Updated | YYYY-MM-DD |

---

# 2. Purpose

This document defines the deployment architecture of the MedMatch platform.

It describes:

- Container deployment
- Kubernetes architecture
- Service communication
- Configuration management
- Secret management
- Persistent storage
- Scaling strategy
- Production deployment standards

---

# 3. Deployment Overview

MedMatch is deployed as a containerized microservice application.

High-level architecture:

```
                Users
                  |
                  |
             Ingress Controller
                  |
                  |
        +---------+----------+
        |                    |
        v                    v
 React Frontend        Backend API
                           |
                           |
              +------------+-------------+
              |                          |
              v                          v
       Authentication Service       AI Service
       (Spring Boot)                (FastAPI)
              |                          |
              |                          |
              +------------+-------------+
                           |
                           v
                    PostgreSQL
                    + pgvector

                           |
                           v

                         Redis

                           |
                           v

                    Celery Workers
```

---

# 4. Deployment Environments

MedMatch supports multiple environments.

| Environment | Purpose |
|---|---|
| Development | Local development and testing |
| Staging | Pre-production validation |
| Production | Live deployment |

---

# 5. Container Architecture

Each service runs as an independent container.

## Services

| Service | Technology | Container |
|---|---|---|
| Frontend | React + Vite | medmatch-ui |
| Backend | Spring Boot | medmatch-auth |
| AI Service | FastAPI | medmatch-ai |
| Worker | Celery | medmatch-worker |
| Database | PostgreSQL + pgvector | medmatch-postgres |
| Cache/Broker | Redis | medmatch-redis |

---

# 6. Docker Deployment

Local development uses Docker Compose.

Example:

```
docker compose up --build
```

Docker Compose starts:

```
Frontend

Spring Boot Service

FastAPI Service

Celery Worker

PostgreSQL

Redis
```

---

# 7. Kubernetes Architecture

Production deployment uses Kubernetes.

Logical structure:

```
Kubernetes Cluster

        |
        |
    Namespace
      medmatch

        |
        +----------------+
        |                |
        v                v

 Deployments        Stateful Services

 frontend           PostgreSQL

 backend            Redis

 ai-service

 celery-worker
```

---

# 8. Kubernetes Resources

## Deployments

Used for stateless services:

- React frontend
- Spring Boot backend
- FastAPI AI service
- Celery workers

---

## StatefulSets

Used for stateful components:

- PostgreSQL
- Redis (production configuration)

---

## Services

Kubernetes Services provide internal communication.

Examples:

```
backend-service

ai-service

postgres-service

redis-service
```

---

# 9. Configuration Management

Environment-specific configuration must not be stored in application code.

Configuration is managed using:

- ConfigMaps
- Environment variables

Examples:

```
DATABASE_HOST

DATABASE_NAME

REDIS_HOST

AI_SERVICE_URL
```

---

# 10. Secret Management

Sensitive information must use Kubernetes Secrets.

Examples:

```
Database Password

JWT Private Key

JWT Public Key

LLM API Keys
```

Rules:

- Secrets must never be committed to Git.
- Secrets must not appear in logs.
- Production secrets should use external secret managers when possible.

---

# 11. Persistent Storage

Stateful data requires persistent storage.

Storage requirements:

| Component | Storage |
|---|---|
| PostgreSQL | Persistent Volume |
| Uploaded Trial Documents | Persistent/Object Storage |
| Logs | Log Storage |
| Vector Data | PostgreSQL Volume |

---

# 12. Networking

External traffic flow:

```
User

↓

Ingress

↓

Frontend Service

↓

Backend Service

↓

Internal Services
```

Internal services communicate using Kubernetes DNS.

Example:

```
ai-service.medmatch.svc.cluster.local
```

---

# 13. Scaling Strategy

## Horizontal Scaling

Stateless services can scale horizontally.

Examples:

```
backend replicas: 3

ai-service replicas: 3

worker replicas: 5
```

---

## Horizontal Pod Autoscaler

HPA scales services based on:

- CPU usage
- Memory usage
- Custom metrics

Example:

```
CPU > 70%

↓

Increase replicas
```

---

# 14. Health Checks

All services must provide health endpoints.

Kubernetes uses:

## Liveness Probe

Checks if container is running.

## Readiness Probe

Checks if service can receive traffic.

Example:

```
GET /health
```

---

# 15. Monitoring and Logging

Production deployment should include:

## Monitoring

- CPU usage
- Memory usage
- Request latency
- Error rate

## Logging

Services should produce structured logs.

Important fields:

- Timestamp
- Service name
- Request ID
- User ID
- Error code

---

# 16. Deployment Flow

Production deployment process:

```
Developer Push

↓

CI Pipeline

↓

Build Docker Images

↓

Security Scan

↓

Push Image Registry

↓

Deploy Kubernetes Manifest

↓

Run Health Checks

↓

Release Traffic
```

---

# 17. Disaster Recovery

Production systems require:

- Database backups
- Persistent volume backups
- Recovery procedures
- Deployment rollback strategy

---

# 18. Future Cloud Deployment

Supported cloud targets:

- AWS
- Azure
- Google Cloud Platform

Recommended production components:

| Requirement | AWS Example |
|---|---|
| Kubernetes | EKS |
| Database | RDS PostgreSQL |
| Storage | S3 |
| Secrets | Secrets Manager |
| Monitoring | CloudWatch |

---

# 19. Revision History

| Version | Date | Description |
|---|---|---|
| 1.0.0 | YYYY-MM-DD | Initial deployment architecture |

---

# End of Document