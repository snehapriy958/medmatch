# Authentication Load Test

## Environment

- Platform: Docker Compose (Local)
- Virtual Users: 50
- Duration: 3 minutes

## Results

| Metric | Value |
|---------|------:|
| Total Requests | 2885 |
| Requests/sec | 15.94 |
| Average | 74.53 ms |
| Median | 72.60 ms |
| P90 | 85.92 ms |
| P95 | 89.31 ms |
| Maximum | 118.77 ms |
| Error Rate | 0% |

## Observations

- Authentication remained stable throughout the benchmark.
- No failed requests were observed.
- Average latency remained below 100 ms.
- P95 latency remained below 100 ms.
- Maximum latency remained below 120 ms.
- No degradation was observed while ramping to 50 virtual users.