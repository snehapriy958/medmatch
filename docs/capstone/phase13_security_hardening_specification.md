# Phase 13 — Security Hardening Specification

## 1. Executive Summary

This specification establishes remediation controls for vulnerabilities and misconfigurations identified during the repository audit, covering key management, Kubernetes network policies, container privileges, endpoint authorization, and logging hygiene.

---

## 2. Key Management & Secret Rotation

### 2.1 Remediation of Working-Tree RSA Private Key
- **Finding**: A 2048-bit RSA private key exists unencrypted in the local working tree at `services/auth-service/src/main/resources/keys/private.pem` and is duplicated in local `infra/kubernetes/secrets/secrets.yaml`. Repository audit verifies that these files are git-ignored and have never been committed to Git history.
- **Policy**:
  1. The unencrypted working-tree private key constitutes a **credential exposure risk requiring rotation/remediation** prior to production deployment.
  2. A new 4096-bit RSA key pair MUST be generated out-of-band:
     ```bash
     openssl genpkey -algorithm RSA -out private.pem -pkeyopt rsa_keygen_bits:4096
     openssl rsa -pubout -in private.pem -out public.pem
     ```
  3. The private key MUST NEVER be committed to Git or stored unencrypted in repository directories.
  4. In Kubernetes, the private key MUST be injected into `auth-service` via a SealedSecret or external KMS (e.g. HashiCorp Vault, AWS Secrets Manager, GCP Secret Manager).
  5. The public key is mounted into `ai-service` for offline RS256 token verification.

### 2.2 Google API Key Sanitization
- Real Google Gemini API keys present unencrypted in local working tree `.env` and `secrets.yaml` files represent a credential exposure risk requiring rotation/remediation in Google Cloud Console prior to production cutover.
- Ensure all `.env` and secret manifest files remain strictly git-ignored and only sanitized `.env.example` / `secrets.yaml.example` templates with explicit placeholders are tracked in version control.

---

## 3. Kubernetes NetworkPolicy Remediation

### 3.1 Network Traffic Requirements Matrix
| Source | Destination | Protocol / Port | Purpose | Current Status | Required Action |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Ingress Controller** | `frontend-service` | TCP / 5173 | Web UI HTTP | ALLOWED | Maintain |
| **Ingress Controller** | `auth-service` | TCP / 8081 | Auth REST API | ALLOWED | Maintain |
| **Frontend Pod** | `ai-service` | TCP / 8000 | Reverse-proxied AI API | **BLOCKED** | Add ingress rule in `ai-service-policy` |
| **ai-service Pod** | `postgres` | TCP / 5432 | Relational DB | ALLOWED | Maintain |
| **ai-service Pod** | `redis` | TCP / 6379 | Celery broker & cache | ALLOWED | Maintain |
| **ai-service Pod** | External (Internet) | TCP / 443 | Google Gemini API | **BLOCKED** | Add egress rule to CIDR `0.0.0.0/0` on port 443 |
| **worker Pod** | External (Internet) | TCP / 443 | Gemini / HuggingFace | **BLOCKED** | Add egress rule to CIDR `0.0.0.0/0` on port 443 |
| **worker Pod** | `postgres` | TCP / 5432 | Trial persistence | ALLOWED | Maintain |
| **worker Pod** | `redis` | TCP / 6379 | Celery broker | ALLOWED | Maintain |

### 3.2 Corrected NetworkPolicy Specification for `ai-service`
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: ai-service-policy
  namespace: medmatch
spec:
  podSelector:
    matchLabels:
      app: medmatch
      component: ai-service
  policyTypes:
    - Ingress
    - Egress
  ingress:
    # Allow calls from auth-service (internal service calls)
    - from:
        - podSelector:
            matchLabels:
              app: medmatch
              component: auth-service
      ports:
        - protocol: TCP
          port: 8000
    # Allow calls from frontend (Nginx reverse proxy)
    - from:
        - podSelector:
            matchLabels:
              app: medmatch
              component: frontend
      ports:
        - protocol: TCP
          port: 8000
  egress:
    # Internal DB
    - to:
        - podSelector:
            matchLabels:
              app: medmatch
              component: postgres
      ports:
        - protocol: TCP
          port: 5432
    # Internal Cache / Queue
    - to:
        - podSelector:
            matchLabels:
              app: medmatch
              component: redis
      ports:
        - protocol: TCP
          port: 6379
    # External HTTPS egress for Google Gemini LLM API
    - to:
        - ipBlock:
            cidr: 0.0.0.0/0
      ports:
        - protocol: TCP
          port: 443
```

---

## 4. Endpoint Authorization Hardening

### 4.1 Spring Boot Actuator Lockdown
- **Finding**: `SecurityConfig.java` permits unauthenticated access to `/actuator/**`.
- **Specification**:
  1. Only `/actuator/health` and `/actuator/info` may be unauthenticated (for Kubernetes probes).
  2. Sensitive management endpoints (`/actuator/prometheus`, `/actuator/metrics`, `/actuator/env`) MUST require role `SYSTEM_ADMIN` or be isolated to an internal management port (e.g. port 8082) not exposed via Ingress.
  3. `management.endpoint.health.show-details` MUST be set to `never` or `when_authorized` in `application-production.yml`.

### 4.2 Securing Task Polling Endpoint
- **Finding**: `GET /api/tasks/{task_id}` in `services/ai-service/app/api/routes/tasks.py` lacks authentication.
- **Specification**:
  ```python
  @router.get("/{task_id}")
  def get_task_status(
      task_id: str,
      current_user: Annotated[JWTClaims, Depends(get_current_user)],
      hospital_id: Annotated[UUID, Depends(get_current_hospital_id)],
  ) -> dict:
      result = AsyncResult(task_id)
      # Tenancy check: Celery task metadata must store hospital_id upon creation
      # and verify current_user belongs to that hospital.
      ...
  ```

---

## 5. Container & Infrastructure Privilege Hardening

1. **Eliminate Root InitContainer**:
   - In `infra/kubernetes/worker/deployment.yaml`, remove the `init-uploads` busybox container running as UID 0 with `chmod 777`.
   - Set correct volume ownership via pod `securityContext.fsGroup: 1000`.
2. **Read-Only Root Filesystem**:
   - Enforce `readOnlyRootFilesystem: true` across all application containers (`ai-service`, `auth-service`, `worker`).
   - Explicitly mount `emptyDir` volumes at `/tmp` and required application temporary write paths.
3. **Redis Authentication**:
   - Require password in `redis-statefulset.yaml` via `--requirepass $(REDIS_PASSWORD)`.
   - Update `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` to include `redis://:password@redis:6379/...`.

---

## 6. Information Leakage & Logging Hygiene

1. **Remove Debug Print Statements**:
   - Remove `print("\n========== TRIAL TRANSACTION DEBUG ==========")` from `trial_service.py` (lines 95–100).
   - Remove `print("AI SERVICE JWT USER =", current_user)` from `deps.py` (lines 96–104).
2. **Silence Hibernate Parameter Tracing**:
   - In `application-production.yml` and `application.yml`, set:
     ```yaml
     logging:
       level:
         org.hibernate.SQL: WARN
         org.hibernate.orm.jdbc.bind: WARN
     ```
