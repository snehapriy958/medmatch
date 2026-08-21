# ADR-002: Use PostgreSQL with pgvector

## Status

Accepted

## Context

MedMatch requires:

- Relational healthcare data storage
- Semantic similarity search
- Clinical trial retrieval

---

## Decision

Use PostgreSQL with pgvector extension.

PostgreSQL stores:

- Users
- Hospitals
- Patients
- Trials

pgvector stores:

- Clinical embeddings
- Trial criteria embeddings

---

## Alternatives Considered

### Separate Vector Database

Rejected because:

- Additional infrastructure
- Higher operational complexity

---

## Consequences

Positive:

- Single database system
- Transaction consistency
- Simplified architecture

Negative:

- Requires vector indexing management

---

## References

- database-architecture.md