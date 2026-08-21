# ADR-001: Use Microservice Architecture

## Status

Accepted

## Date

2026-08-08

---

## Context

MedMatch contains multiple independent workloads:

- Authentication
- Business APIs
- AI processing
- Background tasks

AI workloads require different scaling and technology choices compared to backend APIs.

---

## Decision

MedMatch will use a microservice architecture.

Services:

- Spring Boot Backend
- FastAPI AI Service
- React Frontend
- Celery Worker

---

## Alternatives Considered

### Monolithic Application

Rejected because:

- AI workloads cannot scale independently.
- Different technologies are required.
- Deployment becomes harder.

---

## Consequences

Positive:

- Independent scaling
- Clear service boundaries
- Easier maintenance

Negative:

- More deployment complexity
- Service communication required

---

## References

- backend-architecture.md
- system-overview.md