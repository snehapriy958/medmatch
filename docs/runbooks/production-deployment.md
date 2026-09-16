okok# MedMatch Production Deployment Runbook

---

# 1. Document Information

| Field | Value |
|---|---|
| Document Name | MedMatch Production Deployment Runbook |
| Document ID | RUN-002 |
| Version | 1.0.0 |
| Status | Draft |
| Owner | MedMatch Engineering Team |
| Applies To | Production Environment |
| Last Updated | YYYY-MM-DD |

---

# 2. Purpose

This document defines the standard procedure for deploying MedMatch to production.

The goal is to ensure:

- Reliable releases
- Safe database changes
- Minimal downtime
- Deployment traceability
- Fast recovery from failures

---

# 3. Production Architecture

Production deployment consists of:

```
Users

↓

Ingress Controller

↓

Frontend Service

↓

Backend Service

↓

+--------------------+
|                    |
v                    v

AI Service        Database

|
v

Celery Workers

|
v

Redis Queue
```

---

# 4. Pre-Deployment Checklist

Before deployment verify:

## Code

- [ ] Changes merged to main branch
- [ ] Pull request approved
- [ ] CI pipeline successful
- [ ] Security scans passed

---

## Infrastructure

Verify:

- [ ] Kubernetes cluster available
- [ ] Namespace exists
- [ ] Required secrets configured
- [ ] Persistent storage available
- [ ] Container registry accessible

---

## Database

Verify:

- [ ] Database backup completed
- [ ] Migration scripts reviewed
- [ ] Database connectivity tested

---

# 5. Environment Configuration

Production configuration must be provided through:

- Kubernetes ConfigMaps
- Kubernetes Secrets

## Required tools

- `kubectl` (talks to the cluster)
- `kustomize` (recommended for validating changes before deploying;
  `kubectl apply -k` also works without it installed separately, since
  kubectl embeds its own kustomize)
- `docker` (only needed if rebuilding/pushing the `ai-service` image)

## Required namespace

`medmatch` (created by `infra/kubernetes/namespace.yaml`, referenced
by every other manifest).

## Cluster-context verification (do this before anything else)

Confirm `kubectl` is pointed at the cluster you actually intend to
deploy to - applying to the wrong cluster is not recoverable by this
runbook:

```bash
kubectl config current-context
kubectl cluster-info
kubectl get nodes
```

If unsure, switch explicitly rather than assuming:

```bash
kubectl config get-contexts
kubectl config use-context <intended-context-name>
```

## Required Secret keys

The Secret is named `medmatch-secrets`. These are the exact keys
actually referenced by name across every Deployment/Job/StatefulSet
in `infra/kubernetes/` (confirmed by grepping every `secretKeyRef` in
the repository, not assumed):

```
DATABASE_USERNAME
DATABASE_PASSWORD
DATABASE_URL        # single pre-composed connection string, used by
                     # ai-service, ai-migrate, and worker - do not
                     # split this into separate keys
LLM_API_KEY
JWT_PRIVATE_KEY      # auth-service only, mounted as a file (private.pem)
JWT_PUBLIC_KEY       # auth-service (file), ai-service and worker (env var)
```

## Safe Secret creation (never commit real values)

```bash
cp infra/kubernetes/secrets/secrets.yaml.example \
   infra/kubernetes/secrets/secrets.yaml
# then edit infra/kubernetes/secrets/secrets.yaml with real values
```

`infra/kubernetes/secrets/secrets.yaml.example` contains placeholders
only (`REPLACE_ME_...`) and is safe to commit - it is the only file in
that directory tracked by git. The real `secrets.yaml` is excluded by
`.gitignore` (`infra/kubernetes/secrets/secrets.yaml`) and must never
be committed, regardless of environment. **Never populate the
`.example` file in place and commit it** - always copy it first.

---

# 6. Container Image Verification

Before deployment, verify images. Real image references currently
used by `infra/kubernetes/`:

```
ghcr.io/snehapriy958/medmatch-auth-service:latest
ghcr.io/snehapriy958/medmatch-ai-service:phase2-migrations
ghcr.io/snehapriy958/medmatch-worker:latest
ghcr.io/snehapriy958/medmatch-frontend:latest
```

Rules:

- Use immutable/versioned tags where practical.
- Do not deploy unverified images.
- `ai-migrate` and `ai-service` must always reference the **identical**
  image tag - they run the same codebase (one runs
  `alembic upgrade head`, the other runs the app). Verify with:

  ```bash
  grep -h "image: ghcr.io/snehapriy958/medmatch-ai-service" \
    infra/kubernetes/ai-service/migrate-job.yaml \
    infra/kubernetes/ai-service/deployment.yaml
  ```

## Building and pushing the AI service image

```bash
# 1. Build (from the repository root)
docker build -f infra/docker/ai-service.Dockerfile \
  -t ghcr.io/snehapriy958/medmatch-ai-service:phase2-migrations .

# 2. Tag (only add :latest too if you specifically intend to move
#    that floating tag forward - see the tradeoff note below)
docker tag ghcr.io/snehapriy958/medmatch-ai-service:phase2-migrations \
  ghcr.io/snehapriy958/medmatch-ai-service:latest

# 3. Push
docker push ghcr.io/snehapriy958/medmatch-ai-service:phase2-migrations
# docker push ghcr.io/snehapriy958/medmatch-ai-service:latest   # optional, see below

# 4. The Kubernetes image reference is already updated in this repo
#    to :phase2-migrations (infra/kubernetes/ai-service/deployment.yaml
#    and migrate-job.yaml) - no manual edit needed unless you choose
#    a different tag.

# 5. Verify both references match (see grep command above).
```

**Tradeoff on `:latest`:** this repo's own image tag rules above say
"avoid using latest tags," so `:latest` is not pushed by default here.
If your deployment tooling elsewhere still expects `:latest` to exist
and be current, you must explicitly push it too (step 2/3, commented
out above) and accept that doing so silently changes what any
*other* deployment referencing `:latest` will pick up on its next
pull - prefer pointing everything at the versioned tag instead where
possible.

---

# 7. Database Migration

Database migrations run as one-shot Kubernetes Jobs, ordered before
application rollout - not as a manual SQL step:

```
auth-migrate (Flyway: roles, hospitals, users, audit_logs)
    ↓ (must complete successfully)
ai-migrate (Alembic: patients, trials, trial_criteria,
            criteria_embeddings, patient_notes,
            patient_note_embeddings, trial_embeddings)
    ↓ (must complete successfully)
Application Deployments restarted/promoted
```

`infra/scripts/deploy.sh` enforces this exact ordering, including
waiting for PostgreSQL readiness first and printing full Job/pod
status and logs if either migration fails - see Section 8.

Verify migrations after they run:

```bash
kubectl logs job/auth-migrate -n medmatch
kubectl logs job/ai-migrate -n medmatch

# Auth-service schema (Flyway's own bookkeeping table):
kubectl exec -it statefulset/postgres -n medmatch -- \
  psql -U postgres -d medmatch -c "SELECT * FROM flyway_schema_history;"

# AI-service schema (Alembic's own bookkeeping table):
kubectl exec -it statefulset/postgres -n medmatch -- \
  psql -U postgres -d medmatch -c "SELECT * FROM alembic_version;"
```

---

# 8. Kubernetes Deployment

## Storage-class review (required before any cloud deployment)

`infra/kubernetes/storage/storage-class.yaml` currently uses
`provisioner: rancher.io/local-path` - this only works on local/dev
clusters (Rancher Desktop, k3s, kind). It is **not** cloud-ready as
committed. Before deploying to a real cloud cluster, edit that file's
`provisioner:` to match your actual cluster (e.g. `ebs.csi.aws.com`
for EKS, `pd.csi.storage.gke.io` for GKE, `disk.csi.azure.com` for
AKS) - see the warning comment in that file for the full explanation.
Deploying to a local/dev cluster with the placeholder as-is is fine.

Validate before deploying:

```bash
kustomize build .          # from the repository root, NOT infra/kubernetes/
```

`infra/kubernetes/kustomization.yaml` is intentionally not a valid
build entry point by itself (see its header comment) - always build
and apply from the repository root.

## Optional: client-side dry run

Catches manifest/schema errors without touching the cluster:

```bash
kubectl apply --dry-run=client -k .
```

This does not validate against the live cluster's actual state
(existing resources, admission webhooks, RBAC) - only that the
rendered manifests are well-formed. Follow with a real apply (below)
to find anything a dry run can't catch.

Deploy:

```bash
./infra/scripts/deploy.sh
```

This single script performs, in order: applies the full manifest set
(`kubectl apply -k .`), waits for PostgreSQL readiness, deletes and
re-runs both migration Jobs, waits for each to report
`condition=complete` (printing Job status, pod status, and logs and
exiting non-zero if either fails), then restarts and waits for the
`auth-service`, `ai-service`, and `worker` Deployments to roll out
successfully. It requires `infra/kubernetes/secrets/secrets.yaml` to
already exist locally (see Section 5) and refuses to proceed
otherwise.

## Service rollout verification

```bash
kubectl get pods -n medmatch
kubectl rollout status deployment/auth-service -n medmatch
kubectl rollout status deployment/ai-service -n medmatch
kubectl rollout status deployment/worker -n medmatch
```

## Troubleshooting

```bash
# Migration Job failed:
kubectl describe job/auth-migrate -n medmatch   # or ai-migrate
kubectl logs -l job-name=auth-migrate -n medmatch --all-containers

# Application pod not starting:
kubectl describe pod -l app=medmatch,component=ai-service -n medmatch
kubectl logs -l app=medmatch,component=ai-service -n medmatch

# PostgreSQL not ready:
kubectl get pods -n medmatch -l component=postgres
kubectl logs statefulset/postgres -n medmatch
```

---

# 9. Deployment Verification

Check resources:

```bash
kubectl get pods -n medmatch
```

Expected:

```
Running
Ready
```

---

Check services:

```bash
kubectl get services -n medmatch
```

---

Check logs:

```bash
kubectl logs <pod-name>
```

---

# 10. Health Verification

Verify:

## Backend

```
GET /health
```

Expected:

```json
{
 "status":"UP"
}
```

---

## AI Service

```
GET /health
```

---

## Database

Verify:

- Connection successful
- Migrations completed

---

## Redis

Verify:

- Redis reachable
- Celery workers connected

---

# 11. Functional Verification

Test critical flows:

## Authentication

- Login
- JWT validation
- Role permissions

---

## Trial Workflow

- Upload protocol PDF
- Task created
- Worker processing
- Criteria extraction

---

## Matching Workflow

- Create matching request
- AI processing
- Retrieve result

---

# 12. Monitoring After Deployment

Monitor:

## Application

- Error rate
- Response latency
- Failed requests

---

## Infrastructure

- CPU usage
- Memory usage
- Pod restarts

---

## Background Processing

Monitor:

- Celery queue
- Failed tasks
- Worker availability

---

# 13. Rollback Procedure

Rollback when:

- Health checks fail
- Critical bugs appear
- Database migration fails
- Service unavailable

---

## Application Rollback

Using the actual Deployment names in this repository:

```bash
kubectl rollout undo deployment/auth-service -n medmatch
kubectl rollout undo deployment/ai-service -n medmatch
kubectl rollout undo deployment/worker -n medmatch
kubectl rollout undo deployment/frontend -n medmatch
```

---

## Database migration rollback (different from an app rollback)

Neither Flyway nor Alembic was run against a live cluster as part of
this work (see the final report's remaining blockers) - this section
documents the standard procedure, not a verified-safe path specific
to this repository's actual migration content.

Both migrations in this repo (V1-V4, 0001-0007) are additive-only
(`CREATE TABLE`/`CREATE INDEX`, no `DROP`/`ALTER ... DROP COLUMN`) -
confirmed by inspection, see the destructive-command scan in the
deployment report. This means an application-level rollback (above)
is almost always sufficient on its own: older application code
generally continues to work against a schema that only gained new
tables/columns. A full schema rollback (`alembic downgrade`, a Flyway
`undo` migration) should be a last resort, not a routine step, and
must never be run against data you cannot afford to lose - each
migration's `downgrade()`/undo path contains real `DROP TABLE`
statements (expected and correct for a rollback function, but
destructive if actually executed).

---

## Verify Rollback

```bash
kubectl rollout status deployment/auth-service -n medmatch
kubectl rollout status deployment/ai-service -n medmatch
kubectl rollout status deployment/worker -n medmatch
kubectl rollout status deployment/frontend -n medmatch
```

---

## Cleanup procedure

Remove completed migration Jobs once you've confirmed the deployment
succeeded (they are not needed again until the next deploy, and
`ttlSecondsAfterFinished: 3600` on both Jobs already cleans them up
automatically after an hour, but this removes them immediately if
you'd rather not wait):

```bash
kubectl delete job auth-migrate ai-migrate -n medmatch --ignore-not-found
```

To tear down the entire stack (e.g. decommissioning an environment -
**destructive**, do not run against an environment with data you need):

```bash
kubectl delete -k .
```

Note this does **not** delete the `medmatch-storage` StorageClass's
underlying data if `reclaimPolicy: Retain` is honored by your
cluster's provisioner (the default set in
`infra/kubernetes/storage/storage-class.yaml`) - the PersistentVolume
itself may need manual cleanup separately, by design, to avoid
silent data loss on a routine teardown.

---

# 14. Incident Response

During production incidents:

1. Identify affected service
2. Check logs
3. Stop harmful rollout
4. Rollback if required
5. Restore service
6. Document incident

---

# 15. Backup and Recovery

Production requires:

- Database backups
- Persistent volume backups
- Configuration backup
- Deployment history

---

# 16. Deployment Completion Checklist

After deployment:

- [ ] All pods healthy
- [ ] APIs responding
- [ ] Frontend accessible
- [ ] Database connected
- [ ] Redis healthy
- [ ] Celery workers running
- [ ] Monitoring active
- [ ] Release documented

---

# 17. Local Execution Guide

Everything below was written and structurally validated in a sandbox
that has neither Docker, `kubectl`, nor Maven-Central access - every
command here is unverified against a real Docker daemon or cluster
and is presented as the exact command to run, not as a claim that it
has already succeeded. Run these yourself and treat this guide as a
script to follow, not a report of what already happened.

## Safety checks - read before running anything

- **Always run from the repository root** (the directory containing
  this repo's own `kustomization.yaml`, not `infra/kubernetes/`).
  `infra/kubernetes/kustomization.yaml` is deliberately not a valid
  build entry point - see its own header comment.
- **Check `kubectl config current-context` before any apply.**
  Applying to the wrong cluster is not something this guide, or any
  guide, can undo for you.
- **Never commit `infra/kubernetes/secrets/secrets.yaml`.** It holds
  real credentials once you populate it and is `.gitignore`d for
  exactly that reason - `git status` should never show it as
  trackable; if it ever does, stop and check `.gitignore` before
  proceeding.
- **Never apply `secrets.yaml.example` directly.** It contains
  `REPLACE_ME_...` placeholders only and is not a valid Secret for
  anything beyond documenting the required keys.
- **Never run a migration downgrade command casually.** Both
  migration systems' downgrade/undo paths contain real `DROP TABLE`
  statements - see Section 13.
- **Confirm the image name and tag before building/pushing** -
  currently `ghcr.io/snehapriy958/medmatch-ai-service:phase2-migrations`
  in both `infra/kubernetes/ai-service/deployment.yaml` and
  `infra/kubernetes/ai-service/migrate-job.yaml`. If you use a
  different tag, update both files identically first.
- **Review the rendered manifest before applying it** - `kustomize
  build .` output is plain text; read it, especially the Secret
  block, before piping it anywhere.

## Step-by-step sequence

### 1. Verify repository root

**Linux/macOS/Git Bash/WSL:**
```bash
test -f kustomization.yaml && echo "OK: at repository root" || echo "WRONG DIRECTORY"
```
**Windows PowerShell:**
```powershell
if (Test-Path .\kustomization.yaml) { "OK: at repository root" } else { "WRONG DIRECTORY" }
```

### 2. Verify Kubernetes context

**All platforms (same command):**
```bash
kubectl config current-context
kubectl cluster-info
```
Stop here if this is not the cluster you intend to deploy to.

### 3. Verify Docker

**Linux/macOS/Git Bash/WSL:**
```bash
docker --version
docker info
```
**Windows PowerShell:**
```powershell
docker --version
docker info
```
(identical - Docker Desktop exposes the same CLI on Windows)

### 4. Build the AI-service image

**Linux/macOS/Git Bash/WSL/PowerShell (identical):**
```bash
docker build -f infra/docker/ai-service.Dockerfile -t ghcr.io/snehapriy958/medmatch-ai-service:phase2-migrations .
```
Run from the repository root - the build context is `.`, and the
Dockerfile's `COPY` paths (e.g. `services/ai-service/app`) are
relative to that root.

### 5. Log in to GHCR

**Linux/macOS/Git Bash/WSL:**
```bash
echo "$GHCR_TOKEN" | docker login ghcr.io -u <your-github-username> --password-stdin
```
**Windows PowerShell:**
```powershell
$env:GHCR_TOKEN | docker login ghcr.io -u <your-github-username> --password-stdin
```
Use a GitHub personal access token with `write:packages` scope, not
your account password. Never paste the token directly into the
command itself - both forms above read it from an environment
variable so it doesn't land in shell history.

### 6. Push the versioned image

**All platforms (identical):**
```bash
docker push ghcr.io/snehapriy958/medmatch-ai-service:phase2-migrations
```
Confirm step 4 built the tag you expect before pushing - pushing is
not easily undone once other systems may have pulled it.

### 7. Create the real Secret from the example

**Linux/macOS/Git Bash/WSL:**
```bash
cp infra/kubernetes/secrets/secrets.yaml.example infra/kubernetes/secrets/secrets.yaml
```
**Windows PowerShell:**
```powershell
Copy-Item infra\kubernetes\secrets\secrets.yaml.example infra\kubernetes\secrets\secrets.yaml
```

### 8. Edit the Secret safely

Open `infra/kubernetes/secrets/secrets.yaml` in your editor and
replace every `REPLACE_ME_...` placeholder with a real value
(`DATABASE_USERNAME`, `DATABASE_PASSWORD`, `DATABASE_URL`,
`LLM_API_KEY`, `JWT_PRIVATE_KEY`, `JWT_PUBLIC_KEY`). Do not use an
editor or IDE plugin that auto-syncs this file to a cloud
draft/history service. After editing, confirm it's still ignored:
```bash
git status --short infra/kubernetes/secrets/
```
This must show nothing for `secrets.yaml` itself (only
`secrets.yaml.example` should ever be trackable).

### 9. Run Kustomize validation

**All platforms (identical):**
```bash
kustomize build . > /tmp/medmatch-rendered.yaml
```
(On Windows PowerShell, redirect to a real path, e.g.
`kustomize build . > $env:TEMP\medmatch-rendered.yaml`.)
Read the output, at minimum the `Secret` block, before proceeding.

### 10. Run `kubectl apply --dry-run=client -k .`

**All platforms (identical):**
```bash
kubectl apply --dry-run=client -k .
```
This validates manifest structure client-side only - it does not
check against the live cluster's actual state or admission webhooks.

### 11. Run `infra/scripts/deploy.sh`

**Linux/macOS:**
```bash
./infra/scripts/deploy.sh
```
**Git Bash or WSL on Windows:**
```bash
bash infra/scripts/deploy.sh
```
**Windows PowerShell:** this script requires a POSIX shell (`set -euo
pipefail`, `[[`-independent but still bash syntax) - run it via Git
Bash or WSL as shown above, not directly in PowerShell.

### 12. Verify PostgreSQL and Redis

```bash
kubectl get pods -n medmatch -l component=postgres
kubectl get pods -n medmatch -l component=redis
```

### 13. Verify `auth-migrate` and `ai-migrate`

```bash
kubectl get jobs -n medmatch
kubectl logs job/auth-migrate -n medmatch
kubectl logs job/ai-migrate -n medmatch
```

### 14. Verify Deployments and Pods

```bash
kubectl get deployments -n medmatch
kubectl get pods -n medmatch
```

### 15. Verify Services and Ingress

```bash
kubectl get services -n medmatch
kubectl get ingress -n medmatch
```

### 16. Troubleshooting commands

```bash
kubectl describe pod <pod-name> -n medmatch
kubectl logs <pod-name> -n medmatch --previous
kubectl get events -n medmatch --sort-by='.lastTimestamp'
```

### 17. Rollback commands

```bash
kubectl rollout undo deployment/auth-service -n medmatch
kubectl rollout undo deployment/ai-service -n medmatch
kubectl rollout undo deployment/worker -n medmatch
kubectl rollout undo deployment/frontend -n medmatch
```
For database rollback, see Section 13's warning - do not run a
migration downgrade as a routine part of this sequence.

---

| Version | Date | Description |
|---|---|---|
| 1.0.0 | YYYY-MM-DD | Initial production deployment runbook |

---

---

# 18. Revision History

| Version | Date | Description |
|---|---|---|
| 1.0.0 | YYYY-MM-DD | Initial production deployment runbook |
| 1.1.0 | 2026-09 | Added real Secret keys, Kustomize root-build procedure, migration Job verification, Local Execution Guide, and safe validation script |

---

# End of Document