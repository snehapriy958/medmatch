# ADR-003: Use JWT RS256 Authentication

## Status

Accepted

## Context

MedMatch requires authentication across distributed services.

---

## Decision

Use JWT authentication with RS256 signing.

Private key:

- Signs tokens

Public key:

- Validates tokens

---

## Alternatives Considered

### Session Authentication

Rejected because:

- Harder for distributed services
- Requires shared session storage

---

## Consequences

Positive:

- Stateless authentication
- Secure service communication

Negative:

- Key management required

---

## References

- security-policy.md
- openapi.md