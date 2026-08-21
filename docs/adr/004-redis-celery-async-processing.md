# ADR-004: Use Redis and Celery for Async Processing

## Status

Accepted

## Context

Trial processing involves:

- PDF extraction
- Criteria extraction
- Embedding generation
- AI processing

These operations are long-running.

---

## Decision

Use:

Redis:
- Message broker
- Cache

Celery:
- Background task execution

---

## Alternatives Considered

### Synchronous Processing

Rejected because:

- Long response times
- Poor user experience

---

## Consequences

Positive:

- Non-blocking APIs
- Better scalability

Negative:

- Requires worker management

---

## References

- deployment-architecture.md