"""
Production Engineering Baseline Test Suite.

Classification: STATIC / CONFIGURATION VALIDATION.

NOTE: This test suite validates static configuration files, manifests,
and repository structures against production standards. Passing these tests
verifies baseline specification conformance, NOT live production runtime readiness.
"""

import os
import re
from pathlib import Path
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]


class TestDockerAndComposeBaselines:
    """
    Audit Dockerfile and Compose configurations against production standards.
    Classification: STATIC / CONFIGURATION VALIDATION.
    """

    def test_docker_compose_file_exists_and_parses(self):
        compose_path = REPO_ROOT / "docker-compose.yml"
        assert compose_path.exists(), "docker-compose.yml must exist at repo root"
        with open(compose_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert "services" in data, "docker-compose.yml must define services"
        services = data["services"]
        assert "postgres" in services
        assert "redis" in services
        assert "auth-service" in services
        assert "ai-service" in services
        assert "celery-worker" in services
        assert "frontend" in services

    def test_docker_compose_detects_missing_observability_services(self):
        """Verify that Prometheus, Grafana, and Alertmanager are currently absent from Compose."""
        compose_path = REPO_ROOT / "docker-compose.yml"
        with open(compose_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        services = data.get("services", {})
        assert "prometheus" not in services, "Prometheus is currently missing from docker-compose.yml"
        assert "grafana" not in services, "Grafana is currently missing from docker-compose.yml"
        assert "alertmanager" not in services, "Alertmanager is currently missing from docker-compose.yml"

    def test_docker_compose_ai_service_healthcheck_gap(self):
        """Verify that ai-service in docker-compose.yml currently lacks a healthcheck."""
        compose_path = REPO_ROOT / "docker-compose.yml"
        with open(compose_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        ai_service = data["services"]["ai-service"]
        assert "healthcheck" not in ai_service, "ai-service currently lacks healthcheck in docker-compose.yml"

    def test_docker_compose_external_postgres_volume_dependency(self):
        """Verify postgres_data external volume declaration."""
        compose_path = REPO_ROOT / "docker-compose.yml"
        with open(compose_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        volumes = data.get("volumes", {})
        assert "postgres_data" in volumes
        assert volumes["postgres_data"].get("external") is True, (
            "postgres_data requires pre-created external volume medmatch_postgres_data"
        )

    def test_dockerfiles_exist(self):
        docker_dir = REPO_ROOT / "infra" / "docker"
        expected_dockerfiles = [
            "ai-service.Dockerfile",
            "auth-service.Dockerfile",
            "frontend.Dockerfile",
            "worker.Dockerfile",
        ]
        for df in expected_dockerfiles:
            p = docker_dir / df
            assert p.exists() and p.stat().st_size > 0, f"{df} must exist and be non-empty"

    def test_dockerignore_gap(self):
        """Confirm that .dockerignore files are currently missing from repository."""
        root_dockerignore = REPO_ROOT / ".dockerignore"
        assert not root_dockerignore.exists(), "Root .dockerignore is currently missing"


class TestKubernetesManifestBaselines:
    """Audit Kubernetes manifests and Kustomize topology."""

    def test_root_kustomization_exists(self):
        kust_path = REPO_ROOT / "kustomization.yaml"
        assert kust_path.exists()
        with open(kust_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data.get("kind") == "Kustomization"
        assert "resources" in data

    def test_deprecated_k8s_kustomization_has_no_resources(self):
        deprecated_kust = REPO_ROOT / "infra" / "kubernetes" / "kustomization.yaml"
        assert deprecated_kust.exists()
        with open(deprecated_kust, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data is None or "resources" not in data, (
            "Deprecated infra/kubernetes/kustomization.yaml must not contain active resources"
        )

    def test_orphan_worker_manifest(self):
        """Identify empty orphan file in infra/k8s/."""
        orphan_worker = REPO_ROOT / "infra" / "k8s" / "worker-deployment.yaml"
        assert orphan_worker.exists()
        assert orphan_worker.stat().st_size == 0, "infra/k8s/worker-deployment.yaml is an empty 0-byte orphan"

    def test_uploads_pvc_access_mode_risk(self):
        """Verify uploads PVC uses ReadWriteOnce, presenting multi-node attachment risk."""
        pvc_path = REPO_ROOT / "infra" / "kubernetes" / "storage" / "uploads-pvc.yaml"
        assert pvc_path.exists()
        with open(pvc_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        access_modes = data["spec"]["accessModes"]
        assert "ReadWriteOnce" in access_modes, "uploads PVC currently uses ReadWriteOnce"

    def test_worker_deployment_root_init_container_risk(self):
        """Identify root user execution in worker initContainer."""
        worker_deploy = REPO_ROOT / "infra" / "kubernetes" / "worker" / "deployment.yaml"
        with open(worker_deploy, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        init_containers = data["spec"]["template"]["spec"].get("initContainers", [])
        assert len(init_containers) > 0
        init_uploads = init_containers[0]
        assert init_uploads["securityContext"]["runAsUser"] == 0, "worker initContainer runs as root (UID 0)"

    def test_worker_solo_pool_configuration(self):
        """Verify worker deployment configures solo pool."""
        worker_deploy = REPO_ROOT / "infra" / "kubernetes" / "worker" / "deployment.yaml"
        with open(worker_deploy, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        cmd = data["spec"]["template"]["spec"]["containers"][0]["command"]
        assert "--pool=solo" in cmd, "worker deployment currently configures Celery --pool=solo"


class TestDatabaseAndMigrationBaselines:
    """Audit PostgreSQL, Flyway, and Alembic migration state."""

    def test_alembic_single_head_in_ai_service(self):
        """Verify Alembic in services/ai-service resolves to single merge head 6f0604b23df6."""
        head_file = (
            REPO_ROOT
            / "services"
            / "ai-service"
            / "alembic"
            / "versions"
            / "6f0604b23df6_merge_schema_heads.py"
        )
        assert head_file.exists()
        with open(head_file, "r", encoding="utf-8") as f:
            content = f.read()
        assert "revision: str = '6f0604b23df6'" in content
        assert "0008" in content and "3f3884863f27" in content

    def test_root_alembic_disconnected_versions(self):
        """Identify orphan partial alembic/versions at repository root."""
        root_alembic = REPO_ROOT / "alembic" / "versions"
        assert root_alembic.exists()
        files = list(root_alembic.glob("*.py"))
        assert len(files) == 3, "Root alembic/versions contains 3 disconnected partial versions"
        assert not (REPO_ROOT / "alembic.ini").exists(), "Root lacks alembic.ini"

    def test_flyway_version_collision_hazard(self):
        """Identify duplicate version prefixes in auth-service Flyway migrations."""
        migration_dir = (
            REPO_ROOT
            / "services"
            / "auth-service"
            / "src"
            / "main"
            / "resources"
            / "db"
            / "migration"
        )
        assert migration_dir.exists()
        sql_files = [f.name for f in migration_dir.glob("*.sql")]

        version_prefixes = {}
        for fname in sql_files:
            match = re.match(r"^(V\d+)__", fname)
            if match:
                prefix = match.group(1)
                version_prefixes.setdefault(prefix, []).append(fname)

        collisions = {k: v for k, v in version_prefixes.items() if len(v) > 1}
        assert len(collisions) >= 4, f"Found Flyway version collisions: {collisions.keys()}"
        assert "V1" in collisions, "V1 has collisions (create_hospitals.sql vs create_roles_table.sql)"
        assert "V2" in collisions
        assert "V3" in collisions
        assert "V4" in collisions


class TestObservabilityAndScriptsBaselines:
    """Audit observability files and operational deployment scripts."""

    def test_prometheus_monitoring_configs_are_empty(self):
        prom_yaml = REPO_ROOT / "infra" / "monitoring" / "prometheus" / "prometheus.yaml"
        alerts_yaml = REPO_ROOT / "infra" / "monitoring" / "prometheus" / "alerts.yaml"
        am_yaml = REPO_ROOT / "infra" / "monitoring" / "alertmanager" / "alertmanager.yaml"

        assert prom_yaml.exists() and prom_yaml.stat().st_size == 0, "prometheus.yaml is 0 bytes"
        assert alerts_yaml.exists() and alerts_yaml.stat().st_size == 0, "alerts.yaml is 0 bytes"
        assert am_yaml.exists() and am_yaml.stat().st_size == 0, "alertmanager.yaml is 0 bytes"

    def test_operational_scripts_status(self):
        backup_sh = REPO_ROOT / "infra" / "scripts" / "backup.sh"
        health_sh = REPO_ROOT / "infra" / "scripts" / "health-check.sh"
        migrate_sh = REPO_ROOT / "infra" / "scripts" / "migrate.sh"
        deploy_sh = REPO_ROOT / "infra" / "scripts" / "deploy.sh"

        assert backup_sh.exists() and backup_sh.stat().st_size == 0, "backup.sh is 0 bytes"
        assert health_sh.exists() and health_sh.stat().st_size == 0, "health-check.sh is 0 bytes"
        assert migrate_sh.exists() and migrate_sh.stat().st_size == 0, "migrate.sh is 0 bytes"
        assert deploy_sh.exists() and deploy_sh.stat().st_size > 0, "deploy.sh is implemented"


class TestSecurityAndSecretsBaselines:
    """
    Audit security controls, authentication rules, and secret hygiene.
    Classification: STATIC / CONFIGURATION VALIDATION.
    """

    def test_unauthenticated_tasks_endpoint(self):
        """Verify /api/tasks/{task_id} lacks auth dependency (STATIC)."""
        tasks_route_file = REPO_ROOT / "services" / "ai-service" / "app" / "api" / "routes" / "tasks.py"
        assert tasks_route_file.exists()
        with open(tasks_route_file, "r", encoding="utf-8") as f:
            content = f.read()
        assert "get_current_user" not in content, "GET /api/tasks/{task_id} lacks authentication"
        assert "get_current_hospital_id" not in content, "GET /api/tasks/{task_id} lacks tenant isolation"

    def test_spring_security_actuator_permit_all(self):
        """Verify Spring SecurityConfig permits all on /actuator/** (STATIC)."""
        sec_config = (
            REPO_ROOT
            / "services"
            / "auth-service"
            / "src"
            / "main"
            / "java"
            / "com"
            / "medmatch"
            / "auth"
            / "security"
            / "SecurityConfig.java"
        )
        assert sec_config.exists()
        with open(sec_config, "r", encoding="utf-8") as f:
            content = f.read()
        assert '"/actuator/**"' in content, "SecurityConfig matches /actuator/**"
        assert ".permitAll()" in content, "SecurityConfig exposes /actuator/** via permitAll()"

    def test_working_tree_rsa_key_ignored_not_tracked(self):
        """
        Verify RSA private key exists in local working tree but is git-ignored
        and NOT tracked in Git index (STATIC / CONFIGURATION VALIDATION).
        """
        private_key = (
            REPO_ROOT
            / "services"
            / "auth-service"
            / "src"
            / "main"
            / "resources"
            / "keys"
            / "private.pem"
        )
        assert private_key.exists(), "RSA private key exists in working tree"
        assert private_key.stat().st_size > 0, "RSA private key is non-empty"
        
        # Verify it is ignored by .gitignore
        import subprocess
        result = subprocess.run(
            ["git", "check-ignore", "-q", str(private_key)],
            cwd=str(REPO_ROOT),
            capture_output=True
        )
        assert result.returncode == 0, "private.pem must be git-ignored"

