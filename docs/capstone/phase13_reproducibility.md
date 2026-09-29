# Phase 13 — Reproducibility & Audit Verification Guide

## 1. Overview

This document specifies the exact, step-by-step procedures to independently reproduce all findings, validations, and baseline tests conducted during the Phase 13 Production Engineering Audit.

---

## 2. Environment Prerequisites

- **Operating System**: Windows / Linux / macOS
- **Python**: 3.12+ (tested on Python 3.13 / 3.12)
- **Node.js**: 22+ (tested on v22)
- **Docker**: 27+ with Docker Compose v2.30+
- **Kubernetes Client (`kubectl`)**: v1.30+ (tested on v1.36.1 with embedded Kustomize v5.8.1)
- **Git**: 2.40+

---

## 3. Step-by-Step Reproduction Procedures

### Step 3.1: Verify Clean Working Tree & Checkpoint
Verify the branch is `capstone/phase-13-production-engineering` and HEAD matches `2b61977`:

```bash
git status
git log -n 5 --oneline
```
*Expected Output*: Head commit is `2b61977 feat: establish clinical safety foundation`.

---

### Step 3.2: Execute Production Engineering Baseline Tests
Run the automated production baseline verification test suite:

```bash
# Set PYTHONPATH and run pytest
python -m pytest tests/production_engineering/test_production_engineering_baseline.py -v
```
*Expected Output*:
`20 passed in 0.21s` (verifying Docker, Compose, Kubernetes, Flyway collision, Alembic head, observability gaps, and security baselines).

---

### Step 3.3: Execute AI Service Unit & Integration Tests
Run the production AI service test suite:

```bash
# Windows PowerShell
$env:PYTHONPATH="services/ai-service"; .\services\ai-service\.venv\Scripts\python.exe -m pytest services/ai-service/tests

# Linux / macOS
PYTHONPATH=services/ai-service pytest services/ai-service/tests
```
*Expected Output*:
`45 passed in ~73s` (verifies health routes, LLM service, match repository, filters, tenant isolation, and trial embeddings).
*Note*: Duration confirms the ~73-second cold-start initialization of `SentenceTransformer`.

---

### Step 3.4: Verify Frontend Build & Lint
Verify the React 19 + TypeScript + Vite frontend:

```bash
cd frontend/medmatch-ui
npm run lint
npm run build
```
*Expected Output*:
- `npm run lint`: Exits with code 0 (clean, no errors).
- `npm run build`: Generates production bundle in `dist/` in ~2.5 seconds.

---

### Step 3.5: Validate Kubernetes Kustomization
Verify that the root `kustomization.yaml` renders the complete production topology:

```bash
kubectl kustomize .
```
*Expected Output*:
Renders the full multi-document YAML stream containing Namespace, ConfigMaps, Secrets, PVCs, StatefulSets, migration Jobs, Deployments, ServiceMonitors, Ingress, and NetworkPolicies.

---

### Step 3.6: Validate Docker Compose Configuration
Verify Compose syntax and dependency graph:

```bash
docker compose config
```
*Expected Output*:
Renders valid Compose topology for the 8 services and flags the `medmatch_postgres_data` external volume requirement.

---

### Step 3.7: Verify Alembic Migration Head
Verify that the AI service Alembic configuration resolves to a single head:

```bash
# Windows PowerShell
$env:PYTHONPATH="services/ai-service"; .\services\ai-service\.venv\Scripts\python.exe -m alembic -c services/ai-service/alembic.ini heads

# Linux / macOS
PYTHONPATH=services/ai-service alembic -c services/ai-service/alembic.ini heads
```
*Expected Output*:
`6f0604b23df6 (head)`

---

## 4. Summary of Generated Artifacts

- Audit Summary Data: `results/phase13/audit_summary.json`
- Baseline Verification Test: `tests/production_engineering/test_production_engineering_baseline.py`
- All Capstone Audit Specifications: `docs/capstone/phase13_*.md`
