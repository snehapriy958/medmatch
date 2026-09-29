# Phase 13.4: Storage & Volume Permissions Audit Report

**Checkpoint:** `31a9328` — *feat: complete phase 13.3 docker remediation*
**Branch:** `capstone/phase-13-production-engineering`
**Date:** September 2026
**Status:** AUDIT COMPLETE — IMPLEMENTATION PENDING

---

## 1. Executive Summary

This audit assesses the storage architecture, PersistentVolumeClaim (PVC) definitions, volume mounts, filesystem ownership, and security permissions across the MedMatch V2 platform. Specifically, it investigates the deferred Phase 13.3 finding **CONT-08 (Worker initContainer Root Permissions)** and analyzes the end-to-end data lifecycle of uploaded clinical trial PDFs exchanged between the **AI Service** (`ai-service`) and the **Celery Worker** (`worker`).

### Key Findings:
1. **Root Privilege Escalation Workaround (CONT-08):** In `infra/kubernetes/worker/deployment.yaml`, an unpinned `busybox` initContainer runs as root (`runAsUser: 0`) executing `mkdir -p /app/uploads && chmod 777 /app/uploads`. This was implemented because standard Kubernetes CSI drivers format and mount volume roots as `root:root (0755)`, which blocks non-root container user `fastapi` (`UID 1000`) from creating files.
2. **Asymmetric Volume Initialization Vulnerability:** The `init-uploads` container exists **only** in `worker/deployment.yaml`. It is completely absent from `ai-service/deployment.yaml`. However, `ai-service`'s readiness healthcheck (`/api/health/ready`) actively tests write permissions on `/app/uploads` upon boot. If `ai-service` initializes before `worker` on a fresh volume, `ai-service` fails readiness and cannot serve traffic.
3. **Critical Multi-Node / Multi-Attach Conflict:** `medmatch-uploads-pvc` declares `accessModes: [ReadWriteOnce]` (RWO). On standard cloud block storage (AWS EBS, GKE Persistent Disk, Azure Disk), RWO volumes can only be attached to **a single virtual machine node**. Because `ai-service` and `worker` are distinct Deployments, and `worker-hpa` autoscales workers up to 3 replicas, scheduling these pods across different cluster nodes will trigger Kubernetes `Multi-Attach error` and leave pods stuck in `ContainerCreating`.
4. **POSIX Coupling in Task Contract:** Celery tasks receive raw local filesystem path strings (e.g. `file_path="/app/uploads/<uuid>.pdf"`). Both `ai-service` (which writes the PDF and checks readiness) and `worker` (which reads and then unlinks the PDF) assume direct, POSIX-compliant, shared filesystem access.
5. **Docker Compose vs. Kubernetes Behavioral Divergence:** In Docker Compose, the named volume `uploads_data` automatically inherits UID/GID `1000:1000` from the image's pre-created `/app/uploads` directory. In Kubernetes, CSI volume mounts override directory ownership with `root:root`, necessitating explicit Kubernetes permission controls (`fsGroup`).

---

## 2. PVC & Storage Inventory

All Kubernetes storage manifests in `infra/kubernetes/` were inspected:

| Resource Name | Kind | Namespace | StorageClass | Access Mode | Requested Capacity | Mount Consumers | Mount Path | Mount Mode | Multi-Node Capable | Lifecycle Survival |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| `medmatch-uploads-pvc` | PersistentVolumeClaim | `medmatch` | `medmatch-storage` | **ReadWriteOnce (RWO)** | `5Gi` | `ai-service`<br>`worker` | `/app/uploads`<br>`/app/uploads` | ReadWrite<br>ReadWrite | **NO** (Blocked by RWO on block store) | Yes (`Retain`) |
| `postgres-data` | StatefulSet VolumeClaimTemplate | `medmatch` | Default / dynamically provisioned | ReadWriteOnce (RWO) | `10Gi` | `postgres-0` | `/var/lib/postgresql/data` | ReadWrite | Dedicated per replica | Yes (`Retain`) |
| `redis-data` | StatefulSet VolumeClaimTemplate | `medmatch` | Default / dynamically provisioned | ReadWriteOnce (RWO) | `5Gi` | `redis-0` | `/data` | ReadWrite | Dedicated per replica | Yes (`Retain`) |
| `flyway-sql` | ConfigMap Volume | `medmatch` | N/A | ReadOnly | N/A | `auth-migrate` | `/flyway/sql` | ReadOnly | Yes (ConfigMap) | Pod duration |
| `tmp` | emptyDir | `medmatch` | N/A | ReadWrite | RAM / Host Disk | `ai-service`<br>`worker` | `/tmp`<br>`/tmp` | ReadWrite | Ephemeral | Pod lifecycle only |

### StorageClass Analysis (`infra/kubernetes/storage/storage-class.yaml`)
- **Provisioner:** `rancher.io/local-path`
- **Reclaim Policy:** `Retain`
- **Volume Binding Mode:** `WaitForFirstConsumer`
- **Portability Notice:** The manifest explicitly documents that `rancher.io/local-path` is a local development provisioner (k3s / Rancher Desktop / kind) and will fail on managed cloud clusters (EKS, GKE, AKS) unless replaced with cloud CSI provisioners (`ebs.csi.aws.com`, `pd.csi.storage.gke.io`, etc.).

---

## 3. Uploads Storage & Data Lifecycle Flow

The complete file upload and processing pipeline was traced across the codebase:

```
[ Client / Browser ]
        |
        |  1. POST /api/trials/upload (multipart/form-data)
        v
[ ai-service (FastAPI) ]
  - Container Path: /app/uploads
  - Code: PDFService.save_pdf() in app/services/pdf_service.py
  - Writes: /app/uploads/<uuid>.pdf (UID 1000)
  - Validates: Extension, PDF magic number (%PDF-), size limit (20MB)
  - Also: Readiness probe tests write/delete of .readiness_check.tmp
        |
        |  2. Celery process_trial.delay(file_path=str(file_path), hospital_id=...)
        v
[ Redis Broker (redis:6379/0) ]
        |
        |  3. Dequeues message payload containing filesystem string
        v
[ celery-worker ]
  - Container Path: /app/uploads
  - Code: process_trial() in app/celery/tasks.py
  - Reads: pymupdf.open(file_path) -> extracts text & structures criteria
  - Writes/Deletes: _delete_uploaded_file(file_path) -> Path(file_path).unlink()
  - Deletes file on success, max retries exceeded, or unhandled exception
```

### Detailed Lifecycle Characteristics:

1. **Exact Filesystem Path:**
   - Configured in `app/config/settings.py` via `UPLOAD_DIR: str = Field(default="uploads")`.
   - Because the working directory is `/app` in both container images, relative path resolves to `/app/uploads`.
   - Manifests mount volumes at `/app/uploads`.
2. **Writer Container:**
   - `ai-service` writes the uploaded PDF via `PDFService.save_pdf()`.
   - `ai-service` also writes and unlinks `/app/uploads/.readiness_check.tmp` during Kubernetes readiness probing (`/api/health/ready`).
3. **Reader Container:**
   - `celery-worker` reads the file via `PDFService.extract_text(file_path)` using PyMuPDF.
4. **Mutual Write Requirement:**
   - **Both containers require write access.** `ai-service` must create files; `celery-worker` must delete files via `unlink()` after task completion.
5. **Post-Processing Deletion:**
   - Files are temporary. `_delete_uploaded_file()` unlinks the PDF immediately after trial criteria and embeddings are stored in PostgreSQL.
6. **Task Argument Format:**
   - Celery receives a raw string filesystem path (`/app/uploads/<uuid>.pdf`). It does not pass an object identifier, byte stream, or database ID.
7. **Path Sharing:**
   - The path must be identical and visible to both containers.
8. **Persistence Survival:**
   - With PVC storage, files survive individual container or pod restarts during task execution.
9. **POSIX Dependency:**
   - Application logic directly relies on standard POSIX filesystem semantics (`pathlib.Path`, `with open(..., 'wb')`, `pymupdf.open()`, `unlink()`, `mkdir()`).

---

## 4. CONT-08 Audit: Worker InitContainer Root Permissions

### Current Configuration (`infra/kubernetes/worker/deployment.yaml`)
```yaml
initContainers:
  - name: init-uploads
    image: busybox
    securityContext:
      runAsUser: 0
    command:
      - sh
      - -c
      - |
        mkdir -p /app/uploads
        chmod 777 /app/uploads
    volumeMounts:
      - name: uploads
        mountPath: /app/uploads
```

### Technical & Security Evaluation:
- **Image:** `busybox` (unpinned, pulls `:latest` from Docker Hub, introduces supply chain risk and rate limit failure).
- **UID / GID:** Explicitly runs as `UID 0`, `GID 0` (root).
- **SecurityContext:** Lacks `runAsNonRoot: true`, lacks `allowPrivilegeEscalation: false`, lacks `readOnlyRootFilesystem: true`, retains all root capabilities (`CAP_CHOWN`, `CAP_FOWNER`, `CAP_DAC_OVERRIDE`).
- **Permission Payload:** Applies `chmod 777 /app/uploads`. This makes the directory world-readable, world-writable, and world-executable by any process across shared containers.
- **Why Root Was Used:** When a PVC is formatted and mounted by a CSI driver, the filesystem root is owned by `root:root` with mode `0755`. Non-root processes (`fastapi` with `UID 1000`) cannot write to it. The previous developer introduced a root initContainer with `chmod 777` as an expedient workaround rather than configuring Kubernetes group ownership.
- **Is Root Actually Required?** **NO.** Root is completely unnecessary. Kubernetes provides the declarative, native `fsGroup` mechanism specifically designed to grant group ownership of mounted volumes to non-root pod users.

---

## 5. Evaluation of Permission Strategies

| Strategy | Description | Architecture Compatibility | Security Impact | Operational Complexity | Kubernetes Portability | Simultaneous Pod Support | Code Changes Required | Overall Viability |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| **A. Pod-level `fsGroup`** | Set `fsGroup: 1000` in pod `spec.securityContext` on both `ai-service` and `worker` | **100% Compatible.** Non-root `fastapi` user is already member of GID 1000 | **High Security.** Completely eliminates root initContainer. Enforces non-root execution | **Very Low.** Purely declarative YAML | **Universal.** Supported by all Kubernetes CSI drivers and cloud platforms | Yes, provided volume supports multi-attach | **None** | **RECOMMENDED (Phase 13.4)** |
| **B. Container `runAsUser` / `runAsGroup`** | Declare `runAsUser: 1000` & `runAsGroup: 1000` without `fsGroup` | Incompatible with fresh volumes | Good non-root posture, but non-functional | Low | High | Blocked | **None** | **REJECTED** (Fails on volume root `0755`) |
| **C. Scoped Root InitContainer** | Refactor initContainer to `chown 1000:1000` and `chmod 770` | Compatible | Still requires `runAsUser: 0`; violates Pod Security Standards (Restricted) | Medium (must duplicate in `ai-service`) | Blocked on security-hardened clusters | Yes (if shared node) | **None** | **REJECTED** (Unnecessary root exposure) |
| **D. StorageClass Mount Options** | Specify `mountOptions: [uid=1000, gid=1000]` in StorageClass | Incompatible with ext4/xfs block stores (EBS/GKE PD) | Good | High provider lock-in | Very Poor (only supported by CIFS/NFS) | Driver-dependent | **None** | **REJECTED** (Non-portable) |
| **E. Object Storage Migration** | Replace filesystem exchange with S3 / GCS / MinIO bucket API | Ideal target architecture, but requires code refactor | **Strong Isolation.** Zero shared volumes, IAM/IRSA auth | High initial setup (MinIO in local dev, S3 in prod) | **Maximum Portability.** Decouples compute from storage nodes | **Infinite.** Completely eliminates multi-attach | **Yes** (`PDFService`, endpoints, Celery tasks) | **RECOMMENDED (Post-Phase 13 Roadmap)** |

---

## 6. Access Mode & Multi-Node Multi-Attach Risk Analysis

### The ReadWriteOnce (RWO) Dilemma
`medmatch-uploads-pvc` is configured with:
```yaml
spec:
  accessModes:
    - ReadWriteOnce
```

In Kubernetes:
- `ReadWriteOnce` means the volume can be mounted as read-write by **nodes in the cluster**, specifically **only a single node at any given time**.
- `ai-service` is a Deployment with 1 replica.
- `worker` is a Deployment with 1 replica, governed by `worker-hpa` which scales up to 3 replicas (`infra/kubernetes/hpa.yaml`).

### Failure Scenarios:

```
                           +------------------------+
                           |  medmatch-uploads-pvc  |
                           |    (AccessMode: RWO)   |
                           +------------------------+
                                       |
                   +-------------------+-------------------+
                   | Attached to Node 1                    | Cannot Attach to Node 2!
                   v                                       v
         +-------------------+                   +-------------------+
         |      Node 1       |                   |      Node 2       |
         |-------------------|                   |-------------------|
         | [ai-service Pod]  |                   | [worker Pod]      |
         | (Mounts /uploads) |                   | (CrashLoop /      |
         |                   |                   |  ContainerCreating|
         |                   |                   |  Multi-Attach Err)|
         +-------------------+                   +-------------------+
```

1. **Multi-Node Cluster Scheduling:** If the Kubernetes scheduler places `ai-service` on Node 1 and `worker` on Node 2, the cloud CSI driver (AWS EBS, GKE PD, Azure Disk) attaches the block volume to Node 1. When Node 2 attempts attachment, the kubelet volume manager fails:
   ```
   Multi-Attach error for volume "pvc-...": Volume is already exclusively attached to one node and can't be attached to another
   ```
   The `worker` pod remains indefinitely in `ContainerCreating`.
2. **Worker Horizontal Autoscaling:** If Celery CPU load increases and `worker-hpa` scales worker replicas to 2 or 3, any worker scheduled on a different node will fail to attach the volume.
3. **Local Cluster Illusion:** In Rancher Desktop, k3s, and Docker Desktop, all pods run on a single virtual node. The `rancher.io/local-path` provisioner simply bind-mounts a host directory, masking the multi-attach defect during local testing.

### Remediation Paths for Multi-Attach:
- **Short-Term (Kubernetes Manifest Layer):** If retaining shared filesystem semantics, the production StorageClass and PVC must utilize a `ReadWriteMany` (RWX) provider:
  - AWS: Amazon EFS CSI (`efs.csi.aws.com`)
  - GCP: Cloud Filestore CSI (`filestore.csi.storage.gke.io`)
  - Azure: Azure Files CSI (`file.csi.azure.com`)
  - On-Prem / Local: NFS / CephFS / GlusterFS
- **Long-Term (Application Architecture Layer):** Eliminate shared filesystem mounts entirely by adopting Strategy E (Object Storage).

---

## 7. Docker Compose vs. Kubernetes Storage Semantics

| Dimension | Docker Compose (`docker-compose.yml`) | Kubernetes (`infra/kubernetes/`) | Impact of Difference |
|:---|:---|:---|:---|
| **Volume Type** | Named Volume (`uploads_data`) | PersistentVolumeClaim (`medmatch-uploads-pvc`) | Compose uses Docker engine volume driver; K8s uses CSI driver. |
| **Initial Permissions** | Automatically copies ownership from image (`1000:1000` via `chown -R fastapi:fastapi /app` in Dockerfile) | CSI driver mounts fresh filesystem as `root:root (0755)` | Compose works without workarounds; K8s fails without `fsGroup` or root initContainer. |
| **Multi-Container Sharing** | Both containers run on same Docker daemon host; shared access is native | Pods may run on different nodes; RWO blocks multi-node attachment | Compose masks the multi-node multi-attach defect present in Kubernetes. |
| **Root Workaround** | None needed | Uses root `busybox` initContainer (`init-uploads`) in worker | High-privilege container was introduced solely to compensate for K8s CSI behavior. |

---

## 8. Comprehensive Security Review of Pod SecurityContexts

An audit of all container and pod securityContexts across `infra/kubernetes/` reveals:

1. **`infra/kubernetes/worker/deployment.yaml`:**
   - **`init-uploads`:** `runAsUser: 0` (root), unpinned `busybox`, `chmod 777 /app/uploads`, no dropped capabilities, privilege escalation not blocked. **HIGH RISK.**
   - **`wait-for-ai-migrations`:** `runAsNonRoot: true`, `runAsUser: 1000`, `allowPrivilegeEscalation: false`, `capabilities: drop: [ALL]`. **CLEAN.**
   - **`medmatch-worker`:** `runAsNonRoot: true`, `runAsUser: 1000`, `allowPrivilegeEscalation: false`, `capabilities: drop: [ALL]`. **CLEAN.**
   - **Pod Spec:** Missing `fsGroup: 1000`.
2. **`infra/kubernetes/ai-service/deployment.yaml`:**
   - **`wait-for-ai-migrations`:** `runAsNonRoot: true`, `runAsUser: 1000`, `allowPrivilegeEscalation: false`, `capabilities: drop: [ALL]`. **CLEAN.**
   - **`ai-service`:** `runAsNonRoot: true`, `runAsUser: 1000`, `allowPrivilegeEscalation: false`, `capabilities: drop: [ALL]`. **CLEAN.**
   - **Pod Spec:** Missing `fsGroup: 1000`. Missing upload initContainer (relies entirely on worker).
3. **`infra/kubernetes/postgres/postgres-statefulset.yaml`:**
   - Pod Spec: `fsGroup: 999`. Container: `runAsUser: 999`, `runAsNonRoot: true`. **PROPERLY CONFIGURED.**
4. **`infra/kubernetes/redis/redis-statefulset.yaml`:**
   - Pod Spec: `fsGroup: 999`. Container: `runAsUser: 999`, `runAsNonRoot: true`. **PROPERLY CONFIGURED.**

---

## 9. Recommended Remediation Strategy & Implementation Plan

### Recommended Strategy for Phase 13.4:
Adopt **Strategy A (Pod-level `fsGroup: 1000`)** combined with **removing `init-uploads`**.

### Implementation Steps:
1. **Remove `init-uploads` InitContainer:**
   - Delete the `init-uploads` block from `infra/kubernetes/worker/deployment.yaml`.
2. **Apply `fsGroup: 1000` to Pod Specs:**
   - Add pod-level `securityContext` to `infra/kubernetes/worker/deployment.yaml`:
     ```yaml
     spec:
       securityContext:
         fsGroup: 1000
         fsGroupChangePolicy: "OnRootMismatch"
     ```
   - Add pod-level `securityContext` to `infra/kubernetes/ai-service/deployment.yaml`:
     ```yaml
     spec:
       securityContext:
         fsGroup: 1000
         fsGroupChangePolicy: "OnRootMismatch"
     ```
3. **Document Multi-Node RWX Storage Requirement:**
   - Update `infra/kubernetes/storage/uploads-pvc.yaml` and `storage-class.yaml` comments to explicitly note that for multi-node production deployment, the StorageClass must provide `ReadWriteMany` (RWX) backing (e.g., AWS EFS or NFS).
4. **Validation Plan:**
   - Validate manifests with `kubectl kustomize .` and `kubectl apply --dry-run=client -k .`.
   - Verify that all containers across `ai-service` and `worker` run as non-root (`runAsNonRoot: true`).
   - Confirm zero occurrences of `runAsUser: 0` in application deployments.

---

## 10. Audit Conclusions & Next Steps

Phase 13.4 audit has isolated the exact mechanics of CONT-08 and the storage architecture. Remediation can be executed safely without modifying application code or database schemas. All changes will be confined to Kubernetes deployment manifests.
