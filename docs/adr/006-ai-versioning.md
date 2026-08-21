# ADR-006: Store AI Model Version Metadata

## Status

Accepted

## Context

AI outputs must remain reproducible.

Models and prompts change over time.

---

## Decision

Store:

```json
{
 "modelVersion": "medmatch-v1",
 "embeddingModel": "all-MiniLM-L6-v2",
 "promptVersion": "eligibility-v1",
 "generatedAt": "timestamp"
}
```

with every AI result.

---

## Alternatives Considered

### Only Store Final Result

Rejected because:

- Cannot reproduce decisions
- Difficult auditing

---

## Consequences

Positive:

- Traceable AI decisions
- Easier debugging

Negative:

- Additional metadata storage

---

## References

- ai-governance.md
- openapi.md