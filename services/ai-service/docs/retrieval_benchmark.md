# Retrieval Benchmark

## Embedding Model

sentence-transformers/all-MiniLM-L6-v2

---

## Vector Database

PostgreSQL + pgvector

---

## Similarity Metric

Cosine Distance

---

## Configuration

Top K = 5

Similarity Threshold = 0.75

---

## Benchmark Queries

| Query | Expected | Result |
|--------|----------|--------|
| Advanced NSCLC | NSCLC | PASS |
| ECOG 1 | ECOG | PASS |
| Checkpoint inhibitor | Previous checkpoint inhibitor | PASS |
| Cardiovascular disease | Cardiovascular disease | PASS |
| Autoimmune disease | Autoimmune disease | PASS |

---

## Accuracy

Top-1 Accuracy

100%

5 / 5 Queries

---

## Observations

- Clinical terminology retrieved accurately.
- ECOG criteria consistently ranked first.
- Cardiovascular exclusion criteria retrieved correctly.
- Autoimmune disease retrieved correctly.
- Vector similarity behaves consistently on the current dataset.

---

## Future Improvements

- Larger benchmark dataset.
- Recall@K.
- Precision@K.
- MRR.
- Cross-encoder reranking. 