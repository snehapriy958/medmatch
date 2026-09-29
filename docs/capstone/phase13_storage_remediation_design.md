# Phase 13.4: Storage Remediation Design & Verification Report

**Checkpoint:** `31a9328` — *feat: complete phase 13.3 docker remediation*
**Branch:** `capstone/phase-13-production-engineering`
**Date:** September 2026
**Status:** DESIGN VERIFICATION COMPLETE — IMPLEMENTATION PENDING

---

## 1. Executive Summary

This report establishes the engineering design and pre-implementation verification for Phase 13.4 Storage & Volume Permissions remediation. It isolates two distinct issues discovered during the Phase 13.4 Storage Audit:

1. **CONT-08 (Security Vulnerability):** In [infra/kubernetes/worker/deployment.yaml](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/infra/kubernetes/worker/deployment.yaml), the `init-uploads` initContainer runs as root (`runAsUser: 0`) using unpinned `busybox` and executes `chmod 777 /app/uploads`. Furthermore, `init-uploads` is omitted from `ai-service/deployment.yaml`, leaving `ai-service`'s readiness probe vulnerable to permission failures on fresh volumes.
2. **ARCH-08 (Architectural Limitation):** [infra/kubernetes/storage/uploads-pvc.yaml](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/infra/kubernetes/storage/uploads-pvc.yaml) configures `medmatch-uploads-pvc` with `accessModes: [ReadWriteOnce]` (RWO). Both `ai-service` and `worker` Deployments mount `/app/uploads` with read/write requirements, and [infra/kubernetes/hpa.yaml](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/infra/kubernetes/hpa.yaml) autoscales `worker` up to 3 replicas. On multi-node cloud clusters using block storage, scheduling pods across different nodes causes `Multi-Attach error`.

This document evaluates the current Kubernetes target, verifies StorageClass capabilities, audits the HPA/scheduler interaction, rigorously compares three concrete storage architectures, verifies `fsGroup` behavior, and establishes the safe remediation scope for Phase 13.4.

---

## 2. Kubernetes Deployment Target Verification

Based strictly on repository evidence, the current Kubernetes target was determined:

| Evidence Source | Exact Repository Finding | Deployment Target Implication |
|:---|:---|:---|
| [infra/kubernetes/storage/storage-class.yaml](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/infra/kubernetes/storage/storage-class.yaml#L12-L36) | `provisioner: rancher.io/local-path # LOCAL/DEV ONLY`<br>Header comment: *"`provisioner: rancher.io/local-path` is the provisioner bundled with Rancher Desktop, k3s, and (as an addon) kind - it works out of the box ONLY on those local/dev cluster types. It does NOT exist on a real cloud cluster (EKS, GKE, AKS)..."* | Local/dev Kubernetes clusters (Rancher Desktop, k3s, kind). |
| [docs/runbooks/production-deployment.md](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/runbooks/production-deployment.md#L281-L290) | Section 8: *"`infra/kubernetes/storage/storage-class.yaml` currently uses `provisioner: rancher.io/local-path` - this only works on local/dev clusters (Rancher Desktop, k3s, kind). It is **not** cloud-ready as committed. Before deploying to a real cloud cluster, edit that file's `provisioner:` to match your actual cluster..."* | Manifests are intentionally configured for local development; cloud storage provisioners are documented as external requirements. |
| [infra/scripts/deploy.sh](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/infra/scripts/deploy.sh) | Enforces procedural ordering for Flyway/Alembic Jobs and applies rendered Kustomize manifests via `kubectl`. Contains no cloud-provider specific CLI commands. | Generic `kubectl` environment. |

**Conclusion:** The repository's committed Kubernetes storage configuration explicitly targets **local development clusters** (Rancher Desktop, k3s, kind). Cloud Kubernetes deployment targets (AWS EKS, GCP GKE, Azure AKS) are acknowledged as future deployment environments requiring manual or pipeline-driven provisioner substitution.

---

## 3. StorageClass & RWX Capability Verification

Inspection of [infra/kubernetes/storage/storage-class.yaml](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/infra/kubernetes/storage/storage-class.yaml) and [infra/kubernetes/storage/uploads-pvc.yaml](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/infra/kubernetes/storage/uploads-pvc.yaml):

1. **Intended Environment:** `medmatch-storage` is explicitly intended only for local development.
2. **RWX Support in `rancher.io/local-path`:** Local Path Provisioner provisions hostPath directories on a single node. It lacks distributed network filesystem synchronization across multiple physical/virtual nodes.
3. **Effect of Changing `accessModes: [ReadWriteMany]`:**
   - On local clusters with `local-path`, the provisioner may bind if pods run on the same node, but does not provide multi-node capability.
   - On cloud clusters (AWS, GCP, Azure), standard block storage CSI drivers (`ebs.csi.aws.com`, `pd.csi.storage.gke.io`, `disk.csi.azure.com`) **reject** `ReadWriteMany` PVC requests because block storage hardware cannot be mounted read-write by multiple instances simultaneously.
4. **Presence of RWX Provisioners:** The repository contains **zero** RWX-capable storage provisioners (no AWS EFS CSI, GCP Filestore, Azure Files, or in-cluster NFS server manifests).

---

## 4. Worker HPA & Shared PVC Scheduler Interaction

Inspection of [infra/kubernetes/hpa.yaml](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/infra/kubernetes/hpa.yaml), [infra/kubernetes/worker/deployment.yaml](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/infra/kubernetes/worker/deployment.yaml), and [infra/kubernetes/ai-service/deployment.yaml](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/infra/kubernetes/ai-service/deployment.yaml):

- **Worker Replicas:** `minReplicas: 1`, `maxReplicas: 3` (triggered by CPU > 80% or Memory > 150%).
- **AI Service Replicas:** `replicas: 1`.
- **Pod Affinity / Anti-Affinity:** **None defined.**
- **Node Affinity / NodeSelector:** **None defined.**
- **Topology Spread Constraints:** **None defined.**
- **Node Co-location Guarantee:** **Zero.** Nothing in the current manifests prevents kube-scheduler from scheduling `ai-service` on Node 1, `worker-replica-1` on Node 2, and `worker-replica-2` on Node 3 in a multi-node cluster.
- **Consequence:** In a multi-node cluster with block storage, any worker scheduled on a node different from `ai-service` will fail with `Multi-Attach error for volume "medmatch-uploads-pvc"`, keeping the pod in `ContainerCreating`.

---

## 5. Concrete Architecture Evaluation

Three concrete architectures were evaluated against the MedMatch repository:

### Architecture A: RWO + `fsGroup` + Scheduling Co-Location Constraint
- **Concept:** Maintain `ReadWriteOnce` on `medmatch-uploads-pvc`. Add `spec.securityContext.fsGroup: 1000` to both `ai-service` and `worker`. Add `spec.affinity.podAffinity` on `worker` to force all worker replicas onto the same node as `ai-service`.
- **Repository Changes:**
  - `infra/kubernetes/worker/deployment.yaml`: Delete `init-uploads`. Add `fsGroup: 1000`. Add `podAffinity` matching `app: medmatch, component: ai-service` with `topologyKey: kubernetes.io/hostname`.
  - `infra/kubernetes/ai-service/deployment.yaml`: Add `fsGroup: 1000`.
- **Application Code Changes:** None.
- **Storage-Provider Dependency:** Local-path or cloud block storage (EBS/PD/Disk).
- **Multi-Replica Behavior:** Worker can scale up to 3 replicas on the single shared node. If the node lacks CPU/memory, autoscaled pods fail with `PodFitsResources`.
- **Multi-Node Behavior:** Disabled. All upload consumers are pinned to a single cluster node.
- **Security Posture:** Clean. Eliminates root `init-uploads` container entirely.
- **Operational Complexity:** Low for single-node/dev; Medium in multi-node clusters.
- **Advantages:** Zero code changes; immediately fixes CONT-08; prevents multi-attach errors on multi-node clusters by forcing co-location.
- **Limitations:** Pinned node represents a single point of failure; limits vertical and horizontal scaling to node capacity.
- **Prerequisites:** A node with sufficient capacity for AI service + 3 worker pods.
- **Validity Conditions:** Valid for single-node development clusters and small-scale multi-node clusters where AI & worker are colocated on a dedicated heavy node.

---

### Architecture B: RWX Shared Network Filesystem + `fsGroup`
- **Concept:** Update `medmatch-uploads-pvc` to `ReadWriteMany` (RWX), backed by an enterprise network filesystem (AWS EFS, GCP Filestore, Azure Files, or NFS), with `fsGroup: 1000` on both Pod specs.
- **Repository Changes:**
  - `infra/kubernetes/storage/uploads-pvc.yaml`: Change `accessModes` to `ReadWriteMany`.
  - `infra/kubernetes/storage/storage-class.yaml`: Update provisioner to cloud RWX CSI (e.g. `efs.csi.aws.com`).
  - `infra/kubernetes/worker/deployment.yaml`: Delete `init-uploads`. Add `fsGroup: 1000`.
  - `infra/kubernetes/ai-service/deployment.yaml`: Add `fsGroup: 1000`.
- **Application Code Changes:** None. Code continues using `/app/uploads`.
- **Storage-Provider Dependency:** Managed network filesystem (AWS EFS, GCP Filestore, Azure Files, NFS).
- **Multi-Replica Behavior:** Fully supported across all worker replicas.
- **Multi-Node Behavior:** Fully supported across all cluster nodes and availability zones.
- **Security Posture:** Clean non-root execution via `fsGroup: 1000`.
- **Operational Complexity:** Medium-High. Requires provisioning cloud NFS infrastructure, security groups, mount targets, and IAM roles.
- **Advantages:** Zero application code changes; full multi-node distribution; full HPA scaling; fixes CONT-08.
- **Limitations:** Cannot run on local-path without an in-cluster NFS server; higher cloud storage costs than block/object storage.
- **Prerequisites:** Target cluster must have a functioning RWX CSI driver and provisioned network filesystem.
- **Validity Conditions:** Valid for production cloud deployments with managed NFS infrastructure.

---

### Architecture C: Object Storage (S3 / GCS / Azure Blob / MinIO)
- **Concept:** Decouple file exchange from POSIX filesystem mounts. `ai-service` streams uploaded PDFs to an S3/GCS bucket and passes `s3://bucket/key` to Celery. The worker downloads the object to `/tmp` (emptyDir), processes it, and deletes/archives the object.
- **Repository Changes:**
  - `services/ai-service/app/services/pdf_service.py`: Replace local disk write with object storage client.
  - `services/ai-service/app/celery/tasks.py`: Change `process_trial` to accept object URI, stream to `/tmp`, process, and delete.
  - `services/ai-service/app/api/routes/health.py`: Replace directory write check with bucket health check.
  - `services/ai-service/requirements.txt`: Add `boto3` or cloud storage SDK.
  - `infra/kubernetes/ai-service/deployment.yaml` & `worker/deployment.yaml`: Delete `uploads` PVC volume and volumeMounts; delete `init-uploads`.
  - `docker-compose.yml`: Add MinIO container for local parity.
- **Application Code Changes:** **SUBSTANTIAL.** Requires modifying `PDFService`, `trial.py`, `tasks.py`, `health.py`, settings, and unit tests.
- **Storage-Provider Dependency:** S3 / GCS / Azure Blob / MinIO.
- **Multi-Replica Behavior:** Flawless horizontal scaling.
- **Multi-Node Behavior:** Flawless multi-node and multi-region scaling.
- **Security Posture:** Strong isolation. Zero shared volumes, fine-grained IAM authentication, encryption at rest.
- **Operational Complexity:** Low long-term complexity; high upfront development and testing effort.
- **Advantages:** Cloud-native architecture; zero volume attach limits; lowest storage cost; complete decoupling.
- **Limitations:** Violates the Phase 13 boundary ("DO NOT MODIFY APPLICATION LOGIC"). Requires extensive regression testing.
- **Prerequisites:** S3/GCS bucket and IAM roles.
- **Validity Conditions:** Valid as a strategic post-Phase 13 architectural milestone.

---

## 6. Specific `fsGroup` Verification

### Technical Mechanics:
In Kubernetes, declaring `spec.securityContext.fsGroup: 1000` at the Pod level instructs kubelet to:
1. Change the group ownership of the volume root directory to GID 1000 (`chown :1000 /app/uploads`).
2. Grant group read, write, and execute permissions (`chmod g+rwx /app/uploads`).
3. Set the `setgid` bit on directories (`chmod g+s /app/uploads`), ensuring newly created files automatically inherit GID 1000.
4. Add GID 1000 to the supplemental groups of all containers in the Pod.

### Impact on MedMatch Services:
- `ai-service` runs as UID 1000, GID 1000 (`fastapi`). It can create, write, and read files in `/app/uploads`.
- `worker` runs as UID 1000, GID 1000 (`fastapi`). Because files created by `ai-service` have GID 1000 with group write/delete permissions, `worker` can read and delete (`unlink()`) files.
- **Elimination of Root:** This completely eliminates the need for:
  - Root `init-uploads` container (`runAsUser: 0` deleted)
  - Wide-open `chmod 777`
  - Privileged containers
  - Additional Linux capabilities (both workloads keep `capabilities: drop: [ALL]`)

### Compatibility with `rancher.io/local-path`:
- Kubelet handles `fsGroup` permissions natively for local volumes.
- Adding `fsGroupChangePolicy: "OnRootMismatch"` ensures kubelet only updates permissions if the root directory GID does not match 1000, avoiding startup latency on volumes with existing files.
- No documented behavior in `rancher.io/local-path` blocks or interferes with kubelet's native `fsGroup` processing.

---

## 7. Phase 13.4 Scope Determination

Based on repository evidence, the two options were evaluated:

- **Option 1:** Remediate CONT-08 permissions now (`fsGroup: 1000` on both workloads, delete `init-uploads`, add worker `podAffinity` co-location), and explicitly document ARCH-08 (RWO multi-node limitation) in architecture docs and runbooks.
- **Option 2:** Remediate CONT-08 AND change storage architecture in the same phase.

### Definitive Recommendation: **OPTION 1**

### Rationale:
1. **Repository Target Alignment:** The committed manifests explicitly declare `provisioner: rancher.io/local-path` for local development. Local development environments (Rancher Desktop, k3s, kind) run on a single node where RWO functions without multi-attach errors.
2. **Absence of Cloud RWX Provisioner:** The repository contains zero RWX storage classes. Introducing an unverified AWS EFS or Azure Files provisioner cannot be tested locally and would break existing k3s/Rancher Desktop deployments.
3. **Application Logic Integrity:** Migrating to Object Storage (Architecture C) requires rewriting `PDFService`, `trial.py`, `tasks.py`, `health.py`, and adding MinIO to Docker Compose, directly violating Phase 13 constraints.
4. **Immediate Risk Elimination:** Option 1 immediately eliminates the active security violation (`runAsUser: 0` and `chmod 777`) and resolves the latent `ai-service` startup dependency bug without architectural disruption.

---

## 8. Implementation Details & Architectural Bounds (Option 1)

1. **Remediation of CONT-08:**
   - In `infra/kubernetes/worker/deployment.yaml`, the root-based `init-uploads` container (`runAsUser: 0`, `chmod 777`) is completely removed.
   - Pod-level `securityContext.fsGroup: 1000` and `fsGroupChangePolicy: "OnRootMismatch"` are added to both `ai-service` and `worker` Deployments.
   - Both workloads run exclusively as non-root `UID 1000` with native filesystem group access.
2. **ARCH-08 Deliberate RWO Constraint:**
   - `medmatch-uploads-pvc` deliberately remains `accessModes: [ReadWriteOnce]` (RWO).
   - `storageClassName: medmatch-storage` (`rancher.io/local-path`) remains unchanged.
   - To prevent `Multi-Attach error` when `worker-hpa` scales worker replicas up to 3, `podAffinity` is added to `worker/deployment.yaml` requiring worker pods to land on the same node as `ai-service`:
     ```yaml
     affinity:
       podAffinity:
         requiredDuringSchedulingIgnoredDuringExecution:
           - labelSelector:
               matchLabels:
                 app: medmatch
                 component: ai-service
             topologyKey: kubernetes.io/hostname
     ```
3. **Architectural Bounds & Future Work:**
   - **Local Development Model:** This design supports the current local development deployment model (k3s, Rancher Desktop, kind).
   - **Scaling Limitation:** Worker replicas are constrained to the single node hosting `ai-service`. Total worker replica capacity is bound by the compute resources of that node.
   - **Future Multi-Node Cloud Storage:** Decoupling uploads across multi-node cloud clusters via a distributed RWX filesystem (AWS EFS / Azure Files) or migrating to an S3-compatible Object Storage service remains future architectural work outside the Phase 13 boundary.


---

## 9. Design Artifacts Summary

The design findings and machine-readable summaries are recorded in:
- [docs/capstone/phase13_storage_remediation_design.md](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/docs/capstone/phase13_storage_remediation_design.md)
- [results/phase13/storage_remediation_design_summary.json](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/results/phase13/storage_remediation_design_summary.json)
