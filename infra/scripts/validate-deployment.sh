#!/usr/bin/env bash
#
# infra/scripts/validate-deployment.sh
#
# READ-ONLY validation checklist. This script never modifies your
# cluster, your Docker registry, or any file in this repository.
# Specifically, it never runs:
#   - kubectl apply / kubectl delete / kubectl create
#   - docker push
#   - anything that writes to infra/kubernetes/secrets/secrets.yaml
#     or prints its contents
#
# Run from the repository root:
#   bash infra/scripts/validate-deployment.sh
#
# Every check reports exactly one of: PASS, FAIL, BLOCKED, REQUIRES APPROVAL
#
set -uo pipefail   # deliberately NOT -e: one failed check must not stop the rest

NAMESPACE="medmatch"
EXPECTED_IMAGE="ghcr.io/snehapriy958/medmatch-ai-service:phase2-migrations"
RESULTS=()

report() {
    # report <check-name> <STATUS> <detail>
    RESULTS+=("$2|$1|$3")
    printf "[%s] %s - %s\n" "$2" "$1" "$3"
}

echo "=== MedMatch deployment validation (read-only) ==="
echo

# -------------------------------------------------------------------
# 1. Repository root
# -------------------------------------------------------------------
if [ -f "kustomization.yaml" ]; then
    report "repository-root" "PASS" "kustomization.yaml found - running from repo root"
else
    report "repository-root" "FAIL" "kustomization.yaml not found - run this from the repository root"
fi

# -------------------------------------------------------------------
# 2. Required files exist
# -------------------------------------------------------------------
for f in \
    "infra/kubernetes/secrets/secrets.yaml.example" \
    "infra/kubernetes/auth-service/migrate-job.yaml" \
    "infra/kubernetes/ai-service/migrate-job.yaml" \
    "infra/scripts/deploy.sh" \
    "infra/docker/ai-service.Dockerfile"
do
    if [ -f "$f" ]; then
        report "file-exists:${f}" "PASS" "present"
    else
        report "file-exists:${f}" "FAIL" "missing"
    fi
done

# -------------------------------------------------------------------
# 3. Real Secret exists locally but stays out of git (never printed)
# -------------------------------------------------------------------
if [ -f "infra/kubernetes/secrets/secrets.yaml" ]; then
    if command -v git >/dev/null 2>&1 && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        if git check-ignore -q infra/kubernetes/secrets/secrets.yaml; then
            report "secret-exists-and-ignored" "PASS" "secrets.yaml exists locally and is git-ignored (contents not read by this script)"
        else
            report "secret-exists-and-ignored" "FAIL" "secrets.yaml exists but is NOT git-ignored - check .gitignore before committing anything"
        fi
    else
        report "secret-exists-and-ignored" "BLOCKED" "not a git repository - cannot confirm ignore status"
    fi
else
    report "secret-exists-and-ignored" "REQUIRES APPROVAL" "secrets.yaml does not exist yet - create it from secrets.yaml.example with real values before deploying (see runbook Section 17, step 7-8)"
fi

# Confirm the example is placeholder-only, without ever touching the real file
if [ -f "infra/kubernetes/secrets/secrets.yaml.example" ]; then
    if grep -q "REPLACE_ME" "infra/kubernetes/secrets/secrets.yaml.example"; then
        report "secret-example-is-placeholder" "PASS" "secrets.yaml.example contains only REPLACE_ME placeholders"
    else
        report "secret-example-is-placeholder" "FAIL" "secrets.yaml.example does not look like a placeholder template - inspect manually before trusting it"
    fi
else
    report "secret-example-is-placeholder" "FAIL" "secrets.yaml.example is missing"
fi

# -------------------------------------------------------------------
# 4. Kustomize validation (build only - never apply)
# -------------------------------------------------------------------
if command -v kustomize >/dev/null 2>&1; then
    if kustomize build . > /tmp/medmatch-validate-rendered.yaml 2>/tmp/medmatch-validate-err.log; then
        report "kustomize-build" "PASS" "kustomize build . succeeded, output at /tmp/medmatch-validate-rendered.yaml"
    else
        report "kustomize-build" "FAIL" "kustomize build . failed - see /tmp/medmatch-validate-err.log"
    fi
elif command -v kubectl >/dev/null 2>&1; then
    if kubectl kustomize . > /tmp/medmatch-validate-rendered.yaml 2>/tmp/medmatch-validate-err.log; then
        report "kustomize-build" "PASS" "kubectl kustomize . succeeded (kustomize binary not found, used kubectl's embedded version)"
    else
        report "kustomize-build" "FAIL" "kubectl kustomize . failed - see /tmp/medmatch-validate-err.log"
    fi
else
    report "kustomize-build" "BLOCKED" "neither kustomize nor kubectl found on PATH"
fi

# -------------------------------------------------------------------
# 5. Image tag consistency (only if the build above succeeded)
# -------------------------------------------------------------------
if [ -f /tmp/medmatch-validate-rendered.yaml ]; then
    image_count=$(grep -c "image: ${EXPECTED_IMAGE}" /tmp/medmatch-validate-rendered.yaml || true)
    if [ "${image_count}" -eq 2 ]; then
        report "image-tag-consistency" "PASS" "ai-service and ai-migrate both reference ${EXPECTED_IMAGE}"
    else
        report "image-tag-consistency" "FAIL" "expected exactly 2 references to ${EXPECTED_IMAGE}, found ${image_count} - check infra/kubernetes/ai-service/deployment.yaml and migrate-job.yaml"
    fi

    dupe_check=$(python3 - <<'PYEOF' 2>/dev/null || echo "PYTHON_UNAVAILABLE"
import yaml, sys
from collections import Counter
try:
    with open('/tmp/medmatch-validate-rendered.yaml') as f:
        docs = [d for d in yaml.safe_load_all(f) if d]
    ids = [(d['kind'], d['metadata']['name']) for d in docs]
    dupes = [k for k, v in Counter(ids).items() if v > 1]
    print("NONE" if not dupes else str(dupes))
except Exception as e:
    print(f"ERROR: {e}")
PYEOF
)
    if [ "${dupe_check}" = "NONE" ]; then
        report "no-duplicate-resources" "PASS" "no duplicate (kind, name) pairs in rendered output"
    elif [ "${dupe_check}" = "PYTHON_UNAVAILABLE" ]; then
        report "no-duplicate-resources" "BLOCKED" "python3/PyYAML not available to check for duplicates"
    else
        report "no-duplicate-resources" "FAIL" "duplicates found: ${dupe_check}"
    fi

    if grep -qiE "DROP |TRUNCATE|DELETE FROM|rm -rf" /tmp/medmatch-validate-rendered.yaml; then
        report "no-destructive-commands" "FAIL" "a destructive-looking command string was found in the rendered manifest - inspect manually"
    else
        report "no-destructive-commands" "PASS" "no DROP/TRUNCATE/DELETE FROM/rm -rf found in rendered output"
    fi
else
    report "image-tag-consistency" "BLOCKED" "kustomize build did not produce output to check"
    report "no-duplicate-resources" "BLOCKED" "kustomize build did not produce output to check"
    report "no-destructive-commands" "BLOCKED" "kustomize build did not produce output to check"
fi

# -------------------------------------------------------------------
# 6. Destructive-command scan of migration files themselves (upgrade paths only)
# -------------------------------------------------------------------
bad_upgrade=0
for f in $(find services/auth-service/src/main/resources/db/migration -name "*.sql" 2>/dev/null); do
    if grep -qiE "DROP |TRUNCATE|DELETE FROM" "$f"; then
        bad_upgrade=1
        echo "  !! destructive statement found in ${f}"
    fi
done
for f in $(find services/ai-service/alembic/versions -name "*.py" 2>/dev/null); do
    if awk '/def upgrade/{flag=1} /def downgrade/{flag=0} flag' "$f" | grep -qiE "drop_table|drop_index|drop_column"; then
        bad_upgrade=1
        echo "  !! destructive statement found in ${f}'s upgrade() function"
    fi
done
if [ "${bad_upgrade}" -eq 0 ]; then
    report "migration-upgrade-paths-clean" "PASS" "no destructive statements in any upgrade()/Flyway migration file"
else
    report "migration-upgrade-paths-clean" "FAIL" "destructive statement(s) found in an upgrade path - see output above"
fi

# -------------------------------------------------------------------
# 7. Shell syntax of deploy.sh
# -------------------------------------------------------------------
if command -v bash >/dev/null 2>&1 && [ -f "infra/scripts/deploy.sh" ]; then
    if bash -n infra/scripts/deploy.sh 2>/tmp/medmatch-validate-deploy-syntax.log; then
        report "deploy-sh-syntax" "PASS" "bash -n infra/scripts/deploy.sh succeeded"
    else
        report "deploy-sh-syntax" "FAIL" "syntax error - see /tmp/medmatch-validate-deploy-syntax.log"
    fi
else
    report "deploy-sh-syntax" "BLOCKED" "bash or deploy.sh not found"
fi

# -------------------------------------------------------------------
# 8. Docker availability (never builds or pushes)
# -------------------------------------------------------------------
if command -v docker >/dev/null 2>&1; then
    if docker info >/dev/null 2>&1; then
        report "docker-available" "PASS" "docker CLI present and daemon reachable (image was NOT built or pushed by this script)"
    else
        report "docker-available" "FAIL" "docker CLI present but daemon not reachable (is Docker Desktop running?)"
    fi
else
    report "docker-available" "BLOCKED" "docker not found on PATH"
fi

# -------------------------------------------------------------------
# 9. kubectl availability and context (never applies anything)
# -------------------------------------------------------------------
if command -v kubectl >/dev/null 2>&1; then
    ctx=$(kubectl config current-context 2>/dev/null || echo "")
    if [ -n "${ctx}" ]; then
        report "kubectl-context" "REQUIRES APPROVAL" "kubectl is configured for context '${ctx}' - confirm this is the intended cluster before running deploy.sh or any apply command (this script did NOT apply anything)"
    else
        report "kubectl-context" "FAIL" "kubectl found but no current-context set"
    fi
else
    report "kubectl-context" "BLOCKED" "kubectl not found on PATH"
fi

# -------------------------------------------------------------------
# 10. AI-service test suite (read-only, does not touch the cluster)
# -------------------------------------------------------------------
if command -v pytest >/dev/null 2>&1 || python3 -c "import pytest" >/dev/null 2>&1; then
    (cd services/ai-service && python3 -m pytest tests/ -q > /tmp/medmatch-validate-pytest.log 2>&1)
    pytest_rc=$?
    if [ "${pytest_rc}" -eq 0 ]; then
        report "ai-service-tests" "PASS" "pytest tests/ passed - see /tmp/medmatch-validate-pytest.log"
    else
        report "ai-service-tests" "FAIL" "pytest tests/ failed (exit ${pytest_rc}) - see /tmp/medmatch-validate-pytest.log (may also be BLOCKED if DATABASE_URL/GOOGLE_API_KEY env vars or dependencies are not set up in this shell)"
    fi
else
    report "ai-service-tests" "BLOCKED" "pytest not available in this environment"
fi

# -------------------------------------------------------------------
# Summary
# -------------------------------------------------------------------
echo
echo "=== Summary ==="
pass=0; fail=0; blocked=0; approval=0
for r in "${RESULTS[@]}"; do
    status="${r%%|*}"
    case "$status" in
        PASS) pass=$((pass+1)) ;;
        FAIL) fail=$((fail+1)) ;;
        BLOCKED) blocked=$((blocked+1)) ;;
        "REQUIRES APPROVAL") approval=$((approval+1)) ;;
    esac
done
echo "PASS: ${pass}  FAIL: ${fail}  BLOCKED: ${blocked}  REQUIRES APPROVAL: ${approval}"
echo
echo "This script performed NO cluster changes, NO image pushes, and did NOT print any secret value."
if [ "${fail}" -gt 0 ]; then
    exit 1
fi
exit 0
