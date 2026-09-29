# Phase 13 — Observability & Monitoring Specification

## 1. Overview & Objective

This specification details the observability architecture required to provide full visibility into MedMatch production operations, including metrics collection, Prometheus scrape configs, alerting rules, Grafana dashboards, and distributed tracing contracts.

---

## 2. Observability Architecture

```
+--------------------------------------------------------------------------+
|                            MEDMATCH CLUSTER                              |
|                                                                          |
|  +--------------------+         +-------------------+                    |
|  | auth-service:8081  |         | ai-service:8000   |                    |
|  | /actuator/prom     |         | /metrics          |                    |
|  +---------+----------+         +---------+---------+                    |
|            |                              |                              |
|            +--------------+---------------+                              |
|                           |                                              |
|                           v Scrapes                                      |
|               +-----------------------+                                  |
|               | Prometheus Server     |                                  |
|               +-----------+-----------+                                  |
|                           |                                              |
|            +--------------+--------------+                               |
|            | Alerts                      | Visualizes                    |
|            v                             v                               |
|  +-------------------+       +-----------------------+                   |
|  | Alertmanager      |       | Grafana 11.x          |                   |
|  | (Slack / Pager)   |       | Dashboards: System,   |                   |
|  +-------------------+       | AI, Celery, DB        |                   |
|                              +-----------------------+                   |
+--------------------------------------------------------------------------+
```

---

## 3. Prometheus Scrape Configuration

To replace the 0-byte `infra/monitoring/prometheus/prometheus.yaml`, the canonical scrape configuration is defined below:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  scrape_timeout: 10s

rule_files:
  - "/etc/prometheus/alerts.yaml"

alerting:
  alertmanagers:
    - static_configs:
        - targets: ["alertmanager:9093"]

scrape_configs:
  - job_name: "ai-service"
    metrics_path: "/metrics"
    static_configs:
      - targets: ["ai-service:8000"]
    relabel_configs:
      - target_label: component
        replacement: ai-service

  - job_name: "auth-service"
    metrics_path: "/actuator/prometheus"
    static_configs:
      - targets: ["auth-service:8081"]
    relabel_configs:
      - target_label: component
        replacement: auth-service

  - job_name: "postgres"
    static_configs:
      - targets: ["postgres-exporter:9187"]

  - job_name: "redis"
    static_configs:
      - targets: ["redis-exporter:9121"]
```

---

## 4. Production Metrics Catalog

### 4.1 Application & API Metrics
| Metric Name | Type | Labels | Description |
| :--- | :--- | :--- | :--- |
| `http_requests_total` | Counter | `method`, `handler`, `status` | Total HTTP requests processed. |
| `http_request_duration_seconds` | Histogram | `method`, `handler`, `status` | Request latency distribution. Buckets: `[0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]`. |
| `auth_failures_total` | Counter | `reason`, `hospital_id` | Authentication rejections and expired tokens. |
| `rate_limit_exceeded_total` | Counter | `client_ip`, `endpoint` | Requests rejected by SlowAPI rate limiter. |

### 4.2 AI & Clinical Reasoning Metrics
| Metric Name | Type | Labels | Description |
| :--- | :--- | :--- | :--- |
| `medmatch_ai_embedding_duration_seconds` | Histogram | `model`, `batch_size` | Embedding generation latency. Buckets: `[0.05, 0.1, 0.5, 1.0, 2.0, 5.0]`. |
| `medmatch_ai_retrieval_duration_seconds` | Histogram | `hospital_id`, `top_k` | pgvector cosine similarity search duration. |
| `medmatch_ai_llm_duration_seconds` | Histogram | `model`, `operation` | Gemini API roundtrip latency. Buckets: `[0.5, 1.0, 2.0, 5.0, 10.0, 30.0]`. |
| `medmatch_ai_llm_errors_total` | Counter | `error_type` | Failures classified by type (`TIMEOUT`, `RATE_LIMIT`, `EMPTY_RESPONSE`, `SERVER_ERROR`). |
| `medmatch_ai_circuit_breaker_state` | Gauge | `service` | 0=Closed (Normal), 1=Half-Open, 2=Open (Tripped). |

### 4.3 Celery & Asynchronous Pipeline Metrics
| Metric Name | Type | Labels | Description |
| :--- | :--- | :--- | :--- |
| `medmatch_celery_queue_depth` | Gauge | `queue_name` | Number of tasks waiting in Redis list. |
| `medmatch_celery_task_duration_seconds` | Histogram | `task_name` | Total execution time for `process_trial`. Buckets: `[5, 15, 30, 60, 120, 300]`. |
| `medmatch_celery_task_retries_total` | Counter | `task_name`, `exception` | Retry counts by trigger reason. |
| `medmatch_celery_tasks_failed_total` | Counter | `task_name` | Terminal task failures. |

---

## 5. Alerting Rules Specification

Canonical alert definitions for `infra/monitoring/prometheus/alerts.yaml`:

```yaml
groups:
  - name: medmatch-service-alerts
    rules:
      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.component }} is DOWN"
          description: "{{ $labels.instance }} has been unreachable for more than 1 minute."

      - alert: HighHttp5xxRate
        expr: sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) > 0.05
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High HTTP 5xx error rate (>5%)"
          description: "Service {{ $labels.component }} is returning elevated 5xx responses."

      - alert: LLMCircuitBreakerTripped
        expr: medmatch_ai_circuit_breaker_state > 0
        for: 30s
        labels:
          severity: warning
        annotations:
          summary: "LLM Circuit Breaker Tripped"
          description: "Gemini API failure rate exceeded threshold. System is operating in degraded fallback mode."

      - alert: CeleryQueueBacklog
        expr: medmatch_celery_queue_depth > 20
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Celery task backlog high (>20 tasks)"
          description: "Trial processing queue depth is growing; check worker health and concurrency."

      - alert: HighDatabaseConnectionPoolSaturation
        expr: pg_stat_activity_count / pg_settings_max_connections > 0.80
        for: 3m
        labels:
          severity: warning
        annotations:
          summary: "PostgreSQL connection pool near exhaustion (>80%)"
          description: "Connection pool is nearing capacity; risk of client timeouts."
```

---

## 6. Grafana Dashboard Blueprint

1. **System Operations Dashboard**:
   - HTTP request rates and 2xx/4xx/5xx status breakdown.
   - P50, P95, and P99 latency panels for `/api/matching/search` and `/api/trials`.
   - Node CPU and memory utilization.
2. **AI & Clinical Matching Dashboard**:
   - Embedding latency distribution.
   - pgvector retrieval query duration.
   - Gemini reasoning latency and token rate.
   - Cache hit ratios (Embedding cache, LLM response cache, retrieval cache).
3. **Async Pipeline Dashboard**:
   - Queue backlog counter.
   - Active worker count.
   - Trial PDF processing throughput and error rate.

---

## 7. Distributed Tracing & Correlation Contract

- Inbound requests MUST have their `X-Request-ID` or `X-Correlation-ID` header extracted in `RequestIDMiddleware`.
- If missing, generate a new UUIDv4.
- Injected into logging context: `[req_id=<uuid>] [tenant=<hospital_id>] [user=<user_id>]`.
- Propagated downstream to Celery tasks via `task.apply_async(headers={"correlation_id": req_id})`.
