# MedMatch Alerting Rules

---

# 1. Document Information

| Field | Value |
|---|---|
| Document Name | MedMatch Alerting Rules |
| Document ID | ALERT-001 |
| Version | 1.0.0 |
| Status | Draft |
| Owner | MedMatch Engineering Team |
| Applies To | Production Monitoring |
| Last Updated | YYYY-MM-DD |

---

# 2. Purpose

This document defines alerting rules used to detect failures, performance degradation, and operational risks in the MedMatch platform.

Alerts help identify:

- Service failures
- Infrastructure problems
- Security issues
- AI pipeline failures
- Data processing problems

---

# 3. Alert Severity Levels

| Severity | Meaning | Response |
|---|---|---|
| Critical | Service unavailable or major impact | Immediate action |
| High | Significant degradation | Investigate quickly |
| Warning | Potential issue | Monitor and investigate |
| Info | Informational event | No immediate action |

---

# 4. Application Alerts

## ALERT-APP-001: Service Unavailable

| Field | Value |
|---|---|
| Severity | Critical |
| Condition | Service health check failing |
| Services | Backend, AI Service, Frontend |
| Threshold | Failed for 2 minutes |

Action:

- Check pod status
- Check application logs
- Restart or rollback if required

---

## ALERT-APP-002: High API Error Rate

| Field | Value |
|---|---|
| Severity | High |
| Condition | HTTP 5xx errors increase |
| Threshold | >5% requests for 5 minutes |

Action:

- Check backend logs
- Identify failing endpoint
- Investigate deployment changes

---

## ALERT-APP-003: High API Latency

| Field | Value |
|---|---|
| Severity | Warning |
| Condition | API response time increases |
| Threshold | P95 latency >2 seconds |

Action:

- Check database queries
- Check service load
- Review recent changes

---

# 5. Authentication Alerts

## ALERT-AUTH-001: Login Failure Spike

| Field | Value |
|---|---|
| Severity | High |
| Condition | Large number of failed logins |
| Threshold | Abnormal increase within 5 minutes |

Possible causes:

- Brute force attempt
- Incorrect deployment
- Authentication issue

Action:

- Review authentication logs
- Check suspicious activity

---

## ALERT-AUTH-002: JWT Validation Failures

| Field | Value |
|---|---|
| Severity | Warning |
| Condition | Increased invalid token errors |

Action:

- Verify key configuration
- Check token expiration issues

---

# 6. Database Alerts

## ALERT-DB-001: Database Unavailable

| Field | Value |
|---|---|
| Severity | Critical |
| Condition | PostgreSQL connection failure |

Action:

- Check database status
- Verify credentials
- Check network connectivity

---

## ALERT-DB-002: High Database Latency

| Field | Value |
|---|---|
| Severity | Warning |
| Condition | Slow database queries |

Monitor:

- Query latency
- Connection count
- CPU usage

---

## ALERT-DB-003: Storage Capacity Warning

| Field | Value |
|---|---|
| Severity | Warning |
| Condition | Persistent storage nearing capacity |

Action:

- Increase storage
- Remove unnecessary data
- Review retention policy

---

# 7. Redis Alerts

## ALERT-REDIS-001: Redis Unavailable

| Field | Value |
|---|---|
| Severity | Critical |
| Condition | Redis connection failure |

Impact:

- Background tasks affected
- Cache unavailable

Action:

- Verify Redis pod
- Check memory usage

---

## ALERT-REDIS-002: High Memory Usage

| Field | Value |
|---|---|
| Severity | Warning |
| Condition | Redis memory usage high |

Action:

- Review cache policy
- Increase resources

---

# 8. Celery Worker Alerts

## ALERT-WORKER-001: Worker Unavailable

| Field | Value |
|---|---|
| Severity | Critical |
| Condition | No active workers |

Impact:

- Trial processing stops
- Matching requests delayed

---

## ALERT-WORKER-002: Task Failure Rate High

| Field | Value |
|---|---|
| Severity | High |
| Condition | Background task failures increase |

Monitor:

- Failed tasks
- Error messages
- Worker logs

---

## ALERT-WORKER-003: Queue Backlog

| Field | Value |
|---|---|
| Severity | Warning |
| Condition | Queue size continuously increasing |

Possible causes:

- Worker shortage
- Slow AI processing
- Resource limitation

---

# 9. AI Service Alerts

## ALERT-AI-001: Matching Failure Rate High

| Field | Value |
|---|---|
| Severity | High |
| Condition | AI matching failures increase |

Check:

- Model availability
- Prompt failures
- Database retrieval
- Service logs

---

## ALERT-AI-002: Embedding Generation Failure

| Field | Value |
|---|---|
| Severity | High |
| Condition | Embedding generation failures |

Impact:

- Trial retrieval affected
- Matching accuracy affected

---

## ALERT-AI-003: AI Processing Latency

| Field | Value |
|---|---|
| Severity | Warning |
| Condition | Matching execution time increases |

Monitor:

- Retrieval latency
- LLM response time
- Worker processing time

---

# 10. Kubernetes Alerts

## ALERT-K8S-001: Pod Restart Loop

| Field | Value |
|---|---|
| Severity | High |
| Condition | Pod restarting repeatedly |

Action:

- Check container logs
- Check resource limits
- Review deployment

---

## ALERT-K8S-002: High Resource Usage

| Field | Value |
|---|---|
| Severity | Warning |
| Condition | CPU or memory exceeds limits |

Action:

- Scale deployment
- Increase resources

---

# 11. Security Alerts

## ALERT-SEC-001: Unauthorized Access Attempts

| Field | Value |
|---|---|
| Severity | High |
| Condition | Repeated permission failures |

Action:

- Review audit logs
- Investigate user activity

---

## ALERT-SEC-002: Secret Exposure Detection

| Field | Value |
|---|---|
| Severity | Critical |
| Condition | Credentials detected in repository |

Action:

- Rotate secrets
- Remove exposure
- Investigate access

---

# 12. Notification Channels

Alerts may be delivered through:

- Email
- Slack
- PagerDuty
- Cloud monitoring systems

---

# 13. Alert Handling Workflow

```
Alert Triggered

↓

Notification Sent

↓

Engineer Investigation

↓

Root Cause Identification

↓

Fix Applied

↓

Alert Resolved

↓

Incident Documented
```

---

# 14. Revision History

| Version | Date | Description |
|---|---|---|
| 1.0.0 | YYYY-MM-DD | Initial alerting rules |

---

# End of Document