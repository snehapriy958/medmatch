<!-- # MedMatch Performance Baseline

## Test Environment

| Item | Value |
|------|-------|
| Platform | Windows + Docker Desktop |
| Deployment | Docker Compose |
| Spring Boot | Healthy |
| FastAPI | Healthy |
| PostgreSQL | Healthy |
| Redis | Healthy |
| Celery | Healthy |
| Flower | Healthy |
| Prometheus | Healthy |
| Grafana | Healthy |

---

# Authentication Load Test

## Scenario

- Endpoint: `POST /auth/login`
- Duration: 3 minutes
- Virtual Users: 50 (staged)
- Benchmark Tool: k6

## Results

| Metric | Value |
|--------|-------:|
| Total Requests | 2885 |
| Requests/sec | 15.94 |
| Average Latency | 74.53 ms |
| Median Latency | 72.60 ms |
| P90 | 85.92 ms |
| P95 | 89.31 ms |
| Maximum | 118.77 ms |
| Error Rate | 0.00% |

## Observations

- Authentication remained stable throughout the benchmark.
- No failed login requests were observed.
- Average latency remained below 100 ms.
- P95 latency remained below 100 ms.
- Maximum latency remained below 120 ms.
- No noticeable degradation occurred while ramping to 50 concurrent users.

---

# Dataset Used

| Entity | Count |
|---------|------:|
| Hospitals | 1 |
| Users | 4 |
| Trials | 2 |
| Trial Criteria | 41 |
| Criteria Embeddings | 41 |

---

# Baseline Conclusion

The authentication service demonstrated stable behavior under a staged load of up to **50 concurrent virtual users**, maintaining low response times and zero request failures. This benchmark establishes the baseline for subsequent performance evaluation of semantic search, eligibility evaluation, and asynchronous trial processing. -->


# Matching Search Performance

Dataset

- Trials: 2
- Trial Criteria: 41
- Embeddings: 41

Benchmark

- Duration: 3 minutes
- Virtual Users: 40
- Total Requests: 3096
- Throughput: 17.12 req/s

Latency

- Average: 33.32 ms
- Median: 11.81 ms
- P90: 24.68 ms
- P95: 30.63 ms
- Maximum: 23.71 s

Reliability

- HTTP Failure Rate: 0.00%
- Successful Requests: 100%