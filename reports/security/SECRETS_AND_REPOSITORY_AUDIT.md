# MedMatch V2 — Secrets, Privacy & Repository Hygiene Audit

**Date:** November 17, 2026
**Auditor:** Automated DevSecOps Pipeline
**Repository:** `c:/Developers/Sneha/Projects/MEDMATCH_V2`

---

> [!IMPORTANT]
> **SYNTHETIC DATA VERIFICATION & PRIVACY AUDIT**
> This audit confirms that **zero real patient data, zero protected health information (PHI), and zero real production secrets** exist within the tracked Git commit history, configuration files, or demo datasets of the MedMatch V2 repository.

---

## 1. Git History Secret Audit (Gitleaks Scan)

### 1.1 Methodology
The complete Git commit history of the repository was audited using **Gitleaks v8.24.0** running against all 80 commits from the root commit to the latest HEAD (`21e46165a35220fec4167f46ac0bd2c3a5ee7542`):

```bash
docker run --rm -v "C:\Developers\Sneha\Projects\MEDMATCH_V2:/repo" \
  zricethezav/gitleaks:latest detect --source=/repo --config=/repo/.gitleaks.toml -v
```

### 1.2 Findings Analysis
The scan identified 5 historical matches, which were subjected to rigorous manual verification:

1. **`GOOGLE_API_KEY: test-synthetic-ci-key-12345`** (`.github/workflows/ci.yaml` line 97)
   - *Classification:* Synthetic CI Mock Key.
   - *Verification:* An intentionally fake string used to satisfy client initialization during headless test execution. It does not communicate with any Google Cloud billing account or live API.
2. **`mock_gemini_api_key = "test-synthetic-key-12345"`** (`services/ai-service/tests/test_llm_service.py`)
   - *Classification:* Unit Test Fixture.
   - *Verification:* Hardcoded mock string within a mock patch test. Never transmitted over the wire.
3. **`"Authorization: Bearer <uuid-sample-token>"`** (`docs/architecture/api-guidelines.md`)
   - *Classification:* Documentation Example.
   - *Verification:* Static placeholder UUID format for developers reading API markdown guidelines.
4. **`"replace(\"-----BEGIN PRIVATE KEY-----\", \"\")"`** (`services/auth-service/.../JwtService.java`)
   - *Classification:* Code Parser Logic.
   - *Verification:* String replacement method call used to strip header banners from PEM formatted keys loaded from files. Not a key.
5. **`"replace(\"-----END PRIVATE KEY-----\", \"\")"`** (`services/auth-service/.../PemUtils.java`)
   - *Classification:* Code Parser Logic.
   - *Verification:* String replacement method call used to strip footer banners from PEM formatted keys. Not a key.

### 1.3 Gitleaks Allowlist & Result
All 5 items are legitimate false positives. They were codified into [.gitleaks.toml](file:///c:/Developers/Sneha/Projects/MEDMATCH_V2/.gitleaks.toml).
- **Commits Scanned:** 80 commits (~8.77 MB).
- **Actual Leaks Detected:** **0**.
- **Exit Code:** `0`.

---

## 2. Working Tree & Untracked File Hygiene

### 2.1 Sensitive File Exclusion Verification
All sensitive file patterns were verified against `.gitignore` and `.git/info/exclude`:

| Sensitive Pattern | Expected Exclusion | Actual Status | Verification Method |
| :--- | :--- | :--- | :--- |
| **`.env` files** | Excluded | Excluded (`.env*` in `.gitignore`) | `git check-ignore -v .env` |
| **Private Keys (`private.pem`, `*.key`)** | Excluded | Excluded (`*.pem`, `*.key`) | `git check-ignore -v private.pem` |
| **Virtual Environments (`.venv/`, `venv/`)** | Excluded | Excluded (`.venv/`) | `git check-ignore -v services/ai-service/.venv` |
| **Node Modules (`node_modules/`)** | Excluded | Excluded (`node_modules/`) | `git check-ignore -v frontend/medmatch-ui/node_modules` |
| **Build Artifacts (`target/`, `dist/`)** | Excluded | Excluded (`target/`, `dist/`) | `git check-ignore -v services/auth-service/target` |
| **Model Weights & Cache (`.cache/`, `*.bin`)**| Excluded | Excluded (`.cache/`, `*.bin`) | `git check-ignore -v models/cache` |

### 2.2 Docker Build Context Isolation (`.dockerignore`)
Both `infra/docker/ai-service.Dockerfile` and `infra/docker/auth-service.Dockerfile` are shielded by comprehensive `.dockerignore` files preventing accidental staging of local secrets, `.git`, `.venv`, or temporary test dumps into container image layers.

---

## 3. Patient Data & Clinical Privacy (HIPAA / PHI Verification)

An exhaustive text search was conducted across all datasets, seed files, and fixtures:
- `data/demo/`
- `data/fixtures/`
- `research/`
- `evaluation/`

**Key Findings:**
1. **100% Synthetic Patient Records:** All patient profiles contain synthetically generated demographics (e.g., fictitious patient names like "Jane Doe-1234", "Synthetic Patient A", synthetic age/gender combinations).
2. **Open Registry Trials:** Clinical trials referenced in the database (e.g., NCT04280788, NCT03478891) are public information sourced directly from the U.S. National Library of Medicine (ClinicalTrials.gov) public API.
3. **Absence of Real PHI:** Zero names, social security numbers, medical record numbers (MRNs), hospital discharge summaries, or real diagnostic reports exist anywhere in the codebase.
4. **Regulatory Boundaries:** The repository and documentation consistently state that MedMatch V2 is a research and capstone evaluation system, not an active medical device or HIPAA-regulated production system.

---

## 4. Conclusion

The repository adheres to strict security hygiene: zero private keys, zero cloud API credentials, zero database passwords, and zero real patient records are committed or tracked in Git history.
