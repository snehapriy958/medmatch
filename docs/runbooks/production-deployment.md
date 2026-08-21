okok# MedMatch Production Deployment Runbook

---

# 1. Document Information

| Field | Value |
|---|---|
| Document Name | MedMatch Production Deployment Runbook |
| Document ID | RUN-002 |
| Version | 1.0.0 |
| Status | Draft |
| Owner | MedMatch Engineering Team |
| Applies To | Production Environment |
| Last Updated | YYYY-MM-DD |

---

# 2. Purpose

This document defines the standard procedure for deploying MedMatch to production.

The goal is to ensure:

- Reliable releases
- Safe database changes
- Minimal downtime
- Deployment traceability
- Fast recovery from failures

---

# 3. Production Architecture

Production deployment consists of:

```
Users

↓

Ingress Controller

↓

Frontend Service

↓

Backend Service

↓

+--------------------+
|                    |
v                    v

AI Service        Database

|
v

Celery Workers

|
v

Redis Queue
```

---

# 4. Pre-Deployment Checklist

Before deployment verify:

## Code

- [ ] Changes merged to main branch
- [ ] Pull request approved
- [ ] CI pipeline successful
- [ ] Security scans passed

---

## Infrastructure

Verify:

- [ ] Kubernetes cluster available
- [ ] Namespace exists
- [ ] Required secrets configured
- [ ] Persistent storage available
- [ ] Container registry accessible

---

## Database

Verify:

- [ ] Database backup completed
- [ ] Migration scripts reviewed
- [ ] Database connectivity tested

---

# 5. Environment Configuration

Production configuration must be provided through:

- Kubernetes ConfigMaps
- Kubernetes Secrets

Required configuration:

```
DATABASE_HOST

DATABASE_NAME

REDIS_HOST

JWT_PUBLIC_KEY

JWT_PRIVATE_KEY

AI_SERVICE_URL
```

---

# 6. Container Image Verification

Before deployment verify images:

Example:

```
medmatch-backend:v1.0.0

medmatch-ai:v1.0.0

medmatch-worker:v1.0.0

medmatch-ui:v1.0.0
```

Rules:

- Use immutable tags.
- Do not deploy unverified images.
- Avoid using latest tags.

---

# 7. Database Migration

Database migrations must execute before application rollout.

Process:

```
Backup Database

↓

Run Migration

↓

Validate Schema

↓

Deploy Application
```

Verify:

```sql
SELECT * FROM flyway_schema_history;
```

---

# 8. Kubernetes Deployment

Deploy resources in order:

## Step 1

Namespace:

```
kubectl apply -f namespace.yaml
```

---

## Step 2

Secrets:

```
kubectl apply -f secrets.yaml
```

---

## Step 3

ConfigMaps:

```
kubectl apply -f configmap.yaml
```

---

## Step 4

Database and Redis:

```
kubectl apply -f statefulsets/
```

---

## Step 5

Applications:

```
kubectl apply -f deployments/
```

---

## Step 6

Ingress:

```
kubectl apply -f ingress.yaml
```

---

# 9. Deployment Verification

Check resources:

```bash
kubectl get pods -n medmatch
```

Expected:

```
Running
Ready
```

---

Check services:

```bash
kubectl get services -n medmatch
```

---

Check logs:

```bash
kubectl logs <pod-name>
```

---

# 10. Health Verification

Verify:

## Backend

```
GET /health
```

Expected:

```json
{
 "status":"UP"
}
```

---

## AI Service

```
GET /health
```

---

## Database

Verify:

- Connection successful
- Migrations completed

---

## Redis

Verify:

- Redis reachable
- Celery workers connected

---

# 11. Functional Verification

Test critical flows:

## Authentication

- Login
- JWT validation
- Role permissions

---

## Trial Workflow

- Upload protocol PDF
- Task created
- Worker processing
- Criteria extraction

---

## Matching Workflow

- Create matching request
- AI processing
- Retrieve result

---

# 12. Monitoring After Deployment

Monitor:

## Application

- Error rate
- Response latency
- Failed requests

---

## Infrastructure

- CPU usage
- Memory usage
- Pod restarts

---

## Background Processing

Monitor:

- Celery queue
- Failed tasks
- Worker availability

---

# 13. Rollback Procedure

Rollback when:

- Health checks fail
- Critical bugs appear
- Database migration fails
- Service unavailable

---

## Application Rollback

Example:

```bash
kubectl rollout undo deployment/<deployment-name>
```

---

## Verify Rollback

Check:

```bash
kubectl rollout status deployment/<deployment-name>
```

---

# 14. Incident Response

During production incidents:

1. Identify affected service
2. Check logs
3. Stop harmful rollout
4. Rollback if required
5. Restore service
6. Document incident

---

# 15. Backup and Recovery

Production requires:

- Database backups
- Persistent volume backups
- Configuration backup
- Deployment history

---

# 16. Deployment Completion Checklist

After deployment:

- [ ] All pods healthy
- [ ] APIs responding
- [ ] Frontend accessible
- [ ] Database connected
- [ ] Redis healthy
- [ ] Celery workers running
- [ ] Monitoring active
- [ ] Release documented

---

# 17. Revision History

| Version | Date | Description |
|---|---|---|
| 1.0.0 | YYYY-MM-DD | Initial production deployment runbook |

---

# End of Document