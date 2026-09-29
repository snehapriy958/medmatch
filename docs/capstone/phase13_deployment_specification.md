# Phase 13 — Production Deployment Specification

## 1. Overview & Objectives

This specification details the release engineering, deployment gating, migration sequencing, and rollback procedures required for zero-downtime continuous deployment of MedMatch on Kubernetes and Docker Compose.

---

## 2. Image Tagging & Release Immutability

### 2.1 Current Defects
- `ai-service/deployment.yaml` uses mutable development tag `ghcr.io/snehapriy958/medmatch-ai-service:phase2-migrations`.
- `auth-service/deployment.yaml`, `worker/deployment.yaml`, and `frontend/deployment.yaml` all reference `:latest`.
- **Consequence**: Deployments are non-deterministic, rollbacks cannot reliably pinpoint artifact revisions, and caching causes node drift.

### 2.2 Immutable Tagging Standard
- Every build in CI MUST produce images tagged with:
  1. Full Git Commit SHA: `ghcr.io/snehapriy958/medmatch-<service>:<git-sha>`
  2. Semantic Release Version: `ghcr.io/snehapriy958/medmatch-<service>:v1.0.0`
- Kubernetes manifests MUST use Kustomize image overrides (`kustomize edit set image`) during deployment rather than referencing mutable tags.

---

## 3. Two-Phase Migration Deployment Sequence

### 3.1 The Problem with Single-Pass Apply
- In `infra/scripts/deploy.sh`, `kubectl apply -k .` currently applies all resources (ConfigMaps, Secrets, StatefulSets, migration Jobs, and Deployments) simultaneously.
- If a migration adds a required column or table, application pods starting up concurrently fail validation or queries.
- If the migration Job fails, the Deployments have already been updated to the new image, resulting in a broken cluster state.

### 3.2 Two-Phase Gating Architecture

```
+--------------------------------------------------------------------------+
| PHASE 1: PRE-FLIGHT & SCHEMA MIGRATION                                   |
|                                                                          |
| 1. Apply ConfigMaps, Secrets, StatefulSets (Postgres, Redis)             |
| 2. Wait for PostgreSQL readiness (pg_isready condition=Ready)            |
| 3. Apply Flyway auth-migrate Job                                         |
| 4. Wait for auth-migrate Job condition=complete (timeout: 180s)          |
| 5. Apply Alembic ai-migrate Job                                          |
| 6. Wait for ai-migrate Job condition=complete (timeout: 180s)            |
|                                                                          |
| [GATE]: If ANY migration fails -> TRIGGER IMMEDIATE ROLLBACK & ABORT     |
+--------------------------------------------------------------------------+
                                    |
                                    v (Migrations Verified)
+--------------------------------------------------------------------------+
| PHASE 2: APPLICATION ROLLOUT                                             |
|                                                                          |
| 1. Apply auth-service Deployment (RollingUpdate, maxSurge 1, maxUnavail 0)|
| 2. Wait for auth-service rollout status                                  |
| 3. Apply ai-service Deployment (RollingUpdate, maxSurge 1, maxUnavail 0) |
| 4. Wait for ai-service startup probe and readiness probe completion      |
| 5. Apply worker Deployment (RollingUpdate)                               |
| 6. Apply frontend Deployment                                             |
| 7. Apply Ingress & NetworkPolicies                                       |
| 8. Execute post-deployment smoke verification tests                      |
+--------------------------------------------------------------------------+
```

---

## 4. Zero-Downtime Deployment Configuration

### 4.1 Deployment Strategy Updates
- Change `strategy.type: Recreate` in `ai-service/deployment.yaml` and `worker/deployment.yaml` to:
  ```yaml
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  ```
- Increase `replicas: 2` (minimum) for `ai-service` and `auth-service` to maintain continuous availability during rolling updates.
- Define `PodDisruptionBudget` for both core services:
  ```yaml
  apiVersion: policy/v1
  kind: PodDisruptionBudget
  metadata:
    name: ai-service-pdb
    namespace: medmatch
  spec:
    minAvailable: 1
    selector:
      matchLabels:
        component: ai-service
  ```

---

## 5. Kubernetes Ingress Architecture

### 5.1 Corrected Ingress Routing Specification
The current Ingress incorrectly routes all `/api` traffic to `auth-service`. The corrected Ingress configuration partitions API prefixes appropriately:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: medmatch-ingress
  namespace: medmatch
  annotations:
    kubernetes.io/ingress.class: "nginx"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "25m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "120"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "120"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - medmatch.internal
      secretName: medmatch-tls-secret
  rules:
    - host: medmatch.internal
      http:
        paths:
          # Spring Boot Auth Service Routes
          - path: /api/auth
            pathType: Prefix
            backend:
              service:
                name: auth-service
                port:
                  number: 8081

          # FastAPI AI Service Routes
          - path: /api/matching
            pathType: Prefix
            backend:
              service:
                name: ai-service
                port:
                  number: 8000

          - path: /api/patients
            pathType: Prefix
            backend:
              service:
                name: ai-service
                port:
                  number: 8000

          - path: /api/trials
            pathType: Prefix
            backend:
              service:
                name: ai-service
                port:
                  number: 8000

          - path: /api/tasks
            pathType: Prefix
            backend:
              service:
                name: ai-service
                port:
                  number: 8000

          # React SPA Frontend
          - path: /
            pathType: Prefix
            backend:
              service:
                name: frontend-service
                port:
                  number: 5173
```

---

## 6. Automated Rollback Protocol

When deployment validation fails at any stage:
1. **Migration Failure**:
   - Application Deployments are NOT modified.
   - Script triggers rollback migration (if safe) or reports exact revision and exits.
2. **Rollout Failure**:
   - Trigger automated rollback:
     ```bash
     kubectl rollout undo deployment/ai-service -n medmatch
     kubectl rollout undo deployment/auth-service -n medmatch
     ```
   - Re-verify previous revision health via readiness probes.
   - Send critical alert via Alertmanager / webhook.

---

## 7. Post-Deployment Verification (Smoke Tests)

Every deployment pipeline execution MUST conclude with automated smoke tests executing against the live ingress:
1. `GET /api/health/live` returns HTTP 200 on all services.
2. `GET /api/health/ready` returns HTTP 200 on `ai-service`.
3. `POST /api/auth/login` validates credentials against test hospital.
4. `POST /api/matching/search` executes semantic retrieval against test patient.
5. All smoke test assertions must pass within 60 seconds before deployment is marked complete.
