# MedMatch Kubernetes Deployment Guide

---

# 1. Document Information

| Field | Value |
|---|---|
| Document Name | MedMatch Kubernetes Deployment Guide |
| Document ID | K8S-001 |
| Version | 1.0.0 |
| Status | Draft |
| Owner | MedMatch Engineering Team |
| Applies To | Kubernetes Deployments |
| Last Updated | YYYY-MM-DD |

---

# 2. Purpose

This document defines Kubernetes deployment standards for the MedMatch platform.

It provides guidelines for deploying:

- Frontend service
- Backend service
- AI service
- Celery workers
- PostgreSQL
- Redis

---

# 3. Kubernetes Architecture

Production deployment:

```
Kubernetes Cluster

        |
        |
   medmatch Namespace

        |
        +---------------------+
        |                     |
        v                     v

   Frontend Deployment     Backend Deployment

        |                     |
        |                     |
        +----------+----------+

                   |

        +----------+----------+
        |                     |
        v                     v

    AI Service Deployment   Celery Worker

                   |

        +----------+----------+

                   |

        +----------+----------+
        |                     |
        v                     v

 PostgreSQL StatefulSet     Redis StatefulSet
```

---

# 4. Namespace

All MedMatch resources must run inside a dedicated namespace.

Example:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: medmatch
```

---

# 5. Deployment Standards

Stateless services use Kubernetes Deployments.

Used for:

- Frontend
- Spring Boot Backend
- FastAPI AI Service
- Celery Workers

---

## Example Deployment Structure

```yaml
apiVersion: apps/v1
kind: Deployment

metadata:
  name: medmatch-backend
  namespace: medmatch

spec:

  replicas: 2

  selector:
    matchLabels:
      app: medmatch-backend

  template:

    metadata:
      labels:
        app: medmatch-backend

    spec:

      containers:

      - name: backend

        image: medmatch/backend:latest

        ports:

        - containerPort: 8081
```

---

# 6. Kubernetes Services

Services provide internal communication between components.

Example:

```yaml
apiVersion: v1
kind: Service

metadata:
  name: backend-service
  namespace: medmatch

spec:

  selector:
    app: medmatch-backend

  ports:

  - port: 8081
    targetPort: 8081
```

---

# 7. Service Communication

Internal communication uses Kubernetes DNS.

Examples:

Backend to AI:

```
http://ai-service:8000
```

Backend to PostgreSQL:

```
postgres-service:5432
```

Backend to Redis:

```
redis-service:6379
```

---

# 8. ConfigMaps

Non-sensitive configuration uses ConfigMaps.

Examples:

```
DATABASE_HOST

DATABASE_NAME

REDIS_HOST

AI_SERVICE_URL

APPLICATION_PROFILE
```

Example:

```yaml
apiVersion: v1
kind: ConfigMap

metadata:
  name: medmatch-config
  namespace: medmatch

data:

  DATABASE_HOST:
    postgres-service

  REDIS_HOST:
    redis-service
```

---

# 9. Secrets

Sensitive values use Kubernetes Secrets.

Examples:

```
DATABASE_PASSWORD

JWT_PRIVATE_KEY

JWT_PUBLIC_KEY

OPENAI_API_KEY
```

Example:

```yaml
apiVersion: v1
kind: Secret

metadata:
  name: medmatch-secrets
  namespace: medmatch

type: Opaque

data:

  DATABASE_PASSWORD:
    <encoded-value>
```

---

# 10. Persistent Volumes

Stateful services require persistent storage.

Required components:

| Component | Storage |
|---|---|
| PostgreSQL | Persistent Volume |
| Redis | Persistent Volume |
| Trial Documents | Object Storage/Persistent Volume |

---

Example:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim

metadata:

  name: postgres-pvc

spec:

  accessModes:

  - ReadWriteOnce

  resources:

    requests:

      storage: 20Gi
```

---

# 11. Stateful Services

Stateful workloads:

- PostgreSQL
- Redis

Use:

```
StatefulSet
```

because they require:

- Stable identity
- Persistent storage
- Ordered deployment

---

# 12. Health Probes

Every application must define health checks.

---

## Liveness Probe

Determines if container should restart.

Example:

```yaml
livenessProbe:

  httpGet:

    path: /health

    port: 8081
```

---

## Readiness Probe

Determines if container receives traffic.

Example:

```yaml
readinessProbe:

  httpGet:

    path: /health

    port: 8081
```

---

# 13. Resource Management

Every container must define resources.

Example:

```yaml
resources:

  requests:

    cpu: "250m"

    memory: "512Mi"

  limits:

    cpu: "1"

    memory: "2Gi"
```

---

# 14. Horizontal Pod Autoscaler

HPA automatically scales services.

Example:

```yaml
apiVersion: autoscaling/v2

kind: HorizontalPodAutoscaler

metadata:

  name: backend-hpa

spec:

  minReplicas: 2

  maxReplicas: 10

  metrics:

  - type: Resource

    resource:

      name: cpu

      target:

        averageUtilization: 70
```

---

# 15. Rolling Updates

Deployments use rolling updates.

Benefits:

- Zero downtime
- Gradual replacement
- Easy rollback

Example:

```
Old Pods

↓

New Pods Created

↓

Health Check

↓

Traffic Shift

↓

Old Pods Removed
```

---

# 16. Environment Separation

Use separate namespaces:

```
medmatch-dev

medmatch-stage

medmatch-prod
```

Each environment has:

- Separate secrets
- Separate databases
- Separate configurations

---

# 17. Deployment Workflow

```
Code Commit

↓

CI Pipeline

↓

Docker Build

↓

Image Registry

↓

Kubernetes Deployment

↓

Health Checks

↓

Release
```

---

# 18. Security Requirements

Kubernetes deployment must enforce:

- Namespace isolation
- Secret protection
- Network policies
- RBAC permissions
- Container image scanning

---

# 19. Monitoring

Production clusters should monitor:

- Pod health
- CPU usage
- Memory usage
- Request latency
- Error rates
- Worker queues

---

# 20. Revision History

| Version | Date | Description |
|---|---|---|
| 1.0.0 | YYYY-MM-DD | Initial Kubernetes deployment guide |

---

# End of Document