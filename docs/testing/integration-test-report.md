# Integration Test Report

## Environment

- Docker Compose
- PostgreSQL 17 + pgvector
- Redis 8
- Spring Boot Auth Service
- FastAPI AI Service
- Celery Worker
- Flower
- Prometheus
- Grafana

---

## Infrastructure Health

| Component | Result |
|-----------|--------|
| Auth Service | PASS |
| AI Service | PASS |
| PostgreSQL | PASS |
| Redis | PASS |
| Celery Worker | PASS |
| Flower | PASS |
| Prometheus | PASS |
| Grafana | PASS |

All services started successfully and passed their respective health checks.

Result: PASS


---

## Authentication Integration

### Scenario

Doctor authenticates using Spring Boot and invokes the AI matching endpoint using a JWT.

### Expected

- JWT generated successfully
- JWT validated by AI Service
- Doctor role authorized
- Hospital ID extracted from JWT
- Semantic search executed
- Matching results returned

### Result

PASS

Response Status: 200 OK

Verified Components

- Spring Security
- JWT Authentication
- JWT Verification
- RBAC
- Multi-tenancy
- Redis
- pgvector
- PostgreSQL


---

## Security Integration Tests

### Test 1

Scenario

Doctor attempted to access the ADMIN-only registration endpoint.

Expected

403 Forbidden

Actual

403 Forbidden

Result

PASS

---

### Test 2

Scenario

Researcher attempted to access the doctor-only eligibility endpoint.

Expected

403 Forbidden

Actual

403 Forbidden

Result

PASS

Verified RBAC restrictions were correctly enforced by both services.


## Multi-Tenant Validation

Implementation Status: PASS

Verified

- JWT contains hospital_id claim.
- Matching queries are filtered using hospital_id.
- Trial retrieval is tenant-aware.
- Repository enforces hospital isolation.

Runtime Validation

The current test environment contains a single hospital (DEFAULT).

Because no second tenant dataset exists, runtime cross-hospital isolation testing could not be performed.

The implementation supports multi-tenancy, but full validation requires multiple populated hospital datasets.