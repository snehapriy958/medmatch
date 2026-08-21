# ADR-005: Use Kubernetes for Deployment

## Status

Accepted

## Context

MedMatch contains multiple containers requiring:

- Scaling
- Service discovery
- Configuration management

---

## Decision

Deploy MedMatch using Kubernetes.

---

## Alternatives Considered

### Docker Compose Only

Rejected because:

- Not suitable for production scaling
- Limited orchestration

---

## Consequences

Positive:

- Automated deployment
- Scaling support
- Health management

Negative:

- Higher operational complexity

---

## References

- kubernetes-guide.md